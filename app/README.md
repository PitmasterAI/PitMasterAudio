# PitMasterAudio — panel local

Panel web que masteriza audio en local: subes un tema, eliges ajuste e
intensidad, escuchas A/B y descargas. Sin cuenta y sin subir nada a terceros.

## Arrancar

```bash
systemctl --user status pitmasteraudio.service     # servicio ya habilitado
# o a mano:
cd ~/pitmasteraudio-engine/app && PUERTO=5077 /usr/bin/python3 app.py
```

Abrir <http://127.0.0.1:5077>. Solo escucha en local (127.0.0.1); para entrar desde
el móvil en la LAN hay que arrancarlo con host 0.0.0.0.

## Qué hace

- **Subida**: WAV, FLAC, MP3, M4A u OGG hasta 600 MB. Se convierte a WAV 48 kHz
  estéreo y se analiza (LUFS, pico real, cresta, correlación, graves y agudos).
- **25 ajustes**: 8 estilos propios (universal, fuego, claridad, cinta, natural,
  espacial, cinemático, empuje), 15 variaciones de intensidad y timbre, y 2 de voz
  (audiolibro y podcast). Recomendación automática según el tipo de audio.
- **Intensidad** 0–200 % (100 % = el ajuste de fábrica).
- **Sonido propio**: el servidor abre la tarjeta de sonido y mantiene un único
  flujo de salida con una sola posición, así cambiar de ajuste no corta el audio ni
  lo devuelve al principio, y no depende de la política de reproducción del
  navegador. Si no hay tarjeta, el panel usa los reproductores del navegador.
- **A/B** Original / Masterizado y **descarga** en WAV 24 bits y MP3 320k.
- Medidas comparadas original vs masterizado en pantalla.

## Cómo está montado

- `app.py` — Flask. Rutas: `/api/subir`, `/api/masterizar`, `/api/estado/<id>`,
  `/api/audio/<id>/<original|master>` (con Range), `/api/descargar/<id>?formato=`
  y `/api/repro/*` (sonido propio). El proceso corre en un hilo y el panel consulta
  el estado cada 1,2 s.
- `audio_nativo.py` — motor de sonido: un flujo de salida continuo y una posición
  compartida por todas las versiones (cambio de ajuste con cruce de 10 ms).
- `static/` + `templates/` — interfaz (negro, tarjetas #08080a, acento #e30b5d).
- Motor: `../motor.py` + `../dsp.py`, ajustes en `../presets.json`.
- Datos: `data/subidos/` y `data/salidas/`.

## Verificado

- Subida de 60 s: LUFS original −16,36; masterizado con empuje −11,00 (pico −0,3),
  cresta 14,66.
- `GET /api/audio/<id>/master` responde **206** con `Content-Range` al pedir un
  tramo (necesario para que el reproductor permita buscar).
- Descarga WAV 24 bits (17,3 MB por minuto) y MP3 320k (2,4 MB por minuto).
