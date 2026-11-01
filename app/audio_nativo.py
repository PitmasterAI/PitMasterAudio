
import os
import sys
import threading
import time

import numpy as np

def afinar_interprete():
    try:
        sys.setswitchinterval(0.001)
    except Exception:
        pass
    try:
        import gc as _gc
        _gc.freeze()
        _gc.set_threshold(80000, 800, 800)
    except Exception:
        pass

SR = 48000
CANALES = 2
BLOQUE = 2048
LATENCIA = 0.25
FUNDIDO = 480
PRESUPUESTO_MIN_MB = 700
PRESUPUESTO_MAX_MB = 2600

def _precargar_portaudio():
    import ctypes
    import ctypes.util
    aqui = os.path.dirname(os.path.abspath(__file__))
    arriba = os.path.dirname(os.path.dirname(aqui))
    candidatos = [os.environ.get('PORTAUDIO_LIB'), os.environ.get('PORTAAUDIO_LIB')]
    for carpeta in (os.path.join(arriba, 'lib'), os.path.join(os.path.dirname(arriba), 'lib'),
                    os.path.join(aqui, 'lib')):
        candidatos.append(os.path.join(carpeta, 'libportaudio.so.2'))
        candidatos.append(os.path.join(carpeta, 'libportaudio.so'))
    for ruta in candidatos:
        if not ruta or not os.path.exists(ruta):
            continue
        try:
            ctypes.CDLL(ruta, mode=ctypes.RTLD_GLOBAL)
        except Exception:
            continue
        original = ctypes.util.find_library
        if not getattr(original, '_pitmaster', False):
            def buscar(nombre, _ruta=ruta, _original=original):
                if 'portaudio' in str(nombre):
                    return _ruta
                return _original(nombre)
            buscar._pitmaster = True
            ctypes.util.find_library = buscar
        return ruta
    return None

_precargar_portaudio()

try:
    try:
        import sounddevice as sd
    except ImportError:

        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                        '_vendor'))
        import sounddevice as sd
except Exception:
    sd = None

try:
    import soundfile as sf
except Exception:
    sf = None

def _decodificar(ruta, frecuencia=SR):

    trozos = []
    with sf.SoundFile(ruta) as fichero:
        sr = fichero.samplerate
        while True:
            bloque = fichero.read(SR * 2, dtype='float32', always_2d=True)
            if len(bloque) == 0:
                break
            trozos.append(bloque)
            time.sleep(0.002)
    datos = np.concatenate(trozos) if trozos else np.zeros((0, 2), dtype='float32')
    if datos.shape[1] == 1:
        datos = np.repeat(datos, 2, axis=1)
    elif datos.shape[1] > 2:
        datos = datos[:, :2]
    if int(sr) != int(frecuencia):
        from scipy import signal
        from math import gcd
        factor = gcd(int(sr), int(frecuencia))
        datos = signal.resample_poly(datos, int(frecuencia) // factor, int(sr) // factor, axis=0)
    return np.ascontiguousarray(datos, dtype=np.float32)

class MotorAudio:

    def __init__(self):
        self._lk = threading.Lock()
        self._cache = {}
        self._orden = []
        self._cargando = set()
        self._clave = None
        self._fuente = None
        self._pos = 0
        self._sonando = False
        self._entrante = None
        self._fase = 0
        self._pendiente = None
        self._flujo = None
        self._error = ''
        self._desbordes = 0
        self._ultimo_desborde = 0
        self._bloque = BLOQUE
        self._sr = SR
        self._abrir()

    def _abrir(self):
        if sd is None or sf is None:
            self._error = 'sin portaudio'
            return

        dispositivo = self._dispositivo_salida()
        intentos = [dict(samplerate=SR, channels=CANALES, blocksize=self._bloque, latency=LATENCIA),
                    dict(samplerate=SR, channels=CANALES, blocksize=self._bloque * 2, latency=0.4),
                    dict(samplerate=SR, channels=CANALES, blocksize=self._bloque, latency='high'),
                    dict(channels=CANALES, blocksize=self._bloque * 2),
                    dict()]
        if dispositivo is not None:
            intentos = [dict(extra, device=dispositivo) for extra in intentos]
        for extra in intentos:
            try:
                self._flujo = sd.OutputStream(dtype='float32', callback=self._callback,
                                              **extra)
                self._flujo.start()
                self._sr = int(self._flujo.samplerate) or SR
                self._error = ''
                if not getattr(self, '_vigilando', False):
                    self._vigilando = True
                    threading.Thread(target=self._vigilar, daemon=True).start()
                return
            except Exception as e:
                self._error = str(e) or e.__class__.__name__
        self._flujo = None

    @staticmethod
    def _dispositivo_salida():
        try:
            if not sys.platform.startswith('win'):
                return None
            for api in sd.query_hostapis():
                if 'WASAPI' in str(api.get('name', '')).upper():
                    indice = api.get('default_output_device', -1)
                    if indice is not None and indice >= 0:
                        return int(indice)
        except Exception:
            pass
        return None

    def _vigilar(self):
        while True:
            time.sleep(2.0)
            actual = self._desbordes
            if actual <= self._ultimo_desborde + 30:
                continue
            self._ultimo_desborde = actual
            if self._bloque >= BLOQUE * 4:
                continue
            self._bloque *= 2
            try:
                flujo = self._flujo
                self._flujo = None
                flujo.stop()
                flujo.close()
            except Exception:
                pass
            self._abrir()

    def disponible(self):
        return self._flujo is not None

    @staticmethod
    def _leer(datos, pos, n):
        salida = np.empty((n, CANALES), dtype=np.float32)
        hecho = 0
        largo = len(datos)
        while hecho < n and largo:
            if pos >= largo:
                pos = 0
            trozo = min(n - hecho, largo - pos)
            salida[hecho:hecho + trozo] = datos[pos:pos + trozo]
            pos += trozo
            hecho += trozo
        if hecho < n:
            salida[hecho:] = 0.0
        return salida

    def _callback(self, salida, fotogramas, _momento, estado):
        if estado:
            self._desbordes += 1
        salida.fill(0.0)
        if not self._sonando or self._fuente is None:
            return
        fuente = self._fuente
        n = fotogramas
        base = self._pos
        salida[:] = self._leer(fuente, base, n)
        self._pos = (base + n) % max(1, len(fuente))
        ent = self._entrante
        if ent is not None and self._fase > 0:
            clave, datos, e0 = ent
            k = min(n, self._fase)
            nuevo = self._leer(datos, e0, k)
            t = np.linspace(0.0, 1.0, k, endpoint=False, dtype=np.float32)
            seco = np.cos(t * (np.pi / 2))[:, None]
            entra = np.sin(t * (np.pi / 2))[:, None]
            salida[:k] = salida[:k] * seco + nuevo * entra
            self._fase -= k
            e0 += k
            if self._fase <= 0:

                self._clave = clave
                self._fuente = datos
                self._entrante = None
            else:
                self._entrante = (clave, datos, e0)

    @staticmethod
    def _ram_libre_mb():
        try:
            if sys.platform.startswith('win'):
                import ctypes

                class Estado(ctypes.Structure):
                    _fields_ = [('dwLength', ctypes.c_ulong), ('dwMemoryLoad', ctypes.c_ulong),
                                ('ullTotalPhys', ctypes.c_ulonglong),
                                ('ullAvailPhys', ctypes.c_ulonglong),
                                ('ullTotalPageFile', ctypes.c_ulonglong),
                                ('ullAvailPageFile', ctypes.c_ulonglong),
                                ('ullTotalVirtual', ctypes.c_ulonglong),
                                ('ullAvailVirtual', ctypes.c_ulonglong),
                                ('ullAvailExtendedVirtual', ctypes.c_ulonglong)]

                estado = Estado()
                estado.dwLength = ctypes.sizeof(Estado)
                ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(estado))
                return int(estado.ullAvailPhys) // (1024 * 1024)
            with open('/proc/meminfo') as f:
                for linea in f:
                    if linea.startswith('MemAvailable:'):
                        return int(linea.split()[1]) // 1024
        except Exception:
            pass
        return None

    def _presupuesto_mb(self):
        libre = self._ram_libre_mb()
        if libre is None:
            return PRESUPUESTO_MIN_MB
        return int(max(PRESUPUESTO_MIN_MB, min(PRESUPUESTO_MAX_MB, libre * 0.45)))

    def _guardar(self, clave, datos):
        with self._lk:
            self._cache[clave] = datos
            if clave in self._orden:
                self._orden.remove(clave)
            self._orden.append(clave)
            presupuesto = self._presupuesto_mb() * 1024 * 1024
            en_ram = sum(getattr(v, 'nbytes', 0) for v in self._cache.values())
            otras = [c for c in self._orden if c not in (self._clave, clave)]
            while en_ram > presupuesto and otras:
                vieja = otras.pop(0)
                datos_viejos = self._cache.pop(vieja, None)
                en_ram -= getattr(datos_viejos, 'nbytes', 0)
                if vieja in self._orden:
                    self._orden.remove(vieja)

    def preparar(self, clave, ruta):
        return self.cargar(clave, ruta)

    def cargar(self, clave, ruta):
        if not self.disponible() or not ruta or not os.path.exists(ruta):
            return False
        with self._lk:
            if clave in self._cache or clave in self._cargando:
                return True
            self._cargando.add(clave)

        def trabajo():
            try:
                datos = _decodificar(ruta, self._sr)
                self._guardar(clave, datos)
            except Exception as e:
                self._error = 'no se pudo leer %s: %s' % (ruta, e)
            finally:
                with self._lk:
                    self._cargando.discard(clave)
                self._aplicar_pendiente()

        threading.Thread(target=trabajo, daemon=True).start()
        return True

    def lista(self, clave):
        with self._lk:
            return clave in self._cache

    def poner(self, clave, ruta, desde=None, sonar=True):
        self.cargar(clave, ruta)
        self._pendiente = {'accion': 'poner', 'clave': clave, 'desde': desde, 'sonar': sonar}
        self._aplicar_pendiente()
        return True

    def cambiar(self, clave, ruta, sonar=None):
        self.cargar(clave, ruta)
        self._pendiente = {'accion': 'cambiar', 'clave': clave, 'sonar': sonar}
        self._aplicar_pendiente()
        return True

    def _aplicar_pendiente(self):
        pendiente = self._pendiente
        if not pendiente:
            return
        clave = pendiente['clave']
        with self._lk:
            datos = self._cache.get(clave)
        if datos is None:
            if self.lista(clave) is False and self._cargando:
                return
            return
        self._pendiente = None
        if pendiente['accion'] == 'poner':
            with self._lk:
                self._clave = clave
                self._fuente = datos
                self._pos = int(max(0.0, float(pendiente['desde'] or 0)) * self._sr) % max(1, len(datos))
                self._entrante = None
                self._fase = 0
                if pendiente['sonar']:
                    self._sonando = True
            return

        with self._lk:
            queria_sonar = pendiente['sonar']
            if self._clave == clave and self._entrante is None:
                if queria_sonar:
                    self._sonando = True
                return
            self._entrante = (clave, datos, self._pos)
            self._fase = FUNDIDO
            if queria_sonar:
                self._sonando = True

    def pausar(self):
        with self._lk:
            self._sonando = False

    def seguir(self, desde=None):
        with self._lk:
            if desde is not None and self._fuente is not None:
                self._pos = int(max(0.0, float(desde)) * self._sr) % max(1, len(self._fuente))
            if self._fuente is not None:
                self._sonando = True

    def ir_a(self, segundos):
        with self._lk:
            if self._fuente is None:
                return
            self._pos = int(max(0.0, float(segundos)) * self._sr) % max(1, len(self._fuente))
            if self._entrante is not None:
                self._entrante = (self._entrante[0], self._entrante[1], self._pos)

    def parar(self):
        with self._lk:
            self._sonando = False
            self._pos = 0
            self._entrante = None
            self._fase = 0

    def soltar(self, conservar=None):
        with self._lk:
            for clave in list(self._cache):
                if clave == self._clave or (conservar and str(clave).startswith(conservar)):
                    continue
                self._cache.pop(clave, None)
                if clave in self._orden:
                    self._orden.remove(clave)
            if self._clave and conservar and not str(self._clave).startswith(conservar):
                self._fuente = None
                self._clave = None
                self._sonando = False
                self._pos = 0
                self._entrante = None
                self._fase = 0

    def estado(self):
        with self._lk:
            fuente = self._fuente
            largo = (len(fuente) / float(self._sr)) if fuente is not None else 0.0
            return {
                'disponible': self.disponible(),
                'sonando': bool(self._sonando),
                'clave': self._clave,
                'pos': round(self._pos / float(self._sr), 3),
                'dur': round(largo, 3),
                'listas': list(self._cache.keys()),
                'error': self._error,
                'sr': self._sr,
                'desbordes': self._desbordes,
            }

MOTOR = None

def motor():
    global MOTOR
    if MOTOR is None:
        MOTOR = MotorAudio()
    return MOTOR

ACCIONES = ('poner', 'cambiar', 'preparar', 'pausa', 'seguir', 'ir', 'parar', 'soltar')

def servir(puerto, padre=None):
    import json
    import socket
    motor()

    def padre_vivo(pid):
        if sys.platform.startswith('win'):
            try:
                import ctypes
                SYNCHRONIZE = 0x00100000
                manejador = ctypes.windll.kernel32.OpenProcess(SYNCHRONIZE, False, int(pid))
                if not manejador:
                    return False
                vivo = ctypes.windll.kernel32.WaitForSingleObject(manejador, 0) != 0
                ctypes.windll.kernel32.CloseHandle(manejador)
                return vivo
            except Exception:
                return True
        return os.getppid() == pid

    def vigilar_padre():
        while True:
            time.sleep(1.0)
            if padre and not padre_vivo(padre):
                os._exit(0)

    def atender(conexion):
        try:
            with conexion:
                f = conexion.makefile('rwb')
                linea = f.readline()
                if not linea:
                    return
                datos = json.loads(linea.decode('utf-8'))
                accion = datos.get('accion', 'estado')
                m = motor()
                if accion == 'poner':
                    m.poner(datos.get('clave'), datos.get('ruta'),
                            desde=datos.get('desde'), sonar=datos.get('sonar', True))
                elif accion == 'cambiar':
                    m.cambiar(datos.get('clave'), datos.get('ruta'), sonar=datos.get('sonar'))
                elif accion == 'preparar':
                    m.preparar(datos.get('clave'), datos.get('ruta'))
                elif accion == 'pausa':
                    m.pausar()
                elif accion == 'seguir':
                    m.seguir(datos.get('desde'))
                elif accion == 'ir':
                    m.ir_a(datos.get('t') or 0)
                elif accion == 'parar':
                    m.parar()
                elif accion == 'soltar':
                    m.soltar(datos.get('conservar'))
                respuesta = dict(m.estado())
                respuesta['ok'] = accion in ACCIONES or accion == 'estado'
                f.write((json.dumps(respuesta) + chr(10)).encode('utf-8'))
                f.flush()
        except Exception as e:
            try:
                conexion.sendall((json.dumps({'ok': False, 'error': str(e)}) + chr(10)).encode())
            except Exception:
                pass

    if padre:
        threading.Thread(target=vigilar_padre, daemon=True).start()
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind(('127.0.0.1', int(puerto)))
    servidor.listen(8)
    while True:
        try:
            conexion, _ = servidor.accept()
        except OSError:
            break
        threading.Thread(target=atender, args=(conexion,), daemon=True).start()

class ClienteProceso:

    def __init__(self, puerto, pid=None):
        self.puerto = int(puerto)
        self.pid = pid
        self._cache = {}

    def _mando(self, datos, tiempo=3.0):
        import json
        import socket
        with socket.create_connection(('127.0.0.1', self.puerto), timeout=tiempo) as c:
            f = c.makefile('rwb')
            f.write((json.dumps(datos) + chr(10)).encode('utf-8'))
            f.flush()
            linea = f.readline()
            if not linea:
                raise OSError('el proceso de sonido no contesta')
            return json.loads(linea.decode('utf-8'))

    def estado(self):
        try:
            datos = self._mando({'accion': 'estado'}, tiempo=1.5)
            self._cache = datos
            return datos
        except Exception as e:
            return {'disponible': False, 'sonando': False, 'clave': None, 'pos': 0.0,
                    'dur': 0.0, 'listas': [], 'error': str(e)}

    def disponible(self):
        return bool(self.estado().get('disponible'))

    def poner(self, clave, ruta, desde=None, sonar=True):
        return self._llamar('poner', clave=clave, ruta=ruta, desde=desde, sonar=sonar)

    def cambiar(self, clave, ruta, sonar=None):
        return self._llamar('cambiar', clave=clave, ruta=ruta, sonar=sonar)

    def preparar(self, clave, ruta):
        return self._llamar('preparar', clave=clave, ruta=ruta)

    def pausar(self):
        return self._llamar('pausa')

    def seguir(self, desde=None):
        return self._llamar('seguir', desde=desde)

    def ir_a(self, segundos):
        return self._llamar('ir', t=segundos)

    def parar(self):
        return self._llamar('parar')

    def soltar(self, conservar=None):
        return self._llamar('soltar', conservar=conservar)

    def _llamar(self, accion, **datos):
        datos['accion'] = accion
        try:
            self._cache = self._mando(datos)
            return True
        except Exception as e:
            self._cache = {'disponible': False, 'error': str(e)}
            return False
