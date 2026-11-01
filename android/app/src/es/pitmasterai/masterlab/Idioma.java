package es.pitmasterai.masterlab;

import android.content.Context;
import android.content.SharedPreferences;
import java.util.HashMap;
import java.util.Locale;

public final class Idioma {
    public static final String ES = "es";
    public static final String EN = "en";
    private static final String PREFS = "pitmasteraudio";
    private static final String CLAVE = "idioma";

    private static String actual = ES;
    private static final HashMap<String, String> MAPA = new HashMap<>();

    private Idioma() {
    }

    
    private static final HashMap<String, String> INVERSA = new HashMap<>();

    

    public static String de(String texto) {
        if (texto == null) {
            return null;
        }
        String limpio = texto.trim();
        if (limpio.length() == 0) {
            return null;
        }
        if (MAPA.containsKey(limpio)) {
            return t(limpio);
        }
        String espanol = INVERSA.get(limpio);
        if (espanol != null) {
            return t(espanol);
        }
        return null;
    }

    private static void m(String es, String en) {
        MAPA.put(es, en);
    }

    static {
        
        m("Remasterizado de Audio por Ecualización", "Audio Remastering by Equalization");
        m("Elegir audio", "Choose audio");
        m("***No se recomienda subir audio ya remasterizado***", "***Uploading already-remastered audio is not recommended***");
        m("Ningún audio elegido", "No audio selected");
        m("Qué se ha analizado", "What has been analyzed");
        m("Sube una canción para verlo", "Load a song to see it");
        m("Comparar", "Compare");
        m("Original", "Original");
        m("Masterizado", "Mastered");
        m("▶ Escuchar", "▶ Listen");
        m("■ Parar", "■ Stop");
        m("Descargar", "Download");
        m("Habituales", "Essentials");
        m("Empiezas con Amplificador. Toca otro para cambiarlo.", "You start with Amplifier. Tap another one to change it.");
        m("Recomendadas por tipo de audio", "Recommended by audio type");
        m("Más variaciones (20) ▾", "More variations (20) ▾");
        m("Más variaciones (20) ▴", "More variations (20) ▴");
        m("Más variaciones (%d) ▾", "More variations (%d) ▾");
        m("Más variaciones (%d) ▴", "More variations (%d) ▴");
        m("Ajustes finos ▸", "Fine tuning ▸");
        m("Ajustes finos ▾", "Fine tuning ▾");

        
        m("Sonoridad (LUFS)", "Loudness (LUFS)");
        m("Auto", "Auto");
        m("Auto ✓", "Auto ✓");
        m("Fijo", "Fixed");
        m("Fijo ✓", "Fixed ✓");
        m("Intensidad del efecto: 100 %", "Effect intensity: 100 %");
        m("Intensidad del efecto: ", "Effect intensity: ");
        m("♥ Donar", "♥ Donate");

        
        m("Analizando…", "Analyzing…");
        m("Trabajando…", "Working…");
        m("Aplicando ", "Applying ");
        m("Por cómo suena, encaja ", "Based on how it sounds, ");
        m(". Empiezas con Amplificador; cámbialo cuando quieras.", ". You start with Amplifier; change it whenever you want.");

        
        m("%s · %.1f LUFS · pico %.2f dBTP", "%s · %.1f LUFS · peak %.2f dBTP");
        m("%s · %.1f LUFS · audio largo", "%s · %.1f LUFS · long audio");
        m("%s · %.1f LUFS", "%s · %.1f LUFS");
        m("Original · %.1f LUFS", "Original · %.1f LUFS");
        m("Original · %.1f LUFS · pico %.2f dBTP", "Original · %.1f LUFS · peak %.2f dBTP");
        m(" · graves %+.1f dB · agudos %+.1f dB", " · lows %+.1f dB · highs %+.1f dB");
        m("%.1f LUFS · cresta %.1f dB · estéreo %.2f", "%.1f LUFS · crest %.1f dB · stereo %.2f");

        
        m("Esa canción es muy larga para el móvil (más de 6 minutos).", "That song is too long for this phone (over 6 minutes).");
        m("La canción ocupa demasiado para este móvil. Prueba con un fragmento.", "The song is too big for this phone. Try a shorter clip.");
        m("No se pudo leer el audio: ", "Could not read the audio: ");
        m("Sin memoria al masterizar. Prueba con una canción más corta.", "Out of memory while mastering. Try a shorter song.");
        m("Fallo al masterizar: ", "Mastering failed: ");
        m("No hay selector de archivos", "No file picker available");
        m("No se puede guardar", "Cannot save");
        m("Intensidad fija", "Fixed intensity");
        m("Intensidad manual", "Manual intensity");
        m("No hay navegador", "No browser available");
        m("No hay apps para compartir", "No apps available to share");
        m("En automático: carga una canción", "Auto mode: load a song first");
        m("Sonoridad manual", "Manual loudness");
        m("Primero carga una canción", "Load a song first");
        m("Guardado", "Saved");
        m("No se pudo guardar: ", "Could not save: ");
        m("Compartir registro", "Share log");
        m("MasterLab registro", "MasterLab log");

        
        m("Motor principal: ", "Main engine: ");
        m("Motor secundario: ", "Secondary engine: ");
        m("Motor: ", "Engine: ");
        m("GPU (forzada)", "GPU (forced)");

        
        m("Preparando versiones", "Preparing versions");
        m("Se muestra mientras se calculan los ajustes por detrás", "Shown while presets are computed in the background");
        m("Preparando los ajustes de la canción…", "Preparing the song's presets…");

        
        m("Radiante", "Radiant");
        m("Deslumbrante", "Dazzling");
        m("Firme", "Firm");
        m("Densa", "Dense");
        m("Oscura", "Dark");
        m("Luminosa", "Luminous");
        m("Aire", "Air");
        m("Sencilla", "Simple");
        m("Suave", "Soft");
        m("Terciopelo", "Velvet");
        m("Viva", "Vivid");
        m("Chispa", "Spark");
        m("Habitual", "Everyday");
        m("Calida", "Warm");
        m("Sedosa", "Silky");
        m("Amplia", "Wide");
        m("Caliente", "Hot");
        m("Claro", "Clear");
        m("Amplificador", "Amplifier");
        m("Film", "Film");
        m("Neutra", "Neutral");
        m("Potente", "Powerful");
        m("Retro", "Retro");
        m("Audiolibro", "Audiobook");
        m("Podcast", "Podcast");
        
        for (String clave : MAPA.keySet()) {
            INVERSA.put(MAPA.get(clave), clave);
        }
    }

    
    public static void iniciar(Context c) {
        if (c == null) {
            return;
        }
        try {
            SharedPreferences preferencias = c.getSharedPreferences(PREFS, 0);
            String guardado = preferencias.getString(CLAVE, null);
            
            
            
            if (guardado == null || guardado.length() == 0) {
                guardado = Locale.getDefault().getLanguage().toLowerCase(Locale.US).startsWith(ES) ? ES : EN;
                preferencias.edit().putString(CLAVE, guardado).apply();
            }
            actual = EN.equals(guardado) ? EN : ES;
        } catch (Throwable th) {
            actual = ES;
        }
    }

    public static String idioma() {
        return actual;
    }

    public static boolean esIngles() {
        return EN.equals(actual);
    }

    public static void poner(Context c, String idioma) {
        actual = EN.equals(idioma) ? EN : ES;
        if (c == null) {
            return;
        }
        try {
            
            c.getSharedPreferences(PREFS, 0).edit().putString(CLAVE, actual).apply();
        } catch (Throwable unused) {
        }
    }

    
    public static String t(String es) {
        if (es == null || !EN.equals(actual)) {
            return es;
        }
        String en = MAPA.get(es);
        return en == null ? es : en;
    }
}
