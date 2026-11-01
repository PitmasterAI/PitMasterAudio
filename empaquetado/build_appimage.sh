#!/bin/bash

set -e
APP=~/appimage-build/PitMasterAudio.AppDir/usr/pitmasteraudio
SRC=~/PitmasterAudio
SAL=~/pitmasteraudio-dist/PitMasterAudio-x86_64.AppImage

MODULOS="motor.py dsp.py aceleracion.py gpuops.py vk_compute.py paralelo.py ventana.py"
for f in "$APP"/*.py; do
  n=$(basename "$f")
  case " $MODULOS " in
    *" $n "*) [ -f "$SRC/$n" ] || rm -f "$f" ;;
    *) rm -f "$f" ;;
  esac
done
for m in $MODULOS; do cp "$SRC/$m" "$APP"/; done
cp "$SRC"/presets.json "$APP"/
rm -rf "$APP"/vk
cp -r "$SRC"/vk "$APP"/vk

rm -rf "$APP"/app
cp -r "$SRC"/app "$APP"/app
rm -f "$APP"/_prueba_*.py
rm -rf "$APP"/app/data "$APP"/app/__pycache__ "$APP"/app/*.log
find "$APP" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true

for f in app/app.py app/analiza.py app/static/app.js app/static/style.css app/templates/index.html; do
  if ! cmp -s "$SRC/$f" "$APP/$f"; then echo "NO COINCIDE: $f"; exit 1; fi
done
echo "ficheros copiados y verificados"

ICONOS=~/pitmasteraudio-dist/iconos
if [ -f "$ICONOS/icono-256.png" ]; then
  cp "$ICONOS/icono-256.png" ~/appimage-build/PitMasterAudio.AppDir/pitmasteraudio.png
  cp "$ICONOS/icono-256.png" ~/appimage-build/PitMasterAudio.AppDir/.DirIcon
  mkdir -p ~/appimage-build/PitMasterAudio.AppDir/usr/share/icons/hicolor/256x256/apps
  cp "$ICONOS/icono-256.png" ~/appimage-build/PitMasterAudio.AppDir/usr/share/icons/hicolor/256x256/apps/pitmasteraudio.png
  echo "iconos actualizados"
fi

rm -f "$SAL"
cd ~/appimage-build
ARCH=x86_64 ./appimagetool --no-appstream "$PWD/PitMasterAudio.AppDir" "$SAL" 2>&1 | tail -3 || \
  ARCH=x86_64 ./appimagetool --appimage-extract-and-run --no-appstream "$PWD/PitMasterAudio.AppDir" "$SAL" 2>&1 | tail -3
ls -la "$SAL"
md5sum "$SAL"
