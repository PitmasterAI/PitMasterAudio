; ---------------------------------------------------------------------------
;  PitMasterAudio 1.0 - Instalador Windows (NSIS 3 / Unicode)
;  Empaqueta el arbol portatil ya construido por build_windows.py
;  Instalacion POR USUARIO (sin UAC) en %LOCALAPPDATA%\Programs\PitMasterAudio
;  para que la carpeta "datos" quede escribible junto a la app.
; ---------------------------------------------------------------------------
Unicode true
SetCompressor /SOLID lzma
SetCompressorDictSize 64
CRCCheck on
XPStyle on
RequestExecutionLevel user

!include "MUI2.nsh"
!include "LogicLib.nsh"

!define APPNAME     "PitMasterAudio"
!define APPVERSION  "1.0"
!define APIVER4     "1.0.0.0"
!define PUBLISHER   "PitmasterAI"
!define APPURL      "https://pitmasterai.es"
!define SRCDIR      "/home/iaradio/win-portable/PitMasterAudio-Windows"
!define ICONFILE    "/home/iaradio/pitmasteraudio-dist/nsis/pitmasteraudio.ico"
!define UNINSTKEY   "Software\Microsoft\Windows\CurrentVersion\Uninstall\PitMasterAudio"
!define APPSIZE_KB  183668

Name "${APPNAME} ${APPVERSION}"
OutFile "/home/iaradio/pitmasteraudio-dist/PitMasterAudio-1.0-Setup.exe"
InstallDir "$LOCALAPPDATA\Programs\PitMasterAudio"
InstallDirRegKey HKCU "${UNINSTKEY}" "InstallLocation"
BrandingText "${APPNAME} ${APPVERSION} - ${PUBLISHER}"

VIProductVersion "${APIVER4}"
VIAddVersionKey "ProductName"     "${APPNAME}"
VIAddVersionKey "ProductVersion"  "${APPVERSION}"
VIAddVersionKey "FileVersion"     "${APPVERSION}"
VIAddVersionKey "CompanyName"     "${PUBLISHER}"
VIAddVersionKey "FileDescription" "Instalador de ${APPNAME}"
VIAddVersionKey "LegalCopyright"  "(c) 2026 ${PUBLISHER}"
VIAddVersionKey "Comments"        "Masterizador de audio local: panel Flask + motor DSP"

; ------------------------------- Interfaz MUI -------------------------------
!define MUI_ICON   "${ICONFILE}"
!define MUI_UNICON "${ICONFILE}"
!define MUI_ABORTWARNING
!define MUI_WELCOMEPAGE_TITLE "Instalar ${APPNAME} ${APPVERSION}"
!define MUI_WELCOMEPAGE_TEXT "Este asistente instalara ${APPNAME} en tu cuenta de usuario.$\r$\n$\r$\nIncluye todo lo necesario: Python embebido, NumPy/SciPy, el panel web y el motor de masterizacion. No hace falta instalar nada mas ni tener permisos de administrador.$\r$\n$\r$\nOcupa unos 180 MB en disco."
!define MUI_DIRECTORYPAGE_TEXT_TOP "Elige la carpeta donde se instalara ${APPNAME}. Tus audios y proyectos se guardaran en la subcarpeta $\"datos$\"."
!define MUI_FINISHPAGE_TITLE "${APPNAME} esta listo"
!define MUI_FINISHPAGE_TEXT "${APPNAME} ${APPVERSION} se ha instalado correctamente.$\r$\n$\r$\nAl abrirlo se levanta el panel en http://127.0.0.1:5077 dentro de su propia ventana. Al cerrar esa ventana se detiene todo.$\r$\n$\r$\nTus archivos quedan en la carpeta datos."
!define MUI_FINISHPAGE_RUN
!define MUI_FINISHPAGE_RUN_TEXT "Abrir ${APPNAME} ahora"
!define MUI_FINISHPAGE_RUN_FUNCTION LaunchApp
!define MUI_FINISHPAGE_LINK "Web de ${APPNAME}"
!define MUI_FINISHPAGE_LINK_LOCATION "${APPURL}"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "Spanish"

; ------------------------------- Instalacion -------------------------------
Section "PitMasterAudio (obligatorio)" SEC_MAIN
  SectionIn RO
  SetShellVarContext current

  ; Si ya hay una version instalada, se reemplaza el programa pero se
  ; respeta la carpeta datos del usuario (File /r solo sobrescribe lo suyo).
  SetOutPath "$INSTDIR"
  File /r "${SRCDIR}\*.*"

  ; Icono propio (para accesos directos y para Agregar o quitar programas)
  SetOutPath "$INSTDIR"
  File "${ICONFILE}"

  ; Desinstalador
  WriteUninstaller "$INSTDIR\Desinstalar.exe"

  ; Registro: Agregar o quitar programas (por usuario, HKCU)
  WriteRegStr   HKCU "${UNINSTKEY}" "DisplayName"     "${APPNAME} ${APPVERSION}"
  WriteRegStr   HKCU "${UNINSTKEY}" "DisplayVersion"  "${APPVERSION}"
  WriteRegStr   HKCU "${UNINSTKEY}" "Publisher"       "${PUBLISHER}"
  WriteRegStr   HKCU "${UNINSTKEY}" "DisplayIcon"     "$INSTDIR\PitMasterAudio.ico"
  WriteRegStr   HKCU "${UNINSTKEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr   HKCU "${UNINSTKEY}" "URLInfoAbout"    "${APPURL}"
  WriteRegStr   HKCU "${UNINSTKEY}" "UninstallString" '"$INSTDIR\Desinstalar.exe"'
  WriteRegStr   HKCU "${UNINSTKEY}" "QuietUninstallString" '"$INSTDIR\Desinstalar.exe" /S'
  WriteRegDWORD HKCU "${UNINSTKEY}" "NoModify" 1
  WriteRegDWORD HKCU "${UNINSTKEY}" "NoRepair" 1
  WriteRegDWORD HKCU "${UNINSTKEY}" "EstimatedSize" ${APPSIZE_KB}

  ; Menu Inicio
  CreateDirectory "$SMPROGRAMS\${APPNAME}"
  CreateShortcut  "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\PitMasterAudio.exe" "" "$INSTDIR\PitMasterAudio.ico" 0
  CreateShortcut  "$SMPROGRAMS\${APPNAME}\Leeme.lnk" "$INSTDIR\LEEME.txt"
  CreateShortcut  "$SMPROGRAMS\${APPNAME}\Desinstalar ${APPNAME}.lnk" "$INSTDIR\Desinstalar.exe"
SectionEnd

Section "Acceso directo en el escritorio" SEC_DESKTOP
  SetShellVarContext current
  CreateShortcut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\PitMasterAudio.exe" "" "$INSTDIR\PitMasterAudio.ico" 0
SectionEnd

; --------------------------------- Funciones -------------------------------
Function LaunchApp
  ; .vbs no se puede lanzar con CreateProcess: hay que usar ShellExecute
  ExecShell "open" "$INSTDIR\PitMasterAudio.exe"
FunctionEnd

Function .onInit
  ; Aviso si ya esta instalado en otra ruta
  ReadRegStr $0 HKCU "${UNINSTKEY}" "InstallLocation"
  ${If} $0 != ""
  ${AndIf} $0 != "$INSTDIR"
    MessageBox MB_YESNO|MB_ICONQUESTION \
      "${APPNAME} ya aparece instalado en:$\r$\n$0$\r$\n$\r$\nSi continuas, se instalara otra copia en la carpeta elegida.$\r$\n$\r$\n¿Quieres continuar?" \
      IDYES +2
    Abort
  ${EndIf}
FunctionEnd

; -------------------------------- Desinstalar -------------------------------
Section "Uninstall"
  SetShellVarContext current

  Delete "$DESKTOP\${APPNAME}.lnk"
  Delete "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk"
  Delete "$SMPROGRAMS\${APPNAME}\Leeme.lnk"
  Delete "$SMPROGRAMS\${APPNAME}\Desinstalar ${APPNAME}.lnk"
  RMDir  "$SMPROGRAMS\${APPNAME}"
  DeleteRegKey HKCU "${UNINSTKEY}"

  ; ¿Conservar los audios/proyectos del usuario?
  IfFileExists "$INSTDIR\datos\*.*" 0 uninst_all
    MessageBox MB_YESNO|MB_DEFBUTTON1|MB_ICONQUESTION \
      "¿Quieres borrar tambien tus audios y proyectos guardados en:$\r$\n$INSTDIR\datos?$\r$\n$\r$\nSi respondes No, se conservaran." \
      IDYES uninst_all

    ; --- Conservar datos: borrar solo lo que instalo el instalador ---
    RMDir /r "$INSTDIR\app"
    RMDir /r "$INSTDIR\python"
    RMDir /r "$INSTDIR\vk"
    Delete "$INSTDIR\*.py"
    Delete "$INSTDIR\*.json"
    Delete "$INSTDIR\*.txt"
    Delete "$INSTDIR\*.bat"
    Delete "$INSTDIR\*.vbs"
    Delete "$INSTDIR\*.ico"
    Delete "$INSTDIR\Desinstalar.exe"
    RMDir  "$INSTDIR"       ; solo se borra si ha quedado vacia (datos la mantiene)
    Goto uninst_done

  uninst_all:
    RMDir /r "$INSTDIR"

  uninst_done:
SectionEnd
