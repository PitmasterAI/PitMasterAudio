
import os
import subprocess
import time

DIST = os.path.expanduser('~/pitmasteraudio-dist')
PAYLOAD = os.path.expanduser('~/win-portable/PitMasterAudio-Windows')
VERSION = '1.0'
NSI = os.path.join(DIST, 'nsis', 'PitMasterAudioPortable.nsi')
SALIDA = os.path.join(DIST, f'PitMasterAudio-{VERSION}-Portable.exe')

PLANTILLA = '''; PitMasterAudio portatil: un solo .exe que se abre sin instalar nada.
; No escribe en el registro, no crea desinstalador y no pide administrador.
Unicode true
Name "PitMasterAudio"
OutFile "{salida}"
RequestExecutionLevel user
SilentInstall silent
SetCompressor /SOLID lzma
SetCompressorDictSize 64
Icon "{icono}"

!define APPVERSION "{version}"
!define SELLO "{sello}"
!define PAYLOAD "{payload}"

Var CARPETA

Function .onInit
  StrCpy $CARPETA "$LOCALAPPDATA\\PitMasterAudio-${{APPVERSION}}"
FunctionEnd

Section "Descomprimir"
  ; Si la carpeta trae la MISMA construcción, se reutiliza; si es de otra, se
  ; reemplaza entera. Sin esto, al reconstruir el paquete con la misma versión se
  ; seguían usando los ficheros viejos ya descomprimidos.
  IfFileExists "$CARPETA\\CONSTRUCCION.txt" 0 descomprimir
  FileOpen $0 "$CARPETA\\CONSTRUCCION.txt" r
  FileRead $0 $1
  FileClose $0
  StrCmp $1 "${{SELLO}}" Listo descomprimir
descomprimir:
  RMDir /r "$CARPETA"
  CreateDirectory "$CARPETA"
  SetOutPath "$CARPETA"
  File /r "${{PAYLOAD}}\\*.*"
Listo:
SectionEnd

Section "Abrir"
  Exec '"$CARPETA\\PitMasterAudio.exe"'
  Quit
SectionEnd
'''

def main():
    if not os.path.isdir(PAYLOAD):
        raise SystemExit('falta el paquete de Windows: ejecuta antes build_windows.py')
    os.makedirs(os.path.dirname(NSI), exist_ok=True)

    sello = time.strftime('%Y%m%d-%H%M%S')
    with open(os.path.join(PAYLOAD, 'CONSTRUCCION.txt'), 'w') as f:
        f.write(sello)
    print('sello de construcción:', sello)
    open(NSI, 'w').write(PLANTILLA.format(
        sello=sello,
        salida=SALIDA,
        icono=os.path.join(DIST, 'nsis', 'pitmasteraudio.ico'),
        version=VERSION,
        payload=PAYLOAD))
    if os.path.exists(SALIDA):
        os.remove(SALIDA)
    entorno = dict(os.environ)
    entorno.setdefault('TMPDIR', os.path.expanduser('~/nsis-tmp'))
    r = subprocess.run(['makensis', NSI], capture_output=True, text=True, env=entorno)
    if r.returncode != 0:
        print((r.stdout or '')[-1500:])
        print((r.stderr or '')[-1500:])
        raise SystemExit('fallo makensis')
    print('OK -> %s (%.0f MB)' % (SALIDA, os.path.getsize(SALIDA) / 1e6))

if __name__ == '__main__':
    main()
