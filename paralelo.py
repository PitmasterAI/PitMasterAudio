import json
import os
import subprocess
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
FICHERO = os.path.join(os.path.expanduser('~'), '.masterlab_paralelo.json')

CPU = 1
GPU = 1

def memoria_libre_gb():
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
    pct, otros = uso_gpu()
    if pct is None:
        return False
    return pct >= umbral

def en_vivo():
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
