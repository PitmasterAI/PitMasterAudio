"""Capa de GPU del motor: Vulkan primero, torch/CUDA después, CPU si no hay nada.

Vulkan es el camino que vale en todas partes (AMD, Intel, NVIDIA, Android): no
necesita CUDA ni drivers propietarios. Si el aparato no tiene driver Vulkan se
intenta torch con CUDA, y si tampoco hay, cada función devuelve None y el motor
sigue en numpy.

Todas las operaciones avisan de lo mismo: devuelven None cuando no se puede.
"""
import os
import threading

import numpy as np

try:
    import vk_compute
except Exception:                     # sin módulo Vulkan
    vk_compute = None

_torch = None
_torch_probado = False
_local = threading.local()


_MODO_GLOBAL = [None]


def fijar(modo):
    """Fija el motor del trabajo en curso: 'GPU', 'CPU' o None.

    Se guarda además como valor POR DEFECTO del proceso. La cadena reparte el trabajo
    en hilos (`motor.troceado`, `motor._troceado_con_env`) y esos hilos nacen sin
    modo; antes se iban al motor de GPU aunque el trabajo fuera el de CPU y, como el
    envoltorio Vulkan tiene un cerrojo único, se quedaban esperando turno uno detrás
    de otro: el ajuste pasaba de 8 s a 26-30 s en el panel del usuario.
    """
    _local.modo = modo
    if modo is not None:
        _MODO_GLOBAL[0] = modo


def modo_hilo():
    local = getattr(_local, 'modo', None)
    return local if local is not None else _MODO_GLOBAL[0]


def en_cpu():
    """True cuando este hilo tiene que ir en CPU a propósito."""
    return modo_hilo() == 'CPU'


def _torch_cuda():
    global _torch, _torch_probado
    if not _torch_probado:
        _torch_probado = True
        try:
            import torch
            _torch = torch if torch.cuda.is_available() else None
        except Exception:
            _torch = None
    return _torch


def _vk():
    if vk_compute is None:
        return None
    v = vk_compute.motor()
    return v if (v is not None and v.listo) else None


def listo():
    return _vk() is not None or _torch_cuda() is not None


def describe():
    v = _vk()
    if v is not None:
        return 'Vulkan · ' + v.nombre
    t = _torch_cuda()
    if t is not None:
        return 'CUDA · ' + t.cuda.get_device_name(0)
    return 'sin GPU'


def backend():
    if _vk() is not None:
        return 'VULKAN'
    if _torch_cuda() is not None:
        return 'CUDA'
    return 'CPU'


# ------------------------------------------------------------------ operaciones
def escalar(x, g):
    """x * g sobre toda la señal."""
    if en_cpu():
        return None

    v = _vk()
    if v is not None:
        try:
            return v.escalar(x, float(g)).astype(np.float64)
        except Exception:
            pass
    t = _torch_cuda()
    if t is not None:
        try:
            salida = t.from_numpy(np.ascontiguousarray(x, dtype=np.float32)).cuda() * float(g)
            return salida.cpu().numpy().astype(np.float64)
        except Exception:
            pass
    return None


def mul_por_vector(x, gan, canales=None):
    """x * gan[trama]: una ganancia distinta por muestra."""
    if en_cpu():
        return None

    if canales is None:
        canales = x.shape[1] if x.ndim > 1 else 1
    v = _vk()
    if v is not None:
        try:
            return v.mul_por_vector(x, np.asarray(gan, dtype=np.float32),
                                    int(canales)).astype(np.float64)
        except Exception:
            pass
    t = _torch_cuda()
    if t is not None:
        try:
            a = t.from_numpy(np.ascontiguousarray(x, dtype=np.float32)).cuda()
            b = t.from_numpy(np.ascontiguousarray(gan, dtype=np.float32)).cuda()
            salida = a * b[:, None] if a.dim() > 1 else a * b
            return salida.cpu().numpy().astype(np.float64)
        except Exception:
            pass
    return None


def estereo_ms(x, gm, gl):
    """Matriz medio/lado con sus ganancias (necesita dos canales)."""
    if en_cpu():
        return None

    v = _vk()
    if v is not None:
        try:
            return v.estereo_ms(x, float(gm), float(gl)).astype(np.float64)
        except Exception:
            pass
    t = _torch_cuda()
    if t is not None:
        try:
            a = t.from_numpy(np.ascontiguousarray(x, dtype=np.float32)).cuda()
            izq, der = a[:, 0], a[:, 1]
            medio = (izq + der) * 0.5 * float(gm)
            lado = (izq - der) * 0.5 * float(gl)
            return t.stack([medio + lado, medio - lado], dim=1).cpu().numpy().astype(np.float64)
        except Exception:
            pass
    return None


def saturar(x, k):
    """tanh(x * k); los armónicos pares y el filtro de tono se quedan en la CPU."""
    if en_cpu():
        return None

    v = _vk()
    if v is not None:
        try:
            return v.saturar(x, float(k)).astype(np.float64)
        except Exception:
            pass
    t = _torch_cuda()
    if t is not None:
        try:
            a = t.from_numpy(np.ascontiguousarray(x, dtype=np.float32)).cuda()
            return t.tanh(a * float(k)).cpu().numpy().astype(np.float64)
        except Exception:
            pass
    return None


def pico_real(x, taps, desfases):
    """Envolvente de pico real por fases polifásicas, muestra a muestra."""
    if en_cpu():
        return None

    v = _vk()
    if v is not None:
        try:
            return v.pico_real(x, taps, desfases).astype(np.float64)
        except Exception:
            pass
    return None


if __name__ == '__main__':
    print('backend:', backend(), '·', describe())
