import json
import numpy as np
from scipy import signal
import pyloudnorm as pyln

NOMBRES = {
    'base_equilibrado': ('Amplificador', 'Balance tonal neutro, no toca el color'),
    'base_caliente': ('Caliente', 'Bajos con cuerpo y medios claros'),
    'base_claro': ('Claro', 'Agudos abiertos, más aire arriba'),
    'base_retro': ('Retro', 'Saturación cálida de cinta'),
    'base_neutra': ('Neutra', 'Compresión suave, casi no se nota'),
    'base_amplia': ('Amplia', 'Escena estéreo abierta'),
    'base_film': ('Film', 'Saturación intensa, sonido grande'),
    'base_potente': ('Potente', 'Graves y agudos con más pegada'),
    'voz_clara': ('Audiolibro', 'Voz hablada: quita retumbe y aclara la dicción sin saturar'),
    'podcast': ('Podcast', 'Voz al frente, compresión firme y nivel −16 LUFS'),
}

OTRAS = {
    'alt_low_brighter': ('Aire', 'Poca compresión, timbre muy brillante'),
    'alt_low_bright': ('Luminosa', 'Poca compresión, timbre brillante'),
    'alt_low_neutral': ('Sencilla', 'Poca compresión, timbre neutro'),
    'alt_low_warm': ('Suave', 'Poca compresión, timbre cálido'),
    'alt_low_warmer': ('Terciopelo', 'Poca compresión, timbre muy cálido'),
    'alt_medium_brighter': ('Chispa', 'Compresión media, timbre muy brillante'),
    'alt_medium_bright': ('Viva', 'Compresión media, timbre brillante'),
    'alt_medium_neutral': ('Habitual', 'Compresión media, timbre neutro'),
    'alt_medium_warm': ('Cálida', 'Compresión media, timbre cálido'),
    'alt_medium_warmer': ('Sedosa', 'Compresión media, timbre muy cálido'),
    'alt_high_brighter': ('Deslumbrante', 'Mucha compresión, timbre muy brillante'),
    'alt_high_bright': ('Radiante', 'Mucha compresión, timbre brillante'),
    'alt_high_neutral': ('Firme', 'Mucha compresión, timbre neutro'),
    'alt_high_warm': ('Densa', 'Mucha compresión, timbre cálido'),
    'alt_high_warmer': ('Oscura', 'Mucha compresión, timbre muy cálido'),
}

INTENSIDAD_ES = {'Low': 'Suave', 'Medium': 'Medio', 'High': 'Intenso'}
EQ_ES = {'Brighter': 'muy brillante', 'Bright': 'brillante', 'Neutral': 'neutro',
         'Warm': 'cálido', 'Warmer': 'muy cálido'}

def nombre(clave):
    if clave in NOMBRES:
        return NOMBRES[clave][0]
    if clave in OTRAS:
        return OTRAS[clave][0]
    return clave

def descripcion(clave):
    if clave in NOMBRES:
        return NOMBRES[clave][1]
    if clave in OTRAS:
        return OTRAS[clave][1]
    return ''

def _energia_banda(x, sr, centro):
    sos_bajo = signal.butter(2, min(centro * 1.4, sr / 2 * 0.9) / (sr / 2), 'low', output='sos')
    sos_alto = signal.butter(2, max(centro * 0.7, 20) / (sr / 2), 'high', output='sos')
    y = signal.sosfiltfilt(sos_bajo, x, axis=0)
    y = signal.sosfiltfilt(sos_alto, y, axis=0)
    return float(np.mean(y ** 2))

def analizar(x, sr):
    mono = x.mean(axis=1)
    lufs = float(pyln.Meter(sr).integrated_loudness(x.astype(np.float64)))
    pico = float(np.max(np.abs(x)))
    rms = float(np.sqrt(np.mean(x ** 2)))
    cresta = 20 * np.log10(max(pico, 1e-9) / max(rms, 1e-9))
    corr = 1.0
    if x.shape[1] > 1:
        corr = float(np.corrcoef(x[:, 0], x[:, 1])[0, 1])
    graves = _energia_banda(mono, sr, 110.0)
    medios = _energia_banda(mono, sr, 1000.0)
    agudos = _energia_banda(mono, sr, 8000.0)
    ref = max(medios, 1e-12)

    def finito(valor, defecto=0.0):
        try:
            numero = float(valor)
        except (TypeError, ValueError):
            return defecto
        if numero != numero or numero in (float('inf'), float('-inf')):
            return defecto
        return numero

    return {
        'lufs': round(finito(lufs, -70.0), 2),
        'cresta': round(finito(cresta, 0.0), 2),
        'correlacion': round(finito(corr, 1.0), 3),

        'graves_db': round(finito(10 * np.log10(max(graves, 1e-12) / ref) - SESGO_GRAVES_DB, -6.0), 2),
        'agudos_db': round(finito(10 * np.log10(max(agudos, 1e-12) / ref), -6.0), 2),
    }

def _perfil_preset(preset):
    g = m = a = 0.0
    ng = nm = na = 0
    for f, v in preset.get('eq', []):
        if f < 150:
            g += v; ng += 1
        elif f < 3000:
            m += v; nm += 1
        else:
            a += v; na += 1
    return (g / ng if ng else 0.0, m / nm if nm else 0.0, a / na if na else 0.0)

def _acotar(v, lo, hi):
    return lo if v < lo else hi if v > hi else v

ORDEN_APP = (
    'alt_high_bright', 'alt_high_brighter', 'alt_high_neutral', 'alt_high_warm',
    'alt_high_warmer', 'alt_low_bright', 'alt_low_brighter', 'alt_low_neutral',
    'alt_low_warm', 'alt_low_warmer', 'alt_medium_bright', 'alt_medium_brighter',
    'alt_medium_neutral', 'alt_medium_warm', 'alt_medium_warmer', 'base_amplia',
    'base_caliente', 'base_claro', 'base_equilibrado', 'base_film', 'base_neutra',
    'base_potente', 'base_retro', 'voz_clara', 'podcast',
)
_ORDEN_APP = {c: i for i, c in enumerate(ORDEN_APP)}

_ESCALA_APP = {'voz_clara': 0.65, 'podcast': 0.8}

SESGO_GRAVES_DB = 0.5

def _silencio(x, sr):
    paso = max(1, int(sr) // 50)
    n = x.shape[0] // paso
    if n <= 0:
        return 0.0
    bloques = x[:n * paso, 0].astype(np.float64).reshape(n, paso)
    rms = np.sqrt(np.mean(bloques ** 2, axis=1))
    pico = float(np.max(rms))
    if pico <= 0:
        return 0.0
    return round(float(np.count_nonzero(rms < pico * 0.0178)) / n, 3)

def puntuar(perfil, presets):
    graves_db = float(perfil.get('graves_db', 0.0))
    agudos_db = float(perfil.get('agudos_db', 0.0))
    cresta = float(perfil.get('cresta', 12.0))
    lufs = float(perfil.get('lufs', -14.0))
    corr = float(perfil.get('correlacion', 1.0))

    silencio = float(perfil.get('silencio', 0.0) or 0.0)

    necesita_graves = _acotar(2.0 - graves_db, -3.0, 3.0)
    necesita_agudos = _acotar(0.0 - agudos_db, -6.0, 6.0)

    aplastado = cresta < 10.0
    flojo = lufs < -20.0
    estrecho = corr > 0.95
    abierto = corr < 0.35

    voz = silencio >= 0.06 and cresta >= 12.0 and lufs < -16.0
    sin_dinamica = lufs < -28.0 or cresta < 9.0

    notas = []
    for clave, p in presets.items():
        pg = _perfil_preset(p)
        w_graves = 0.25 if voz else 1.0
        w_agudos = 0.5 if voz else 1.0
        nota = 10.0 - (w_graves * abs(necesita_graves - pg[0])
                       + 0.6 * abs(pg[1])
                       + w_agudos * abs(necesita_agudos - pg[2]))

        escala = p.get('comp_scale')
        escala = float(_ESCALA_APP.get(clave, 1.0) if escala is None else escala)
        lado = float((p.get('width') or {}).get('side_db') or 0.0)
        mezcla = float((p.get('sat') or {}).get('mix') or 0.0)
        hpf = float(p.get('hpf_hz') or 0.0)

        if aplastado and escala > 0.85:
            nota -= 3.0
        if flojo and escala < 0.6:
            nota -= 1.5
        if estrecho and lado < 2.0:
            nota -= 1.0
        if abierto and lado > 5.0:
            nota -= 1.0

        if voz:
            nota += 2.0 if mezcla < 0.15 else -1.5
            if pg[0] > 1.0:
                nota -= 1.5
            if hpf >= 60.0:
                nota += 0.5

        es_voz = clave in ('voz_clara', 'podcast')
        if voz and es_voz:
            nota += 5.0

            if (clave == 'podcast') == (silencio < 0.15):
                nota += 1.5
        if not voz and es_voz:
            nota -= 3.0

        if sin_dinamica:
            nota += 1.5 if abs(pg[0]) + abs(pg[2]) < 2.0 else -1.0

        notas.append((clave, round(max(0.0, nota), 2)))
    notas.sort(key=lambda t: (-t[1], _ORDEN_APP.get(t[0], len(ORDEN_APP))))
    return notas

SUBIDA_AUTO_DB = 1.5

def auto_ajuste(perfil, preset_lufs=None, neutro_lufs=None):
    lufs_in = float(perfil.get('lufs', -14.0))
    cresta = float(perfil.get('cresta', 12.0))
    base = float(preset_lufs) if preset_lufs is not None else lufs_in
    desplazamiento = max(-1.5, min(1.5, 0.30 * (cresta - 14.0)))

    objetivo = max(-16.0, min(-6.0, base + desplazamiento + SUBIDA_AUTO_DB))
    intensidad = max(0.50, min(1.20, 0.55 + (cresta - 9.0) * 0.05))
    return {'lufs': round(objetivo, 1), 'intensidad': round(intensidad, 2),
            'ganancia_predicha': round(objetivo - lufs_in, 2)}

def recomendar(x, sr, presets):
    perfil = analizar(x, sr)

    interno = dict(perfil, silencio=_silencio(x, sr))
    orden = puntuar(interno, presets)
    neutro = presets.get('base_equilibrado', {}).get('lufs')
    autos = {}
    for clave, _ in orden:
        propio = presets.get(clave, {}).get('lufs')
        autos[clave] = auto_ajuste(perfil, propio, neutro)['lufs']
    return {
        'perfil': perfil,
        'auto': dict(auto_ajuste(perfil, presets.get(orden[0][0], {}).get('lufs'), neutro),
                     ajuste=orden[0][0]),
        'auto_lufs': autos,
        'orden': [{'clave': c, 'nombre': nombre(c), 'descripcion': descripcion(c), 'nota': n}
                  for c, n in orden],
        'recomendado': orden[0][0],
    }
