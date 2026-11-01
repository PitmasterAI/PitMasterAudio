package es.pitmasterai.masterlab;

import android.net.Uri;
import es.pitmasterai.masterlab.motor.Analizador;
import es.pitmasterai.masterlab.motor.Wav;
import java.io.File;
import java.util.Set;

/* loaded from: classes.dex */
public final class Estado {
    static Estado ultima;
    Wav.Datos datos;
    double duracion;
    boolean entradaLarga;
    File ficheroMaster;
    File ficheroOriginal;
    Set<Integer> hechos;
    int indiceActual;
    double lufsMaster;
    String nombre;
    int[] orden;
    Analizador.Perfil perfil;
    int[] recomendados;
    double tpMaster;
    double tpOriginal;
    Uri uri;
    boolean viendoOriginal;

    public static boolean hay() {
        Estado estado = ultima;
        return (estado == null || estado.datos == null) ? false : true;
    }

    public static void limpiar() {
        ultima = null;
    }
}
