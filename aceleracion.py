
import json
import os
import time

RUTA = os.path.expanduser('~/.masterlab_motor.json')
MARCA = os.path.expanduser('~/.masterlab_forzar_gpu')
_cache = None

def forzado():
    valor = os.environ.get('MASTERLAB_FORZAR_GPU', '').strip().lower()
    if valor in ('1', 'si', 'sí', 'true', 'yes', 'on', 'gpu', 'cuda'):
        return True
    if valor in ('0', 'no', 'false', 'off', 'cpu'):
        return False
    return os.path.exists(MARCA)

def _probar(fn, repeticiones=3):
    tiempos = []
    for _ in range(repeticiones):
        t0 = time.perf_counter()
        fn()
        tiempos.append(time.perf_counter() - t0)
    tiempos.sort()
    return tiempos[len(tiempos) // 2]

def _vulkan():
    try:
        import gpuops
        if gpuops.listo() and gpuops.backend() == 'VULKAN':
            return gpuops.describe()
    except Exception:
        pass
    return None

def _candidatos():
    salida = []
    vk = _vulkan()
    if vk:
        salida.append(('GPU', vk, 'vulkan'))
    try:
        import torch
        if torch.cuda.is_available():
            salida.append(('GPU', 'CUDA · ' + torch.cuda.get_device_name(0), 'torch'))
    except Exception:
        pass
    try:
        import torch
        if hasattr(torch, 'xpu') and torch.xpu.is_available():
            salida.append(('GPU', 'XPU · ' + torch.xpu.get_device_name(0), 'torch'))
    except Exception:
        pass
    try:
        import cupy
        cupy.zeros(8)
        salida.append(('GPU', 'CuPy', 'cupy'))
    except Exception:
        pass
    return salida

def _banco_numpy(escala):
    import numpy as np
    x = np.random.rand(int(2.5e6)).astype(np.float32)
    def trabajo():
        a = np.abs(x)
        b = np.sqrt(np.maximum(a * a, 1e-20))
        c = b * np.float32(0.5)
        return float(c.sum())
    return _probar(trabajo)

def _banco_torch(escala):
    import torch
    x = torch.rand(int(2.5e6), device='cuda')
    def trabajo():
        a = torch.abs(x)
        b = torch.sqrt(torch.clamp(a * a, min=1e-20))
        c = b * 0.5
        return float(c.sum().item())
    return _probar(trabajo)

def _eligiendo():
    candidatos = _candidatos()
    if not candidatos:
        return None
    cpu = _banco_numpy(1.0)
    mejor = None
    for nombre, detalle, backend in candidatos:
        try:
            gpu = _banco_torch(1.0) if backend == 'torch' else cpu
        except Exception:
            continue
        if mejor is None or gpu < mejor[0]:
            mejor = (gpu, detalle)
    if mejor is not None and mejor[0] < cpu * 0.9:
        return {'motor': 'GPU', 'detalle': mejor[1], 'segundos': round(mejor[0], 4),
                'cpu': round(cpu, 4)}
    return {'motor': 'CPU', 'detalle': 'numpy', 'segundos': round(cpu, 4)}

def motor():
    global _cache
    if _cache is not None:
        return _cache

    vk = _vulkan()
    if vk:

        _cache = {'motor': 'GPU', 'detalle': vk, 'forzado': forzado()}
        return _cache

    if forzado():

        candidatos = _candidatos()
        if candidatos:
            _cache = {'motor': 'GPU', 'detalle': candidatos[0][1], 'forzado': True}
            return _cache
        _cache = {'motor': 'CPU', 'detalle': 'numpy (forzado, sin GPU)',
                  'forzado': True, 'segundos': None}
        return _cache

    if os.path.exists(RUTA):
        try:
            _cache = json.load(open(RUTA))
            return _cache
        except Exception:
            pass

    elegido = _eligiendo()
    _cache = elegido if elegido else {'motor': 'CPU', 'detalle': 'numpy', 'segundos': None}
    try:
        json.dump(_cache, open(RUTA, 'w'))
    except Exception:
        pass
    return _cache

def elegir(recargar=True):
    global _cache
    elegido = _eligiendo()
    _cache = elegido if elegido else {'motor': 'CPU', 'detalle': 'numpy', 'segundos': None}
    try:
        json.dump(_cache, open(RUTA, 'w'))
    except Exception:
        pass
    return _cache

def describe():
    m = motor()
    if m['motor'] == 'GPU':
        return 'Motor: GPU (' + m['detalle'] + (', forzada)' if m.get('forzado') else ')')
    if m.get('forzado'):
        return 'Motor: CPU (numpy, forzado pero sin GPU)'
    return 'Motor: CPU (numpy)'

def motores():
    if motor()['motor'] == 'GPU':
        return ('GPU', 'CPU')
    return ('CPU', 'CPU')

def describe_doble():
    principal, secundario = motores()
    if principal == secundario:
        return 'Motor principal: %s' % principal
    return 'Motor principal: %s · Motor secundario: %s' % (principal, secundario)

def es_gpu():
    return motor()['motor'] == 'GPU'

def forzar(activar=True):
    global _cache
    _cache = None
    if activar:
        with open(MARCA, 'w') as f:
            f.write('gpu\n')
    else:
        try:
            os.unlink(MARCA)
        except FileNotFoundError:
            pass
    return motor()

if __name__ == '__main__':
    import sys
    orden = (sys.argv[1] if len(sys.argv) > 1 else 'estado').lower()
    if orden == 'forzar':
        m = forzar(True)
        print('Forzado:', m)
    elif orden in ('libre', 'auto'):
        elegir()
        print('Automático:', motor())
    elif orden == 'quitar':
        print('Automático:', forzar(False))
    print(describe())
    print(motor())
