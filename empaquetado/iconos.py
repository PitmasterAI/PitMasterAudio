
import os

from PIL import Image, ImageDraw

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(AQUI, 'iconos')
OSCURO = (18, 18, 22, 255)
MAGENTA = (227, 11, 93, 255)
TAMANOS = (1024, 512, 256, 192, 128, 96, 72, 64, 48, 32, 24, 16)
ESCALA = 4

def dibujar(lado):
    n = lado * ESCALA

    img = Image.new('RGBA', (n, n), (0, 0, 0, 255))
    d = ImageDraw.Draw(img)

    margen = n * 0.06
    aro = n * 0.03

    d.ellipse([margen, margen, n - margen, n - margen], fill=OSCURO)
    d.ellipse([margen, margen, n - margen, n - margen], outline=MAGENTA, width=int(aro))

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

    hechos[256].save(os.path.join(AQUI, 'nsis', 'pitmasteraudio.png'), 'PNG')
    print('nsis/pitmasteraudio.png (256)')

if __name__ == '__main__':
    main()
