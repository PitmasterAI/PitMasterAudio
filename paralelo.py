"""Cuántas instancias de cada motor lleva el equipo: regla fija, igual que la APK.

Regla:
  · Un solo trabajador de CPU.
  · Un solo trabajador de GPU si el aparato tiene tarjeta; ninguno si no la tiene.
  · Es la misma que la app de Android: un motor principal y otro secundario, y nada más.

No hay banco de pruebas: con una instancia por motor no hay nada que calibrar.

El resultado se guarda en ~/.masterlab_paralelo.json para poder consultarlo.

Uso:
  python3 paralelo.py            muestra la configuración del equipo
"""
import json
import os
import subprocess
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
FICHERO = os.path.join(os.path.expanduser('~'), '.masterlab_paralelo.json')

CPU = 1        # un trabajador de CPU
GPU = 1        # un trabajador de GPU (si hay tarjeta)


# ------------------------------------------------------------------ detectar
def memoria_libre_gb():
    """RAM disponible ahora mismo (GB)."""
    try:
        with open('/proc/meminfo', encoding='utf-8') as f:
            for linea in f:
                if linea.startswith('MemAvailable'):
                    return int(linea.split()[1]) / 1024.0 / 1024.0
    except OSError:
        pass
    try:
        return os.sysconf('SC_AVPHYS_PAGES') * os.sysconf('SC_PAGE_SIZE') / 1e9
    except (ValueError, OSError, AttributeError):
        return 1.0


def gpu():
    """(clase, nombre): 'dedicada', 'integrada' o None si no hay tarjeta.

    Mira el mismo motor que usa el masterizado (Vulkan o CUDA): así un equipo con
    tarjeta tiene siempre su trabajador de GPU, sea cual sea el sistema.
    """
    sys.path.insert(0, AQUI)
    try:
        import gpuops
        if not gpuops.listo():
            return None, 'sin GPU'
        nombre = gpuops.describe()
    except Exception:
        return None, 'sin GPU'
    minus = nombre.lower()
    if 'cuda' in minus:
        return 'dedicada', nombre
    if any(x in minus for x in ('nvidia', 'geforce', 'rtx', 'radeon rx', 'arc a')):
        return 'dedicada', nombre
    return 'integrada', nombre


_USO_CACHE = {'cuando': 0.0, 'valor': (None, False)}


def uso_gpu():
    """(uso en %, otros programas usando la tarjeta). Solo se puede mirar con NVIDIA.

    Si el equipo está generando vídeo o entrenando con la tarjeta a tope, nuestros
    cálculos se quedan esperando en la cola de la GPU mientras la CPU está vacía.

    El resultado se guarda unos segundos: lanzar `nvidia-smi` en cada ajuste cuesta
    entre medio segundo y dos segundos (dos veces por petición del usuario: uso y
    procesos), y eso se notaba como un retraso al pulsar cada ajuste.
    """
    now = time.time()
    if now - _USO_CACHE['cuando'] < 10.0:
        return _USO_CACHE['valor']
    try:
        salida = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu',
                                 '--format=csv,noheader,nounits'],
                                capture_output=True, text=True, timeout=4)
        if salida.returncode != 0:
            _USO_CACHE.update({'cuando': now, 'valor': (None, False)})
            return None, False
        lineas = [x.strip() for x in salida.stdout.strip().splitlines() if x.strip().isdigit()]
        if not lineas:
            _USO_CACHE.update({'cuando': now, 'valor': (None, False)})
            return None, False
        pct = max(int(x) for x in lineas)
    except Exception:
        _USO_CACHE.update({'cuando': now, 'valor': (None, False)})
        return None, False
    otros = False
    try:
        apps = subprocess.run(['nvidia-smi', '--query-compute-apps=pid',
                               '--format=csv,noheader'],
                              capture_output=True, text=True, timeout=4).stdout.split()
        otros = any(p.strip().isdigit() and int(p) != os.getpid() for p in apps)
    except Exception:
        pass
    _USO_CACHE.update({'cuando': now, 'valor': (pct, otros)})
    return pct, otros


def gpu_ocupada(umbral=50):
    """True si otro programa está usando la tarjeta de verdad (no solo reservando memoria)."""
    pct, otros = uso_gpu()
    if pct is None:
        return False
    return pct >= umbral


# ------------------------------------------------------------------ guardar
def en_vivo():
    """La configuración de este equipo, mirando la tarjeta que hay ahora mismo."""
    clase, nombre = gpu()
    pct, otros = uso_gpu()
    return {
        'cpu': CPU,
        'ram_libre_gb': round(memoria_libre_gb(), 1),
        'gpu': GPU if clase else 0,
        'gpu_clase': clase,
        'gpu_nombre': nombre,
        'gpu_uso': pct,
        'gpu_ocupada': bool(pct is not None and pct >= 50),
        'gpu_otros': otros,
        'fecha': time.strftime('%Y-%m-%d %H:%M'),
    }


def guardar(cfg):
    try:
        with open(FICHERO, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=1)
    except OSError:
        pass


def config(recalcular=False):
    """Configuración del equipo (se recalcula y se guarda; `recalcular` se acepta por compatibilidad)."""
    cfg = en_vivo()
    guardar(cfg)
    return cfg


def describe(cfg):
    gpu_txt = ('sin GPU' if not cfg['gpu']
               else '%s %s' % (cfg['gpu_clase'], cfg['gpu_nombre']))
    return ('instancias CPU %d · GPU %d (%s)'
            % (cfg['cpu'], cfg['gpu'], gpu_txt))


if __name__ == '__main__':
    print(describe(config()))
