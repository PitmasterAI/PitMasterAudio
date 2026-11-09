
import glob
import os
import shutil
import subprocess
import urllib.request
import zipfile

BASE = os.path.expanduser('~/win-portable')
DIST = os.path.expanduser('~/pitmasteraudio-dist')
SRC = os.path.expanduser('~/PitmasterAudio')
W = os.path.join(BASE, 'PitMasterAudio-Windows')
ZIP = os.path.join(DIST, 'PitMasterAudio-1.0-Windows-portable.zip')
PY_URL = 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip'
PAQUETES = ['numpy', 'scipy', 'soundfile', 'flask', 'pyloudnorm', 'cffi', 'pycparser', 'sounddevice']

LANZAR_VBS = r'''Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")
comillas = Chr(34)
carpeta = fso.GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = carpeta
shell.Environment("PROCESS")("PUERTO") = "5077"
shell.Environment("PROCESS")("HOST") = "127.0.0.1"
shell.Environment("PROCESS")("MASTERLAB_DATA") = carpeta & "\datos"
servidor = shell.Run(comillas & carpeta & "\python\python.exe" & comillas & " " & comillas & carpeta & "\app\app.py" & comillas, 0, False)
WScript.Sleep 2500

' El perfil del navegador nace pidiendo donde guardar cada descarga: sin esto el
' boton "Descargar" del panel se guardaba el archivo en Descargas sin preguntar.
On Error Resume Next
For Each trozo In Array("datos", "datos\navegador", "datos\navegador\Default")
  If Not fso.FolderExists(carpeta & "\" & trozo) Then fso.CreateFolder carpeta & "\" & trozo
Next
preferencias = carpeta & "\datos\navegador\Default\Preferences"
If Not fso.FileExists(preferencias) Then
  Set fichero = fso.CreateTextFile(preferencias, True)
  fichero.Write "{""download"":{""prompt_for_download"":true}}"
  fichero.Close
End If
On Error GoTo 0

url = "http://127.0.0.1:5077/"
perfil = "--user-data-dir=" & comillas & carpeta & "\datos\navegador" & comillas
modoApp = "--app=" & url & " --window-size=1180,900 --autoplay-policy=no-user-gesture-required " & perfil

' Ventana propia, sin barras del navegador: igual que la ventana del AppImage.
' Se prueba Edge (viene con Windows 10/11), luego Chrome, luego Brave, luego Firefox.
' Se espera a que se cierre la ventana: al cerrarla se para el servidor.
' El perfil propio (datos\navegador) hace que sea un proceso aparte, asi el script
' sabe cuando se ha cerrado la ventana aunque el usuario tenga el navegador abierto.
Function AbrirYEsperar(navegador, argumentos)
  On Error Resume Next
  AbrirYEsperar = False
  shell.Run comillas & navegador & comillas & " " & argumentos, 1, True
  If Err.Number = 0 Then AbrirYEsperar = True
  Err.Clear
  On Error GoTo 0
End Function

' La ventana propia trae el dialogo de guardar del sistema en las descargas.
ventana = carpeta & "\ventana.exe"
If fso.FileExists(ventana) Then
  shell.Run comillas & ventana & comillas & " " & comillas & url & comillas & " --datos " & comillas & carpeta & "\datos\webview2" & comillas, 1, True
Else
  abierto = AbrirYEsperar("msedge.exe", modoApp)
  If Not abierto Then abierto = AbrirYEsperar("chrome.exe", modoApp)
  If Not abierto Then abierto = AbrirYEsperar("brave.exe", modoApp)
  If Not abierto Then abierto = AbrirYEsperar("C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", modoApp)
  If Not abierto Then abierto = AbrirYEsperar("C:\Program Files\Google\Chrome\Application\chrome.exe", modoApp)
  If Not abierto Then abierto = AbrirYEsperar("firefox.exe", "-new-window " & url)
  ' Sin navegador (por ejemplo bajo Wine): se abre la consola del .bat, que deja el panel
  ' vivo y muestra la direccion. Al cerrar esa ventana se para todo igual que la otra.
  If Not abierto Then
    shell.Run comillas & carpeta & "\PitMasterAudio.bat" & comillas, 1, True
  End If
End If

' Al cerrar la ventana se para el servidor y se libera la memoria.
' Solo se termina el python de esta carpeta, no otros python del sistema.
On Error Resume Next
Set wmi = GetObject("winmgmts:\\.\root\cimv2")
Set lista = wmi.ExecQuery("SELECT ProcessId, CommandLine FROM Win32_Process WHERE Name='python.exe'")
For Each proceso In lista
  If InStr(LCase(proceso.CommandLine), LCase(carpeta)) > 0 Then
    proceso.Terminate
  End If
Next
'''

LANZAR_BAT = r'''@echo off
title PitMasterAudio
cd /d "%~dp0"
set "PUERTO=5077"
set "HOST=127.0.0.1"
set "MASTERLAB_DATA=%~dp0datos"
if exist "%~dp0ffmpeg.exe" set "FFMPEG=%~dp0ffmpeg.exe"
if not exist "%~dp0datos\navegador\Default\Preferences" (
  mkdir "%~dp0datos\navegador\Default" 2>nul
  >"%~dp0datos\navegador\Default\Preferences" echo {"download":{"prompt_for_download":true}}
)
start "" "%~dp0python\python.exe" "%~dp0app\app.py"
timeout /t 3 >nul
if exist "%~dp0ventana.exe" (
  start "" "%~dp0ventana.exe" "http://127.0.0.1:5077/" --datos "%~dp0datos\webview2"
) else (
  start "" msedge --app=http://127.0.0.1:5077/ --window-size=1180,900 --autoplay-policy=no-user-gesture-required --user-data-dir="%~dp0datos\navegador"
)
echo PitMasterAudio en http://127.0.0.1:5077  (cierra esta ventana para parar)
pause >nul
taskkill /F /IM python.exe >nul 2>&1
'''

LEEME = '''PitMasterAudio — Windows (portable, no instala nada)
==================================================

Trae dentro Python, NumPy, SciPy, soundfile, Flask y el panel con el mismo
aspecto que la app de Android.

CÓMO USARLO
-----------
1. Descomprime la carpeta donde quieras (por ejemplo C:\\PitMasterAudio).
2. Doble clic en  PitMasterAudio.vbs  → se abre en su propia ventana.
3. Cierra esa ventana y el programa se para entero.

Si el .vbs no arrancara, usa PitMasterAudio.bat (abre una consola y el navegador).

NOTAS
-----
· La primera vez Windows puede tardar unos segundos en abrir la ventana.
· Los archivos que subas y los masterizados quedan en la carpeta  datos\\.
· Para exportar MP3 hace falta ffmpeg.exe en esta carpeta; sin él se guarda WAV.
'''


def bajar(url, destino):
    if not os.path.exists(destino):
        print('descargando', url.split('/')[-1], flush=True)
        urllib.request.urlretrieve(url, destino)
    return destino


def main():
    os.makedirs(BASE, exist_ok=True)
    if os.path.exists(W):
        shutil.rmtree(W)
    os.makedirs(os.path.join(W, 'python'), exist_ok=True)

    py_zip = bajar(PY_URL, os.path.join(BASE, 'python-embed.zip'))
    with zipfile.ZipFile(py_zip) as z:
        z.extractall(os.path.join(W, 'python'))

    wheels = os.path.join(BASE, 'wheels')
    os.makedirs(wheels, exist_ok=True)
    if not glob.glob(os.path.join(wheels, 'numpy*.whl')):
        subprocess.run([os.sys.executable, '-m', 'pip', 'download',
                        '--dest', wheels, '--only-binary=:all:',
                        '--platform', 'win_amd64', '--python-version', '3.11',
                        '--implementation', 'cp', '--abi', 'cp311'] + PAQUETES, check=True)
    lib = os.path.join(W, 'python', 'Lib', 'site-packages')
    os.makedirs(lib, exist_ok=True)
    with open(os.path.join(W, 'python', 'python311._pth'), 'w', newline='\r\n') as f:
        f.write('python311.zip\n.\nLib\\site-packages\nimport site\n')
    for whl in glob.glob(os.path.join(wheels, '*.whl')):
        with zipfile.ZipFile(whl) as z:
            z.extractall(lib)

    destino_app = os.path.join(W, 'app')
    shutil.copytree(os.path.join(SRC, 'app'), destino_app,
                    ignore=shutil.ignore_patterns('__pycache__', 'data', '*.wav', '*.mp3'))
    for fichero in ('motor.py', 'dsp.py', 'aceleracion.py', 'gpuops.py', 'vk_compute.py',
                    'paralelo.py', 'ventana.py', 'presets.json'):
        ruta = os.path.join(SRC, fichero)
        if os.path.exists(ruta):
            shutil.copy2(ruta, os.path.join(W, fichero))
    if os.path.isdir(os.path.join(SRC, 'vk')):
        shutil.copytree(os.path.join(SRC, 'vk'), os.path.join(W, 'vk'))

    with open(os.path.join(W, 'PitMasterAudio.vbs'), 'w', newline='\r\n') as f:
        f.write(LANZAR_VBS)
    ventana_cpp = os.path.join(DIST, 'ventana_win.cpp')
    sdk_webview = os.path.expanduser('~/webview2-sdk')
    if (os.path.exists(ventana_cpp) and os.path.isdir(sdk_webview)
            and shutil.which('x86_64-w64-mingw32-g++')):
        subprocess.run(['x86_64-w64-mingw32-g++', '-municode', '-mwindows', '-O2', '-std=c++17',
                        '-static', '-static-libgcc', '-static-libstdc++',
                        '-I', os.path.join(DIST, 'mingw-include'),
                        '-I', os.path.join(sdk_webview, 'include'),
                        '-o', os.path.join(W, 'ventana.exe'), ventana_cpp,
                        '-lole32', '-luuid', '-lshell32', '-lcomdlg32'], check=True)
        shutil.copy2(os.path.join(sdk_webview, 'x64', 'WebView2Loader.dll'), W)
        print('ventana propia compilada: ventana.exe + WebView2Loader.dll')

    lanzador = os.path.join(DIST, 'lanzador.c')
    if os.path.exists(lanzador) and shutil.which('x86_64-w64-mingw32-gcc'):
        subprocess.run(['x86_64-w64-mingw32-gcc', '-municode', '-mwindows', '-O2',
                        '-static', '-static-libgcc',
                        '-o', os.path.join(W, 'PitMasterAudio.exe'), lanzador,
                        '-lws2_32', '-lshell32'], check=True)
        print('lanzador compilado: PitMasterAudio.exe')

    with open(os.path.join(W, 'PitMasterAudio.bat'), 'w', newline='\r\n') as f:
        f.write(LANZAR_BAT)
    with open(os.path.join(W, 'LEEME.txt'), 'w', encoding='utf-8') as f:
        f.write(LEEME)

    print('comprimiendo', flush=True)
    subprocess.run(['zip', '-qr9', ZIP, os.path.basename(W)], cwd=BASE, check=True)
    print('OK ->', ZIP, round(os.path.getsize(ZIP) / 1e6, 1), 'MB')


if __name__ == '__main__':
    main()
