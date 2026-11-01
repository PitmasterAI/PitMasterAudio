

Unicode true
Name "PitMasterAudio"
OutFile "/home/iaradio/pitmasteraudio-dist/PitMasterAudio-1.0-Portable.exe"
RequestExecutionLevel user
SilentInstall silent
SetCompressor /SOLID lzma
SetCompressorDictSize 64
Icon "/home/iaradio/pitmasteraudio-dist/nsis/pitmasteraudio.ico"

!define APPVERSION "1.0"
!define SELLO "20261101-002049"
!define PAYLOAD "/home/iaradio/win-portable/PitMasterAudio-Windows"

Var CARPETA

Function .onInit
  StrCpy $CARPETA "$LOCALAPPDATA\PitMasterAudio-${APPVERSION}"
FunctionEnd

Section "Descomprimir"

  IfFileExists "$CARPETA\CONSTRUCCION.txt" 0 descomprimir
  FileOpen $0 "$CARPETA\CONSTRUCCION.txt" r
  FileRead $0 $1
  FileClose $0
  StrCmp $1 "${SELLO}" Listo descomprimir
descomprimir:
  RMDir /r "$CARPETA"
  CreateDirectory "$CARPETA"
  SetOutPath "$CARPETA"
  File /r "${PAYLOAD}\*.*"
Listo:
SectionEnd

Section "Abrir"
  Exec '"$CARPETA\PitMasterAudio.exe"'
  Quit
SectionEnd
