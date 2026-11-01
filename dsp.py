import ctypes
import os

import numpy as np

_KERNEL = None
_KERNEL_PROBADO = False

def _kernel():
    global _KERNEL, _KERNEL_PROBADO
    if _KERNEL_PROBADO:
        return _KERNEL
    _KERNEL_PROBADO = True
    aqui = os.path.dirname(os.path.abspath(__file__))
    for nombre in ('kernel.so', 'kernel.dll', 'libkernel.so'):
        for carpeta in (aqui, os.path.join(aqui, 'app')):
            ruta = os.path.join(carpeta, nombre)
            if not os.path.exists(ruta):
                continue
            try:
                lib = ctypes.CDLL(ruta)
                f32 = np.ctypeslib.ndpointer(np.float32, flags='C')
                f64 = np.ctypeslib.ndpointer(np.float64, flags='C')
                lib.pico_real_movil.argtypes = [f32, ctypes.c_int, ctypes.c_int, f32]
                lib.pico_real_movil_d.argtypes = [f64, ctypes.c_int, ctypes.c_int, f64]
                lib.aplicar_ganancia_d.argtypes = [f64, ctypes.c_int, ctypes.c_int, f64]
                lib.maximo_deslizante_d.argtypes = [f64, ctypes.c_int, ctypes.c_int, f64]
                lib.sos_cascada.argtypes = [f64, ctypes.c_int, ctypes.c_int, f64, ctypes.c_int]
                _KERNEL = lib
                return lib
            except Exception:
                continue
    _KERNEL = None
    return None

try:
    import aceleracion
except Exception:
    aceleracion = None

try:
    import gpuops
except Exception:
    gpuops = None

def _motor_gpu():
    try:
        if gpuops is not None:
            if gpuops.modo_hilo() == 'CPU':
                return False
            if gpuops.listo():
                return True
    except Exception:
        pass
    try:
        return aceleracion is not None and aceleracion.es_gpu()
    except Exception:
        return False
from scipy import signal

def _rbj(btype, sr, f0, gain_db=0.0, q=0.707):
    A = 10 ** (gain_db / 40.0)
    w0 = 2 * np.pi * f0 / sr
    cw, sw = np.cos(w0), np.sin(w0)
    al = sw / (2 * q)
    if btype == 'peak':
        b = [1 + al * A, -2 * cw, 1 - al * A]
        a = [1 + al / A, -2 * cw, 1 - al / A]
    elif btype == 'low_shelf':
        sq = 2 * np.sqrt(A) * al
        b = [A * ((A + 1) - (A - 1) * cw + sq),
             2 * A * ((A - 1) - (A + 1) * cw),
             A * ((A + 1) - (A - 1) * cw - sq)]
        a = [(A + 1) + (A - 1) * cw + sq,
             -2 * ((A - 1) + (A + 1) * cw),
             (A + 1) + (A - 1) * cw - sq]
    elif btype == 'high_shelf':
        sq = 2 * np.sqrt(A) * al
        b = [A * ((A + 1) + (A - 1) * cw + sq),
             -2 * A * ((A - 1) + (A + 1) * cw),
             A * ((A + 1) + (A - 1) * cw - sq)]
        a = [(A + 1) - (A - 1) * cw + sq,
             2 * ((A - 1) - (A + 1) * cw),
             (A + 1) - (A - 1) * cw - sq]
    elif btype == 'highpass':
        b = [(1 + cw) / 2, -(1 + cw), (1 + cw) / 2]
        a = [1 + al, -2 * cw, 1 - al]
    elif btype == 'lowpass':
        b = [(1 - cw) / 2, 1 - cw, (1 - cw) / 2]
        a = [1 + al, -2 * cw, 1 - al]
    else:
        raise ValueError(btype)
    b = np.array(b, dtype=np.float64); a = np.array(a, dtype=np.float64)
    return b / a[0], a / a[0]

def eq_apply(x, sr, bands):
    y = x.astype(np.float64, copy=False)
    if not bands:
        return y
    sos = []
    for bd in bands:
        b, a = _rbj(bd.get('type', 'peak'), sr, float(bd['f']),
                    float(bd.get('gain', 0.0)), float(bd.get('q', 0.707)))
        b = np.asarray(b, dtype=np.float64)
        a = np.asarray(a, dtype=np.float64)
        if a[0] != 1.0:
            b = b / a[0]
            a = a / a[0]
        sos.append(np.concatenate([b, a]))

    return signal.sosfilt(np.asarray(sos, dtype=np.float64), y, axis=0)

def eq_response(sr, bands, freqs=None):
    if freqs is None:
        freqs = np.logspace(np.log10(20), np.log10(min(20000, sr / 2 - 100)), 200)
    h = np.ones(len(freqs), dtype=np.complex128)
    for bd in bands:
        b, a = _rbj(bd.get('type', 'peak'), sr, float(bd['f']),
                    float(bd.get('gain', 0.0)), float(bd.get('q', 0.707)))
        _, hh = signal.freqz(b, a, worN=freqs, fs=sr)
        h *= hh
    return freqs, 20 * np.log10(np.abs(h) + 1e-12)

def _db(x):
    return 20 * np.log10(np.maximum(np.abs(x), 1e-9))

def _slope_gain_db(level_db, threshold, ratio, knee):
    over = level_db - threshold
    if knee <= 0:
        return np.minimum(0.0, over * (1.0 / ratio - 1.0))
    g = np.zeros_like(level_db)
    lo, hi = threshold - knee / 2, threshold + knee / 2
    m1 = level_db < lo
    m2 = level_db > hi
    m3 = ~(m1 | m2)
    g[m1] = 0.0
    g[m2] = over[m2] * (1.0 / ratio - 1.0)
    g[m3] = ((1.0 / ratio - 1.0) * (level_db[m3] - lo) ** 2) / (2 * knee)
    return g

def _compress_gpu(x, sr, threshold, ratio, attack_ms, release_ms, knee_db,
                  makeup_db, rms_win_ms, link):
    import torch
    from scipy.ndimage import uniform_filter1d
    from scipy.signal import lfilter as _lf

    mono = np.max(np.abs(x), axis=1) if (link and x.ndim > 1) else \
        np.abs(x if x.ndim == 1 else x.mean(axis=1))
    w = max(1, int(sr * rms_win_ms / 1000))
    if w > 1:
        mono = np.sqrt(np.maximum(uniform_filter1d(mono ** 2, w, mode='nearest'), 1e-20))
    lvl = _db(mono)
    a_at = np.exp(-1.0 / (max(attack_ms, 0.1) * 1e-3 * sr))
    a_rl = np.exp(-1.0 / (max(release_ms, 0.1) * 1e-3 * sr))
    lv = _lf([1 - a_at], [1, -a_at], lvl)
    lv = np.maximum(lv, _lf([1 - a_rl], [1, -a_rl], lv))
    red = _slope_gain_db(lv, threshold, ratio, knee_db)
    gain = np.power(10.0, (red + makeup_db) / 20.0).astype(np.float32)

    canales = x.shape[1] if x.ndim > 1 else 1
    salida = gpuops.mul_por_vector(x, gain, canales) if gpuops is not None else None
    if salida is not None:
        return salida
    t = torch.from_numpy(np.ascontiguousarray(x, dtype=np.float32)).cuda()
    g = torch.from_numpy(gain).cuda()
    salida = t * g[:, None] if t.dim() > 1 else t * g
    return salida.cpu().numpy()

def compress(x, sr, threshold=-20.0, ratio=2.0, attack_ms=20.0,
             release_ms=200.0, knee_db=6.0, makeup_db=0.0,
             rms_win_ms=10.0, link=True):
    if _motor_gpu():
        try:
            return _compress_gpu(x, sr, threshold, ratio, attack_ms, release_ms,
                                 knee_db, makeup_db, rms_win_ms, link)
        except Exception:
            pass
    from scipy.ndimage import uniform_filter1d
    mono = np.max(np.abs(x), axis=1) if (link and x.ndim > 1) else np.abs(x if x.ndim == 1 else x.mean(axis=1))
    w = max(1, int(sr * rms_win_ms / 1000))
    if w > 1:
        mono = np.sqrt(np.maximum(uniform_filter1d(mono ** 2, w, mode='nearest'), 1e-20))
    lvl = _db(mono)

    a_at = np.exp(-1.0 / (max(attack_ms, 0.1) * 1e-3 * sr))
    a_rl = np.exp(-1.0 / (max(release_ms, 0.1) * 1e-3 * sr))
    lvl_s = signal.lfilter([1 - a_at], [1, -a_at], lvl)
    lvl_s = np.maximum(lvl_s, signal.lfilter([1 - a_rl], [1, -a_rl], lvl_s))

    red = _slope_gain_db(lvl_s, threshold, ratio, knee_db)
    gain = 10 ** ((red + makeup_db) / 20.0)
    return x * gain[:, None] if x.ndim > 1 else x * gain

def _crossover(x, sr, f, kind='low'):
    sos = signal.butter(2, f / (sr / 2), kind, output='sos')
    return signal.sosfiltfilt(sos, x, axis=0)

def compress_multiband(x, sr, cross=250.0, settings=None):
    settings = settings or {}
    lof = settings.get('low', {}); hif = settings.get('high', {})
    lo = _crossover(x, sr, cross, 'low')
    hi = x - lo
    if lof:
        lo = compress(lo, sr, **lof)
    if hif:
        hi = compress(hi, sr, **hif)
    return lo + hi

def _a_torch(x):
    import torch
    return torch.from_numpy(np.ascontiguousarray(x, dtype=np.float32)).cuda()

def _a_numpy(t):
    return t.detach().cpu().numpy()

def picos_saturacion(x, drive_db=0.0, even=0.0):
    k = float(10 ** (drive_db / 20.0))
    pico_seco = float(np.max(np.abs(x))) if x.size else 0.0
    if not even:

        return (float(np.tanh(k * pico_seco)), pico_seco, 0.0)
    wet = gpuops.saturar(x, k) if gpuops is not None else None
    if wet is None:
        wet = np.tanh(x * k)
    media = float(np.mean(wet ** 2))
    wet = wet + float(even) * (wet ** 2 - media)
    return (float(np.max(np.abs(wet))), pico_seco, media)

def _saturate_gpu(x, sr, drive_db, mix, even, tone_hz, picos=None):
    k = float(10 ** (drive_db / 20.0))
    wet = gpuops.saturar(x, k) if gpuops is not None else None
    if wet is None:
        import torch
        t = _a_torch(x)
        wet = _a_numpy(torch.tanh(t * k))
    pico_wet, pico_dry, media = picos if picos else picos_saturacion(x, drive_db, even)
    if even:
        wet = wet + float(even) * (wet ** 2 - media)
    wet = wet / max(pico_wet, 1e-9) * max(pico_dry, 1e-9)
    if tone_hz and tone_hz < sr / 2:
        sos = signal.butter(2, tone_hz / (sr / 2), 'low', output='sos')
        wet = signal.sosfilt(sos, wet, axis=0)
    return (1 - mix) * x + mix * wet

def saturate(x, sr, drive_db=0.0, mix=0.25, even=0.0, tone_hz=12000.0, picos=None):
    if _motor_gpu():
        try:
            return _saturate_gpu(x, sr, drive_db, mix, even, tone_hz, picos)
        except Exception:
            pass
    k = 10 ** (drive_db / 20.0)
    xn = x * k
    wet = np.tanh(xn)
    pico_wet, pico_dry, media = picos if picos else picos_saturacion(x, drive_db, even)
    if even:
        wet = wet + even * (wet ** 2 - media)
    if tone_hz and tone_hz < sr / 2:
        sos = signal.butter(2, tone_hz / (sr / 2), 'low', output='sos')
        wet = signal.sosfilt(sos, wet, axis=0)
    wet = wet / max(pico_wet, 1e-9) * max(pico_dry, 1e-9)
    return (1 - mix) * x + mix * wet

def _stereo_gpu(x, side_gain_db, mid_gain_db):
    gm = float(10 ** (mid_gain_db / 20.0))
    gl = float(10 ** (side_gain_db / 20.0))
    salida = gpuops.estereo_ms(x, gm, gl) if gpuops is not None else None
    if salida is not None:
        return salida
    import torch
    t = _a_torch(x)
    izq, der = t[:, 0], t[:, 1]
    medio = (izq + der) * 0.5
    lado = (izq - der) * 0.5
    salida = torch.stack([medio * gm + lado * gl, medio * gm - lado * gl], dim=1)
    return _a_numpy(salida)

def stereo_width(x, side_gain_db=0.0, mid_gain_db=0.0):
    if x.ndim == 1:
        return x
    if _motor_gpu():
        try:
            return _stereo_gpu(x, side_gain_db, mid_gain_db)
        except Exception:
            pass
    m = (x[:, 0] + x[:, 1]) / 2
    s = (x[:, 0] - x[:, 1]) / 2
    m *= 10 ** (mid_gain_db / 20.0)
    s *= 10 ** (side_gain_db / 20.0)
    return np.stack([m + s, m - s], axis=1)

def reverb(x, sr, room=0.3, damp=0.5, wet=0.0, width=1.0):
    if wet <= 0:
        return x
    try:
        from pedalboard import Reverb
    except Exception:
        return x
    r = Reverb(room_size=float(room), damping=float(damp), wet_level=float(wet),
               dry_level=1.0, width=float(width))
    return r.process(x.astype(np.float32), sr, reset=True).astype(np.float64)

def _tp_env_cpu(x, sr, block_s=10.0):
    n = len(x)
    out = np.zeros(n, dtype=np.float32)
    bs = max(1, int(block_s * sr))
    ctx = 64
    for s in range(0, n, bs):
        e = min(n, s + bs)

        ini = max(0, s - ctx)
        seg = x[ini:min(n, e + ctx)]
        ov = signal.resample_poly(seg, 4, 1, axis=0)
        pk = np.max(np.abs(ov), axis=1) if ov.ndim > 1 else np.abs(ov)
        m = len(seg)
        if len(pk) >= 4 * m:
            pk = pk[:4 * m].reshape(m, 4).max(axis=1)
        else:
            pk = np.interp(np.linspace(0, 1, m), np.linspace(0, 1, len(pk)), pk)
        off = s - ini
        out[s:e] = np.maximum(out[s:e], pk[off:off + (e - s)].astype(np.float32))
    return out

_ramas_cache = None

def _fases_polifasicas():
    global _ramas_cache
    if _ramas_cache is None:
        import torch
        h = signal.firwin(20 * 4 + 1, 1.0 / 4, window=('kaiser', 5.0)) * 4
        fases = [(h[0::4], 10), (h[1::4][::-1], 9), (h[2::4], 9), (h[3::4][::-1], 9)]
        _ramas_cache = [(torch.tensor(k.copy(), dtype=torch.float32).cuda(), d)
                        for k, d in fases]
    return _ramas_cache

_H_MOVIL = None

def _filtro_movil():
    global _H_MOVIL
    if _H_MOVIL is None:
        d = np.zeros(32, dtype=np.float64)
        for i in range(32):
            k = i - 16
            d[i] = (1.0 if k == 0 else np.sin(k * np.pi / 4) / (k * np.pi / 4)) \
                * 0.25 * (0.54 - 0.46 * np.cos(i * 2.0 * np.pi / 31.0))
        h = np.zeros((4, 8), dtype=np.float64)
        for fase in range(4):
            suma = sum(d[j * 4 + fase] for j in range(8))
            for j in range(8):
                h[fase, j] = d[j * 4 + fase] / suma if abs(suma) > 1e-12 else 0.0
        _H_MOVIL = h
    return _H_MOVIL

def _tp_env_movil(x, bloque=65536):

    canales = np.ascontiguousarray(x if x.ndim > 1 else x[:, None], dtype=np.float32)
    n, nc = canales.shape
    h = _filtro_movil().astype(np.float32)
    env = np.abs(canales).max(axis=1)
    ctx = 8
    for s0 in range(0, n, bloque):
        s1 = min(n, s0 + bloque)
        a = max(0, s0 - ctx)
        b = min(n, s1 + ctx)
        seg = canales[a:b]
        m = b - a
        acc = np.zeros((m, nc), dtype=np.float32)
        rato = np.empty((m, nc), dtype=np.float32)
        for fase in range(4):
            acc[:] = 0.0
            for j in range(8):
                desfase = 4 - j
                coef = h[fase, j]
                if desfase > 0:
                    trozo = rato[desfase:]
                    np.multiply(seg[:-desfase], coef, out=trozo)
                    acc[desfase:] += trozo
                elif desfase < 0:
                    k = -desfase
                    trozo = rato[:m - k]
                    np.multiply(seg[k:], coef, out=trozo)
                    acc[:m - k] += trozo
                else:
                    np.multiply(seg, coef, out=rato)
                    acc += rato
            ini = s0 - a
            fin = ini + (s1 - s0)
            np.maximum(env[s0:s1], np.abs(acc[ini:fin]).max(axis=1), out=env[s0:s1])
    return env

def _tp_env_picos(x, sr, ceiling_db, margen_db=6.0):
    from scipy.ndimage import maximum_filter1d

    canales = np.ascontiguousarray(x if x.ndim > 1 else x[:, None], dtype=np.float32)
    n = canales.shape[0]
    pico = np.abs(canales).max(axis=1)
    umbral = float(10 ** ((float(ceiling_db) - float(margen_db)) / 20.0))
    env = pico.copy()
    if not (pico >= umbral).any():
        return env

    candidatos = np.nonzero((pico >= umbral) & (pico >= maximum_filter1d(pico, 5)))[0]
    if candidatos.size == 0:
        return env
    h = _filtro_movil().astype(np.float32)
    desfases = np.arange(4, -4, -1)
    idx = np.clip(candidatos[:, None] + desfases[None, :], 0, n - 1)
    trozos = canales[idx]
    mejor = np.abs(trozos).max(axis=(1, 2))
    for fase in range(4):
        acc = (trozos * h[fase][None, :, None]).sum(axis=1)
        np.maximum(mejor, np.abs(acc).max(axis=1), out=mejor)
    np.maximum.at(env, candidatos, mejor)
    return env

def _tp_env_candidatos(x, sr, ceiling_db, margen_db=3.0, hilos=None):
    canales = np.ascontiguousarray(x if x.ndim > 1 else x[:, None], dtype=np.float32)
    n = canales.shape[0]
    pico = np.abs(canales).max(axis=1)
    umbral = float(10 ** ((float(ceiling_db) - float(margen_db)) / 20.0))
    fuera = pico < umbral
    env = pico.copy()
    if fuera.all():
        return env
    if not fuera.any():
        return _tp_env_movil(canales)

    cambio = np.diff(np.concatenate(([1], fuera.view(np.int8), [1])))
    inicios = np.nonzero(cambio == -1)[0]
    finales = np.nonzero(cambio == 1)[0]
    ctx = 32
    for ini, fin in zip(inicios, finales):
        a = max(0, int(ini) - ctx)
        b = min(n, int(fin) + ctx)
        env[a:b] = _tp_env_movil(canales[a:b])
    return env

_taps_global = None

def _taps_y_desfases():
    global _taps_global
    if _taps_global is None:
        h = signal.firwin(20 * 4 + 1, 1.0 / 4, window=('kaiser', 5.0)) * 4
        fases = [h[0::4], h[1::4][::-1], h[2::4], h[3::4][::-1]]
        largo = max(len(f) for f in fases)
        taps = np.zeros((4, largo), dtype=np.float32)
        for i, f in enumerate(fases):
            taps[i, :len(f)] = f
        _taps_global = (taps, (10, 9, 9, 9))
    return _taps_global

def _tp_env_gpu(x, sr, block_s=10.0):
    if gpuops is not None:
        taps, desfases = _taps_y_desfases()
        env = gpuops.pico_real(x, taps, desfases)
        if env is not None:
            return env.astype(np.float32)
    return _tp_env_torch(x, sr, block_s)

def _tp_env_torch(x, sr, block_s=10.0):
    import torch
    import torch.nn.functional as F

    mono = (np.ascontiguousarray(x.T) if x.ndim > 1 else np.ascontiguousarray(x[None, :]))
    canales = mono.shape[0]
    n = mono.shape[1]
    fases = _fases_polifasicas()
    out = np.zeros(n, dtype=np.float32)
    bs = max(1, int(block_s * sr))
    ctx = 64
    for s in range(0, n, bs):
        e = min(n, s + bs)
        ini = max(0, s - ctx)
        ctx_real = s - ini
        seg = torch.from_numpy(
            np.ascontiguousarray(mono[:, ini:min(n, e + ctx)], dtype=np.float32)).cuda()[None]
        cuantas = e - s
        mejor = None
        for k, desfase in fases:
            w = k.view(1, 1, -1).repeat(canales, 1, 1)

            r = F.conv1d(F.pad(seg, (desfase, k.numel() - 1)), w, groups=canales)[0]
            a = r[:, ctx_real:ctx_real + cuantas].abs()
            mejor = a if mejor is None else torch.maximum(mejor, a)
        pk = mejor.amax(dim=0).cpu().numpy()
        out[s:e] = np.maximum(out[s:e], pk)
    return out

def _tp_env(x, sr, block_s=10.0):
    if _motor_gpu():
        try:
            return _tp_env_gpu(x, sr, block_s)
        except Exception:
            pass
    return _tp_env_cpu(x, sr, block_s)

def _max_filter(pico, tam):
    from scipy.ndimage import maximum_filter1d
    if _motor_gpu():
        try:
            import torch
            import torch.nn.functional as F
            t = torch.from_numpy(np.ascontiguousarray(pico, dtype=np.float32)).cuda()
            mitad = max(0, (tam - 1) // 2)
            p = F.pad(t[None, None, :], (mitad, mitad), mode='replicate')
            r = F.max_pool1d(p, kernel_size=2 * mitad + 1, stride=1)[0, 0]
            return r.cpu().numpy().astype(np.float64)
        except Exception:
            pass
    return maximum_filter1d(pico, size=tam, mode='nearest')

def limiter(x, sr, ceiling_db=-1.0, lookahead_ms=5.0, release_ms=60.0, true_peak=True,
            env=None, escala=1.0):
    """Limitador con lookahead y techo true-peak (4x sobremuestreo, sin bajar todo el tema)."""
    ceiling = 10 ** (ceiling_db / 20.0)
    la = max(1, int(sr * lookahead_ms / 1000))

    def _envolvente(z):
        if gpuops is not None and not gpuops.en_cpu():
            return _tp_env(z, sr).astype(np.float64)
        return _tp_env_movil(z).astype(np.float64)

    peak = np.max(np.abs(x), axis=1) if x.ndim > 1 else np.abs(x)
    tp_max = 0.0
    if true_peak:
        if env is not None:
            tp_in = np.asarray(env, dtype=np.float64) * abs(float(escala))
            tp_max = float(np.max(tp_in))
        else:
            tp_in = _envolvente(x)
            tp_max = float(np.max(tp_in))
        peak = np.maximum(peak, tp_in)
    peak_la = _max_filter(peak, 2 * la + 1)
    target = np.minimum(1.0, ceiling / np.maximum(peak_la, 1e-9))
    a_rl = np.exp(-1.0 / (max(release_ms, 1.0) * 1e-3 * sr))
    g = signal.lfilter([1 - a_rl], [1, -a_rl], target)
    g = np.minimum(g, target)
    y = x * (g[:, None] if x.ndim > 1 else g)

    if true_peak:

        cota = float(np.max(tp_in * g))
        if cota <= ceiling * 1.0005:
            return y
        tp = _envolvente(y)
        if tp.max() > ceiling:
            corr = np.minimum(1.0, ceiling / np.maximum(tp, 1e-9))
            corr = _max_filter(corr, 2 * la + 1)
            corr = np.minimum(corr, signal.lfilter([1 - a_rl], [1, -a_rl], corr))
            y = y * (corr[:, None] if y.ndim > 1 else corr)
    return y

_METERS = {}

_GANANCIAS = [1.0, 1.0, 1.0, 1.41, 1.41]

def measure_lufs(x, sr):
    import threading

    import pyloudnorm as pyln

    datos = np.asarray(x, dtype=np.float64)
    if datos.ndim == 1:
        datos = np.reshape(datos, (-1, 1))
    meter = _METERS.get(sr)
    if meter is None:
        meter = pyln.Meter(sr)
        _METERS[sr] = meter
    muestras, canales = datos.shape
    tg = float(meter.block_size)
    if muestras < tg or canales > 5:
        return meter.integrated_loudness(datos)

    filtrado = datos.copy()
    etapas = list(meter._filters.values())
    contexto = int(sr)
    try:
        import motor as _motor
        hilos_total = _motor.hilos_cpu()
    except Exception:
        hilos_total = min(8, os.cpu_count() or 1)

    def _filtrar_trozo(canal, ini, fin):
        desde = max(0, ini - contexto)
        for etapa in etapas:
            trozo = filtrado[desde:fin, canal]
            salida = etapa.apply_filter(trozo)
            filtrado[ini:fin, canal] = salida[ini - desde:]

    if muestras > 4 * contexto and hilos_total > 1:
        tareas = max(1, hilos_total // max(1, canales))
        tam = max(contexto, muestras // tareas)
        tramos = [(c, ini, min(muestras, ini + tam))
                  for c in range(canales) for ini in range(0, muestras, tam)]
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=hilos_total) as pozo:
            list(pozo.map(lambda t: _filtrar_trozo(*t), tramos))
    else:
        for canal in range(canales):
            _filtrar_trozo(canal, 0, muestras)

    paso = 1.0 - float(meter.overlap)
    duracion = muestras / float(sr)
    bloques = int(np.round(((duracion - tg) / (tg * paso))) + 1)
    if bloques < 1:
        return meter.integrated_loudness(datos)
    paso_muestras = int(round(tg * paso * sr))
    if paso_muestras < 1:
        return meter.integrated_loudness(datos)
    n_pasos = int(np.ceil(muestras / paso_muestras))
    relleno = n_pasos * paso_muestras - muestras
    cuad = filtrado * filtrado
    if relleno:
        cuad = np.vstack([cuad, np.zeros((relleno, canales))])
    por_paso = cuad.reshape(n_pasos, paso_muestras, canales).sum(axis=1)
    del cuad
    acumulado = np.vstack([np.zeros((1, canales)), np.cumsum(por_paso, axis=0)])
    siguientes = np.minimum(np.arange(bloques) + 4, n_pasos)
    suma = acumulado[siguientes] - acumulado[np.arange(bloques)]
    z = (suma / (tg * sr)).T

    ganancias = np.array(_GANANCIAS[:canales])
    with np.errstate(divide='ignore', invalid='ignore'):
        l_j = -0.691 + 10.0 * np.log10(np.sum(ganancias[:, None] * z, axis=0))
        j_g = [j for j, valor in enumerate(l_j) if valor >= -70.0]
        if not j_g:
            return float('-inf')
        z_media = np.array([np.mean(z[i, j_g]) for i in range(canales)])
        gamma_r = -0.691 + 10.0 * np.log10(np.sum(ganancias * z_media)) - 10.0
        j_g = [j for j, valor in enumerate(l_j) if valor > gamma_r and valor > -70.0]
        z_media = np.nan_to_num(np.array([np.mean(z[i, j_g]) for i in range(canales)]))
        return float(-0.691 + 10.0 * np.log10(np.sum(ganancias * z_media)))

def normalize_lufs(x, sr, target=-14.0, ceiling_db=-1.0):
    cur = measure_lufs(x, sr)
    if not np.isfinite(cur):
        return x
    y = x * (10 ** ((target - cur) / 20.0))
    return y
