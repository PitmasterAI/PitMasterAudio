package es.pitmasterai.masterlab;

import android.content.Context;
import android.os.Build;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.lang.Thread;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

public final class Registro {
    private static File archivo;

    public static void iniciar(Context context) {
        try {
            File externalFilesDir = context.getExternalFilesDir(null);
            if (externalFilesDir == null) {
                externalFilesDir = context.getFilesDir();
            }
            archivo = new File(externalFilesDir, "pitmasteraudio.log");
            escribir("=== MasterLab " + datosVersion(context) + " en " + Build.MANUFACTURER + " " + Build.MODEL + " (Android " + Build.VERSION.RELEASE + ") ===");
            Thread.setDefaultUncaughtExceptionHandler(new Thread.UncaughtExceptionHandler() { 
                @Override 
                public void uncaughtException(Thread thread, Throwable th) {
                    StringWriter stringWriter = new StringWriter();
                    th.printStackTrace(new PrintWriter(stringWriter));
                    Registro.escribir("CIERRE INESPERADO en " + thread.getName() + ":\n" + stringWriter.toString());
                    try {
                        Thread.sleep(400L);
                    } catch (InterruptedException unused) {
                    }
                    System.exit(2);
                }
            });
        } catch (Throwable unused) {
        }
    }

    private static String datosVersion(Context context) {
        try {
            return context.getPackageManager().getPackageInfo(context.getPackageName(), 0).versionName;
        } catch (Exception unused) {
            return "?";
        }
    }

    public static void escribir(String str) {
        if (archivo == null) {
            return;
        }
        String format = new SimpleDateFormat("HH:mm:ss", Locale.US).format(new Date());
        try {
            FileWriter fileWriter = new FileWriter(archivo, true);
            fileWriter.write("[" + format + "] " + str + "\n");
            fileWriter.close();
        } catch (Throwable unused) {
        }
    }

    public static void memoria(String str) {
        Runtime runtime = Runtime.getRuntime();
        escribir(str + ": memoria " + ((runtime.totalMemory() - runtime.freeMemory()) / 1048576) + " MB de " + (runtime.maxMemory() / 1048576) + " MB");
    }

    public static File fichero() {
        return archivo;
    }

    public static String contenido() {
        File file = archivo;
        if (file == null || !file.exists()) {
            return "Sin registro todavía.";
        }
        try {
            byte[] bArr = new byte[(int) Math.min(archivo.length(), 200000L)];
            FileInputStream fileInputStream = new FileInputStream(archivo);
            int read = fileInputStream.read(bArr);
            fileInputStream.close();
            return new String(bArr, 0, Math.max(read, 0), "UTF-8");
        } catch (Exception e) {
            return "No se pudo leer el registro: " + e;
        }
    }
}
