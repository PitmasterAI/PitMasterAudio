
import argparse, json, os, sys
from concurrent.futures import ThreadPoolExecutor
import threading

import numpy as np

_info = threading.local()

def ultima_medida():
    return dict(getattr(_info, 'datos', {}) or {})
import soundfile as sf
from scipy import signal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dsp

try:
    import aceleracion
except Exception:
    aceleracion = None

PRESETS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'presets.json')

VUELTAS_SONORIDAD = 8
MARGEN_LUFS = 0.12

def load_presets():
    with open(PRESETS_FILE) as f:
        return json.load(f)

def curve_to_bands(curve, sr, q=4.32, gain_scale=1.0, max_gain=15.0):
    bands = []
    for f, g in curve:
        if f <= 25:
            bands.append(dict(type='low_shelf', f=min(f*1.4, 200), gain=np.clip(g, -max_gain, max_gain)*gain_scale, q=0.707))
            continue
        if f >= 16000:
            bands.append(dict(type='high_shelf', f=min(f*0.8, sr/2*0.8), gain=np.clip(g, -max_gain, max_gain)*gain_scale, q=0.707))
            continue
        bands.append(dict(type='peak', f=float(f), gain=float(np.clip(g, -max_gain, max_gain)*gain_scale), q=q))
    return bands

def compensate(bands, curve, sr, iters=2):
    freqs = np.array([c[0] for c in curve], dtype=np.float64)
    target = np.array([c[1] for c in curve], dtype=np.float64)
    work = [dict(b) for b in bands]
    for _ in range(iters):
        _, resp = dsp.eq_response(sr, work, freqs)
        err = target - resp
        for b, e in zip(work, err):
            b['gain'] = float(np.clip(b['gain'] + e, -18.0, 18.0))
    return work

def hilos_cpu():
    try:
        nucleos = os.cpu_count() or 1
    except Exception:
        nucleos = 1
    try:
        trabajos = max(1, int(os.environ.get('MASTERLAB_TRABAJOS_CPU', '1')))
    except Exception:
        trabajos = 1
    return max(1, min(12, (nucleos - 1) // trabajos))

def troceado(func, y, sr, solape_s=2.0, hilos=None):
    n = int(hilos or hilos_cpu())
    total = len(y)
    solape = int(sr * solape_s)
    if n < 2 or total < 8 * solape:
        return func(y)
    trozo = max(2 * solape, total // n)
    cortes = list(range(0, total, trozo))

    modo_padre = None
    try:
        import gpuops as _gpuops
        modo_padre = _gpuops.modo_hilo()
    except Exception:
        pass

    def _hacer(k):
        if modo_padre is not None:
            try:
                import gpuops as _gpuops
                _gpuops.fijar(modo_padre)
            except Exception:
                pass
        ini = cortes[k]
        fin = cortes[k + 1] if k + 1 < len(cortes) else total
        desde = max(0, ini - solape)
        hasta = min(total, fin + solape)
        return ini, fin, desde, func(y[desde:hasta].copy())

    with ThreadPoolExecutor(max_workers=n) as pozo:
        partes = list(pozo.map(_hacer, range(len(cortes))))
    salida = np.empty_like(y)
    for ini, fin, desde, datos in partes:
        salida[ini:fin] = datos[ini - desde:ini - desde + (fin - ini)]
    return salida

def chain(x, sr, preset, intensity=1.0, verbose=False,
          loudness_mode=None, input_gain_db=None, ceiling_db=None):
    P = preset
    i = float(intensity)
    y = x.astype(np.float64, copy=True)

    y = y - y.mean(axis=0, keepdims=True)

    picos_sat = None
    _sat = P.get('sat', {})
    if _sat and float(_sat.get('mix', 0)) > 0:
        picos_sat = dsp.picos_saturacion(y, float(_sat.get('drive', 0)) * i,
                                         float(_sat.get('even', 0)))

    def _color(z):
        return _color_etapas(z, P, sr, i, picos_sat)

    y = troceado(_color, y, sr)

    return _final(y, P, sr, verbose, loudness_mode, input_gain_db, ceiling_db)

def _color_etapas(y, P, sr, i, picos_sat=None):

    hp = P.get('hpf_hz', 0)
    if hp:
        b, a = dsp._rbj('highpass', sr, float(hp), 0, 0.707)
        y = signal.lfilter(b, a, y, axis=0)

    curve = [(float(f), float(g)) for f, g in P['eq']]
    bands = compensate(curve_to_bands(curve, sr, gain_scale=i), curve, sr)
    y = dsp.eq_apply(y, sr, bands)

    mb = P.get('comp', {})
    if mb:
        cs = float(P.get('comp_scale', 1.0))
        cross = mb.get('cross', [250.0, 3000.0])
        parts = []
        lo = dsp._crossover(y, sr, cross[0], 'low')
        rest = y - lo
        mid = dsp._crossover(rest, sr, cross[1], 'low')
        hi = rest - mid
        for part, key in ((lo, 'low'), (mid, 'mid'), (hi, 'high')):
            st = mb.get(key)
            if not st:
                parts.append(part); continue
            parts.append(dsp.compress(part, sr,
                                      threshold=float(st['threshold']),
                                      ratio=1 + (float(st['ratio']) - 1) * i * cs,
                                      attack_ms=float(st.get('attack', 20)),
                                      release_ms=float(st.get('release', 200)),
                                      knee_db=float(st.get('knee', 6))))
        y = sum(parts)

    sat = P.get('sat', {})
    if sat and sat.get('mix', 0) > 0:
        y = dsp.saturate(y, sr, drive_db=float(sat.get('drive', 0)) * i,
                         mix=min(1.0, float(sat['mix']) * i),
                         even=float(sat.get('even', 0)),
                         tone_hz=float(sat.get('tone', 16000)),
                         picos=picos_sat)

    w = P.get('width', {})
    if w:
        y = dsp.stereo_width(y, side_gain_db=float(w.get('side_db', 0)) * i,
                             mid_gain_db=float(w.get('mid_db', 0)) * i)
    rv = P.get('reverb', {})
    if rv and rv.get('wet', 0) > 0:
        y = dsp.reverb(y, sr, room=float(rv.get('room', 0.3)), damp=float(rv.get('damp', 0.5)),
                       wet=float(rv['wet']) * i, width=float(rv.get('width', 1.0)))

    return y

def _envolvente(y, sr):
    try:
        en_cpu = dsp.gpuops is not None and dsp.gpuops.en_cpu()
    except Exception:
        en_cpu = True
    if not en_cpu:
        return dsp._tp_env(y, sr)

    total = len(y)
    hilos = hilos_cpu()
    solape = max(8, int(sr * 0.05))
    if hilos < 2 or total < 8 * solape:
        return dsp._tp_env_movil(y)
    trozo = max(2 * solape, total // hilos)
    cortes = list(range(0, total, trozo))

    def _hacer(k):
        ini = cortes[k]
        fin = cortes[k + 1] if k + 1 < len(cortes) else total
        desde = max(0, ini - solape)
        hasta = min(total, fin + solape)
        return ini, fin, desde, dsp._tp_env_movil(y[desde:hasta].copy())

    with ThreadPoolExecutor(max_workers=hilos) as pozo:
        partes = list(pozo.map(_hacer, range(len(cortes))))
    env = np.zeros(total, dtype=np.float32)
    for ini, fin, desde, datos in partes:
        env[ini:fin] = datos[ini - desde:ini - desde + (fin - ini)]
    return env

def _troceado_con_env(func, y, env, sr, escala, hilos, solape_s=1.0):
    total = len(y)
    solape = int(sr * solape_s)
    n = max(1, hilos)
    trozo = max(2 * solape, total // n)
    cortes = list(range(0, total, trozo))

    def _hacer(k):
        ini = cortes[k]
        fin = cortes[k + 1] if k + 1 < len(cortes) else total
        desde = max(0, ini - solape)
        hasta = min(total, fin + solape)
        trozo_env = None if env is None else env[desde:hasta]
        return ini, fin, desde, func(y[desde:hasta].copy(), trozo_env)

    with ThreadPoolExecutor(max_workers=n) as pozo:
        partes = list(pozo.map(_hacer, range(len(cortes))))
    salida = np.empty_like(y)
    for ini, fin, desde, datos in partes:
        salida[ini:fin] = datos[ini - desde:ini - desde + (fin - ini)]
    return salida

def _limitar(y, sr, P, techo, env=None, escala=1.0):
    def _uno(z, e=None):
        return dsp.limiter(z, sr, ceiling_db=techo,
                           lookahead_ms=float(P.get('lookahead_ms', 5.0)),
                           release_ms=float(P.get('limit_release_ms', 60.0)),
                           env=e, escala=escala)

    try:
        en_cpu = dsp.gpuops is not None and dsp.gpuops.en_cpu()
    except Exception:
        en_cpu = True
    n = hilos_cpu()
    if en_cpu and n > 1 and len(y) >= 8 * int(sr):
        return _troceado_con_env(_uno, y, env, sr, escala, n)
    return _uno(y, env)

def _final(y, P, sr, verbose=False, loudness_mode=None, input_gain_db=None, ceiling_db=None):
    if loudness_mode == 'none':
        return y
    if loudness_mode == 'input':

        g = float(input_gain_db if input_gain_db is not None else 0.0)
        yy = _limitar(y * (10 ** (g / 20.0)), sr, P,
                      float(ceiling_db if ceiling_db is not None else 0.0))
        if verbose:
            print(f'  [entrada {g:+.2f} dB, techo {ceiling_db if ceiling_db is not None else 0.0} dBTP]')
        return yy

    target = float(P.get('lufs', -13.0))
    ceiling = float(ceiling_db if ceiling_db is not None else P.get('ceiling_db', -0.3))
    gain_db = 0.0
    yy = y

    env_base = _envolvente(y, sr)

    lufs_y0 = dsp.measure_lufs(y, sr)
    for _ in range(VUELTAS_SONORIDAD):
        cur = lufs_y0 + gain_db
        gain_db += (target - cur) * 0.9
        yy = _limitar(y * (10 ** (gain_db / 20.0)), sr, P, ceiling,
                      env=env_base, escala=10 ** (gain_db / 20.0))
        got = dsp.measure_lufs(yy, sr)
        if verbose:
            print(f'  [gain {gain_db:+.2f} dB -> LUFS {got:.2f} (objetivo {target})]')
        _info.datos = {'lufs': got}
        if abs(got - target) < MARGEN_LUFS:
            break
        gain_db += (target - got) * 0.9
    return yy

def read_audio(path):
    if path.lower().endswith(('.m4a', '.mp3', '.aac', '.ogg', '.opus')):
        import subprocess, tempfile
        tmp = tempfile.mktemp(suffix='.wav')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', path, '-c:a', 'pcm_f32le', tmp], check=True)
        x, sr = sf.read(tmp, dtype='float32', always_2d=True)
        os.unlink(tmp)
        return x.astype(np.float64), sr
    x, sr = sf.read(path, dtype='float32', always_2d=True)
    return x.astype(np.float64), sr

def write_audio(path, x, sr, bits=24):
    if path.lower().endswith(('.wav', '.flac')):
        sf.write(path, np.clip(x, -1, 1), sr, subtype='PCM_24' if path.endswith('.wav') else 'PCM_24')
    else:
        import subprocess
        tmp = open('/tmp/.bl_out.wav', 'wb')
        sf.write(tmp.name, np.clip(x, -1, 1), sr, subtype='PCM_24')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', tmp.name, '-b:a', '320k', path], check=True)

def main():
    ap = argparse.ArgumentParser(description='Masterizacion local estilo Referencia')
    ap.add_argument('input', nargs='*')
    ap.add_argument('-p', '--preset', default='universal')
    ap.add_argument('-o', '--output')
    ap.add_argument('-d', '--outdir')
    ap.add_argument('-i', '--intensity', type=float, default=1.0)
    ap.add_argument('-l', '--lufs', type=float, default=None,
                    help='objetivo de sonoridad de salida (por defecto el del preset)')
    ap.add_argument('--ceiling', type=float, default=None,
                    help='techo de pico real en dBTP (por defecto el del preset, -0.3)')
    ap.add_argument('--list', action='store_true')
    ap.add_argument('-v', '--verbose', action='store_true')
    a = ap.parse_args()
    presets = load_presets()
    if a.list or not a.input:
        for k, v in presets.items():
            print(f"{k:12} LUFS {v.get('lufs'):>6}  {v.get('label','')}")
        return
    key = a.preset.lower()
    if key not in presets:
        sys.exit(f"preset desconocido: {key}. Opciones: {', '.join(presets)}")
    if a.output and len(a.input) > 1:
        sys.exit('-o solo vale con un fichero de entrada; usa -d para varios')
    for path in a.input:
        x, sr = read_audio(path)
        if a.verbose:
            print(f"entrada {path}: {len(x)/sr:.1f}s {sr} Hz {x.shape[1]}ch LUFS {dsp.measure_lufs(x, sr):.2f}")
        P = dict(presets[key])
        if a.lufs is not None:
            P['lufs'] = float(a.lufs)
        y = chain(x, sr, P, intensity=a.intensity, verbose=a.verbose,
                  ceiling_db=(a.ceiling if a.ceiling is not None else None))
        if a.outdir:
            os.makedirs(a.outdir, exist_ok=True)
            out = os.path.join(a.outdir, os.path.splitext(os.path.basename(path))[0] + f'_{key}.wav')
        else:
            out = a.output or (os.path.splitext(path)[0] + f'_{key}.wav')
        write_audio(out, y, sr)
        print(f"OK -> {out}  ({len(y)/sr:.1f}s, LUFS {dsp.measure_lufs(y, sr):.2f})")

if __name__ == '__main__':
    main()
