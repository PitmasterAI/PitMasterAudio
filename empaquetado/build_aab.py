#!/usr/bin/env python3
"""Compila el AAB de PitMasterAudio: el mismo contenido que la APK, ofuscado a tope.

Sin Gradle: javac -> R8 (ofuscado) -> aapt2 en formato proto -> empaquetado del módulo
-> bundletool. Firma el .aab con la misma clave que la APK (clave de subida).

Uso:  python3 build_aab.py
"""
import glob
import json
import os
import shutil
import subprocess
import zipfile

SDK = os.path.expanduser('~/android-sdk-tmp')
BT = os.path.join(SDK, 'build-tools/android-14')
ANDROID_JAR = None
for cand in glob.glob(os.path.join(SDK, 'android-34*/android.jar')):
    ANDROID_JAR = cand
    break
PROY = os.path.expanduser('~/pitmasteraudio-dist/android/app')
OUT = os.path.expanduser('~/pitmasteraudio-dist')
WORK = os.path.join(SDK, 'pitmasteraudio-aab')
R8 = os.path.expanduser('~/pitmasteraudio-dist/r8.jar')
BUNDLETOOL = os.path.expanduser('~/bundletool/bundletool.jar')
FINAL = os.path.join(OUT, 'PitMasterAudio-1.0.aab')

# lo que R8 no puede tocar: lo que Android y la librería nativa buscan por nombre
REGLAS = r"""
-dontwarn **
-dontnote **
-keep class es.pitmasterai.masterlab.MainActivity { *; }
-keep class es.pitmasterai.masterlab.ServicioPrecalculado { *; }
-keep class es.pitmasterai.masterlab.motor.VulkanNativo { *; }
-keepclasseswithmembernames class * { native <methods>; }
-keepattributes Signature,InnerClasses,EnclosingMethod,*Annotation*
-repackageclasses ''
-allowaccessmodification
-overloadaggressively
-flattenpackagehierarchy 'x'
-adaptclassstrings
-optimizationpasses 5
-printmapping mapping.txt
"""


def sh(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        print('FALLO:', ' '.join(cmd)[:400])
        print((r.stdout or '')[-2000:])
        print((r.stderr or '')[-2000:])
        raise SystemExit(1)
    return r


def main():
    if os.path.exists(WORK):
        shutil.rmtree(WORK)
    os.makedirs(WORK)

    # 1. recursos en formato proto (manifest protobuf + resources.pb)
    res_zip = os.path.join(WORK, 'res.zip')
    sh([os.path.join(BT, 'aapt2'), 'compile', '--dir', os.path.join(PROY, 'res'), '-o', res_zip])
    proto = os.path.join(WORK, 'proto.zip')
    sh([os.path.join(BT, 'aapt2'), 'link', '--proto-format', '-o', proto, '-I', ANDROID_JAR,
        '--manifest', os.path.join(PROY, 'AndroidManifest.xml'), '-R', res_zip,
        '--auto-add-overlay'])

    # 2. javac
    clases = os.path.join(WORK, 'classes')
    os.makedirs(clases)
    fuentes = glob.glob(os.path.join(PROY, 'src/**/*.java'), recursive=True)
    sh(['javac', '--release', '8', '-classpath', ANDROID_JAR, '-d', clases] + fuentes)

    # 3. R8: ofusca y optimiza
    reglas = os.path.join(WORK, 'reglas.pro')
    open(reglas, 'w').write(REGLAS)
    dexout = os.path.join(WORK, 'dex')
    os.makedirs(dexout)
    class_files = glob.glob(os.path.join(clases, '**/*.class'), recursive=True)
    sh(['java', '-cp', R8, 'com.android.tools.r8.R8', '--release', '--min-api', '24',
        '--lib', ANDROID_JAR, '--pg-conf', reglas, '--output', dexout] + class_files)
    dex = os.path.join(dexout, 'classes.dex')
    if not os.path.exists(dex):
        raise SystemExit('R8 no ha dejado classes.dex')

    # 4. módulo base del bundle
    modulo = os.path.join(WORK, 'base.zip')
    with zipfile.ZipFile(modulo, 'w', zipfile.ZIP_DEFLATED) as z:
        with zipfile.ZipFile(proto) as p:
            for nombre in p.namelist():
                # dentro del módulo, las rutas van sin el nombre del módulo:
                # bundletool lo toma del nombre del fichero (base.zip -> base)
                if nombre == 'AndroidManifest.xml':
                    z.writestr('manifest/AndroidManifest.xml', p.read(nombre))
                elif nombre == 'resources.pb':
                    z.writestr('resources.pb', p.read(nombre))
                elif nombre.startswith('res/'):
                    z.writestr(nombre, p.read(nombre))
        z.write(dex, 'dex/classes.dex')
        so = os.path.expanduser('~/pitmasteraudio-dist/libmasterlabvk.so')
        if os.path.exists(so):
            z.write(so, 'lib/arm64-v8a/libmasterlabvk.so')

    # 5. bundle con bundletool
    config = os.path.join(WORK, 'BundleConfig.json')
    json.dump({'compression': {'uncompressedGlob': ['resources.pb']}}, open(config, 'w'))
    if os.path.exists(FINAL):
        os.remove(FINAL)
    sh(['java', '-jar', BUNDLETOOL, 'build-bundle', '--modules=' + modulo,
        '--output=' + FINAL, '--config=' + config])

    # 6. firma con la clave de subida (la misma de la APK)
    ks = os.path.expanduser('~/pitmasteraudio-dist/android/masterlab.keystore')
    passwd = open(os.path.expanduser('~/pitmasteraudio-dist/android/keystore_password.txt')).read().strip()
    sh(['jarsigner', '-keystore', ks, '-storepass', passwd, '-keypass', passwd,
        FINAL, 'masterlab'])
    sh(['jarsigner', '-verify', FINAL])

    # 7. comprobar que el bundle genera el mismo APK
    apks = os.path.join(WORK, 'universal.apks')
    sh(['java', '-jar', BUNDLETOOL, 'build-apks', '--bundle=' + FINAL,
        '--output=' + apks, '--mode=universal', '--ks=' + ks, '--ks-pass=pass:' + passwd,
        '--ks-key-alias=masterlab', '--key-pass=pass:' + passwd])
    univ = os.path.join(WORK, 'universal.apk')
    with zipfile.ZipFile(apks) as z:
        open(univ, 'wb').write(z.read('universal.apk'))
    badging = sh([os.path.join(BT, 'aapt2'), 'dump', 'badging', univ]).stdout
    for linea in badging.splitlines():
        if linea.startswith(('package:', 'sdkVersion', 'targetSdkVersion',
                             'application-label', 'launchable-activity')):
            print(' ', linea)
    # R8 escribe el mapping en el cwd (WORK), no en dexout
    mapa = os.path.join(WORK, 'mapping.txt')
    renombradas = sum(1 for l in open(mapa) if l and '->' in l and l.strip().endswith(':') and not l.startswith(' ')) if os.path.exists(mapa) else 0
    print('clases renombradas por R8:', renombradas)
    print('OK -> %s (%.0f KB)' % (FINAL, os.path.getsize(FINAL) / 1024))


if __name__ == '__main__':
    main()
