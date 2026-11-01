package es.pitmasterai.masterlab;

import android.content.Context;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import org.json.JSONObject;

/* loaded from: classes.dex */
public final class Sesion {
    public final int indice;
    public final float intensidad;
    public final double lufs;
    public final boolean modoAuto;
    public final String nombre;
    public final String uri;

    private Sesion(String str, String str2, int i, float f, boolean z, double d) {
        this.uri = str;
        this.nombre = str2;
        this.indice = i;
        this.intensidad = f;
        this.modoAuto = z;
        this.lufs = d;
    }

    private static File fichero(Context context) {
        return new File(context.getFilesDir(), "sesion.json");
    }

    public static void guardar(Context context, String str, String str2, int i, float f, boolean z, double d) {
        if (str == null) {
            return;
        }
        try {
            JSONObject jSONObject = new JSONObject();
            jSONObject.put("uri", str);
            if (str2 == null) {
                str2 = "";
            }
            jSONObject.put("nombre", str2);
            jSONObject.put("indice", i);
            jSONObject.put("intensidad", Double.valueOf(f));
            jSONObject.put("auto", z);
            jSONObject.put("lufs", d);
            FileWriter fileWriter = new FileWriter(fichero(context));
            fileWriter.write(jSONObject.toString());
            fileWriter.close();
        } catch (Exception e) {
            Registro.escribir("no se pudo guardar la sesión: " + e);
        }
    }

    public static Sesion leer(Context context) {
        File fichero = fichero(context);
        if (!fichero.exists()) {
            return null;
        }
        try {
            StringBuilder sb = new StringBuilder();
            BufferedReader bufferedReader = new BufferedReader(new FileReader(fichero));
            while (true) {
                String readLine = bufferedReader.readLine();
                if (readLine == null) {
                    break;
                }
                sb.append(readLine);
            }
            bufferedReader.close();
            JSONObject jSONObject = new JSONObject(sb.toString());
            String optString = jSONObject.optString("uri", "");
            if (optString.isEmpty()) {
                return null;
            }
            return new Sesion(optString, jSONObject.optString("nombre", ""), jSONObject.optInt("indice", -1), (float) jSONObject.optDouble("intensidad", 1.0d), jSONObject.optBoolean("auto", true), jSONObject.optDouble("lufs", 0.0d));
        } catch (Exception e) {
            Registro.escribir("no se pudo leer la sesión: " + e);
            return null;
        }
    }

    public static void borrar(Context context) {
        fichero(context).delete();
    }
}
