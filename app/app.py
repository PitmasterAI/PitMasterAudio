
import os
import sys
import json
import time
import ctypes
import uuid
import shutil
import threading
import subprocess
import traceback

from flask import Flask, request, jsonify, send_file, render_template, abort

BASE = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, BASE)
sys.path.insert(0, os.path.dirname(BASE))
sys.path.insert(0, os.path.join(BASE, '_vendor'))
import motor as motor_dsp
import dsp
import analiza

try:
    import aceleracion
except Exception:
    aceleracion = None
try:
    import audio_nativo
except Exception:
    audio_nativo = None
import numpy as np
import soundfile as sf
from scipy import signal
import pyloudnorm as pyln

def _ffmpeg():
    for cand in (os.environ.get('FFMPEG'), shutil.which('ffmpeg'),
                 shutil.which('ffmpeg.exe'),
                 os.path.join(os.path.dirname(BASE), 'ffmpeg.exe'),
                 os.path.join(BASE, 'ffmpeg.exe'),
                 os.path.join(os.path.dirname(BASE), 'ffmpeg')):
        if cand and os.path.exists(cand):
            return cand
    return 'ffmpeg'

FFMPEG = _ffmpeg()
FFPROBE = FFMPEG.replace('ffmpeg', 'ffprobe') if FFMPEG else 'ffprobe'

APP_DIR = BASE
DATA = os.environ.get('MASTERLAB_DATA') or os.path.join(APP_DIR, 'data')
UP = os.path.join(DATA, 'subidos')
OUT = os.path.join(DATA, 'salidas')
os.makedirs(UP, exist_ok=True)
os.makedirs(OUT, exist_ok=True)

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['MAX_CONTENT_LENGTH'] = 600 * 1024 * 1024

JOBS = {}
PICOS = {}
LOCK = threading.Lock()
PRESETS = motor_dsp.load_presets()

def _send_audio(path):
    ext = str(path).rsplit('.', 1)[-1].lower()
    tipo = {'mp3': 'audio/mpeg', 'wav': 'audio/wav', 'ogg': 'audio/ogg',
            'm4a': 'audio/mp4', 'flac': 'audio/flac'}.get(ext, 'audio/mpeg')
    resp = send_file(path, conditional=True, mimetype=tipo, max_age=3600)
    resp.headers['Accept-Ranges'] = 'bytes'
    return resp

def limpiar_anteriores(conservar=None):
    with LOCK:
        for clave in list(JOBS.keys()):
            if clave != conservar:
                JOBS.pop(clave, None)
    with FUENTES_LOCK:
        for clave in list(FUENTES.keys()):
            if clave != conservar:
                FUENTES.pop(clave, None)
    for carpeta in (UP, OUT):
        for f in os.listdir(carpeta):
            base = f.split('__')[0].split('_master')[0].rsplit('.', 1)[0]
            if conservar is None or not f.startswith(conservar):
                try:
                    os.unlink(os.path.join(carpeta, f))
                except OSError:
                    pass

def _info_audio(ruta):
    info = {'ext': (os.path.splitext(ruta)[1] or '.wav').lower().lstrip('.'),
            'codec': '', 'bitrate': 0, 'sr': 0, 'canales': 2, 'bits': 0, 'portada': False}
    datos = None
    try:
        salida = subprocess.run([FFPROBE, '-v', 'quiet', '-print_format', 'json',
                                 '-show_streams', '-show_format', ruta],
                                capture_output=True, text=True, timeout=60)
        datos = json.loads(salida.stdout or '{}')
    except Exception:
        datos = None
    if datos:
        for pista in datos.get('streams') or []:
            if pista.get('codec_type') == 'audio' and not info['codec']:
                info['codec'] = pista.get('codec_name') or ''
                info['sr'] = int(pista.get('sample_rate') or 0)
                info['canales'] = int(pista.get('channels') or 2)
                info['bits'] = int(pista.get('bits_per_raw_sample')
                                   or pista.get('bits_per_sample') or 0)
                info['bitrate'] = int(pista.get('bit_rate')
                                      or (datos.get('format') or {}).get('bit_rate') or 0)
            if pista.get('codec_type') == 'video':
                info['portada'] = True
    else:
        try:
            with sf.SoundFile(ruta) as f:
                info['sr'] = int(f.samplerate)
                info['canales'] = int(f.channels)
                info['bits'] = 24 if 'PCM_24' in str(f.subtype) else 16
                info['codec'] = str(f.subtype).lower()
        except Exception:
            pass
    if info['ext'] == 'wave':
        info['ext'] = 'wav'
    if not info['sr']:
        info['sr'] = 48000
    return info

def _a_formato(origen, original, destino, info):
    ext = info.get('ext') or 'wav'
    sr = str(info.get('sr') or 48000)
    bits = info.get('bits') or 0
    bitrate = int(info.get('bitrate') or 0)
    if not os.path.exists(original):
        original = origen
    orden = [FFMPEG, '-v', 'error', '-y', '-i', origen]
    if original != origen:
        orden += ['-i', original, '-map', '0:a', '-map_metadata', '1']
        if info.get('portada'):
            orden += ['-map', '1:v?', '-c:v', 'copy']
    if ext == 'mp3':
        orden += ['-c:a', 'libmp3lame', '-b:a', str(bitrate if bitrate >= 96000 else 320000)]
    elif ext == 'flac':
        orden += ['-c:a', 'flac', '-sample_fmt', 's32' if bits > 16 else 's16']
    elif ext in ('m4a', 'mp4', 'aac'):
        orden += ['-c:a', 'aac', '-b:a', str(bitrate if bitrate >= 96000 else 256000)]
    elif ext == 'ogg':
        orden += ['-c:a', 'libvorbis', '-b:a', str(bitrate if bitrate >= 96000 else 192000)]
    elif ext == 'opus':
        orden += ['-c:a', 'libopus', '-b:a', str(bitrate if bitrate >= 24000 else 128000)]
    else:
        ext = 'wav'
        orden += ['-c:a', 'pcm_s24le' if (bits == 0 or bits > 16) else 'pcm_s16le']
    if sr not in ('0', ''):
        orden += ['-ar', sr]
    if int(info.get('canales') or 2) == 1:
        orden += ['-ac', '1']
    orden += [destino]
    try:
        subprocess.run(orden, check=True, timeout=900)
        return True
    except Exception as e:
        print('[formato] no se pudo escribir %s: %s' % (ext, e), flush=True)
        return False

def _finito(valor, defecto=0.0):
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return defecto
    if numero != numero or numero in (float('inf'), float('-inf')):
        return defecto
    return numero

def _pico_real(x64, sr, bloque=4.0):
    n = len(x64)
    if n == 0:
        return 0.0
    tam = max(int(bloque * sr), 8192)
    borde = min(4096, n)
    pico = 0.0
    for ini in range(0, n, tam):
        fin = min(n, ini + tam)
        a = max(0, ini - borde)
        b = min(n, fin + borde)
        sobremuestreado = signal.resample_poly(x64[a:b], 4, 1, axis=0)
        izq = (ini - a) * 4
        der = sobremuestreado.shape[0] - (b - fin) * 4
        centro = sobremuestreado[izq:der] if der > izq else sobremuestreado
        if centro.size:
            pico = max(pico, float(np.max(np.abs(centro))))
    return pico

def analizar(x, sr, medidas=None):
    x64 = np.asarray(x, dtype=np.float64)
    lufs = None
    if medidas and medidas.get('lufs') is not None:
        lufs = float(medidas['lufs'])
    if lufs is None:

        lufs = float(dsp.measure_lufs(x64, sr))
    mono = x64.mean(axis=1)
    crest = float(20 * np.log10((np.max(np.abs(mono)) + 1e-12) / (np.sqrt(np.mean(mono ** 2)) + 1e-12)))
    tp = float(20 * np.log10(max(_pico_real(x64, sr), 1e-9)))
    corr = 1.0
    if x64.shape[1] > 1:
        corr = float(np.corrcoef(x64[:, 0], x64[:, 1])[0, 1])
    return {'lufs': round(_finito(lufs, -70.0), 2), 'crest': round(_finito(crest, 0.0), 2),
            'tp': round(_finito(tp, -70.0), 2), 'corr': round(_finito(corr, 1.0), 3)}

def ruta_original(sid):
    for ext in ('wav', 'mp3', 'flac', 'm4a'):
        p = os.path.join(UP, f'{sid}.{ext}')
        if os.path.exists(p):
            return p
    return None

def firma(preset, lufs_obj, techo, intensidad=None):
    l = 'auto' if lufs_obj is None else f'{float(lufs_obj):.1f}'
    t = 'auto' if techo is None else f'{float(techo):.1f}'
    i = 'auto' if intensidad is None else f'{float(intensidad) * 100:.0f}'
    return f'{preset}_{l}.{t}_i{i}'.replace('/', '_')

def _marcar(sid, clave, activo):
    with LOCK:
        job = JOBS.get(sid)
        if job is None:
            return
        conjunto = job.setdefault('calculando', set())
        if activo:
            conjunto.add(clave)
        else:
            conjunto.discard(clave)

def _apuntar_hecho(sid, clave):
    with LOCK:
        job = JOBS.get(sid)
        if job is None:
            return
        (job.get('calculando') or set()).discard(clave)
        job.setdefault('hechos', set()).add(clave)

def lufs_para(sid, clave, lufs_panel=None):
    job = JOBS.get(sid) or {}
    panel = job.get('panel') or {}
    auto_lufs = job.get('auto_lufs') or {}
    if panel.get('auto') and auto_lufs.get(clave) is not None:
        return float(auto_lufs[clave])
    if lufs_panel is None:
        lufs_panel = panel.get('lufs')
    if lufs_panel is not None:
        return float(lufs_panel)
    propio = PRESETS.get(clave, {}).get('lufs')
    return float(propio) if propio is not None else None

def _hechos(sid):
    job = JOBS.get(sid) or {}
    intensidad = (job.get('panel') or {}).get('intensidad', 1.0)
    techo = (job.get('panel') or {}).get('techo')
    listos = list(job.get('hechos') or [])
    for clave, p in PRESETS.items():
        if clave in listos:
            continue
        lufs_ajuste = lufs_para(sid, clave)
        marca = firma(clave, lufs_ajuste, techo, intensidad)
        if os.path.exists(ruta_de(sid, marca)):
            listos.append(clave)
    return listos

def ruta_de(sid, marca, ext='wav'):
    return os.path.join(OUT, f'{sid}__{marca}.{ext}')

def ruta_entrega(sid, marca, ext):
    return os.path.join(OUT, '%s__%s__entrega.%s' % (sid, marca, ext))

def ruta_salida(sid):
    j = JOBS.get(sid) or {}
    marca = j.get('salida_marca')
    if marca:
        p = ruta_de(sid, marca)
        if os.path.exists(p):
            return p
    for ext in ('wav', 'mp3'):
        p = os.path.join(OUT, f'{sid}_master.{ext}')
        if os.path.exists(p):
            return p
    return None

FUENTES = {}
FUENTES_LOCK = threading.Lock()
COLA_LOCK = threading.Lock()
TRABAJANDO = {'n': 0}

def _memoria_libre_mb():
    try:
        with open('/proc/meminfo') as f:
            for linea in f:
                if linea.startswith('MemAvailable:'):
                    return int(linea.split()[1]) // 1024
    except Exception:
        pass
    return None

def _ocupado():
    with COLA_LOCK:
        return TRABAJANDO['n'] > 0

def _fuente(sid):
    with FUENTES_LOCK:
        if sid in FUENTES:
            return FUENTES[sid]
    x, sr = motor_dsp.read_audio(ruta_original(sid))
    with FUENTES_LOCK:
        FUENTES[sid] = (x, sr)
    return x, sr

_TURNOS = threading.Condition()
_EN_CURSO = {'n': 0}
_URGENTES = {'n': 0}

def _memoria_total_mb():
    try:
        with open('/proc/meminfo') as f:
            for linea in f:
                if linea.startswith('MemTotal:'):
                    return int(linea.split()[1]) / 1024.0
    except Exception:
        pass
    try:
        import ctypes

        class _Mem(ctypes.Structure):
            _fields_ = [('dwLength', ctypes.c_ulong), ('dwMemoryLoad', ctypes.c_ulong),
                        ('ullTotalPhys', ctypes.c_ulonglong), ('ullAvailPhys', ctypes.c_ulonglong),
                        ('ullTotalPageFile', ctypes.c_ulonglong), ('ullAvailPageFile', ctypes.c_ulonglong),
                        ('ullTotalVirtual', ctypes.c_ulonglong), ('ullAvailVirtual', ctypes.c_ulonglong),
                        ('ullAvailExtendedVirtual', ctypes.c_ulonglong)]

        m = _Mem()
        m.dwLength = ctypes.sizeof(_Mem)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):
            return m.ullTotalPhys / (1024.0 * 1024.0)
    except Exception:
        pass
    return None

def _concurrencia():
    libre = _memoria_libre_mb()
    if libre is None:
        return 2

    if libre < 3500:
        return 1
    return max(1, min(3, int(libre // 2500)))

def _entrar_calculo(urgente=False):
    with _TURNOS:
        if urgente:

            _URGENTES['n'] += 1
            while _EN_CURSO['n'] >= _concurrencia():
                _TURNOS.wait(0.2)
            _EN_CURSO['n'] += 1
            return
        while _EN_CURSO['n'] >= _concurrencia() or _URGENTES['n'] > 0:
            _TURNOS.wait(0.2)
        _EN_CURSO['n'] += 1

def _salir_calculo(urgente=False):
    try:
        ctypes.CDLL('libc.so.6').malloc_trim(0)
    except Exception:
        pass
    with _TURNOS:
        _EN_CURSO['n'] = max(0, _EN_CURSO['n'] - 1)
        if urgente:
            _URGENTES['n'] = max(0, _URGENTES['n'] - 1)
        _TURNOS.notify_all()

def _motor_urgente():
    try:
        import paralelo
        if paralelo.gpu_ocupada():
            return 'CPU'
    except Exception:
        pass
    return 'GPU'

def _motor_hilo(modo):
    try:
        import gpuops
        gpuops.fijar(modo)
    except Exception:
        pass

def _masterizar(sid, preset, intensidad, lufs_obj, techo, urgente=False):
    _entrar_calculo(urgente)
    try:
        return _masterizar_sin_turno(sid, preset, intensidad, lufs_obj, techo)
    finally:
        _salir_calculo(urgente)

def _masterizar_sin_turno(sid, preset, intensidad, lufs_obj, techo):
    x, sr = _fuente(sid)
    P = dict(PRESETS[preset])
    if lufs_obj is not None:
        P['lufs'] = float(lufs_obj)
    y = motor_dsp.chain(x, sr, P, intensity=float(intensidad),
                       ceiling_db=(float(techo) if techo is not None else None))
    techo_real = float(techo) if techo is not None else float(P.get('ceiling_db', -0.3) or -0.3)

    objetivo = float(lufs_obj) if lufs_obj is not None else float(P.get('lufs', 0) or 0)
    if objetivo:
        techo_real = float(techo) if techo is not None else float(P.get('ceiling_db', -0.3) or -0.3)
        _m = motor_dsp.ultima_medida() or {}
        pico_real = float(_m.get('tp')) if _m.get('tp') is not None else techo_real

        for _ in range(2):
            delta = objetivo - float(dsp.measure_lufs(y, sr))
            if abs(delta) < 0.08:
                break
            if delta > 0:
                g = 10 ** (delta / 20.0)

                if pico_real + 20 * np.log10(g) <= techo_real - 0.01:
                    y = y * g
                    pico_real = pico_real + 20 * np.log10(g)
                else:
                    y = dsp.limiter(y * g, sr, ceiling_db=techo_real,
                                    lookahead_ms=float(P.get('lookahead_ms', 5.0)),
                                    release_ms=float(P.get('limit_release_ms', 60.0)))
                    pico_real = techo_real
            else:
                y = y * (10 ** (delta / 20.0))
                pico_real = pico_real + 20 * np.log10(10 ** (delta / 20.0))
    return y, sr

def _generacion(sid):
    j = JOBS.get(sid) or {}
    return int(j.get('generacion', 0))

def precalentar(sid, intensidad, lufs_obj, techo, saltar, generacion, cola, motor,
                esperar_libre):
    _motor_hilo(motor)
    try:
        while True:
            if esperar_libre:
                while _ocupado():
                    if _generacion(sid) != generacion:
                        return
                    time.sleep(0.25)
            with COLA_LOCK:
                if _generacion(sid) != generacion:
                    return
                if cola['i'] >= len(cola['claves']):
                    return
                clave = cola['claves'][cola['i']]
                cola['i'] += 1
            if clave == saltar:
                continue
            libre = _memoria_libre_mb()
            if libre is not None and libre < 400:

                print('[precalculado] quedan %d MB libres, se suelta la cola' % libre, flush=True)
                return

            lufs_ajuste = lufs_para(sid, clave, lufs_obj)
            marca = firma(clave, lufs_ajuste, techo, intensidad)
            if os.path.exists(ruta_de(sid, marca)):
                continue
            _marcar(sid, clave, True)
            try:
                _tin = time.time()
                y, sr = _masterizar(sid, clave, intensidad, lufs_ajuste, techo)
                if _generacion(sid) != generacion:
                    return
                print('[ajuste] %s: cadena %.1f s' % (clave, time.time() - _tin), flush=True)
                salida = ruta_de(sid, marca)
                sf.write(salida, np.clip(y, -1, 1), sr, subtype='PCM_24')
                with LOCK:
                    PICOS.setdefault(sid, {})['master'] = (os.path.getmtime(salida), _picos(y))
                _guardar_medidas(salida, analizar(y, sr, motor_dsp.ultima_medida()))

                _apuntar_hecho(sid, clave)
                print('[precalculado] %s %s listo (%s)' % (sid, clave, motor), flush=True)
            except Exception as e:
                print('[precalculado] falló %s: %s' % (clave, e), flush=True)
            finally:
                _marcar(sid, clave, False)
    finally:
        _motor_hilo(None)

DESTACADOS = ('base_claro', 'base_retro')

def lanzar_precalculado(sid, intensidad, lufs_obj, techo, saltar):
    with LOCK:
        job = JOBS.get(sid)
        if job is None:
            return
        job['generacion'] = int(job.get('generacion', 0)) + 1
        generacion = job['generacion']
        orden = (job.get('consejo') or {}).get('orden') or []
        todas = []
        for o in orden:
            clave = o.get('clave') if isinstance(o, dict) else o
            if clave in PRESETS and clave not in todas:
                todas.append(clave)
    if not todas:
        return

    claves = [c for c in DESTACADOS if c in PRESETS]
    claves += [c for c in todas if c not in DESTACADOS][:2]
    claves += [c for c in todas if c not in claves]
    cola = {'claves': claves, 'i': 0}
    with LOCK:
        if JOBS.get(sid) is not None:
            JOBS[sid]['cola'] = cola

    try:
        import paralelo as _paralelo
        _cfg = _paralelo.en_vivo()
        n_cpu = 1
        n_gpu = 0

        clase_gpu = str(_cfg.get('gpu_clase') or '')
        if os.environ.get('MASTERLAB_USAR_GPU') == '1' and int(_cfg.get('gpu', 0)) > 0:
            n_gpu = 1
            if _memoria_total_mb() is not None and _memoria_total_mb() < 11000:
                n_gpu = 0
            if 'integrad' in clase_gpu.lower():
                n_gpu = 0
        if n_gpu and _cfg.get('gpu_ocupada'):

            n_gpu = 0
            n_cpu = 2
            clase_gpu = 'GPU al %s %% ocupada por otro programa, se usa la CPU' % _cfg.get('gpu_uso')
    except Exception:
        n_cpu, n_gpu, clase_gpu = 1, 0, ''

    motores = [('CPU', True) for _ in range(n_cpu)]
    motores += [('GPU', True) for _ in range(n_gpu)]

    os.environ['MASTERLAB_TRABAJOS_CPU'] = str(max(1, n_cpu + n_gpu))
    print('[precalculado] %d hilos: %d CPU + %d GPU (%s)' % (len(motores), n_cpu, n_gpu,
                                                             clase_gpu or 'sin datos'), flush=True)
    for motor, esperar in motores:
        threading.Thread(target=precalentar,
                         args=(sid, intensidad, lufs_obj, techo, saltar, generacion,
                               cola, motor, esperar), daemon=True).start()

def procesar(sid, preset, intensidad, lufs_obj, techo, fmt, marca, cola_pendiente=None):
    job = JOBS[sid]
    _motor_hilo(_motor_urgente())
    _marcar(sid, preset, True)
    with COLA_LOCK:
        TRABAJANDO['n'] += 1
    try:
        job['estado'] = 'procesando'
        job['paso'] = 'Leyendo el tema'
        job['paso'] = 'Aplicando la cadena del preset'
        y, sr = _masterizar(sid, preset, intensidad, lufs_obj, techo, urgente=True)
        job['paso'] = 'Guardando'
        salida = ruta_de(sid, marca)
        sf.write(salida, np.clip(y, -1, 1), sr, subtype='PCM_24')
        with LOCK:
            PICOS.setdefault(sid, {})['master'] = (os.path.getmtime(salida), _picos(y))
        job['medidas_master'] = analizar(y, sr, motor_dsp.ultima_medida())
        _guardar_medidas(salida, job['medidas_master'])
        _precargar_en_ram(sid, marca)
        job['salida_marca'] = marca
        job.setdefault('hechos', set()).add(preset)
        job['estado'] = 'listo'
        job['paso'] = 'Terminado'
    except Exception as e:
        job['estado'] = 'error'
        job['error'] = str(e)
        job['traza'] = traceback.format_exc()[-800:]
    finally:
        _marcar(sid, preset, False)
        with COLA_LOCK:
            TRABAJANDO['n'] = max(0, TRABAJANDO['n'] - 1)
        _motor_hilo(None)
        if cola_pendiente:

            lanzar_precalculado(*cola_pendiente)

def _quitar_ahorro_windows():
    if os.name != 'nt':
        return
    try:
        import ctypes

        class _Estado(ctypes.Structure):
            _fields_ = [('Version', ctypes.c_ulong), ('ControlMask', ctypes.c_ulong),
                        ('StateMask', ctypes.c_ulong)]

        PROCESS_POWER_THROTTLING_CURRENT_VERSION = 1
        PROCESS_POWER_THROTTLING_EXECUTION_SPEED = 0x1
        estado = _Estado(PROCESS_POWER_THROTTLING_CURRENT_VERSION,
                         PROCESS_POWER_THROTTLING_EXECUTION_SPEED, 0)
        ctypes.windll.kernel32.SetProcessInformation(
            ctypes.windll.kernel32.GetCurrentProcess(), 4, ctypes.byref(estado),
            ctypes.sizeof(estado))
    except Exception:
        pass

_quitar_ahorro_windows()

@app.route('/')
def index():
    return render_template('index.html', presets=PRESETS)

@app.route('/api/presets')
def api_presets():
    return jsonify([{'slug': k, 'label': analiza.nombre(k), 'descripcion': analiza.descripcion(k), 'lufs': v.get('lufs')}
                    for k, v in PRESETS.items()])

@app.route('/api/subir', methods=['POST'])
def api_subir():
    f = request.files.get('audio')
    if not f:
        return jsonify({'error': 'No ha llegado ningún archivo'}), 400
    sid = uuid.uuid4().hex[:12]
    nombre = f.filename or 'tema'
    limpiar_anteriores(sid)

    ext_subida = (os.path.splitext(nombre)[1] or '.wav').lower().lstrip('.')
    if ext_subida in ('wave', 'wavex'):
        ext_subida = 'wav'
    bruto = os.path.join(UP, f'{sid}_bruto.{ext_subida}')
    f.save(bruto)

    info = _info_audio(bruto)
    ext_final = info.get('ext') or ext_subida
    if ext_final in ('', 'bin'):
        ext_final = ext_subida
    info['ext'] = ext_final
    original = os.path.join(UP, '%s_original.%s' % (sid, ext_final))
    os.replace(bruto, original)
    destino = os.path.join(UP, f'{sid}.wav')
    try:
        subprocess.run([FFMPEG, '-v', 'error', '-y', '-i', original,
                        '-ar', '48000', '-ac', '2', '-c:a', 'pcm_f32le', destino],
                       check=True, timeout=300)
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):

        try:
            datos, frecuencia = sf.read(original, dtype='float32', always_2d=True)
        except Exception:
            os.unlink(original)
            return jsonify({'error': 'No se ha podido leer el audio (¿formato no soportado?)'}), 400
        if datos.shape[1] == 1:
            datos = np.repeat(datos, 2, axis=1)
        elif datos.shape[1] > 2:
            datos = datos[:, :2]
        if frecuencia != 48000:
            from math import gcd
            factor = gcd(int(frecuencia), 48000)
            datos = signal.resample_poly(datos, 48000 // factor, int(frecuencia) // factor, axis=0)
        sf.write(destino, datos, 48000, subtype='FLOAT')
    x, sr = motor_dsp.read_audio(destino)
    with FUENTES_LOCK:
        FUENTES[sid] = (x, sr)
    with LOCK:
        PICOS.setdefault(sid, {})['original'] = (os.path.getmtime(destino), _picos(x))
    _precargar_en_ram(sid, 'original')
    medidas = analizar(x, sr)
    if medidas['lufs'] <= -60.0:
        os.unlink(destino)
        return jsonify({'error': 'Ese audio está en silencio (o no se oye nada)'}), 400
    try:
        consejo = analiza.recomendar(x, sr, PRESETS)
    except Exception as e:
        consejo = {'perfil': {}, 'orden': [], 'recomendado': 'universal', 'error': str(e)}
    with LOCK:
        JOBS[sid] = {'estado': 'subido', 'paso': '', 'nombre': nombre,
                     'duracion': round(len(x) / sr, 1), 'medidas_original': medidas,
                     'preset': None, 'intensidad': 1.0, 'consejo': consejo,
                     'auto_lufs': consejo.get('auto_lufs') or {},
                     'formato': info, 'original': original}
    motor = _motor_audio()
    if motor is not None:
        motor.soltar(conservar=sid)
    return jsonify({'id': sid, 'nombre': nombre, 'duracion': round(len(x) / sr, 1),
                    'formato': info, 'medidas': medidas, 'consejo': consejo,
                    'motor': aceleracion.describe_doble() if aceleracion else 'Motor principal: CPU'})

@app.route('/api/masterizar', methods=['POST'])
def api_masterizar():
    d = request.get_json(force=True, silent=True) or {}
    sid = d.get('id')
    if not sid or sid not in JOBS:
        return jsonify({'error': 'Tema desconocido'}), 400
    preset = d.get('preset', 'universal')
    if preset not in PRESETS:
        return jsonify({'error': 'Preset desconocido'}), 400
    intensidad = float(d.get('intensidad', 1.0))
    lufs_obj = d.get('lufs')
    techo = d.get('techo')
    fmt = d.get('formato', 'wav')
    marca = firma(preset, lufs_obj, techo, intensidad)
    with LOCK:
        JOBS[sid]['panel'] = {'intensidad': intensidad, 'lufs': lufs_obj, 'techo': techo,
                              'auto': bool(d.get('auto'))}

    cola_pendiente = (sid, intensidad, lufs_obj, techo, preset)
    cacheado = ruta_de(sid, marca)
    if os.path.exists(cacheado):

        try:
            sr = int(sf.info(ruta_original(sid)).samplerate)
        except Exception:
            sr = 48000
        _precargar_en_ram(sid, marca)
        lanzar_precalculado(*cola_pendiente)
        with LOCK:
            JOBS[sid].update({'estado': 'listo', 'paso': 'Ya estaba hecho', 'preset': preset,
                              'intensidad': intensidad, 'error': None, 'salida_marca': marca,
                              'medidas_master': _medidas_de(cacheado, sr)})
            JOBS[sid].setdefault('hechos', set()).add(preset)
            return jsonify({'ok': True, 'cache': True})
    with LOCK:
        JOBS[sid].update({'estado': 'en cola', 'paso': 'Preparando', 'preset': preset,
                          'intensidad': intensidad, 'error': None})
    h = threading.Thread(target=procesar,
                         args=(sid, preset, intensidad, lufs_obj, techo, fmt, marca,
                               cola_pendiente), daemon=True)
    h.start()
    return jsonify({'ok': True})

@app.route('/api/estado/<sid>')
def api_estado(sid):
    j = JOBS.get(sid)
    if not j:
        return jsonify({'error': 'desconocido'}), 404
    datos = {k: v for k, v in j.items() if k not in ('calculando', 'hechos', 'cola')}
    datos['calculando'] = sorted(j.get('calculando') or [])
    datos['hechos'] = _hechos(sid)

    cola = j.get('cola') or {}
    claves = cola.get('claves') or []
    datos['pendientes'] = max(0, len(claves) - int(cola.get('i') or 0))
    return jsonify(datos)

@app.route('/api/motor')
def api_motor():
    principal, secundario = 'CPU', 'GPU'
    try:
        principal, secundario = aceleracion.motores()
    except Exception:
        try:
            texto = aceleracion.describe_doble()
            if '·' in texto:
                principal = texto.split('principal: ')[1].split(' ·')[0]
                secundario = texto.split('secundario: ')[1]
        except Exception:
            pass
    return jsonify({'principal': principal, 'secundario': secundario})

def _medidas_de(wav, sr):
    ficha = wav + '.json'
    try:
        if os.path.exists(ficha):
            with open(ficha, encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    try:
        medidas = analizar(motor_dsp.read_audio(wav)[0], sr)
    except Exception:
        return {}
    try:
        with open(ficha, 'w', encoding='utf-8') as f:
            json.dump(medidas, f)
    except Exception:
        pass
    return medidas

def _guardar_medidas(wav, medidas):
    try:
        with open(wav + '.json', 'w', encoding='utf-8') as f:
            json.dump(medidas, f)
    except Exception:
        pass

def _precargar_en_ram(sid, marca):
    motor = _motor_audio()
    if motor is None:
        return
    ruta = ruta_original(sid) if marca == 'original' else ruta_de(sid, marca)
    if not ruta or not os.path.exists(ruta):
        return
    try:
        motor.preparar('%s:%s' % (sid, marca), ruta)
    except Exception:
        pass

def _picos(datos, barras=220):
    x = np.asarray(datos, dtype=np.float32)
    if x.ndim > 1:
        x = x.mean(axis=1)
    if len(x) == 0:
        return [0.0] * barras
    bloque = max(1, len(x) // barras)
    salida = []
    for i in range(barras):
        trozo = x[i * bloque:(i + 1) * bloque]
        salida.append(round(float(np.max(np.abs(trozo))) if len(trozo) else 0.0, 4))
    return salida

@app.route('/api/picos/<sid>/<cual>')
def api_picos(sid, cual):
    ruta = ruta_original(sid) if cual == 'original' else ruta_salida(sid)
    if not ruta or not os.path.exists(ruta):
        abort(404)
    marca = os.path.getmtime(ruta)
    with LOCK:
        guardado = (PICOS.get(sid) or {}).get(cual)
        if guardado and guardado[0] == marca:
            return jsonify({'picos': guardado[1]})

    try:
        datos, _sr = sf.read(ruta, dtype='float32', always_2d=True)
    except Exception:
        abort(404)
    picos = _picos(datos)
    with LOCK:
        PICOS.setdefault(sid, {})[cual] = (marca, picos)
    return jsonify({'picos': picos})

@app.route('/api/audio/<sid>/<cual>')
def api_audio(sid, cual):
    p = ruta_original(sid) if cual == 'original' else ruta_salida(sid)
    if not p or not os.path.exists(p):
        abort(404)
    return _send_audio(p)

def _version_audio(sid, cual):
    j = JOBS.get(sid) or {}
    if cual == 'original':
        return '%s:original' % sid, ruta_original(sid)
    marca = j.get('salida_marca') or 'master'
    return '%s:%s' % (sid, marca), ruta_salida(sid)

_SONIDO = {}
AUDIO_HIJO = {}

def _puerto_libre():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 0))
    puerto = s.getsockname()[1]
    s.close()
    return puerto

def _arrancar_proceso_audio():
    if os.environ.get('PITMA_SIN_AUDIO_PROPIO'):
        return None
    puerto = _puerto_libre()
    guion = os.path.join(BASE, 'audio_proceso.py')
    if not os.path.exists(guion):
        return None
    try:
        hijo = subprocess.Popen([sys.executable, guion, str(puerto), str(os.getpid())],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                cwd=BASE)
    except Exception as e:
        print('[sonido] no se pudo lanzar el proceso: %s' % e, flush=True)
        return None
    cliente = audio_nativo.ClienteProceso(puerto, hijo.pid)
    for _ in range(50):
        if cliente.estado().get('disponible'):
            break
        time.sleep(0.2)
    AUDIO_HIJO['proceso'] = hijo
    print('[sonido] proceso propio en el puerto %d (pid %d), tarjeta: %s'
          % (puerto, hijo.pid, 'sí' if cliente.disponible() else 'no'), flush=True)

    import atexit

    def cerrar():
        try:
            if hijo.poll() is None:
                hijo.terminate()
        except Exception:
            pass

    atexit.register(cerrar)
    return cliente

def _motor_audio():
    if audio_nativo is None:
        return None
    if 'motor' not in _SONIDO:
        cliente = _arrancar_proceso_audio()
        _SONIDO['motor'] = cliente if cliente is not None else audio_nativo.motor()
    return _SONIDO['motor']

@app.route('/api/repro/estado')
def api_repro_estado():
    motor = _motor_audio()
    if motor is None:
        return jsonify({'disponible': False})
    datos = motor.estado()
    sid = request.args.get('id')
    if sid:
        datos['original'] = _version_audio(sid, 'original')[0]
        datos['master'] = _version_audio(sid, 'master')[0]
    return jsonify(datos)

@app.route('/api/repro/mando', methods=['POST'])
def api_repro_mando():
    motor = _motor_audio()
    d = request.get_json(force=True, silent=True) or {}
    if motor is None or not motor.disponible():
        return jsonify({'disponible': False, 'ok': False})
    sid = d.get('id')
    accion = d.get('accion') or 'estado'
    if accion == 'pausa':
        motor.pausar()
    elif accion == 'seguir':
        motor.seguir()
    elif accion == 'parar':
        motor.parar()
    elif accion == 'ir':
        motor.ir_a(float(d.get('t') or 0))
    elif accion in ('poner', 'cambiar'):
        if not sid or sid not in JOBS:
            return jsonify({'disponible': True, 'ok': False, 'error': 'tema desconocido'})
        clave, ruta = _version_audio(sid, d.get('cual') or 'original')
        if not ruta or not os.path.exists(ruta):
            return jsonify({'disponible': True, 'ok': False, 'error': 'sin audio'})
        if accion == 'poner':
            motor.poner(clave, ruta, desde=d.get('desde'), sonar=bool(d.get('sonar', True)))
        else:
            sonar = d.get('sonar')
            motor.cambiar(clave, ruta, sonar=(None if sonar is None else bool(sonar)))
    else:
        return jsonify({'error': 'acción desconocida'}), 400
    datos = motor.estado()
    datos['ok'] = True
    return jsonify(datos)

@app.after_request
def _sin_cache(respuesta):

    if respuesta.mimetype in ('text/html', 'text/javascript', 'application/javascript',
                              'text/css'):
        respuesta.headers['Cache-Control'] = 'no-store, must-revalidate'
        respuesta.headers['Pragma'] = 'no-cache'
    return respuesta

def _abrir_en_sistema(url):
    if not url.startswith(('http://', 'https://')):
        return False
    ordenes = []
    if os.name == 'nt':
        ordenes = [['cmd', '/c', 'start', '', url], ['rundll32', 'url.dll,FileProtocolHandler', url]]
    else:
        ordenes = [['xdg-open', url], ['gio', 'open', url],
                   ['sensible-browser', url], ['x-www-browser', url]]
    for orden in ordenes:
        try:
            subprocess.Popen(orden, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             start_new_session=True)
            return True
        except Exception:
            continue
    return False

@app.route('/api/abrir', methods=['POST'])
def api_abrir():
    datos = request.get_json(silent=True) or {}
    url = str(datos.get('url') or '')
    if not url:
        return jsonify({'ok': False, 'error': 'falta la dirección'}), 400
    abierto = _abrir_en_sistema(url)
    return jsonify({'ok': abierto, 'url': url})

@app.route('/api/consola', methods=['POST'])
def api_consola():
    try:
        datos = request.get_json(force=True, silent=True) or {}
    except Exception:
        datos = {}
    ruta = os.path.join(DATA, 'consola.log')
    try:
        os.makedirs(DATA, exist_ok=True)
        with open(ruta, 'a', encoding='utf-8') as f:
            f.write(time.strftime('%Y-%m-%d %H:%M:%S '))
            f.write(json.dumps(datos, ensure_ascii=False)[:4000])
            f.write('\n')
    except Exception:
        pass
    return jsonify({'ok': True})

@app.route('/api/descargar/<sid>')
def api_descargar(sid):
    j = JOBS.get(sid, {})
    info = j.get('formato') or {}

    fmt = (request.args.get('formato') or info.get('ext') or 'wav').lower().lstrip('.')
    if fmt in ('wave', 'wavex'):
        fmt = 'wav'
    marca = j.get('salida_marca')
    p = ruta_entrega(sid, marca, fmt) if marca else os.path.join(OUT, f'{sid}_master.{fmt}')
    if not os.path.exists(p) and marca:

        wav = ruta_de(sid, marca)
        if os.path.exists(wav):
            _a_formato(wav, j.get('original'), p, dict(info, ext=fmt))
    if not os.path.exists(p):
        abort(404)
    j = JOBS.get(sid, {})
    base = (j.get('nombre') or 'tema').rsplit('.', 1)[0].strip()
    ajuste = analiza.nombre(j.get('preset') or '') or 'Master'
    seguro = ''.join(c if (c.isalnum() or c in ' ._-') else '_' for c in f'{base}_{ajuste}')
    return send_file(p, as_attachment=True, download_name=f'{seguro}.{fmt}')

if __name__ == '__main__':
    host = os.environ.get('HOST', '127.0.0.1')
    app.run(host=host, port=int(os.environ.get('PUERTO', '5077')), threaded=True)
