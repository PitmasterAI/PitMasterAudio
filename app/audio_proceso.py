#!/usr/bin/env python3
"""Proceso de sonido del panel: solo abre la tarjeta y reproduce.

Se lanza aparte desde app.py para que ningún masterizado, análisis o recolección
de basura del panel pueda dejar al hilo de audio sin turno (eso se oía como
tirones al empezar y al cambiar de ajuste).

Uso: python audio_proceso.py <puerto> <pid_del_panel>
"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, '_vendor'))   # sounddevice y pyloudnorm embebidos

import audio_nativo


def subir_prioridad():
    """El hilo de audio va por delante del trabajo pesado. Si no se puede, da igual."""
    try:
        if sys.platform.startswith('win'):
            import ctypes
            ctypes.windll.kernel32.SetPriorityClass(
                ctypes.windll.kernel32.GetCurrentProcess(), 0x00000080)  # HIGH
        else:
            os.nice(-10)
    except Exception:
        pass


def main():
    if len(sys.argv) < 2:
        print('uso: audio_proceso.py <puerto> [pid del panel]', file=sys.stderr)
        return 2
    subir_prioridad()
    audio_nativo.afinar_interprete()   # solo aquí, no en el panel
    puerto = int(sys.argv[1])
    padre = int(sys.argv[2]) if len(sys.argv) > 2 else None
    audio_nativo.servir(puerto, padre)
    return 0


if __name__ == '__main__':
    sys.exit(main())
