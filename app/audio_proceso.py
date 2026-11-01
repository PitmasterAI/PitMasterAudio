
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, '_vendor'))

import audio_nativo

def subir_prioridad():
    try:
        if sys.platform.startswith('win'):
            import ctypes
            ctypes.windll.kernel32.SetPriorityClass(
                ctypes.windll.kernel32.GetCurrentProcess(), 0x00000080)
        else:
            os.nice(-10)
    except Exception:
        pass

def main():
    if len(sys.argv) < 2:
        print('uso: audio_proceso.py <puerto> [pid del panel]', file=sys.stderr)
        return 2
    subir_prioridad()
    audio_nativo.afinar_interprete()
    puerto = int(sys.argv[1])
    padre = int(sys.argv[2]) if len(sys.argv) > 2 else None
    audio_nativo.servir(puerto, padre)
    return 0

if __name__ == '__main__':
    sys.exit(main())
