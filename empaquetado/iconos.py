#!/usr/bin/env python3
"""Genera los iconos de PitMasterAudio (el mismo diseño que la app de Android).

Círculo oscuro con aro magenta y tres barras de ecualizador. Se dibuja a 4x y se
reduce con LANCZOS para que los bordes queden suaves en todos los tamaños.

Escribe:
  icons/icono-<N>.png      varios tamaños para el .deb (hicolor) y la AppImage
  nsis/pitmasteraudio.ico   icono de Windows con todos los tamaños
Uso:  python3 iconos.py
"""
import os

from PIL import Image, ImageDraw

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(AQUI, 'iconos')
OSCURO = (18, 18, 22, 255)
MAGENTA = (227, 11, 93, 255)
TAMANOS = (1024, 512, 256, 192, 128, 96, 72, 64, 48, 32, 24, 16)
ESCALA = 4


def dibujar(lado):
    """Devuelve la imagen a `lado` px, dibujada a ESCALA x y reducida."""
    n = lado * ESCALA
    # fondo NEGRO OPACO, no transparente: el icono original era un cuadro negro con el
    # círculo encima, y con transparencia el lanzador lo pinta sobre su propio fondo y
    # parece otro icono (el usuario lo notó en cuanto actualizó).
    img = Image.new('RGBA', (n, n), (0, 0, 0, 255))
    d = ImageDraw.Draw(img)
    # proporciones del diseño original (el que le gustaba al usuario): círculo con
    # margen visible, aro fino y barras más cortas. Se mantiene el dibujo a 4x con
    # reducción LANCZOS, que es lo que quita los bordes dentados de antes.
    margen = n * 0.06
    aro = n * 0.03
    # disco oscuro y aro magenta
    d.ellipse([margen, margen, n - margen, n - margen], fill=OSCURO)
    d.ellipse([margen, margen, n - margen, n - margen], outline=MAGENTA, width=int(aro))
    # tres barras de ecualizador, centradas (separación de centros 0,17 del lado)
    ancho = n * 0.15
    hueco = n * 0.02
    alto_barras = (0.30, 0.52, 0.40)
    cx = n / 2.0
    for i, alto_rel in enumerate(alto_barras):
        x0 = cx + (i - 1) * (ancho + hueco) - ancho / 2.0
        alto = n * alto_rel
        d.rectangle([x0, n / 2.0 - alto / 2.0, x0 + ancho, n / 2.0 + alto / 2.0],
                    fill=MAGENTA)
    return img.resize((lado, lado), Image.LANCZOS)


def main():
    os.makedirs(SALIDA, exist_ok=True)
    hechos = {}
    for lado in TAMANOS:
        img = dibujar(lado)
        ruta = os.path.join(SALIDA, 'icono-%d.png' % lado)
        img.save(ruta, 'PNG')
        hechos[lado] = img
        print('icono-%d.png' % lado)

    grande = hechos[1024]
    ico = os.path.join(AQUI, 'nsis', 'pitmasteraudio.ico')
    grande.save(ico, format='ICO', sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)])
    print('nsis/pitmasteraudio.ico')

    # la AppImage y el instalador de Windows usan este PNG de 256
    hechos[256].save(os.path.join(AQUI, 'nsis', 'pitmasteraudio.png'), 'PNG')
    print('nsis/pitmasteraudio.png (256)')


if __name__ == '__main__':
    main()
