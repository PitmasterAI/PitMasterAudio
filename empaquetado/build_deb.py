#!/usr/bin/env python3
"""Construye el paquete .deb de MasterLab (Debian/Ubuntu)."""
import os, shutil, subprocess, stat, zlib, struct

SRC = os.path.expanduser('~/PitmasterAudio')
APP = os.path.join(SRC, 'app')
VENV = os.path.expanduser('~/audio-master-venv')
DIST = os.path.expanduser('~/pitmasteraudio-dist')
BUILD = os.path.join(DIST, 'pitmasteraudio_1.0_all')
DEB = os.path.join(DIST, 'pitmasteraudio_1.0_all.deb')
VERSION = '1.0'

CONTROL = f"""Package: pitmasteraudio
Version: {VERSION}
Section: sound
Priority: optional
Architecture: all
Depends: python3 (>= 3.10), python3-numpy, python3-scipy, python3-soundfile, python3-flask, libportaudio2, ffmpeg
Recommends: python3-gi, gir1.2-webkit2-4.1
Maintainer: PitmasterAI <pitmasterai@gmail.com>
Homepage: https://www.iaradio.es
Description: PitMasterAudio - Remasterizado de Audio por Ecualizacion
 Masteriza audio en local con 25 preajustes musicales (8 estilos propios, 15
 variaciones de intensidad y color, y 2 de voz) mas recomendacion automatica
 segun el tipo de audio.
 Incluye comparacion A/B, medidas de sonoridad y descarga en WAV/MP3.
"""

LAUNCHER = """#!/bin/sh
# PitMasterAudio — servicio de usuario y ventana propia del panel.
# Al cerrar la ventana se para el servidor: no queda nada ocupando memoria.
URL="http://127.0.0.1:5077/"
ICONO="/usr/share/icons/hicolor/192x192/apps/pitmasteraudio.png"
VENTANA="/opt/pitmasteraudio/ventana.py"
PERFIL="$HOME/.local/share/pitmasteraudio/navegador"

esperar_panel() {
  i=0
  while [ "$i" -lt 80 ]; do
    if curl -s -o /dev/null --max-time 1 "$URL" 2>/dev/null; then return 0; fi
    i=$((i + 1))
    sleep 0.25
  done
  return 1
}

# 1. ventana propia con GTK + WebKit (sin barra de navegador)
# 2. si no hay WebKit, el navegador que haya en modo aplicacion (--app)
# 3. si no hay ninguno, el navegador normal (entonces NO se para el servicio)
abrir_ventana() {
  if [ -f "$VENTANA" ] && python3 -c 'import gi; gi.require_version("Gtk", "3.0")' >/dev/null 2>&1; then
    INICIO=$(date +%s)
    python3 "$VENTANA" "$URL" "$ICONO"
    RC=$?
    SEGUNDOS=$(( $(date +%s) - INICIO ))
    # 0 = la cerró el usuario, 128+ = la mataron: se para el servidor.
    # 3 = no se pudo abrir o se cayó sola: se pasa al navegador en modo aplicacion.
    if [ "$RC" -eq 0 ] || [ "$RC" -ge 128 ]; then
      # si se cerró en menos de 3 s es que no había pantalla: no se para el servidor
      [ "$SEGUNDOS" -ge 3 ] && return 0
    fi
  fi
  for NAV in google-chrome-stable google-chrome chromium chromium-browser brave-browser microsoft-edge; do
    if command -v "$NAV" >/dev/null 2>&1; then
      INICIO=$(date +%s)
      "$NAV" --app="$URL" --class=PitMasterAudio --window-size=1180,860 \
             --no-first-run --no-default-browser-check \
             --autoplay-policy=no-user-gesture-required \
             --user-data-dir="$PERFIL" >/dev/null 2>&1
      SEGUNDOS=$(( $(date +%s) - INICIO ))
      if [ "$SEGUNDOS" -lt 3 ]; then
        echo "No se ha podido abrir la ventana; el panel sigue en $URL" >&2
        continue
      fi
      return 0
    fi
  done
  # Sin Chrome/Chromium: Firefox con un perfil propio que permite el sonido automatico
  if command -v firefox >/dev/null 2>&1; then
    PERFIL_FF="${MASTERLAB_DATA:-$HOME/.local/share/pitmasteraudio}/firefox"
    mkdir -p "$PERFIL_FF"
    printf '%s\n' \
      'user_pref("media.autoplay.default", 0);' \
      'user_pref("media.autoplay.blocking_policy", 0);' \
      'user_pref("media.autoplay.block-webaudio", false);' \
      'user_pref("media.autoplay.allow-muted", true);' \
      'user_pref("browser.shell.checkDefaultBrowser", false);' \
      'user_pref("browser.startup.homepage_override.mstone", "ignore");' \
      'user_pref("datareporting.policy.dataSubmissionEnabled", false);' \
      > "$PERFIL_FF/user.js"
    INICIO=$(date +%s)
    firefox --profile "$PERFIL_FF" --new-window "$URL" >/dev/null 2>&1
    SEGUNDOS=$(( $(date +%s) - INICIO ))
    [ "$SEGUNDOS" -ge 3 ] && return 0
  fi
  xdg-open "$URL" >/dev/null 2>&1 &
  return 2
}

case "$1" in
  start)  systemctl --user start pitmasteraudio.service && echo "PitMasterAudio en $URL" ;;
  stop)   systemctl --user stop pitmasteraudio.service ;;
  status) systemctl --user status pitmasteraudio.service --no-pager ;;
  open)
    systemctl --user start pitmasteraudio.service
    if ! esperar_panel; then
      echo "El panel no ha arrancado; mira: pitmasteraudio status" >&2
      exit 1
    fi
    CERROJO="$XDG_RUNTIME_DIR/pitmasteraudio-ventanas"
    mkdir -p "$CERROJO" 2>/dev/null
    touch "$CERROJO/$$"
    abrir_ventana
    ABIERTA=$?
    rm -f "$CERROJO/$$"
    if [ "$ABIERTA" -ne 2 ]; then
      # si no queda otra ventana abierta, se para el servidor y se libera la memoria
      sleep 1
      if [ -z "$(ls -A "$CERROJO" 2>/dev/null)" ]; then
        rmdir "$CERROJO" 2>/dev/null
        systemctl --user stop pitmasteraudio.service
      fi
    fi
    ;;
  *)      echo "uso: pitmasteraudio [open|start|stop|status]" ;;
esac
"""

UNIT = """[Unit]
Description=MasterLab — masterizador local
After=default.target

[Service]
Type=simple
Environment=PUERTO=5077
Environment=HOST=0.0.0.0
Environment=MASTERLAB_DATA=%h/.local/share/masterlab
Environment=MALLOC_ARENA_MAX=2
Environment=MALLOC_TRIM_THRESHOLD_=65536
Environment=MALLOC_MMAP_THRESHOLD_=1048576
ExecStart=/usr/bin/python3 /opt/pitmasteraudio/app/app.py
Restart=on-failure
RestartSec=3

[Install]
WantedBy=default.target
"""

APPDATA = f"""<?xml version="1.0" encoding="UTF-8"?>
<component type="desktop-application">
  <id>es.pitmasterai.PitMasterAudio.desktop</id>
  <name>PitMasterAudio</name>
  <summary>Masterizado de audio por ecualización</summary>
  <developer id="es.pitmasterai">
    <name>PitmasterAI</name>
  </developer>
  <metadata_license>CC0-1.0</metadata_license>
  <project_license>LicenseRef-proprietary</project_license>
  <launchable type="desktop-id">es.pitmasterai.PitMasterAudio.desktop</launchable>
  <icon type="stock">pitmasteraudio</icon>
  <categories>
    <category>AudioVideo</category>
    <category>Audio</category>
    <category>AudioVideoEditing</category>
  </categories>
  <description>
    <p>Masteriza tus audios en local: analiza el tema, propone el ajuste que mejor le
    sienta y aplica la cadena completa (ecualización, compresión, saturación y limitador)
    sin subirlo a ningún servidor.</p>
    <p>Incluye 25 ajustes, recomendación automática por tipo de audio (música, voz,
    podcast, audiolibros) y motor Vulkan cuando la tarjeta lo permite.</p>
  </description>
  <url type="homepage">https://www.pitmasterai.es</url>
  <provides>
    <binary>pitmasteraudio</binary>
  </provides>
  <releases>
    <release version="{VERSION}" date="2026-10-30"/>
  </releases>
  <content_rating type="oars-1.1"/>
</component>
"""

DESKTOP = """[Desktop Entry]
Type=Application
Name=PitMasterAudio
GenericName=Masterizador de audio
Comment=Remasterizado de Audio por Ecualizacion
Exec=pitmasteraudio open
Icon=pitmasteraudio
Terminal=false
Categories=AudioVideo;Audio;AudioVideoEditing;
Keywords=audio;mastering;masterizado;loudness;LUFS;ecualizador;EQ;
MimeType=audio/x-wav;audio/mpeg;audio/flac;audio/ogg;audio/mp4;
StartupNotify=true
StartupWMClass=pitmasteraudio
"""

POSTINST = """#!/bin/sh
set -e
if [ -d /usr/share/icons/hicolor ]; then
  gtk-update-icon-cache -q /usr/share/icons/hicolor 2>/dev/null || true
fi
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database -q /usr/share/applications 2>/dev/null || true
fi
systemctl daemon-reload 2>/dev/null || true
# no se arranca al iniciar sesión: se enciende al abrir la ventana y se apaga al cerrarla
systemctl --global disable pitmasteraudio.service 2>/dev/null || true
exit 0
"""

PRERM = """#!/bin/sh
set -e
systemctl --global disable pitmasteraudio.service 2>/dev/null || true
exit 0
"""


def png_icon(path, size=192):
    """Icono simple: fondo negro, círculo magenta y tres barras de ecualizador."""
    cx = cy = size / 2
    r = size * 0.42
    filas = []
    barra_alto = [0.32, 0.55, 0.42]
    for y in range(size):
        fila = bytearray([0])
        for x in range(size):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if d < r:
                px = (18, 18, 22)
                # barras
                for i, h in enumerate(barra_alto):
                    bx = cx + (i - 1) * size * 0.16
                    bw = size * 0.075
                    bh = size * h
                    if abs(x - bx) < bw and abs(y - cy) < bh / 2:
                        px = (227, 11, 93)
                if d > r - 3:
                    px = (227, 11, 93)
                fila += bytes(px)
            else:
                fila += bytes((0, 0, 0))
        filas.append(bytes(fila))
    raw = b''.join(filas)

    def chunk(tipo, datos):
        c = tipo + datos
        return struct.pack('>I', len(datos)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)

    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(raw, 9))
    png += chunk(b'IEND', b'')
    open(path, 'wb').write(png)


def main():
    if os.path.exists(BUILD):
        shutil.rmtree(BUILD)
    os.makedirs(DIST, exist_ok=True)

    def dst(rel):
        p = os.path.join(BUILD, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        return p

    # motor
    for f in ('motor.py', 'dsp.py', 'presets.json', 'aceleracion.py',
              'gpuops.py', 'vk_compute.py', 'paralelo.py'):
        origen_f = os.path.join(SRC, f)
        if os.path.exists(origen_f):
            shutil.copy2(origen_f, dst('opt/pitmasteraudio/' + f))
    # shaders SPIR-V del motor Vulkan
    vkdir = os.path.join(SRC, 'vk')
    if os.path.isdir(vkdir):
        for f in os.listdir(vkdir):
            if f.endswith(('.spv', '.comp')):
                shutil.copy2(os.path.join(vkdir, f), dst('opt/pitmasteraudio/vk/' + f))
    # app
    os.makedirs(os.path.join(BUILD, 'opt/pitmasteraudio/app/templates'), exist_ok=True)
    os.makedirs(os.path.join(BUILD, 'opt/pitmasteraudio/app/static'), exist_ok=True)
    shutil.copy2(os.path.join(APP, 'app.py'), dst('opt/pitmasteraudio/app/app.py'))
    shutil.copy2(os.path.join(APP, 'analiza.py'), dst('opt/pitmasteraudio/app/analiza.py'))
    # motor de sonido propio del panel (un solo flujo de salida, sin cortes al cambiar)
    shutil.copy2(os.path.join(APP, 'audio_nativo.py'), dst('opt/pitmasteraudio/app/audio_nativo.py'))
    shutil.copy2(os.path.join(APP, 'audio_proceso.py'), dst('opt/pitmasteraudio/app/audio_proceso.py'))
    shutil.copy2(os.path.join(APP, 'templates/index.html'), dst('opt/pitmasteraudio/app/templates/index.html'))
    for f in ('style.css', 'app.js', 'idioma.js'):
        shutil.copy2(os.path.join(APP, 'static', f), dst('opt/pitmasteraudio/app/static/' + f))
    shutil.copy2(os.path.join(APP, 'README.md'), dst('opt/pitmasteraudio/app/README.md'))

    # sounddevice embebido: el paquete python3-sounddevice no existe en todas las
    # distros (en pop-os no está) y sin él el panel se quedaba sin sonido propio.
    # Solo necesita libportaudio2, que sí va como dependencia.
    vd_app = os.path.join(BUILD, 'opt/pitmasteraudio/app/_vendor')
    os.makedirs(vd_app, exist_ok=True)
    for f in ('sounddevice.py', '_sounddevice.py'):
        origen_sd = os.path.join(SRC, 'app/_vendor', f)
        if os.path.exists(origen_sd):
            shutil.copy2(origen_sd, os.path.join(vd_app, f))

    # pyloudnorm embebido (no está en apt)
    vd = os.path.join(BUILD, 'opt/pitmasteraudio/app/_vendor/pyloudnorm')
    os.makedirs(vd, exist_ok=True)
    origen = os.path.join(VENV, 'lib/python3.11/site-packages/pyloudnorm')
    for f in os.listdir(origen):
        if f.endswith('.py'):
            shutil.copy2(os.path.join(origen, f), os.path.join(vd, f))

    # ventana propia (GTK + WebKit): el panel se abre sin navegador
    for origen_v in (os.path.join(SRC, 'ventana.py'),
                     os.path.expanduser('~/appimage-build/ventana.py')):
        if os.path.exists(origen_v):
            shutil.copy2(origen_v, dst('opt/pitmasteraudio/ventana.py'))
            break

    # lanzador, unidad, escritorio, icono
    p = dst('usr/bin/pitmasteraudio')
    open(p, 'w').write(LAUNCHER)
    os.chmod(p, 0o755)
    open(dst('usr/lib/systemd/user/pitmasteraudio.service'), 'w').write(UNIT)
    open(dst('usr/share/applications/es.pitmasterai.PitMasterAudio.desktop'), 'w').write(DESKTOP)
    for tam in (16, 24, 32, 48, 64, 128, 192, 256, 512):
        destino = dst(f'usr/share/icons/hicolor/{tam}x{tam}/apps/pitmasteraudio.png')
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        real = os.path.join(DIST, 'iconos', f'icono-{tam}.png')
        if os.path.exists(real):
            shutil.copy2(real, destino)          # icono bueno, el mismo que la APK
        else:
            png_icon(destino, tam)
    # metadatos para catálogos de software (GNOME Software, KDE Discover…)
    open(dst('usr/share/metainfo/es.pitmasterai.PitMasterAudio.appdata.xml'), 'w', encoding='utf-8').write(APPDATA)
    open(dst('usr/share/doc/masterlab/copyright'), 'w', encoding='utf-8').write(
        'PitMasterAudio (PitmasterAI) — masterizacion de audio en local.\n'
        'Todos los ajustes son de elaboracion propia.\n')

    # control
    open(dst('DEBIAN/control'), 'w').write(CONTROL)
    for nombre, texto in (('postinst', POSTINST), ('prerm', PRERM)):
        p = dst('DEBIAN/' + nombre)
        open(p, 'w').write(texto)
        os.chmod(p, 0o755)
    os.chmod(os.path.join(BUILD, 'DEBIAN'), 0o755)
    for root, dirs, files in os.walk(BUILD):
        os.chmod(root, 0o755)

    r = subprocess.run(['dpkg-deb', '--build', '--root-owner-group', BUILD, DEB],
                       capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip())
    if os.path.exists(DEB):
        print(f'OK -> {DEB}  ({os.path.getsize(DEB)/1024:.0f} KB)')


if __name__ == '__main__':
    main()
