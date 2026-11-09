
import os
import re
import subprocess
import sys
import urllib.parse

URL = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:5077/'
ICONO = sys.argv[2] if len(sys.argv) > 2 else None
CARPETA_FIJA = os.environ.get('PITMA_GUARDAR_EN') or None

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk
    from gi.repository import GLib
except Exception as error:
    print('sin GTK: %s' % error, file=sys.stderr)
    sys.exit(3)

WebKit2 = None
for version in ('4.1', '4.0'):
    try:
        gi.require_version('WebKit2', version)
        from gi.repository import WebKit2
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
        try:
            ajustes.set_media_playback_requires_user_gesture(False)
        except Exception:
            pass
        try:
            ajustes.set_hardware_acceleration_policy(
                WebKit2.HardwareAccelerationPolicy.NEVER)
        except Exception:
            pass
    except Exception:
        pass

    def abrir_fuera(destino):

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

        try:
            destino = accion.get_request().get_uri()
        except Exception:
            destino = None
        if destino:
            abrir_fuera(destino)
        return None

    def al_decidir(vista, decision, tipo):

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

    def _nombre_sugerido(descarga, sugerido=None):

        def limpio(nombre):
            nombre = os.path.basename((nombre or '').replace('\\', '/')).strip()
            return '' if nombre in ('', '.', '..') else nombre

        try:
            respuesta = descarga.get_response()
            cabecera = respuesta.get_http_headers().get_one('Content-Disposition') if respuesta else None
            if cabecera:
                coincidencia = re.search(r"filename\*\s*=\s*UTF-8''([^;]+)", cabecera, re.I)
                if coincidencia:
                    nombre = limpio(urllib.parse.unquote(coincidencia.group(1)))
                    if nombre:
                        return nombre
                coincidencia = re.search(r'filename\s*=\s*"([^"]+)"', cabecera, re.I) \
                    or re.search(r'filename\s*=\s*([^;]+)', cabecera, re.I)
                if coincidencia:
                    nombre = limpio(urllib.parse.unquote(coincidencia.group(1)))
                    if nombre:
                        return nombre
        except Exception:
            pass
        if sugerido:
            return sugerido
        try:
            uri = descarga.get_request().get_uri() or ''
            nombre = limpio(urllib.parse.unquote(uri.rsplit('/', 1)[-1].split('?')[0]))
            if nombre:
                return nombre
        except Exception:
            pass
        return 'masterizado.wav'

    def _carpeta_inicial():
        hogar = os.path.expanduser('~')
        for nombre in ('Música', 'Musica', 'Music', 'Descargas', 'Downloads', 'Escritorio'):
            ruta = os.path.join(hogar, nombre)
            if os.path.isdir(ruta):
                return ruta
        return hogar

    def _guardar_en_carpeta_fija(nombre):

        try:
            os.makedirs(CARPETA_FIJA, exist_ok=True)
            return os.path.join(CARPETA_FIJA, nombre)
        except Exception:
            return None

    def _pedir_destino(nombre):

        try:
            dialogo = Gtk.FileChooserDialog(
                title='Guardar la versión masterizada', parent=ventana,
                action=Gtk.FileChooserAction.SAVE)
            dialogo.set_modal(True)
            dialogo.add_button('Cancelar', Gtk.ResponseType.CANCEL)
            dialogo.add_button('Guardar', Gtk.ResponseType.OK)
            dialogo.set_default_response(Gtk.ResponseType.OK)
            try:
                dialogo.set_do_overwrite_confirmation(True)
            except Exception:
                pass
            try:
                filtro = Gtk.FileFilter()
                filtro.set_name('Audio')
                for patron in ('*.wav', '*.mp3', '*.flac', '*.ogg',
                               '*.m4a', '*.aiff', '*.aif'):
                    filtro.add_pattern(patron)
                dialogo.add_filter(filtro)
            except Exception:
                pass
            dialogo.set_current_folder(_carpeta_inicial())
            dialogo.set_current_name(nombre)
            respuesta = dialogo.run()
            ruta = dialogo.get_filename()
            dialogo.destroy()
            if respuesta not in (Gtk.ResponseType.OK, Gtk.ResponseType.ACCEPT):
                return None
            if not ruta:
                return None
            if not os.path.splitext(ruta)[1]:
                extension = os.path.splitext(nombre)[1]
                if extension:
                    ruta += extension
            return ruta
        except Exception as error:
            print('no se pudo preguntar dónde guardar: %s' % error, file=sys.stderr)
            return None

    def _al_terminar_descarga(descarga, *_):
        try:
            destino = descarga.get_destination() or ''
            ruta = GLib.filename_from_uri(destino)[0] if destino.startswith('file:') else destino
        except Exception:
            ruta = ''
        print('descarga guardada en %s' % ruta, file=sys.stderr)

    def _al_fallar_descarga(descarga, error, *_):
        print('la descarga ha fallado: %s' % error, file=sys.stderr)

    def _decidir_destino(descarga, sugerido):

        try:
            nombre = _nombre_sugerido(descarga, sugerido)
            if CARPETA_FIJA:
                ruta = _guardar_en_carpeta_fija(nombre)
            else:
                ruta = _pedir_destino(nombre)
            if not ruta:
                descarga.cancel()
                return True
            try:
                descarga.set_allow_overwrite(True)
            except Exception:
                pass
            descarga.set_destination(GLib.filename_to_uri(ruta, None))
        except Exception as error:
            print('descarga no preparada: %s' % error, file=sys.stderr)
            try:
                descarga.cancel()
            except Exception:
                pass
        return True

    def al_descargar(contexto, descarga):

        try:
            descarga.connect('decide-destination', _decidir_destino)
            descarga.connect('finished', _al_terminar_descarga)
            descarga.connect('failed', _al_fallar_descarga)
        except Exception as error:
            print('sin diálogo de descargas: %s' % error, file=sys.stderr)
        return True

    try:
        contexto = WebKit2.WebContext.get_default()
        if contexto is not None:
            contexto.connect('download-started', al_descargar)
    except Exception as error:
        print('sin diálogo de descargas: %s' % error, file=sys.stderr)

    def al_caer(*_):

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

sys.exit(0 if cerrada['por_usuario'] else 3)
