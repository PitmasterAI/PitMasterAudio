#!/usr/bin/env python3
"""Ventana propia del panel de PitMasterAudio (GTK + WebKit).

Se abre como una ventana normal, con su icono. Al cerrarla termina el programa y
el lanzador para el servidor, así no queda nada ocupando memoria.

Si el proceso web de WebKit se cae, se vuelve a cargar el panel en vez de dejar
la ventana en blanco o cerrar la aplicación.
"""
import subprocess
import sys

URL = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:5077/'
ICONO = sys.argv[2] if len(sys.argv) > 2 else None

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk
except Exception as error:            # sin GTK no hay ventana propia
    print('sin GTK: %s' % error, file=sys.stderr)
    sys.exit(3)

WebKit2 = None
for version in ('4.1', '4.0'):
    try:
        gi.require_version('WebKit2', version)
        from gi.repository import WebKit2  # noqa: F811
        break
    except Exception:
        WebKit2 = None

if WebKit2 is None:
    print('sin WebKit2', file=sys.stderr)
    sys.exit(3)

try:
    cerrada = {'por_usuario': False}

    def al_cerrar(*_):
        cerrada['por_usuario'] = True
        Gtk.main_quit()

    ventana = Gtk.Window(title='PitMasterAudio')
    ventana.set_default_size(1180, 860)
    ventana.set_position(Gtk.WindowPosition.CENTER)
    ventana.connect('destroy', al_cerrar)
    if ICONO:
        try:
            ventana.set_icon_from_file(ICONO)
        except Exception:
            pass

    vista = WebKit2.WebView()
    try:
        ajustes = vista.get_settings()
        ajustes.set_enable_developer_extras(False)
        # sin esto WebKit no deja sonar hasta que se toca algo: el audio que carga
        # solo no arrancaría nunca
        try:
            ajustes.set_media_playback_requires_user_gesture(False)
        except Exception:
            pass
        # sin aceleración por GPU: evita que se caiga la ventana al mover audio
        try:
            ajustes.set_hardware_acceleration_policy(
                WebKit2.HardwareAccelerationPolicy.NEVER)
        except Exception:
            pass
    except Exception:
        pass

    def abrir_fuera(destino):
        """Abre una dirección en el navegador del sistema.

        Dentro de esta ventana no hay pestañas y WebKitGTK descarta en silencio las
        ventanas nuevas, así que sin esto el botón «♥ Donar» (target=_blank) no hacía
        nada al pulsarlo.
        """
        for orden in (['xdg-open', destino], ['gio', 'open', destino],
                      ['sensible-browser', destino], ['x-www-browser', destino]):
            try:
                subprocess.Popen(orden, stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL, start_new_session=True)
                return True
            except FileNotFoundError:
                continue
        return False

    def es_local(destino):
        return (not destino) or destino.startswith(('file:', 'about:', 'blob:', 'data:')) \
            or '127.0.0.1' in destino or 'localhost' in destino

    def al_crear(vista, accion, *resto):
        """Ventana nueva (target=_blank): se abre fuera, no dentro."""
        try:
            destino = accion.get_request().get_uri()
        except Exception:
            destino = None
        if destino:
            abrir_fuera(destino)
        return None

    def al_decidir(vista, decision, tipo):
        """Si el panel intenta navegar fuera de sí mismo, también se abre fuera."""
        try:
            if tipo != WebKit2.PolicyDecisionType.NAVIGATION_ACTION:
                return False
            destino = decision.get_navigation_action().get_request().get_uri()
            if destino and not es_local(destino):
                decision.ignore()
                abrir_fuera(destino)
                return True
        except Exception:
            pass
        return False

    for senal, manejador in (('create', al_crear), ('decide-policy', al_decidir)):
        try:
            vista.connect(senal, manejador)
        except Exception:
            pass

    def al_caer(*_):
        """El proceso web se ha caído: se recarga el panel en vez de cerrar."""
        print('proceso web caído, recargando %s' % URL, file=sys.stderr)
        try:
            vista.load_uri(URL)
        except Exception:
            pass

    for senal in ('web-process-crashed', 'web-process-terminated'):
        try:
            vista.connect(senal, al_caer)
        except Exception:
            pass

    vista.load_uri(URL)
    ventana.add(vista)
    ventana.show_all()
    Gtk.main()
except Exception as error:
    print('no se pudo abrir la ventana: %s' % error, file=sys.stderr)
    sys.exit(3)

# 0 = la cerró el usuario (el lanzador para el servidor); 3 = se cayó sola,
# entonces el lanzador prueba otra ventana y NO para el servidor
sys.exit(0 if cerrada['por_usuario'] else 3)
