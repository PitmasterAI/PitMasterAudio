
import os, shutil, subprocess, zlib, struct, secrets, glob

SDK = os.path.expanduser('~/android-sdk-tmp')
BT = os.path.join(SDK, 'build-tools/android-14')
PJ = None
for cand in glob.glob(os.path.join(SDK, 'android-34*/android.jar')) + glob.glob(os.path.join(SDK, 'platform/*/android.jar')):
    PJ = cand
    break
ANDROID_JAR = PJ
PROY = os.path.expanduser('~/pitmasteraudio-dist/android/app')
OUT = os.path.expanduser('~/pitmasteraudio-dist')
WORK = os.path.expanduser('~/android-sdk-tmp/pitmasteraudio-build')
KS = os.path.expanduser('~/pitmasteraudio-dist/android/masterlab.keystore')
KS_PASS_FILE = os.path.expanduser('~/pitmasteraudio-dist/android/keystore_password.txt')
APK_FINAL = os.path.join(OUT, 'PitMasterAudio-1.0.apk')

def png_icon(path, size=192):
    cx = cy = size / 2
    r = size * 0.44
    filas = []
    for y in range(size):
        fila = bytearray([0])
        for x in range(size):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if d <= r:
                px = (18, 18, 22)
                for i, h in enumerate([0.30, 0.52, 0.40]):
                    bx = cx + (i - 1) * size * 0.17
                    if abs(x - bx) < size * 0.075 and abs(y - cy) < size * h / 2:
                        px = (227, 11, 93)
                if d > r - size * 0.03:
                    px = (227, 11, 93)
                fila += bytes(px)
            else:
                fila += bytes((0, 0, 0))
        filas.append(bytes(fila))
    raw = b''.join(filas)

    def chunk(t, d):
        c = t + d
        return struct.pack('>I', len(d)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)

    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(raw, 9))
    png += chunk(b'IEND', b'')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'wb').write(png)

def sh(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        print('FALLO:', ' '.join(cmd))
        print((r.stdout or '')[-1500:])
        print((r.stderr or '')[-1500:])
        raise SystemExit(1)
    return r

def main():
    print('android.jar:', ANDROID_JAR)
    if os.path.exists(WORK):
        shutil.rmtree(WORK)
    os.makedirs(WORK)

    for tam, carpeta in ((192, 'mipmap-xxxhdpi'), (72, 'mipmap-hdpi')):
        destino = os.path.join(PROY, f'res/{carpeta}/ic_launcher.png')
        real = os.path.join(OUT, 'iconos', f'icono-{tam}.png')
        if os.path.exists(real):
            shutil.copy2(real, destino)
        else:
            png_icon(destino, tam)

    sh([os.path.join(BT, 'aapt2'), 'compile', '--dir', os.path.join(PROY, 'res'),
        '-o', os.path.join(WORK, 'res.zip')])

    base = os.path.join(WORK, 'base.apk')
    sh([os.path.join(BT, 'aapt2'), 'link', '-o', base, '-I', ANDROID_JAR,
        '--manifest', os.path.join(PROY, 'AndroidManifest.xml'),
        '-R', os.path.join(WORK, 'res.zip'), '--auto-add-overlay'])

    clases = os.path.join(WORK, 'classes')
    os.makedirs(clases)
    fuentes = glob.glob(os.path.join(PROY, 'src/**/*.java'), recursive=True)
    print('fuentes:', [os.path.basename(f) for f in fuentes])
    sh(['javac', '--release', '8', '-classpath', ANDROID_JAR, '-d', clases] + fuentes)

    dexout = os.path.join(WORK, 'dexout')
    os.makedirs(dexout)
    class_files = glob.glob(os.path.join(clases, '**/*.class'), recursive=True)
    sh([os.path.join(BT, 'd8'), '--release', '--lib', ANDROID_JAR, '--output', dexout] + class_files)

    sh(['zip', '-q', '-j', base, os.path.join(dexout, 'classes.dex')])

    so = os.path.expanduser('~/pitmasteraudio-dist/libmasterlabvk.so')
    if os.path.exists(so):
        os.makedirs(os.path.join(WORK, 'lib', 'arm64-v8a'), exist_ok=True)
        shutil.copy2(so, os.path.join(WORK, 'lib', 'arm64-v8a', 'libmasterlabvk.so'))
        sh(['zip', '-q', base, 'lib/arm64-v8a/libmasterlabvk.so'], cwd=WORK)

    alineado = os.path.join(WORK, 'aligned.apk')
    sh([os.path.join(BT, 'zipalign'), '-f', '4', base, alineado])

    if not os.path.exists(KS):
        passwd = secrets.token_urlsafe(18)
        sh(['keytool', '-genkeypair', '-keystore', KS, '-alias', 'pitmasteraudio',
            '-keyalg', 'RSA', '-keysize', '2048', '-validity', '10000',
            '-storepass', passwd, '-keypass', passwd,
            '-dname', 'CN=PitMasterAudio,O=PitmasterAI,C=ES'])
        open(KS_PASS_FILE, 'w').write(passwd + '\n')
        os.chmod(KS_PASS_FILE, 0o600)
        print('keystore nuevo; contraseña guardada en', KS_PASS_FILE)
    passwd = open(KS_PASS_FILE).read().strip()
    sh([os.path.join(BT, 'apksigner'), 'sign', '--ks', KS, '--ks-pass', 'pass:' + passwd,
        '--key-pass', 'pass:' + passwd, '--out', APK_FINAL, alineado])

    print(sh([os.path.join(BT, 'apksigner'), 'verify', APK_FINAL]).stdout.strip() or 'firma OK')
    badging = sh([os.path.join(BT, 'aapt2'), 'dump', 'badging', APK_FINAL]).stdout
    for linea in badging.splitlines():
        if linea.startswith(('package:', 'sdkVersion', 'targetSdkVersion', 'application-label', 'launchable-activity')):
            print(' ', linea)
    print(f'OK -> {APK_FINAL}  ({os.path.getsize(APK_FINAL)/1024:.0f} KB)')

if __name__ == '__main__':
    main()
