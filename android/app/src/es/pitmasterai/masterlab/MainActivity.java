package es.pitmasterai.masterlab;

import android.R;
import android.app.Activity;
import android.content.Intent;
import android.content.res.Configuration;
import android.database.Cursor;
import android.graphics.drawable.AnimationDrawable;
import android.graphics.drawable.Drawable;
import android.graphics.drawable.GradientDrawable;
import android.media.MediaPlayer;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.SeekBar;
import android.widget.TextView;
import android.widget.Toast;
import es.pitmasterai.masterlab.OndaSonido;
import es.pitmasterai.masterlab.motor.Analizador;
import es.pitmasterai.masterlab.motor.LectorAudio;
import es.pitmasterai.masterlab.motor.Motor;
import es.pitmasterai.masterlab.motor.Preset;
import es.pitmasterai.masterlab.motor.Presets;
import es.pitmasterai.masterlab.motor.Sonoridad;
import es.pitmasterai.masterlab.motor.Trabajo;
import es.pitmasterai.masterlab.motor.VulkanNativo;
import es.pitmasterai.masterlab.motor.Wav;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.OutputStream;
import java.lang.reflect.Array;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.LinkedHashSet;
import java.util.Locale;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

/* loaded from: classes.dex */
public class MainActivity extends Activity implements View.OnClickListener, SeekBar.OnSeekBarChangeListener, OndaSonido.AlTocar {
    private static final long LIBRE_MINIMO_SISTEMA = 1073741824;
    private static final int ID_BOTON_ES = 20;
    private static final int ID_BOTON_EN = 21;
    private static final int PEDIR_ENTRADA = 11;
    private static final int PEDIR_SALIDA = 12;
    private SeekBar barraIntensidad;
    private SeekBar barraLufs;
    private Button botonAuto;
    private Button botonFijo;
    private Button botonGuardar;
    private Button botonMaster;
    private Button botonOriginal;
    private Button botonPlay;
    private Button botonVariaciones;
    private LinearLayout cajaDestacados;
    private ScrollView raiz;
    private LinearLayout cajaRecomendadaCompleta;
    private LinearLayout cajaRecomendadas;
    private LinearLayout cajaVariaciones;
    private EditText campoIntensidad;
    private EditText campoLufs;
    private Wav.Datos datos;
    private TextView etiquetaArchivo;
    private TextView etiquetaEstado;
    private TextView etiquetaIntensidad;
    private TextView etiquetaLufs;
    private TextView etiquetaPerfil;
    private TextView etiquetaPista;
    private TextView etiquetaSonando;
    private TextView etiquetaMotor;
    private Button botonEs;
    private Button botonEn;
    private int pistaIndice = -1;        // ajuste recomendado que se está enseñando
    private int estadoIndice = -1;       // ajuste que se está aplicando (-1 = sin datos)
    private File ficheroMaster;
    private File ficheroOriginal;
    private ProgressBar giroIntensidad;
    private ProgressBar giroLufs;
    private MediaPlayer jugadorMaster;
    private MediaPlayer jugadorOriginal;
    private OndaSonido onda;
    private Analizador.Perfil perfil;
    private ProgressBar progreso;
    private float[][] resultado;
    private Uri uriEntrada;
    private static final String[] DESTACADOS = {"base_claro", "base_retro"};
    private static final int VOX_INICIO = Presets.CLAVES.length - 2;
    private boolean sincronizando = false;
    private int[] recomendados = {0, 0};
    private int[] ordenCompleto = {0};
    private final Set<String> precalculados = Collections.synchronizedSet(new HashSet());
    private volatile boolean colaBloqueada = false;
    private volatile long colaBloqueadaMs = 0;
    private volatile boolean trabajandoSecundario = false;
    private volatile boolean trabajandoPrincipal = false;
    private volatile int indiceSecundario = -1;
    private volatile int indicePrincipal = -1;
    private volatile int indiceSolicitado = -1;
    private volatile int esperasMemoria = 0;
    private final ConcurrentHashMap<Integer, Long> cuarentena = new ConcurrentHashMap<>();
    private volatile int[] listaCola = null;
    private volatile int prioridadCola = 0;
    private int ticks = 0;
    private boolean entradaLarga = false;
    private double duracionEntrada = 0.0d;
    private boolean modoAuto = true;
    private boolean intensidadFija = true;
    private String nombreEntrada = "";
    private int frecuencia = 44100;
    private int indiceActual = -1;
    private Integer indiceAlRestaurar = null;
    private double tpOriginal = Double.NaN;
    private boolean pausaManual = false;
    private boolean arrastrandoOnda = false;
    private int generacionAnalisis = 0;
    private double lufsMaster = Double.NaN;
    private double tpMaster = Double.NaN;
    private float[] picosOriginal = new float[0];
    private float[] picosMaster = new float[0];
    private boolean viendoOriginal = false;
    private int posicionDeseada = 0;
    private boolean seguiaSonando = false;
    private final Handler hilo = new Handler(Looper.getMainLooper());
    private final AplicarLufs aplicarLufs = new AplicarLufs(this);
    private int motivoPendiente = 0;
    private volatile int motivoUltimo = 0;
    private volatile int trabajoActual = 0;
    private volatile int generacionPrecalentado = 0;
    private volatile boolean interactivoEnMarcha = false;
    private final ArrayList<Button> botonesPreset = new ArrayList<>();
    private final HashSet<Integer> calculando = new HashSet<>();
    private final Set<Integer> hechos = Collections.synchronizedSet(new HashSet());
    private final HashMap<Button, AnimationDrawable> giros = new HashMap<>();
    private final Latido latido = new Latido(this);

    @Override // android.widget.SeekBar.OnSeekBarChangeListener
    public void onStartTrackingTouch(SeekBar seekBar) {
    }

    static /* synthetic */ int access$104(MainActivity mainActivity) {
        int i = mainActivity.ticks + 1;
        mainActivity.ticks = i;
        return i;
    }

    /* JADX INFO: Access modifiers changed from: private */
    public int[] dosRecomendadas(int[] iArr) {
        boolean z;
        int[] iArr2 = new int[2];
        int i = 0;
        for (int i2 = 0; i2 < iArr.length && i < 2; i2++) {
            int i3 = 0;
            while (true) {
                String[] strArr = DESTACADOS;
                if (i3 >= strArr.length) {
                    z = false;
                    break;
                }
                if (indiceDe(strArr[i3]) == iArr[i2]) {
                    z = true;
                    break;
                }
                i3++;
            }
            if (!z) {
                iArr2[i] = iArr[i2];
                i++;
            }
        }
        while (i < 2) {
            iArr2[i] = iArr2[0];
            i++;
        }
        return iArr2;
    }

    void programarAjuste(int i) {
        this.motivoPendiente = i;
        this.hilo.removeCallbacks(this.aplicarLufs);
        this.hilo.postDelayed(this.aplicarLufs, 700L);
    }

    /* loaded from: classes.dex */
    private static class Latido implements Runnable {
        private final MainActivity a;

        Latido(MainActivity mainActivity) {
            this.a = mainActivity;
        }

        @Override // java.lang.Runnable
        public void run() {
            this.a.actualizarProgreso();
            if (MainActivity.access$104(this.a) % 15 == 0) {
                this.a.supervisarCola();
            }
            this.a.hilo.postDelayed(this, 200L);
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    public static Wav.Datos unir(Wav.Datos[] datosArr) {
        int length = datosArr[0].muestras.length;
        int i = datosArr[0].frecuencia;
        int i2 = 0;
        for (Wav.Datos datos : datosArr) {
            i2 += datos.muestras[0].length;
        }
        float[][] fArr = (float[][]) Array.newInstance((Class<?>) Float.TYPE, length, i2);
        int i3 = 0;
        for (Wav.Datos datos2 : datosArr) {
            int length2 = datos2.muestras[0].length;
            for (int i4 = 0; i4 < length; i4++) {
                System.arraycopy(datos2.muestras[i4], 0, fArr[i4], i3, length2);
            }
            i3 += length2;
        }
        return new Wav.Datos(fArr, i);
    }

    /* JADX INFO: Access modifiers changed from: private */
    public static double[] masterizarPorTrozos(MainActivity mainActivity, Preset preset, float f, Double d, File file) throws Exception {
        Wav.Escritor escritor;
        double d2 = mainActivity.duracionEntrada;
        if (d2 <= 0.0d) {
            throw new Exception("no se sabe cuánto dura el audio");
        }
        int i = mainActivity.datos.frecuencia;
        int length = mainActivity.datos.muestras.length;
        double d3 = mainActivity.perfil.lufs;
        double d4 = i;
        Double.isNaN(d4);
        long round = Math.round(d4 * d2);
        double doubleValue = d != null ? d.doubleValue() : preset.lufs;
        Wav.Escritor escritor2 = new Wav.Escritor(file.getAbsolutePath(), length, i, round);
        double d5 = 0.0d;
        int i2 = 0;
        while (d5 < d2) {
            try {
                Trabajo.comprobar();
                double d6 = 60;
                Double.isNaN(d6);
                double d7 = d5 + d6;
                double min = Math.min(d2, d7);
                double d8 = d5;
                double max = Math.max(0.0d, d5 - 2.0d);
                escritor = escritor2;
                double d9 = d3;
                try {
                    Wav.Datos leerTramo = LectorAudio.leerTramo(mainActivity, mainActivity.uriEntrada, max, Math.min(d2, min + 2.0d));
                    float[][] masterizar = Motor.masterizar(leerTramo.muestras, leerTramo.frecuencia, preset, f, Double.valueOf(doubleValue + (Sonoridad.lufs(leerTramo.muestras, leerTramo.frecuencia) - d9)), null);
                    double d10 = d8 - max;
                    double d11 = leerTramo.frecuencia;
                    Double.isNaN(d11);
                    int max2 = (int) Math.max(0L, Math.round(d10 * d11));
                    double d12 = min - d8;
                    double d13 = leerTramo.frecuencia;
                    Double.isNaN(d13);
                    int round2 = ((int) Math.round(d12 * d13)) + max2;
                    float[] fArr = masterizar[0];
                    if (round2 > fArr.length) {
                        round2 = fArr.length;
                    }
                    if (round2 > max2) {
                        escritor.escribir(masterizar, max2, round2);
                    }
                    System.gc();
                    i2++;
                    StringBuilder sb = new StringBuilder();
                    sb.append("Masterizado ");
                    sb.append(Presets.NOMBRES[presetIndice(preset)]);
                    sb.append(": trozo ");
                    sb.append(i2);
                    sb.append(" de ");
                    Double.isNaN(d6);
                    sb.append((int) Math.ceil(d2 / d6));
                    Registro.escribir(sb.toString());
                    escritor2 = escritor;
                    d3 = d9;
                    d5 = d7;
                } finally {
                    escritor.close();
                }
            } catch (Throwable th2) {
                escritor = escritor2;
            }
        }
        escritor2.close();
        return new double[]{doubleValue, Double.NaN};
    }

    private static int presetIndice(Preset preset) {
        for (int i = 0; i < Presets.CLAVES.length; i++) {
            if (Presets.CLAVES[i].equals(preset.clave)) {
                return i;
            }
        }
        return 0;
    }

    /* JADX INFO: Access modifiers changed from: private */
    /* loaded from: classes.dex */
    public static class TareaAnalizar implements Runnable {
        private final MainActivity a;
        final int generacion;
        private final Uri uri;

        TareaAnalizar(MainActivity mainActivity, Uri uri, int i) {
            this.generacion = i;
            this.a = mainActivity;
            this.uri = uri;
        }

        @Override // java.lang.Runnable
        public void run() {
            try {
                Registro.escribir("Análisis: mirando el archivo");
                LectorAudio.Info info = LectorAudio.info(this.a, this.uri);
                if (info.segundos > 300.0d) {
                    long elapsedRealtime = SystemClock.elapsedRealtime();
                    double d = info.segundos;
                    double d2 = d * 0.1d;
                    double d3 = 0.5d * d;
                    double d4 = 0.9d * d;
                    Wav.Datos unir = MainActivity.unir(new Wav.Datos[]{LectorAudio.leerTramo(this.a, this.uri, d2, d2 + 30.0d), LectorAudio.leerTramo(this.a, this.uri, d3, d3 + 30.0d), LectorAudio.leerTramo(this.a, this.uri, d4, d4 + 30.0d)});
                    this.a.entradaLarga = true;
                    this.a.duracionEntrada = d;
                    Registro.escribir("Audio largo: " + ((int) d) + " s · analizado en " + (SystemClock.elapsedRealtime() - elapsedRealtime) + " ms");
                    Analizador.Perfil analizar = Analizador.analizar(unir.muestras, unir.frecuencia);
                    double[] puntuar = Analizador.puntuar(analizar);
                    int[] ordenar = Analizador.ordenar(puntuar);
                    Registro.escribir("Perfil: " + analizar.resumen());
                    this.a.analisisListo(unir, null, analizar, puntuar, ordenar, this.generacion);
                    return;
                }
                Wav.Datos leer = LectorAudio.leer(this.a, this.uri);
                Registro.escribir("Leído: " + leer.tramas() + " muestras a " + leer.frecuencia + " Hz");
                if (leer.tramas() > 16000000) {
                    this.a.error(Idioma.t("Esa canción es muy larga para el móvil (más de 6 minutos)."));
                    return;
                }
                Registro.memoria("tras leer");
                File file = new File(this.a.getCacheDir(), "original.wav");
                Wav.escribir(file.getAbsolutePath(), leer.muestras, leer.frecuencia);
                Analizador.Perfil analizar2 = Analizador.analizar(leer.muestras, leer.frecuencia);
                double[] puntuar2 = Analizador.puntuar(analizar2);
                int[] ordenar2 = Analizador.ordenar(puntuar2);
                Registro.escribir("Perfil: " + analizar2.resumen());
                if (this.generacion != this.a.generacionAnalisis) {
                    Registro.escribir("Análisis descartado: hay uno más nuevo");
                } else {
                    this.a.analisisListo(leer, file, analizar2, puntuar2, ordenar2, this.generacion);
                }
            } catch (OutOfMemoryError unused) {
                this.a.error(Idioma.t("La canción ocupa demasiado para este móvil. Prueba con un fragmento."));
            } catch (Throwable th) {
                Registro.escribir("Fallo al leer: " + th);
                Sesion.borrar(this.a);
                this.a.error(Idioma.t("No se pudo leer el audio: ") + th);
            }
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    /* loaded from: classes.dex */
    public static class TareaMasterizar implements Runnable {
        private final MainActivity a;
        private final File destino;
        private final int indice;
        private final float intensidad;
        private final Double objetivo;
        private final int turno;

        TareaMasterizar(MainActivity mainActivity, int i, float f, Double d, File file, int i2) {
            this.a = mainActivity;
            this.indice = i;
            this.intensidad = f;
            this.objetivo = d;
            this.destino = file;
            this.turno = i2;
        }

        @Override // java.lang.Runnable
        public void run() {
            float[][] masterizar;
            Acelerador.fijarMotorHilo(Acelerador.motorRapido(this.a));
            Trabajo.marcarTipo(0);
            this.a.interactivoEnMarcha = true;
            try {
                try {
                    try {
                        try {
                        } catch (Trabajo.Cancelado unused) {
                            Registro.escribir("Cortado: se pidió otro ajuste");
                        }
                    } catch (OutOfMemoryError unused2) {
                        this.a.error(Idioma.t("Sin memoria al masterizar. Prueba con una canción más corta."));
                    }
                } catch (Throwable th) {
                    Registro.escribir("Fallo al masterizar: " + th);
                    this.a.error(Idioma.t("Fallo al masterizar: ") + th);
                }
                if (this.turno == this.a.trabajoActual) {
                    Acelerador.aplicarForzado(this.a);
                    long elapsedRealtime = SystemClock.elapsedRealtime();
                    Registro.escribir("Masterizando: " + Idioma.t(Presets.NOMBRES[this.indice]));
                    Registro.memoria("antes de masterizar");
                    Preset crear = Presets.crear(this.indice);
                    if (!this.a.entradaLarga) {
                        try {
                            masterizar = Motor.masterizar(this.a.datos.muestras, this.a.datos.frecuencia, crear, this.intensidad, this.objetivo, null);
                        } catch (OutOfMemoryError unused3) {
                            System.gc();
                            this.a.picosMaster = new float[0];
                            masterizar = Motor.masterizar(this.a.datos.muestras, this.a.datos.frecuencia, crear, this.intensidad, this.objetivo, null);
                        }
                        float[][] fArr = masterizar;
                        if (this.turno == this.a.trabajoActual) {
                            double lufs = Sonoridad.lufs(fArr, this.a.datos.frecuencia);
                            double picoReal = Sonoridad.picoReal(fArr, this.a.datos.frecuencia);
                            File file = this.destino;
                            if (file == null) {
                                file = new File(this.a.getCacheDir(), "master.wav");
                            }
                            File file2 = file;
                            Wav.escribir(file2.getAbsolutePath(), fArr, this.a.datos.frecuencia);
                            Object[] objArr = new Object[4];
                            objArr[0] = Idioma.t(Presets.NOMBRES[this.indice]);
                            objArr[1] = Double.valueOf(lufs);
                            objArr[2] = Double.valueOf(picoReal);
                            double elapsedRealtime2 = SystemClock.elapsedRealtime() - elapsedRealtime;
                            Double.isNaN(elapsedRealtime2);
                            objArr[3] = Double.valueOf(elapsedRealtime2 / 1000.0d);
                            Registro.escribir(String.format("Listo %s: %.1f LUFS, %.2f dBTP en %.1f s", objArr));
                            this.a.masterizado(fArr, this.indice, file2, lufs, picoReal);
                            this.a.interactivoEnMarcha = false;
                            this.a.indiceSolicitado = -1;
                            this.a.marcarCalculando(this.indice, false);
                            Trabajo.soltar();
                            Acelerador.limpiarMotorHilo();
                            return;
                        }
                    } else {
                        File file3 = this.destino;
                        if (file3 == null) {
                            file3 = new File(this.a.getCacheDir(), "master_" + this.indice + "_" + this.turno + ".wav");
                        }
                        File file4 = file3;
                        double[] masterizarPorTrozos = MainActivity.masterizarPorTrozos(this.a, crear, this.intensidad, this.objetivo, file4);
                        if (this.turno == this.a.trabajoActual) {
                            this.a.hilo.post(new EntregaMaster(this.a, null, this.indice, file4, masterizarPorTrozos[0], masterizarPorTrozos[1]));
                        }
                    }
                }
                this.a.interactivoEnMarcha = false;
                this.a.indiceSolicitado = -1;
                this.a.marcarCalculando(this.indice, false);
                Trabajo.soltar();
                Acelerador.limpiarMotorHilo();
            } catch (Throwable th4) {
                Registro.escribir("Fallo al masterizar: " + th4);
                this.a.error(Idioma.t("Fallo al masterizar: ") + th4);
            } finally {
                this.a.interactivoEnMarcha = false;
                this.a.indiceSolicitado = -1;
                this.a.marcarCalculando(this.indice, false);
                Trabajo.soltar();
                Acelerador.limpiarMotorHilo();
            }
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    /* loaded from: classes.dex */
    public static class TrabajoPrecalculado implements Runnable {
        private final MainActivity a;
        private final int indice;
        private final float intensidad;
        private final String motor;
        private final Double objetivo;
        private final boolean principal;

        TrabajoPrecalculado(MainActivity mainActivity, int i, float f, Double d, String str, boolean z) {
            this.a = mainActivity;
            this.indice = i;
            this.intensidad = f;
            this.objetivo = d;
            this.motor = str;
            this.principal = z;
        }

        /* JADX WARN: Code restructure failed: missing block: B:13:0x00f2, code lost:
        
            if (r20.principal != false) goto L29;
         */
        /* JADX WARN: Code restructure failed: missing block: B:14:0x016d, code lost:
        
            r20.a.trabajandoSecundario = false;
         */
        /* JADX WARN: Code restructure failed: missing block: B:15:0x0172, code lost:
        
            es.pitmasterai.masterlab.motor.Trabajo.soltar();
            es.pitmasterai.masterlab.Acelerador.limpiarMotorHilo();
         */
        /* JADX WARN: Code restructure failed: missing block: B:16:0x01c5, code lost:
        
            return;
         */
        /* JADX WARN: Code restructure failed: missing block: B:19:0x0167, code lost:
        
            r20.a.trabajandoPrincipal = false;
         */
        /* JADX WARN: Code restructure failed: missing block: B:25:0x0165, code lost:
        
            if (r20.principal == false) goto L30;
         */
        /* JADX WARN: Code restructure failed: missing block: B:43:0x01c2, code lost:
        
            if (r20.principal == false) goto L30;
         */
        /* JADX WARN: Code restructure failed: missing block: B:49:0x013e, code lost:
        
            if (r20.principal == false) goto L30;
         */
        /* JADX WARN: Removed duplicated region for block: B:34:0x01ec  */
        /* JADX WARN: Removed duplicated region for block: B:37:0x01f2  */
        @Override // java.lang.Runnable
        /*
            Code decompiled incorrectly, please refer to instructions dump.
        */
        public void run() {
            Acelerador.fijarMotorHilo(this.motor);
            Trabajo.marcarTipo(this.principal ? Trabajo.PRINCIPAL : Trabajo.SECUNDARIO);
            boolean hecho = false;
            try {
                Thread.currentThread().setPriority(Thread.MIN_PRIORITY);
                this.a.marcarCalculando(this.indice, true);
                long arranque = SystemClock.elapsedRealtime();
                float[][] y = Motor.masterizar(this.a.datos.muestras, this.a.datos.frecuencia,
                        Presets.crear(this.indice), this.intensidad, this.objetivo, null);
                double lufs = Sonoridad.lufs(y, this.a.datos.frecuencia);
                double picoReal = Sonoridad.picoReal(y, this.a.datos.frecuencia);
                File cache = this.a.ficheroCache(this.indice, this.intensidad, this.objetivo);
                Wav.escribir(cache.getAbsolutePath(), y, this.a.datos.frecuencia);
                this.a.escribirFicha(cache, lufs, picoReal, this.indice);
                this.a.precalculados.add(cache.getAbsolutePath());
                this.a.hechos.add(Integer.valueOf(this.indice));
                hecho = true;
                Registro.escribir(String.format(Locale.US,
                        "Precalculado %s: %.1f LUFS en %.1f s (%s)", Idioma.t(Presets.NOMBRES[this.indice]),
                        Double.valueOf(lufs),
                        Double.valueOf((SystemClock.elapsedRealtime() - arranque) / 1000.0d),
                        this.motor));
                System.gc();
                this.a.marcarCalculando(this.indice, false);
                this.a.precalculadoListo(this.indice);
            } catch (Trabajo.Cancelado cancelado) {
                Registro.escribir("Precalculado " + Idioma.t(Presets.NOMBRES[this.indice]) + ": cortado");
                this.a.marcarCalculando(this.indice, false);
            } catch (OutOfMemoryError pocaMemoria) {
                Registro.escribir("Precalculado " + Idioma.t(Presets.NOMBRES[this.indice])
                        + ": sin memoria puntual, se reintenta más tarde");
                this.a.marcarCalculando(this.indice, false);
                this.a.cuarentena.put(Integer.valueOf(this.indice),
                        Long.valueOf(SystemClock.elapsedRealtime() + 60000));
            } catch (Throwable e) {
                Registro.escribir("Precalculado falló " + Idioma.t(Presets.NOMBRES[this.indice]) + ": " + e);
                this.a.marcarCalculando(this.indice, false);
                if (!hecho) {
                    this.a.cuarentena.put(Integer.valueOf(this.indice),
                            Long.valueOf(SystemClock.elapsedRealtime() + 60000));
                }
            } finally {
                if (this.principal) {
                    this.a.trabajandoPrincipal = false;
                } else {
                    this.a.trabajandoSecundario = false;
                }
                Trabajo.soltar();
                Acelerador.limpiarMotorHilo();
            }
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    /* loaded from: classes.dex */
    public static class OndaDesdeFichero implements Runnable {
        private final MainActivity a;
        private final File fichero;
        private final int indice;
        private final boolean medir;

        OndaDesdeFichero(MainActivity mainActivity, File file, int i, boolean z) {
            this.a = mainActivity;
            this.fichero = file;
            this.indice = i;
            this.medir = z;
        }

        @Override // java.lang.Runnable
        public void run() {
            double d;
            double d2;
            try {
                Wav.Datos leer = Wav.leer(this.fichero.getAbsolutePath());
                float[] picosDe = this.a.picosDe(leer.muestras);
                if (this.medir) {
                    d = Sonoridad.lufs(leer.muestras, leer.frecuencia);
                    d2 = Sonoridad.picoReal(leer.muestras, leer.frecuencia);
                } else {
                    d = 0.0d;
                    d2 = 0.0d;
                }
                System.gc();
                this.a.hilo.post(new EntregaOnda(this.a, picosDe, d, d2, this.medir, this.indice));
            } catch (Throwable th) {
                Registro.escribir("no se pudo pintar la onda: " + th);
            }
        }
    }

    /* loaded from: classes.dex */
    private static class EntregaOnda implements Runnable {
        private final MainActivity a;
        private final int indice;
        private final double lufs;
        private final boolean medir;
        private final float[] picos;
        private final double tp;

        EntregaOnda(MainActivity mainActivity, float[] fArr, double d, double d2, boolean z, int i) {
            this.a = mainActivity;
            this.picos = fArr;
            this.lufs = d;
            this.tp = d2;
            this.medir = z;
            this.indice = i;
        }

        @Override // java.lang.Runnable
        public void run() {
            this.a.picosMaster = this.picos;
            this.a.pintarOndaDeLaVersion();
            if (this.medir) {
                this.a.etiquetaSonando.setText(String.format(Idioma.t("%s · %.1f LUFS · pico %.2f dBTP"), Idioma.t(Presets.NOMBRES[this.indice]), Double.valueOf(this.lufs), Double.valueOf(this.tp)));
            }
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    /* loaded from: classes.dex */
    public static class ElegirOpcion implements View.OnClickListener {
        private final MainActivity a;
        private final int indice;

        ElegirOpcion(MainActivity mainActivity, int i) {
            this.a = mainActivity;
            this.indice = i;
        }

        @Override // android.view.View.OnClickListener
        public void onClick(View view) {
            this.a.masterizar(this.indice);
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    /* loaded from: classes.dex */
    public static class AplicarLufs implements Runnable {
        private final MainActivity a;

        AplicarLufs(MainActivity mainActivity) {
            this.a = mainActivity;
        }

        @Override // java.lang.Runnable
        public void run() {
            if (this.a.datos == null || this.a.indiceActual < 0) {
                return;
            }
            MainActivity mainActivity = this.a;
            mainActivity.masterizar(mainActivity.indiceActual, this.a.motivoPendiente);
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    /* loaded from: classes.dex */
    public static class VigilarBarraLufs implements SeekBar.OnSeekBarChangeListener {
        private final MainActivity a;

        @Override // android.widget.SeekBar.OnSeekBarChangeListener
        public void onStartTrackingTouch(SeekBar seekBar) {
        }

        VigilarBarraLufs(MainActivity mainActivity) {
            this.a = mainActivity;
        }

        @Override // android.widget.SeekBar.OnSeekBarChangeListener
        public void onProgressChanged(SeekBar seekBar, int i, boolean z) {
            if (z) {
                Double.isNaN(i);
                this.a.sincronizando = true;
                this.a.campoLufs.setText(String.format(Locale.US, "%.1f", Double.valueOf((i * 0.1d) - 24.0d)));
                this.a.sincronizando = false;
            }
        }

        @Override // android.widget.SeekBar.OnSeekBarChangeListener
        public void onStopTrackingTouch(SeekBar seekBar) {
            if (this.a.indiceActual >= 0) {
                this.a.hilo.removeCallbacks(this.a.aplicarLufs);
                MainActivity mainActivity = this.a;
                mainActivity.masterizar(mainActivity.indiceActual, 2);
            }
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    /* loaded from: classes.dex */
    public static class VigilarIntensidad implements TextWatcher {
        private final MainActivity a;

        @Override // android.text.TextWatcher
        public void beforeTextChanged(CharSequence charSequence, int i, int i2, int i3) {
        }

        @Override // android.text.TextWatcher
        public void onTextChanged(CharSequence charSequence, int i, int i2, int i3) {
        }

        VigilarIntensidad(MainActivity mainActivity) {
            this.a = mainActivity;
        }

        @Override // android.text.TextWatcher
        public void afterTextChanged(Editable editable) {
            if (this.a.sincronizando) {
                return;
            }
            try {
                int parseInt = Integer.parseInt(editable.toString().trim());
                this.a.sincronizando = true;
                this.a.barraIntensidad.setProgress(Math.max(0, Math.min(150, parseInt)));
                this.a.etiquetaIntensidad.setText(Idioma.t("Intensidad del efecto: ") + parseInt + " %");
                this.a.sincronizando = false;
                this.a.programarAjuste(1);
            } catch (Exception unused) {
            }
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    /* loaded from: classes.dex */
    public static class VigilarLufs implements TextWatcher {
        private final MainActivity a;

        @Override // android.text.TextWatcher
        public void beforeTextChanged(CharSequence charSequence, int i, int i2, int i3) {
        }

        @Override // android.text.TextWatcher
        public void onTextChanged(CharSequence charSequence, int i, int i2, int i3) {
        }

        VigilarLufs(MainActivity mainActivity) {
            this.a = mainActivity;
        }

        @Override // android.text.TextWatcher
        public void afterTextChanged(Editable editable) {
            if (this.a.sincronizando) {
                return;
            }
            try {
                double parseDouble = Double.parseDouble(editable.toString().trim());
                this.a.sincronizando = true;
                this.a.barraLufs.setProgress((int) Math.round((parseDouble + 24.0d) * 10.0d));
                this.a.sincronizando = false;
            } catch (Exception unused) {
            }
            this.a.programarAjuste(2);
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    /* loaded from: classes.dex */
    public static class Aviso implements Runnable {
        private final MainActivity a;
        private final String texto;

        Aviso(MainActivity mainActivity, String str) {
            this.a = mainActivity;
            this.texto = str;
        }

        @Override // java.lang.Runnable
        public void run() {
            this.a.etiquetaEstado.setText(this.texto);
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    /* loaded from: classes.dex */
    public static class DesplegarAjustes implements View.OnClickListener {
        private final LinearLayout caja;

        DesplegarAjustes(LinearLayout linearLayout) {
            this.caja = linearLayout;
        }

        @Override // android.view.View.OnClickListener
        public void onClick(View view) {
            boolean z = this.caja.getVisibility() == 0;
            this.caja.setVisibility(z ? 8 : 0);
            ((TextView) view).setText(z ? Idioma.t("Ajustes finos ▸") : Idioma.t("Ajustes finos ▾"));
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    /* loaded from: classes.dex */
    public static class QuitarGiros implements Runnable {
        private final MainActivity a;

        QuitarGiros(MainActivity mainActivity) {
            this.a = mainActivity;
        }

        @Override // java.lang.Runnable
        public void run() {
            this.a.ocultarGiros();
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    /* loaded from: classes.dex */
    public static class Fin implements Runnable {
        private final MainActivity a;

        Fin(MainActivity mainActivity) {
            this.a = mainActivity;
        }

        @Override // java.lang.Runnable
        public void run() {
            this.a.progreso.setVisibility(8);
        }
    }

    @Override // android.app.Activity
    protected void onCreate(Bundle bundle) {
        super.onCreate(bundle);
        Idioma.iniciar(this);      // antes de construir nada, para pintar en el idioma guardado
        Registro.iniciar(this);
        Acelerador.aplicarForzado(this);
        setContentView(construirPantalla());
        aplicarMargenes();
        pintarEstadoAuto();
        pintarEstadoIntensidad();
        Registro.escribir(Acelerador.detalleLinea(this) + String.format(Locale.US, " (CPU %.1f ms, Vulkan %.1f ms)", Double.valueOf(VulkanNativo.milisegundosCpu()), Double.valueOf(VulkanNativo.milisegundosVulkan())));
        this.hilo.postDelayed(this.latido, 300L);
        if (Estado.hay() && cargarDeMemoria()) {
            reanudarEnMemoria();
        }
    }

    private View construirPantalla() {
        LinearLayout linearLayout = new LinearLayout(this);
        linearLayout.setOrientation(1);
        int dp = Estilo.dp(this, 14.0f);
        linearLayout.setPadding(dp, dp, dp, dp);
        linearLayout.setBackgroundColor(Estilo.FONDO);
        LinearLayout linearLayout2 = new LinearLayout(this);
        linearLayout2.setOrientation(1);
        linearLayout2.setPadding(Estilo.dp(this, 18.0f), Estilo.dp(this, 16.0f), Estilo.dp(this, 18.0f), Estilo.dp(this, 16.0f));
        GradientDrawable gradientDrawable = new GradientDrawable(GradientDrawable.Orientation.LEFT_RIGHT, new int[]{Estilo.ROSA, Estilo.VIOLETA});
        gradientDrawable.setCornerRadius(Estilo.dp(this, 22.0f));
        linearLayout2.setBackground(gradientDrawable);
        LinearLayout filaIdioma = Estilo.fila(this);
        filaIdioma.setGravity(8388613);
        LinearLayout.LayoutParams parametrosIdioma = new LinearLayout.LayoutParams(-2, -2);
        parametrosIdioma.gravity = 8388613;
        filaIdioma.setLayoutParams(parametrosIdioma);
        this.botonEs = botonIdioma("es", "🇪🇸");
        this.botonEn = botonIdioma("en", "🇬🇧");
        filaIdioma.addView(this.botonEs);
        filaIdioma.addView(this.botonEn);
        linearLayout2.addView(filaIdioma);
        TextView titulo = Estilo.titulo(this, "PitMasterAudio", 26, -1);
        titulo.setTypeface(titulo.getTypeface(), 1);
        linearLayout2.addView(titulo);
        linearLayout2.addView(Estilo.titulo(this, Idioma.t("Remasterizado de Audio por Ecualización"), PEDIR_SALIDA, -137232));
        TextView titulo2 = Estilo.titulo(this, Acelerador.detalleDoble(this), PEDIR_ENTRADA, -855638017);
        this.etiquetaMotor = titulo2;
        titulo2.setGravity(8388613);
        LinearLayout.LayoutParams ancho = Estilo.ancho(this);
        ancho.setMargins(0, Estilo.dp(this, 8.0f), 0, 0);
        titulo2.setLayoutParams(ancho);
        linearLayout2.addView(titulo2);
        linearLayout.addView(linearLayout2);
        LinearLayout tarjeta = Estilo.tarjeta(this);
        Button principal = Estilo.principal(this, Idioma.t("Elegir audio"));
        principal.setId(1);
        principal.setOnClickListener(this);
        tarjeta.addView(principal);
        TextView detalle = Estilo.detalle(this, Idioma.t("***No se recomienda subir audio ya remasterizado***"));
        detalle.setTypeface(detalle.getTypeface(), 2);
        detalle.setGravity(17);
        tarjeta.addView(detalle);
        TextView detalle2 = Estilo.detalle(this, Idioma.t("Ningún audio elegido"));
        this.etiquetaArchivo = detalle2;
        detalle2.setGravity(17);
        tarjeta.addView(this.etiquetaArchivo);
        ProgressBar progressBar = new ProgressBar(this, null, R.attr.progressBarStyleHorizontal);
        this.progreso = progressBar;
        progressBar.setIndeterminate(true);
        this.progreso.setVisibility(8);
        tarjeta.addView(this.progreso);
        linearLayout.addView(tarjeta);
        LinearLayout tarjeta2 = Estilo.tarjeta(this);
        tarjeta2.addView(Estilo.titulo(this, Idioma.t("Qué se ha analizado"), 14, Estilo.CIAN));
        TextView detalle3 = Estilo.detalle(this, Idioma.t("Sube una canción para verlo"));
        this.etiquetaPerfil = detalle3;
        tarjeta2.addView(detalle3);
        TextView detalle4 = Estilo.detalle(this, "");
        this.etiquetaPista = detalle4;
        tarjeta2.addView(detalle4);
        linearLayout.addView(tarjeta2);
        LinearLayout tarjeta3 = Estilo.tarjeta(this);
        tarjeta3.addView(Estilo.titulo(this, Idioma.t("Comparar"), 14, Estilo.ROSA));
        this.onda = new OndaSonido(this);
        LinearLayout.LayoutParams layoutParams = new LinearLayout.LayoutParams(-1, Estilo.dp(this, 96.0f));
        layoutParams.setMargins(0, Estilo.dp(this, 8.0f), 0, Estilo.dp(this, 8.0f));
        this.onda.setLayoutParams(layoutParams);
        this.onda.setEscucha(this);
        tarjeta3.addView(this.onda);
        LinearLayout fila = Estilo.fila(this);
        Button secundario = Estilo.secundario(this, Idioma.t("Original"));
        this.botonOriginal = secundario;
        secundario.setId(5);
        this.botonOriginal.setEnabled(false);
        this.botonOriginal.setOnClickListener(this);
        this.botonOriginal.setLayoutParams(Estilo.peso(this, 1.0f));
        fila.addView(this.botonOriginal);
        Button secundario2 = Estilo.secundario(this, Idioma.t("Masterizado"));
        this.botonMaster = secundario2;
        secundario2.setId(6);
        this.botonMaster.setEnabled(false);
        this.botonMaster.setOnClickListener(this);
        this.botonMaster.setLayoutParams(Estilo.peso(this, 1.0f));
        fila.addView(this.botonMaster);
        tarjeta3.addView(fila);
        LinearLayout fila2 = Estilo.fila(this);
        Button principal2 = Estilo.principal(this, Idioma.t("▶ Escuchar"));
        this.botonPlay = principal2;
        principal2.setId(2);
        this.botonPlay.setEnabled(false);
        this.botonPlay.setOnClickListener(this);
        this.botonPlay.setLayoutParams(Estilo.peso(this, 1.0f));
        fila2.addView(this.botonPlay);
        Button boton = Estilo.boton(this, Idioma.t("Descargar"), Estilo.CIAN, -16375254, 14.0f);
        this.botonGuardar = boton;
        boton.setId(3);
        this.botonGuardar.setEnabled(false);
        this.botonGuardar.setOnClickListener(this);
        this.botonGuardar.setLayoutParams(Estilo.peso(this, 1.0f));
        fila2.addView(this.botonGuardar);
        LinearLayout.LayoutParams ancho2 = Estilo.ancho(this);
        ancho2.setMargins(0, Estilo.dp(this, 10.0f), 0, 0);
        fila2.setLayoutParams(ancho2);
        tarjeta3.addView(fila2);
        TextView detalle5 = Estilo.detalle(this, "");
        this.etiquetaSonando = detalle5;
        tarjeta3.addView(detalle5);
        TextView detalle6 = Estilo.detalle(this, "");
        this.etiquetaEstado = detalle6;
        tarjeta3.addView(detalle6);
        linearLayout.addView(tarjeta3);
        LinearLayout tarjeta4 = Estilo.tarjeta(this);
        tarjeta4.addView(Estilo.titulo(this, Idioma.t("Habituales"), 14, Estilo.NARANJA));
        tarjeta4.addView(Estilo.detalle(this, Idioma.t("Empiezas con Amplificador. Toca otro para cambiarlo.")));
        LinearLayout linearLayout3 = new LinearLayout(this);
        this.cajaDestacados = linearLayout3;
        linearLayout3.setOrientation(1);
        tarjeta4.addView(this.cajaDestacados);
        LinearLayout linearLayout4 = new LinearLayout(this);
        linearLayout4.setOrientation(1);
        int dp2 = Estilo.dp(this, 12.0f);
        linearLayout4.setPadding(dp2, dp2, dp2, dp2);
        linearLayout4.setBackground(Estilo.redondeado(-14609894, Estilo.dp(this, 14.0f), Estilo.dp(this, 1.0f), Estilo.ROSA));
        LinearLayout.LayoutParams layoutParams2 = new LinearLayout.LayoutParams(-1, -2);
        layoutParams2.setMargins(0, Estilo.dp(this, 12.0f), 0, 0);
        linearLayout4.setLayoutParams(layoutParams2);
        linearLayout4.addView(Estilo.titulo(this, Idioma.t("Recomendadas por tipo de audio"), 13, Estilo.ROSA));
        LinearLayout linearLayout5 = new LinearLayout(this);
        this.cajaRecomendadas = linearLayout5;
        linearLayout5.setOrientation(1);
        linearLayout4.addView(this.cajaRecomendadas);
        tarjeta4.addView(linearLayout4);
        this.cajaRecomendadaCompleta = linearLayout4;
        linearLayout4.setVisibility(8);
        Button secundario3 = Estilo.secundario(this, Idioma.t("Más variaciones (20) ▾"));
        this.botonVariaciones = secundario3;
        secundario3.setId(7);
        this.botonVariaciones.setOnClickListener(this);
        this.botonVariaciones.setLayoutParams(Estilo.ancho(this));
        tarjeta4.addView(this.botonVariaciones);
        LinearLayout linearLayout6 = new LinearLayout(this);
        this.cajaVariaciones = linearLayout6;
        linearLayout6.setOrientation(1);
        this.cajaVariaciones.setVisibility(8);
        tarjeta4.addView(this.cajaVariaciones);
        linearLayout.addView(tarjeta4);
        LinearLayout tarjeta5 = Estilo.tarjeta(this);
        LinearLayout linearLayout7 = new LinearLayout(this);
        linearLayout7.setOrientation(1);
        TextView titulo3 = Estilo.titulo(this, Idioma.t("Ajustes finos ▸"), 18, Estilo.TEXTO);
        titulo3.setGravity(17);
        titulo3.setTypeface(titulo3.getTypeface(), 1);
        titulo3.setPadding(0, Estilo.dp(this, 12.0f), 0, Estilo.dp(this, 12.0f));
        titulo3.setOnClickListener(new DesplegarAjustes(linearLayout7));
        tarjeta5.addView(titulo3);
        tarjeta5.addView(linearLayout7);
        linearLayout7.setVisibility(8);
        LinearLayout fila3 = Estilo.fila(this);
        TextView titulo4 = Estilo.titulo(this, Idioma.t("Sonoridad (LUFS)"), PEDIR_SALIDA, Estilo.TEXTO);
        this.etiquetaLufs = titulo4;
        titulo4.setLayoutParams(Estilo.peso(this, 1.0f));
        fila3.addView(titulo4);
        Button boton2 = Estilo.boton(this, Idioma.t("Auto"), Estilo.CIAN, -16375254, 12.0f);
        this.botonAuto = boton2;
        boton2.setId(10);
        boton2.setOnClickListener(this);
        boton2.setLayoutParams(new LinearLayout.LayoutParams(Estilo.dp(this, 74.0f), Estilo.dp(this, 36.0f)));
        fila3.addView(boton2);
        ProgressBar progressBar2 = new ProgressBar(this);
        this.giroLufs = progressBar2;
        progressBar2.setVisibility(8);
        LinearLayout.LayoutParams layoutParams3 = new LinearLayout.LayoutParams(Estilo.dp(this, 22.0f), Estilo.dp(this, 22.0f));
        this.giroLufs.setLayoutParams(layoutParams3);
        fila3.addView(this.giroLufs);
        linearLayout7.addView(fila3);
        SeekBar seekBar = new SeekBar(this);
        this.barraLufs = seekBar;
        seekBar.setMax(180);
        this.barraLufs.setProgress(140);
        this.barraLufs.setOnSeekBarChangeListener(new VigilarBarraLufs(this));
        linearLayout7.addView(this.barraLufs);
        EditText editText = new EditText(this);
        this.campoLufs = editText;
        editText.setText("-10.0");
        this.campoLufs.setTextColor(Estilo.TEXTO);
        this.campoLufs.setBackground(Estilo.redondeado(-14474438, Estilo.dp(this, 12.0f), 1, Estilo.BORDE));
        this.campoLufs.setPadding(Estilo.dp(this, 12.0f), Estilo.dp(this, 8.0f), Estilo.dp(this, 12.0f), Estilo.dp(this, 8.0f));
        this.campoLufs.setInputType(12290);
        this.campoLufs.addTextChangedListener(new VigilarLufs(this));
        linearLayout7.addView(this.campoLufs);
        LinearLayout fila4 = Estilo.fila(this);
        TextView titulo5 = Estilo.titulo(this, Idioma.t("Intensidad del efecto: 100 %"), PEDIR_SALIDA, Estilo.TEXTO);
        titulo5.setLayoutParams(Estilo.peso(this, 1.0f));
        this.etiquetaIntensidad = titulo5;
        fila4.addView(titulo5);
        Button boton3 = Estilo.boton(this, Idioma.t("Fijo"), Estilo.CIAN, -16375254, 12.0f);
        this.botonFijo = boton3;
        boton3.setId(PEDIR_ENTRADA);
        this.botonFijo.setOnClickListener(this);
        this.botonFijo.setLayoutParams(new LinearLayout.LayoutParams(Estilo.dp(this, 74.0f), Estilo.dp(this, 36.0f)));
        fila4.addView(this.botonFijo);
        ProgressBar progressBar3 = new ProgressBar(this);
        this.giroIntensidad = progressBar3;
        progressBar3.setVisibility(8);
        this.giroIntensidad.setLayoutParams(layoutParams3);
        fila4.addView(this.giroIntensidad);
        linearLayout7.addView(fila4);
        SeekBar seekBar2 = new SeekBar(this);
        this.barraIntensidad = seekBar2;
        seekBar2.setMax(150);
        this.barraIntensidad.setProgress(100);
        this.barraIntensidad.setOnSeekBarChangeListener(this);
        linearLayout7.addView(this.barraIntensidad);
        EditText editText2 = new EditText(this);
        this.campoIntensidad = editText2;
        editText2.setText("100");
        this.campoIntensidad.setTextColor(Estilo.TEXTO);
        this.campoIntensidad.setBackground(Estilo.redondeado(-14474438, Estilo.dp(this, 12.0f), 1, Estilo.BORDE));
        this.campoIntensidad.setPadding(Estilo.dp(this, 12.0f), Estilo.dp(this, 8.0f), Estilo.dp(this, 12.0f), Estilo.dp(this, 8.0f));
        this.campoIntensidad.setInputType(2);
        this.campoIntensidad.addTextChangedListener(new VigilarIntensidad(this));
        linearLayout7.addView(this.campoIntensidad);
        linearLayout.addView(tarjeta5);
        TextView titulo6 = Estilo.titulo(this, "PitmasterAI · IAradio.ES", PEDIR_SALIDA, Estilo.CIAN);
        titulo6.setGravity(17);
        titulo6.setPadding(0, Estilo.dp(this, 18.0f), 0, Estilo.dp(this, 6.0f));
        titulo6.setId(9);
        titulo6.setOnClickListener(this);
        linearLayout.addView(titulo6);
        Button boton4 = Estilo.boton(this, Idioma.t("♥ Donar"), Estilo.VIOLETA, -1, 14.0f);
        boton4.setId(8);
        boton4.setOnClickListener(this);
        LinearLayout.LayoutParams layoutParams4 = new LinearLayout.LayoutParams(-1, -2);
        layoutParams4.setMargins(0, 0, 0, Estilo.dp(this, 18.0f));
        boton4.setLayoutParams(layoutParams4);
        linearLayout.addView(boton4);
        ScrollView scrollView = new ScrollView(this);
        scrollView.setBackgroundColor(Estilo.FONDO);
        scrollView.addView(linearLayout);
        this.raiz = scrollView;
        return scrollView;
    }

    /** Pinta las dos banderas: la del idioma activo en rosa, la otra oscura. */
    private void pintarBanderas() {
        if (this.botonEs != null) {
            pintarBandera(this.botonEs, Idioma.ES.equals(Idioma.idioma()));
        }
        if (this.botonEn != null) {
            pintarBandera(this.botonEn, Idioma.EN.equals(Idioma.idioma()));
        }
    }

    private void pintarBandera(Button boton, boolean activo) {
        boton.setTextColor(activo ? -1 : Estilo.TEXTO);
        boton.setBackground(activo
                ? Estilo.redondeado(Estilo.ROSA, Estilo.dp(this, 12.0f), Estilo.dp(this, 1.0f), -1)
                : Estilo.redondeado(-14474438, Estilo.dp(this, 12.0f), Estilo.dp(this, 1.0f), Estilo.BORDE));
    }

    /** Recorre la pantalla y cambia los textos fijos que sepa traducir. */
    private void repintarTextos(View vista) {
        if (vista instanceof TextView) {
            TextView texto = (TextView) vista;
            CharSequence puesto = texto.getText();
            String nuevo = Idioma.de(puesto == null ? null : puesto.toString());
            if (nuevo != null && !nuevo.contentEquals(puesto)) {
                texto.setText(nuevo);
            }
        }
        if (vista instanceof ViewGroup) {
            ViewGroup grupo = (ViewGroup) vista;
            for (int i = 0; i < grupo.getChildCount(); i++) {
                repintarTextos(grupo.getChildAt(i));
            }
        }
    }

    private boolean algunaSuena() {
        try {
            MediaPlayer activo = this.viendoOriginal ? this.jugadorOriginal : this.jugadorMaster;
            return activo != null && activo.isPlaying();
        } catch (Exception e) {
            return false;
        }
    }

    /**
     * Cambia todos los textos al idioma elegido sin recrear la actividad.
     * Recrearla paraba el audio (onDestroy suelta los reproductores), así que aquí
     * solo se repinta lo que ya está en pantalla y el sonido no se toca.
     */
    private void aplicarIdioma() {
        if (this.raiz != null) {
            repintarTextos(this.raiz);
        }
        for (Button boton : new ArrayList<Button>(this.botonesPreset)) {
            Object etiqueta = boton.getTag();
            if (etiqueta instanceof Integer) {
                boton.setText(Idioma.t(Presets.NOMBRES[((Integer) etiqueta).intValue()]));
            }
        }
        if (this.etiquetaMotor != null) {
            this.etiquetaMotor.setText(Acelerador.detalleDoble(this));
        }
        pintarEstadoAuto();
        pintarEstadoIntensidad();
        if (this.etiquetaIntensidad != null && this.barraIntensidad != null) {
            this.etiquetaIntensidad.setText(Idioma.t("Intensidad del efecto: ")
                    + this.barraIntensidad.getProgress() + " %");
        }
        if (this.botonVariaciones != null) {
            int cuantos = this.cajaVariaciones == null ? 0 : this.cajaVariaciones.getChildCount();
            boolean plegado = this.cajaVariaciones == null || this.cajaVariaciones.getVisibility() != 0;
            this.botonVariaciones.setText(String.format(
                    Idioma.t(plegado ? "Más variaciones (%d) ▾" : "Más variaciones (%d) ▴"),
                    Integer.valueOf(cuantos)));
        }
        if (this.perfil != null && this.etiquetaPerfil != null) {
            this.etiquetaPerfil.setText(resumenPerfil(this.perfil)
                    + String.format(Idioma.t(" · graves %+.1f dB · agudos %+.1f dB"),
                    Double.valueOf(this.perfil.gravesDb), Double.valueOf(this.perfil.agudosDb)));
        }
        if (this.pistaIndice >= 0 && this.etiquetaPista != null) {
            this.etiquetaPista.setText(Idioma.t("Por cómo suena, encaja ")
                    + Idioma.t(Presets.NOMBRES[this.pistaIndice])
                    + Idioma.t(". Empiezas con Amplificador; cámbialo cuando quieras."));
        }
        if (this.estadoIndice >= 0 && this.etiquetaEstado != null) {
            this.etiquetaEstado.setText(Idioma.t("Aplicando ")
                    + Idioma.t(Presets.NOMBRES[this.estadoIndice]) + "…");
        }
        if (this.viendoOriginal || this.indiceActual < 0) {
            mostrarInfoOriginal();
        } else {
            mostrarInfoMaster();
        }
        if (this.botonPlay != null) {
            this.botonPlay.setText(Idioma.t(algunaSuena() ? "■ Parar" : "▶ Escuchar"));
        }
        pintarBanderas();
        Registro.escribir("Idioma: " + Idioma.idioma() + " (sin cortar la reproducción)");
    }

    /** Botón de bandera del selector de idioma: el activo va en rosa con texto blanco. */
    private Button botonIdioma(final String codigo, String bandera) {
        boolean activo = codigo.equals(Idioma.idioma());
        Button boton = new Button(this);
        boton.setText(bandera);
        boton.setTextSize(13.0f);
        boton.setAllCaps(false);
        boton.setTextColor(activo ? -1 : Estilo.TEXTO);
        boton.setBackground(activo
                ? Estilo.redondeado(Estilo.ROSA, Estilo.dp(this, 12.0f), Estilo.dp(this, 1.0f), -1)
                : Estilo.redondeado(-14474438, Estilo.dp(this, 12.0f), Estilo.dp(this, 1.0f), Estilo.BORDE));
        boton.setPadding(Estilo.dp(this, 4.0f), 0, Estilo.dp(this, 4.0f), 0);
        boton.setMinWidth(0);
        boton.setMinimumWidth(0);
        boton.setMinHeight(0);
        boton.setMinimumHeight(0);
        LinearLayout.LayoutParams parametros = new LinearLayout.LayoutParams(Estilo.dp(this, 46.0f), Estilo.dp(this, 32.0f));
        parametros.setMargins(Estilo.dp(this, 6.0f), 0, 0, Estilo.dp(this, 6.0f));
        boton.setLayoutParams(parametros);
        boton.setId(Idioma.ES.equals(codigo) ? ID_BOTON_ES : ID_BOTON_EN);
        boton.setOnClickListener(this);
        return boton;
    }

    /** Resumen del perfil (antes Analizador.resumen(), que estaba solo en español). */
    private static String resumenPerfil(Analizador.Perfil perfil) {
        if (perfil == null) {
            return "";
        }
        return String.format(Idioma.t("%.1f LUFS · cresta %.1f dB · estéreo %.2f"),
                Double.valueOf(perfil.lufs), Double.valueOf(perfil.cresta), Double.valueOf(perfil.correlacion));
    }

    // En horizontal, un cuarto de pantalla de margen a cada lado: el contenido
    // queda centrado y los dos laterales iguales.
    private void aplicarMargenes() {
        if (this.raiz == null) {
            return;
        }
        int lado = 0;
        if (getResources().getConfiguration().orientation == Configuration.ORIENTATION_LANDSCAPE) {
            lado = Math.round(getResources().getDisplayMetrics().widthPixels * 0.25f);
        }
        this.raiz.setPadding(lado, this.raiz.getPaddingTop(), lado, this.raiz.getPaddingBottom());
    }

    @Override // android.app.Activity, android.content.ComponentCallbacks
    public void onConfigurationChanged(Configuration configuration) {
        super.onConfigurationChanged(configuration);
        aplicarMargenes();
    }

    /* JADX INFO: Access modifiers changed from: private */
    public File ficheroCache(int i, float f, Double d) {
        String valueOf = String.valueOf(Math.round(f * 100.0f));
        String valueOf2 = d == null ? "auto" : String.valueOf(Math.round(d.doubleValue() * 10.0d));
        return new File(getCacheDir(), "m_" + i + "_" + valueOf + "_" + valueOf2 + ".wav");
    }

    private void limpiarCache() {
        this.generacionPrecalentado++;
        this.tpOriginal = Double.NaN;
        this.lufsMaster = Double.NaN;
        this.tpMaster = Double.NaN;
        this.pausaManual = false;
        this.hechos.clear();
        this.calculando.clear();
        File[] listFiles = getCacheDir().listFiles();
        if (listFiles == null) {
            return;
        }
        for (File file : listFiles) {
            String name = file.getName();
            if (name.startsWith("m_") || name.equals("original.wav") || name.equals("master.wav")) {
                file.delete();
            }
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    public int indiceDe(String str) {
        for (int i = 0; i < Presets.CLAVES.length; i++) {
            if (Presets.CLAVES[i].equals(str)) {
                return i;
            }
        }
        return 0;
    }

    @Override // android.view.View.OnClickListener
    public void onClick(View view) {
        int id = view.getId();
        if (id == ID_BOTON_ES || id == ID_BOTON_EN) {
            String elegido = id == ID_BOTON_ES ? Idioma.ES : Idioma.EN;
            if (!elegido.equals(Idioma.idioma())) {
                // se repinta la pantalla SIN recrear la actividad: el audio sigue sonando
                Idioma.poner(this, elegido);
                aplicarIdioma();
            }
            return;
        }
        if (id == 1) {
            Intent intent = new Intent("android.intent.action.OPEN_DOCUMENT");
            intent.addCategory("android.intent.category.OPENABLE");
            intent.setType("*/*");
            intent.addFlags(65);
            try {
                startActivityForResult(intent, PEDIR_ENTRADA);
                return;
            } catch (Exception unused) {
                Toast.makeText(this, Idioma.t("No hay selector de archivos"), 1).show();
                return;
            }
        }
        if (id == 2) {
            alternarReproduccion();
            return;
        }
        if (id == 3) {
            Intent intent2 = new Intent("android.intent.action.CREATE_DOCUMENT");
            intent2.addCategory("android.intent.category.OPENABLE");
            intent2.setType("audio/wav");
            intent2.putExtra("android.intent.extra.TITLE", this.nombreEntrada.replaceAll("\\.[^.]+$", "").trim() + "_" + (this.indiceActual >= 0 ? Presets.NOMBRES[this.indiceActual] : "Master") + ".wav");
            try {
                startActivityForResult(intent2, PEDIR_SALIDA);
                return;
            } catch (Exception unused2) {
                Toast.makeText(this, Idioma.t("No se puede guardar"), 1).show();
                return;
            }
        }
        if (id == 10) {
            alternarAuto();
            return;
        }
        if (id == PEDIR_ENTRADA) {
            this.intensidadFija = !this.intensidadFija;
            pintarEstadoIntensidad();
            Toast.makeText(this, this.intensidadFija ? Idioma.t("Intensidad fija") : Idioma.t("Intensidad manual"), 0).show();
            return;
        }
        if (id == 9) {
            try {
                startActivity(new Intent("android.intent.action.VIEW", Uri.parse("https://www.iaradio.es")));
                return;
            } catch (Exception unused3) {
                Toast.makeText(this, Idioma.t("No hay navegador"), 1).show();
                return;
            }
        }
        if (id == 8) {
            try {
                startActivity(new Intent("android.intent.action.VIEW", Uri.parse("https://www.paypal.com/paypalme/PitmasterAI")));
                return;
            } catch (Exception unused4) {
                Toast.makeText(this, Idioma.t("No hay navegador"), 1).show();
                return;
            }
        }
        if (id == 4) {
            Intent intent3 = new Intent("android.intent.action.SEND");
            intent3.setType("text/plain");
            intent3.putExtra("android.intent.extra.SUBJECT", Idioma.t("MasterLab registro"));
            intent3.putExtra("android.intent.extra.TEXT", Registro.contenido());
            try {
                startActivity(Intent.createChooser(intent3, Idioma.t("Compartir registro")));
                return;
            } catch (Exception unused5) {
                Toast.makeText(this, Idioma.t("No hay apps para compartir"), 1).show();
                return;
            }
        }
        if (id == 5) {
            cambiarFuente(false);
            return;
        }
        if (id == 6) {
            cambiarFuente(true);
        } else if (id == 7) {
            boolean z = this.cajaVariaciones.getVisibility() == 0;
            this.cajaVariaciones.setVisibility(z ? 8 : 0);
            this.botonVariaciones.setText(z ? Idioma.t("Más variaciones (20) ▾") : Idioma.t("Más variaciones (20) ▴"));
        }
    }

    @Override // es.pitmasterai.masterlab.OndaSonido.AlTocar
    public void alArrastrar(float f) {
        this.arrastrandoOnda = true;
    }

    @Override // es.pitmasterai.masterlab.OndaSonido.AlTocar
    public void alSoltar(float f) {
        this.arrastrandoOnda = false;
        alBuscar(f);
    }

    @Override // es.pitmasterai.masterlab.OndaSonido.AlTocar
    public void alBuscar(float f) {
        MediaPlayer mediaPlayer = this.viendoOriginal ? this.jugadorOriginal : this.jugadorMaster;
        if (mediaPlayer == null) {
            return;
        }
        try {
            int duration = mediaPlayer.getDuration();
            if (duration <= 0) {
                return;
            }
            int i = (int) (duration * f);
            if (i < 0) {
                i = 0;
            }
            this.posicionDeseada = i;
            boolean isPlaying = mediaPlayer.isPlaying();
            mediaPlayer.seekTo(i);
            if (isPlaying) {
                mediaPlayer.start();
            }
            this.onda.setProgreso(f);
            Registro.escribir("Salto a " + (i / 1000) + " s");
        } catch (Exception e) {
            Registro.escribir("seek onda: " + e);
        }
    }

    @Override // android.widget.SeekBar.OnSeekBarChangeListener
    public void onProgressChanged(SeekBar seekBar, int i, boolean z) {
        EditText editText;
        this.etiquetaIntensidad.setText(Idioma.t("Intensidad del efecto: ") + i + " %");
        if (z && (editText = this.campoIntensidad) != null) {
            this.sincronizando = true;
            editText.setText(String.valueOf(i));
            this.sincronizando = false;
        }
        if (!z || this.indiceActual < 0 || this.datos == null) {
            return;
        }
        this.hilo.removeCallbacks(this.aplicarLufs);
        this.hilo.postDelayed(this.aplicarLufs, 500L);
    }

    @Override // android.widget.SeekBar.OnSeekBarChangeListener
    public void onStopTrackingTouch(SeekBar seekBar) {
        if (this.indiceActual >= 0) {
            this.hilo.removeCallbacks(this.aplicarLufs);
            masterizar(this.indiceActual);
        }
    }

    @Override // android.app.Activity
    protected void onActivityResult(int i, int i2, Intent intent) {
        if (i != PEDIR_ENTRADA) {
            if (i == PEDIR_SALIDA) {
                if (i2 != -1 || intent == null || intent.getData() == null) {
                    return;
                }
                guardarEn(intent.getData());
                return;
            }
            super.onActivityResult(i, i2, intent);
            return;
        }
        if (i2 != -1 || intent == null || intent.getData() == null) {
            return;
        }
        this.uriEntrada = intent.getData();
        try {
            getContentResolver().takePersistableUriPermission(this.uriEntrada, 1);
        } catch (Exception e) {
            Registro.escribir("permiso no persistente: " + e);
        }
        String nombreReal = nombreReal(this.uriEntrada);
        this.nombreEntrada = nombreReal;
        this.etiquetaArchivo.setText(nombreReal);
        empezarAnalisis();
    }

    private void alternarAuto() {
        int i;
        this.modoAuto = !this.modoAuto;
        pintarEstadoAuto();
        if (this.modoAuto) {
            if (this.perfil != null && (i = this.indiceActual) >= 0) {
                masterizar(i, 0);
                return;
            } else {
                Toast.makeText(this, Idioma.t("En automático: carga una canción"), 0).show();
                return;
            }
        }
        Toast.makeText(this, Idioma.t("Sonoridad manual"), 0).show();
    }

    private void pintarEstadoIntensidad() {
        boolean z = this.intensidadFija;
        boolean z2 = !z;
        Button button = this.botonFijo;
        int i = Estilo.CIAN;
        if (button != null) {
            button.setText(z ? Idioma.t("Fijo ✓") : Idioma.t("Fijo"));
            this.botonFijo.setBackground(Estilo.redondeado(this.intensidadFija ? Estilo.CIAN : -16375254, Estilo.dp(this, 14.0f), 0, 0));
            this.botonFijo.setTextColor(this.intensidadFija ? -16375254 : Estilo.TEXTO);
        }
        SeekBar seekBar = this.barraIntensidad;
        if (seekBar != null) {
            seekBar.setEnabled(z2);
            this.barraIntensidad.setAlpha(z2 ? 1.0f : 0.3f);
        }
        EditText editText = this.campoIntensidad;
        if (editText != null) {
            editText.setEnabled(z2);
            this.campoIntensidad.setAlpha(z2 ? 1.0f : 0.35f);
            EditText editText2 = this.campoIntensidad;
            if (!z2) {
                i = -9737344;
            }
            editText2.setTextColor(i);
            this.campoIntensidad.setBackground(Estilo.redondeado(z2 ? Estilo.TARJETA : -15724520, Estilo.dp(this, 14.0f), Estilo.dp(this, 1.0f), z2 ? -13750716 : -14935002));
        }
        TextView textView = this.etiquetaIntensidad;
        if (textView != null) {
            textView.setAlpha(z2 ? 1.0f : 0.45f);
        }
    }

    private void pintarEstadoAuto() {
        boolean z = this.modoAuto;
        boolean z2 = !z;
        Button button = this.botonAuto;
        int i = Estilo.CIAN;
        if (button != null) {
            button.setText(z ? Idioma.t("Auto ✓") : Idioma.t("Auto"));
            this.botonAuto.setBackground(Estilo.redondeado(this.modoAuto ? Estilo.CIAN : -16375254, Estilo.dp(this, 14.0f), 0, 0));
            this.botonAuto.setTextColor(this.modoAuto ? -16375254 : Estilo.TEXTO);
        }
        SeekBar seekBar = this.barraLufs;
        if (seekBar != null) {
            seekBar.setEnabled(z2);
            this.barraLufs.setAlpha(z2 ? 1.0f : 0.3f);
        }
        EditText editText = this.campoLufs;
        if (editText != null) {
            editText.setEnabled(z2);
            this.campoLufs.setAlpha(z2 ? 1.0f : 0.35f);
            EditText editText2 = this.campoLufs;
            if (!z2) {
                i = -9737344;
            }
            editText2.setTextColor(i);
            this.campoLufs.setBackground(Estilo.redondeado(z2 ? Estilo.TARJETA : -15724520, Estilo.dp(this, 14.0f), Estilo.dp(this, 1.0f), z2 ? -13750716 : -14935002));
        }
        TextView textView = this.etiquetaLufs;
        if (textView != null) {
            textView.setAlpha(z2 ? 1.0f : 0.45f);
        }
    }

    private double lufsAutoPara(int i) {
        if (this.perfil == null) {
            return -10.0d;
        }
        Preset crear = Presets.crear(i);
        double d = crear.lufs;
        double max = Math.max(-1.5d, Math.min(1.5d, (this.perfil.cresta - 14.0d) * 0.3d));
        Double.isNaN(d);
        // el usuario quiere 1,5 dB mas en todos los ajustes
        double max2 = Math.max(-16.0d, Math.min(-6.0d, d + max + 1.5d));
        if (this.perfil.lufs > max2) {
            max2 = Math.min(this.perfil.lufs, -6.0d);
        }
        if (this.perfil.lufs <= -12.0d) {
            return max2;
        }
        double d2 = 0.0d;
        if (crear.satMix >= 0.05d) {
            double d3 = crear.satMix;
            Double.isNaN(d3);
            d2 = 0.0d + Math.min(1.8d, d3 * 9.0d);
        }
        if (crear.compScale > 0.85d) {
            double d4 = crear.compScale;
            Double.isNaN(d4);
            d2 += Math.min(1.2d, (d4 - 0.85d) * 8.0d);
        }
        if (this.perfil.cresta < 11.0d) {
            d2 += 0.5d;
        }
        return Math.max(-16.0d, max2 - Math.min(2.5d, d2));
    }

    Double objetivoPara(int i, Double d) {
        if (!this.modoAuto) {
            return d;
        }
        double round = Math.round(lufsAutoPara(i) * 10.0d);
        Double.isNaN(round);
        return Double.valueOf(round / 10.0d);
    }

    float intensidadPara(int i, float f) {
        return (!this.modoAuto || this.intensidadFija) ? f : intensidadAutoPara(i) / 100.0f;
    }

    private Double objetivoManual() {
        try {
            String trim = this.campoLufs.getText().toString().trim();
            if (trim.length() == 0) {
                return null;
            }
            return Double.valueOf(trim);
        } catch (Exception unused) {
            return null;
        }
    }

    private float intensidadManual() {
        if (this.barraIntensidad == null) {
            return 1.0f;
        }
        return this.barraIntensidad.getProgress() / 100.0f;
    }

    private int intensidadAutoPara(int i) {
        Analizador.Perfil perfil = this.perfil;
        if (perfil == null) {
            return 100;
        }
        double d = ((perfil.cresta - 9.0d) * 0.05d) + 0.55d;
        double d2 = Presets.crear(i).compScale;
        Double.isNaN(d2);
        return (int) Math.round(Math.max(50.0d, Math.min(120.0d, d * ((d2 * 0.5d) + 0.7d) * 100.0d)));
    }

    private void aplicarAuto() {
        Analizador.Perfil perfil = this.perfil;
        if (perfil == null) {
            Toast.makeText(this, Idioma.t("Primero carga una canción"), 0).show();
            return;
        }
        double d = ((perfil.lufs * (-0.678d)) + (this.perfil.cresta * 0.336d)) - 11.91d;
        double max = Math.max(-16.0d, Math.min(-8.0d, this.perfil.lufs + d));
        double max2 = Math.max(0.5d, Math.min(1.2d, ((this.perfil.cresta - 9.0d) * 0.05d) + 0.55d));
        this.sincronizando = true;
        double round = Math.round(max * 10.0d);
        Double.isNaN(round);
        double d2 = round / 10.0d;
        this.campoLufs.setText(String.format(Locale.US, "%.1f", Double.valueOf(d2)));
        this.barraLufs.setProgress((int) Math.round((24.0d + d2) * 10.0d));
        int round2 = (int) Math.round(max2 * 100.0d);
        this.campoIntensidad.setText(String.valueOf(round2));
        this.barraIntensidad.setProgress(round2);
        this.etiquetaIntensidad.setText(Idioma.t("Intensidad del efecto: ") + round2 + " %");
        this.sincronizando = false;
        Registro.escribir(String.format("Auto: %.1f LUFS y %d %% (ganancia prevista %.1f dB)", Double.valueOf(d2), Integer.valueOf(round2), Double.valueOf(d)));
        int i = this.indiceActual;
        if (i < 0) {
            i = indiceDe("base_claro");        // todos empiezan en Claro
        }
        masterizar(i, 0);
    }

    void escribirFicha(File file, double d, double d2, int i) {
        try {
            FileWriter fileWriter = new FileWriter(file.getAbsolutePath() + ".txt");
            fileWriter.write(String.format(Locale.US, "%.2f;%.2f;%d", Double.valueOf(d), Double.valueOf(d2), Integer.valueOf(i)));
            fileWriter.close();
        } catch (Exception e) {
            Registro.escribir("sin ficha en precálculo: " + e);
        }
    }

    private double[] leerFicha(File file) {
        try {
            File file2 = new File(file.getAbsolutePath() + ".txt");
            if (!file2.exists()) {
                return null;
            }
            BufferedReader bufferedReader = new BufferedReader(new FileReader(file2));
            String readLine = bufferedReader.readLine();
            bufferedReader.close();
            if (readLine == null) {
                return null;
            }
            String[] split = readLine.split(";");
            if (split.length < 2) {
                return null;
            }
            return new double[]{Double.parseDouble(split[0]), Double.parseDouble(split[1])};
        } catch (Exception unused) {
            return null;
        }
    }

    private String nombreReal(Uri uri) {
        String str = null;
        try {
            Cursor query = getContentResolver().query(uri, null, null, null, null);
            if (query != null) {
                int columnIndex = query.getColumnIndex("_display_name");
                if (query.moveToFirst() && columnIndex >= 0) {
                    str = query.getString(columnIndex);
                }
                query.close();
            }
        } catch (Exception e) {
            Registro.escribir("no se pudo leer el nombre: " + e);
        }
        if (str == null || str.trim().length() == 0) {
            String lastPathSegment = uri.getLastPathSegment();
            if (lastPathSegment == null) {
                lastPathSegment = "cancion";
            }
            str = lastPathSegment;
            int lastIndexOf = str.lastIndexOf(47);
            if (lastIndexOf >= 0) {
                str = str.substring(lastIndexOf + 1);
            }
        }
        return str.trim();
    }

    private void empezarAnalisis() {
        empezarAnalisis(true);
    }

    private void empezarAnalisis(boolean z) {
        pararTodo();
        if (z) {
            limpiarCache();
        }
        this.datos = null;
        this.resultado = null;
        this.ficheroOriginal = null;
        this.ficheroMaster = null;
        System.gc();
        this.datos = null;
        this.indiceActual = -1;
        this.resultado = null;
        this.ficheroMaster = null;
        this.botonPlay.setEnabled(false);
        this.botonGuardar.setEnabled(false);
        this.botonOriginal.setEnabled(false);
        this.botonMaster.setEnabled(false);
        this.etiquetaPerfil.setText(Idioma.t("Analizando…"));
        this.etiquetaSonando.setText("");
        this.etiquetaPista.setText("");
        this.cajaDestacados.removeAllViews();
        this.cajaVariaciones.removeAllViews();
        this.onda.setPicos(new float[0]);
        this.onda.setProgreso(0.0f);
        this.progreso.setVisibility(0);
        this.etiquetaEstado.setText(Idioma.t("Trabajando…"));
        new Thread(new TareaAnalizar(this, this.uriEntrada, this.generacionAnalisis)).start();
    }

    void analisisListo(Wav.Datos datos, File file, Analizador.Perfil perfil, double[] dArr, int[] iArr, int i) {
        if (i != this.generacionAnalisis) {
            Registro.escribir("Análisis descartado: hay uno más nuevo");
        } else {
            this.hilo.post(new EntregaAnalisis(this, datos, file, perfil, dArr, iArr, i));
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    /* loaded from: classes.dex */
    public static class EntregaAnalisis implements Runnable {
        private final MainActivity a;
        private final Wav.Datos d;
        final int generacion;
        private final double[] notas;
        private final int[] orden;
        private final File original;
        private final Analizador.Perfil p;

        EntregaAnalisis(MainActivity mainActivity, Wav.Datos datos, File file, Analizador.Perfil perfil, double[] dArr, int[] iArr, int i) {
            this.generacion = i;
            this.a = mainActivity;
            this.d = datos;
            this.original = file;
            this.p = perfil;
            this.notas = dArr;
            this.orden = iArr;
        }

        @Override // java.lang.Runnable
        public void run() {
            if (this.generacion == this.a.generacionAnalisis) {
                this.a.progreso.setVisibility(8);
                this.a.datos = this.d;
                this.a.frecuencia = this.d.frecuencia;
                this.a.perfil = this.p;
                this.a.ficheroOriginal = this.original;
                this.a.etiquetaPerfil.setText(resumenPerfil(this.p) + String.format(Idioma.t(" · graves %+.1f dB · agudos %+.1f dB"), Double.valueOf(this.p.gravesDb), Double.valueOf(this.p.agudosDb)));
                int[] iArr = this.orden;
                int i = iArr[0];
                MainActivity mainActivity = this.a;
                mainActivity.recomendados = mainActivity.dosRecomendadas(iArr);
                this.a.ordenCompleto = (int[]) this.orden.clone();
                this.a.listaCola = null;
                this.a.pistaIndice = i;
                this.a.etiquetaPista.setText(Idioma.t("Por cómo suena, encaja ") + Idioma.t(Presets.NOMBRES[i]) + Idioma.t(". Empiezas con Amplificador; cámbialo cuando quieras."));
                File file = this.original;
                if (file == null || file.exists()) {
                    this.a.prepararJugador(true);
                } else {
                    Registro.escribir("El original desapareció (otra canción): no se prepara");
                }
                this.a.botonOriginal.setEnabled(true);
                this.a.botonPlay.setEnabled(true);
                MainActivity mainActivity2 = this.a;
                mainActivity2.picosOriginal = mainActivity2.calcularPicos();
                MainActivity mainActivity3 = this.a;
                mainActivity3.picosMaster = mainActivity3.picosOriginal;
                this.a.viendoOriginal = true;
                this.a.marcarFuente();
                this.a.pintarOndaDeLaVersion();
                // en cuanto carga la canción empieza a sonar, marcando Original
                this.a.reproducir();
                this.a.pintarOpciones();
                this.a.etiquetaEstado.setText("");
                if (Double.isNaN(this.a.tpOriginal)) {
                    new Thread(new MedirPico(this.a, this.d), "pico-original").start();
                }
                try {
                    if (this.a.jugadorOriginal != null) {
                        this.a.jugadorOriginal.start();
                        this.a.botonPlay.setText(Idioma.t("■ Parar"));
                        this.a.mostrarInfoOriginal();
                    }
                } catch (Exception e) {
                    Registro.escribir("no arranca el original: " + e);
                }
                if (this.a.indiceAlRestaurar != null && this.a.indiceAlRestaurar.intValue() >= 0 && this.a.indiceAlRestaurar.intValue() < Presets.CLAVES.length) {
                    int intValue = this.a.indiceAlRestaurar.intValue();
                    this.a.indiceAlRestaurar = null;
                    this.a.masterizar(intValue);
                    return;
                } else {
                    MainActivity mainActivity4 = this.a;
                    mainActivity4.masterizar(mainActivity4.indiceDe("base_claro"));
                    return;
                }
            }
            Registro.escribir("Análisis viejo descartado al entregar");
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    public float[] picosDe(float[][] fArr) {
        if (fArr == null || fArr.length == 0) {
            return new float[0];
        }
        int length = fArr[0].length;
        float[] fArr2 = new float[240];
        int max = Math.max(1, length / 240);
        for (int i = 0; i < 240; i++) {
            int i2 = i * max;
            int min = Math.min(length, i2 + max);
            float f = 0.0f;
            while (i2 < min) {
                for (float[] fArr3 : fArr) {
                    float abs = Math.abs(fArr3[i2]);
                    if (abs > f) {
                        f = abs;
                    }
                }
                i2++;
            }
            fArr2[i] = f;
        }
        return fArr2;
    }

    /* JADX INFO: Access modifiers changed from: private */
    public void pintarOndaDeLaVersion() {
        OndaSonido ondaSonido = this.onda;
        if (ondaSonido == null) {
            return;
        }
        ondaSonido.setPicos(this.viendoOriginal ? this.picosOriginal : this.picosMaster);
    }

    /* JADX INFO: Access modifiers changed from: private */
    public float[] calcularPicos() {
        Wav.Datos datos = this.datos;
        if (datos == null) {
            return new float[0];
        }
        int tramas = datos.tramas();
        int canales = this.datos.canales();
        float[] fArr = new float[240];
        int max = Math.max(1, tramas / 240);
        float f = 1.0E-6f;
        for (int i = 0; i < 240; i++) {
            int i2 = i * max;
            int min = Math.min(tramas, i2 + max);
            float f2 = 0.0f;
            while (i2 < min) {
                for (int i3 = 0; i3 < canales; i3++) {
                    float abs = Math.abs(this.datos.muestras[i3][i2]);
                    if (abs > f2) {
                        f2 = abs;
                    }
                }
                i2++;
            }
            fArr[i] = f2;
            if (f2 > f) {
                f = f2;
            }
        }
        for (int i4 = 0; i4 < 240; i4++) {
            fArr[i4] = fArr[i4] / f;
        }
        return fArr;
    }

    /* JADX INFO: Access modifiers changed from: private */
    public void pintarOpciones() {
        LinearLayout linearLayout = this.cajaRecomendadaCompleta;
        if (linearLayout != null) {
            linearLayout.setVisibility(0);
        }
        this.cajaDestacados.removeAllViews();
        this.cajaRecomendadas.removeAllViews();
        this.cajaVariaciones.removeAllViews();
        this.botonesPreset.clear();
        this.giros.clear();
        LinearLayout linearLayout2 = null;
        LinearLayout linearLayout3 = null;
        for (int i = 0; i < this.recomendados.length; i++) {
            if (i % 2 == 0) {
                linearLayout3 = Estilo.fila(this);
                LinearLayout.LayoutParams layoutParams = new LinearLayout.LayoutParams(-1, -2);
                layoutParams.setMargins(0, Estilo.dp(this, 8.0f), 0, 0);
                linearLayout3.setLayoutParams(layoutParams);
                this.cajaRecomendadas.addView(linearLayout3);
            }
            Button botonPreset = botonPreset(this.recomendados[i], -12971996);
            botonPreset.setLayoutParams(Estilo.peso(this, 1.0f));
            linearLayout3.addView(botonPreset);
        }
        int i2 = 0;
        while (true) {
            String[] strArr = DESTACADOS;
            if (i2 >= strArr.length) {
                break;
            }
            if (i2 % 2 == 0) {
                linearLayout2 = Estilo.fila(this);
                LinearLayout.LayoutParams layoutParams2 = new LinearLayout.LayoutParams(-1, -2);
                layoutParams2.setMargins(0, Estilo.dp(this, 8.0f), 0, 0);
                linearLayout2.setLayoutParams(layoutParams2);
                this.cajaDestacados.addView(linearLayout2);
            }
            Button botonPreset2 = botonPreset(indiceDe(strArr[i2]), -14474438);
            botonPreset2.setLayoutParams(Estilo.peso(this, 1.0f));
            linearLayout2.addView(botonPreset2);
            i2++;
        }
        int i3 = 0;
        for (int i4 = 0; i4 < Presets.CLAVES.length; i4++) {
            int i5 = 0;
            boolean z = false;
            while (true) {
                String[] strArr2 = DESTACADOS;
                if (i5 >= strArr2.length) {
                    break;
                }
                if (strArr2[i5].equals(Presets.CLAVES[i4])) {
                    z = true;
                }
                i5++;
            }
            if (!z) {
                i3++;
                LinearLayout.LayoutParams layoutParams3 = new LinearLayout.LayoutParams(-1, -2);
                layoutParams3.setMargins(0, Estilo.dp(this, 6.0f), 0, 0);
                Button botonPreset3 = botonPreset(i4, -15000791);
                botonPreset3.setLayoutParams(layoutParams3);
                this.cajaVariaciones.addView(botonPreset3);
            }
        }
        this.botonVariaciones.setText(String.format(Idioma.t("Más variaciones (%d) ▾"), i3));
    }

    private Button botonPreset(int i, int i2) {
        Button boton = Estilo.boton(this, Idioma.t(Presets.NOMBRES[i]), i2, Estilo.TEXTO, 14.0f);
        boton.setId(i + 2000);
        boton.setOnClickListener(new ElegirOpcion(this, i));
        boton.setPadding(Estilo.dp(this, 14.0f), Estilo.dp(this, 10.0f), Estilo.dp(this, 10.0f), Estilo.dp(this, 10.0f));
        boton.setTag(Integer.valueOf(i));
        this.botonesPreset.add(boton);
        return boton;
    }

    private void girarEn(int i) {
        this.calculando.add(Integer.valueOf(i));
        refrescarIconos();
    }

    private void pararGiros() {
        this.calculando.clear();
        refrescarIconos();
    }

    /* JADX INFO: Access modifiers changed from: private */
    public void refrescarIconos() {
        if (this.botonesPreset.isEmpty()) {
            return;
        }
        Iterator it = new ArrayList(this.botonesPreset).iterator();
        while (it.hasNext()) {
            Button button = (Button) it.next();
            Object tag = button.getTag();
            if (tag instanceof Integer) {
                int intValue = ((Integer) tag).intValue();
                if (this.calculando.contains(Integer.valueOf(intValue))) {
                    AnimationDrawable animationDrawable = this.giros.get(button);
                    if (animationDrawable == null) {
                        animationDrawable = Iconos.giro(this, Estilo.VERDE);
                        this.giros.put(button, animationDrawable);
                    }
                    if (button.getCompoundDrawables()[2] != animationDrawable) {
                        button.setCompoundDrawablesWithIntrinsicBounds((Drawable) null, (Drawable) null, animationDrawable, (Drawable) null);
                        button.setCompoundDrawablePadding(Estilo.dp(this, 8.0f));
                    }
                    if (!animationDrawable.isRunning()) {
                        animationDrawable.start();
                    }
                } else {
                    Drawable drawable = button.getCompoundDrawables()[2];
                    if (drawable instanceof AnimationDrawable) {
                        ((AnimationDrawable) drawable).stop();
                    }
                    if (this.datos != null && hayCacheDe(intValue)) {
                        button.setCompoundDrawablesWithIntrinsicBounds((Drawable) null, (Drawable) null, Iconos.visto(this, Estilo.VERDE), (Drawable) null);
                        button.setCompoundDrawablePadding(Estilo.dp(this, 8.0f));
                    } else {
                        button.setCompoundDrawablesWithIntrinsicBounds((Drawable) null, (Drawable) null, (Drawable) null, (Drawable) null);
                    }
                }
            }
        }
    }

    private boolean hayCacheDe(int i) {
        if (this.hechos.contains(Integer.valueOf(i))) {
            return true;
        }
        if (i == this.indiceActual) {
            return false;
        }
        boolean exists = ficheroCache(i, intensidadPara(i, intensidadManual()), objetivoPara(i, objetivoManual())).exists();
        if (exists) {
            this.hechos.add(Integer.valueOf(i));
        }
        return exists;
    }

    void descartarTrabajo(int i) {
        if (i != this.trabajoActual) {
            this.hilo.post(new QuitarGiros(this));
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    public void actualizarMarcas() {
        refrescarIconos();
    }

    /* JADX INFO: Access modifiers changed from: private */
    public void marcarActivo(int i) {
        LinearLayout[] linearLayoutArr = {this.cajaDestacados, this.cajaRecomendadas, this.cajaVariaciones};
        for (int i2 = 0; i2 < 3; i2++) {
            LinearLayout linearLayout = linearLayoutArr[i2];
            if (linearLayout != null) {
                for (int i3 = 0; i3 < linearLayout.getChildCount(); i3++) {
                    View childAt = linearLayout.getChildAt(i3);
                    if (childAt instanceof LinearLayout) {
                        LinearLayout linearLayout2 = (LinearLayout) childAt;
                        for (int i4 = 0; i4 < linearLayout2.getChildCount(); i4++) {
                            pintarBoton(linearLayout2.getChildAt(i4), i);
                        }
                    } else {
                        pintarBoton(childAt, i);
                    }
                }
            }
        }
    }

    private void pintarBoton(View view, int i) {
        if (view instanceof Button) {
            int i2 = (view.getId() == i + 2000 || view.getId() == i + 3000) ? 1 : 0;
            Button button = (Button) view;
            button.setBackground(Estilo.redondeado(i2 != 0 ? Estilo.ROSA : -14474438, Estilo.dp(this, 14.0f), i2 ^ 1, Estilo.BORDE));
            button.setTextColor(i2 != 0 ? -1 : Estilo.TEXTO);
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    public void masterizar(int i) {
        masterizar(i, 0);
    }

    private void mostrarGiro(int i) {
        ProgressBar progressBar = this.giroIntensidad;
        if (progressBar != null) {
            progressBar.setVisibility(i == 1 ? 0 : 8);
        }
        ProgressBar progressBar2 = this.giroLufs;
        if (progressBar2 != null) {
            progressBar2.setVisibility(i != 2 ? 8 : 0);
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    public void ocultarGiros() {
        ProgressBar progressBar = this.giroIntensidad;
        if (progressBar != null) {
            progressBar.setVisibility(8);
        }
        ProgressBar progressBar2 = this.giroLufs;
        if (progressBar2 != null) {
            progressBar2.setVisibility(8);
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    /* JADX WARN: Removed duplicated region for block: B:27:0x00c2  */
    /* JADX WARN: Removed duplicated region for block: B:29:0x00db  */
    /* JADX WARN: Removed duplicated region for block: B:32:0x00e9  */
    /* JADX WARN: Removed duplicated region for block: B:34:0x00f1  */
    /* JADX WARN: Removed duplicated region for block: B:43:0x019a  */
    /* JADX WARN: Removed duplicated region for block: B:45:0x00c9 A[EXC_TOP_SPLITTER, SYNTHETIC] */
    /* JADX WARN: Removed duplicated region for block: B:49:0x00c5  */
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    /** Aplica un ajuste: si ya está calculado lo reproduce; si no, lo manda a calcular. */
    public void masterizar(int indice, int motivo) {
        if (this.datos == null) {
            return;
        }
        this.motivoUltimo = motivo;
        if (motivo == 1 || motivo == 2) {
            this.hechos.clear();      // cambió la sonoridad o la intensidad a mano
        }
        this.indiceSolicitado = indice;
        this.colaBloqueada = false;
        this.esperasMemoria = 0;
        this.cuarentena.clear();
        Trabajo.cancelar();           // se corta solo el trabajo interactivo anterior

        if (this.modoAuto || this.intensidadFija) {
            this.sincronizando = true;
        }
        if (this.modoAuto) {
            double objetivo = Math.round(lufsAutoPara(indice) * 10.0d) / 10.0d;
            this.campoLufs.setText(String.format(Locale.US, "%.1f", Double.valueOf(objetivo)));
            this.barraLufs.setProgress((int) Math.round((objetivo + 24.0d) * 10.0d));
        }
        if (this.modoAuto && !this.intensidadFija) {
            int porcentaje = intensidadAutoPara(indice);
            this.campoIntensidad.setText(String.valueOf(porcentaje));
            this.barraIntensidad.setProgress(porcentaje);
            this.etiquetaIntensidad.setText(Idioma.t("Intensidad del efecto: ") + porcentaje + " %");
        }
        this.sincronizando = false;

        Double objetivo = objetivoManual();
        float intensidad = intensidadManual();

        // de dónde viene la escucha, para seguir por el mismo punto
        MediaPlayer activo = this.viendoOriginal ? this.jugadorOriginal : this.jugadorMaster;
        if (activo != null) {
            try {
                this.posicionDeseada = activo.getCurrentPosition();
                this.seguiaSonando = activo.isPlaying();
            } catch (Exception e) {
                this.posicionDeseada = 0;
                this.seguiaSonando = false;
            }
        } else {
            this.posicionDeseada = 0;
            this.seguiaSonando = true;
        }

        File cache = ficheroCache(indice, intensidad, objetivo);
        if (!cache.exists()) {
            mostrarGiro(motivo);      // el giro solo si de verdad hay que calcularlo
            girarEn(indice);
        }

        if (cache.exists()) {
            // ya está calculado: se reproduce directamente del fichero
            this.indiceActual = indice;
            this.ficheroMaster = cache;
            this.viendoOriginal = false;
            this.resultado = null;
            prepararJugador(false);
            this.botonPlay.setEnabled(true);
            this.botonGuardar.setEnabled(true);
            this.etiquetaEstado.setText("");
            double[] ficha = leerFicha(cache);
            if (ficha != null) {
                this.lufsMaster = ficha[0];
                this.tpMaster = ficha[1];
            }
            mostrarInfoMaster();
            marcarFuente();
            marcarActivo(indice);
            ocultarGiros();
            this.calculando.remove(Integer.valueOf(indice));
            seguirEnCaliente();
            this.hechos.add(Integer.valueOf(indice));
            actualizarMarcas();
            new Thread(new OndaDesdeFichero(this, cache, indice, ficha == null), "onda-cache").start();
            Registro.escribir("Cache: " + Presets.NOMBRES[indice]);
            this.progreso.setVisibility(View.GONE);
            return;
        }

        this.progreso.setVisibility(View.VISIBLE);
        this.botonGuardar.setEnabled(false);
        this.estadoIndice = indice;
        this.etiquetaEstado.setText(Idioma.t("Aplicando ") + Idioma.t(Presets.NOMBRES[indice]) + "…");
        this.trabajoActual++;
        new Thread(new TareaMasterizar(this, indice, intensidad, objetivo, cache,
                this.trabajoActual)).start();
        arrancarPrecalentado(intensidad, objetivo, indice);
    }

    private void arrancarPrecalentado(float f, Double d, int i) {
        this.colaBloqueada = false;
        this.esperasMemoria = 0;
        supervisarCola();
    }

    private int[] listaPrecalculado() {
        if (this.listaCola != null) {
            return this.listaCola;
        }
        LinkedHashSet linkedHashSet = new LinkedHashSet();
        int i = 0;
        int i2 = 0;
        while (true) {
            String[] strArr = DESTACADOS;
            if (i2 >= strArr.length) {
                break;
            }
            linkedHashSet.add(Integer.valueOf(indiceDe(strArr[i2])));
            i2++;
        }
        int i3 = 0;
        while (true) {
            int[] iArr = this.recomendados;
            if (i3 >= iArr.length) {
                break;
            }
            linkedHashSet.add(Integer.valueOf(iArr[i3]));
            i3++;
        }
        this.prioridadCola = linkedHashSet.size();
        for (int i4 = 0; i4 < Presets.NOMBRES.length; i4++) {
            linkedHashSet.add(Integer.valueOf(i4));
        }
        int[] iArr2 = new int[linkedHashSet.size()];
        Iterator it = linkedHashSet.iterator();
        while (it.hasNext()) {
            iArr2[i] = ((Integer) it.next()).intValue();
            i++;
        }
        this.listaCola = iArr2;
        return iArr2;
    }

    private int siguientePendiente() {
        int[] listaPrecalculado = listaPrecalculado();
        int i = this.prioridadCola;
        int pendienteEntre = pendienteEntre(listaPrecalculado, 0, i, true);
        if (pendienteEntre >= 0) {
            return pendienteEntre;
        }
        if (pendienteEntre(listaPrecalculado, 0, i, false) >= 0) {
            return -1;
        }
        return pendienteEntre(listaPrecalculado, i, listaPrecalculado.length, true);
    }

    private int pendienteEntre(int[] iArr, int i, int i2, boolean z) {
        int i3 = this.trabajandoPrincipal ? this.indicePrincipal : -1;
        int i4 = this.trabajandoSecundario ? this.indiceSecundario : -1;
        while (i < i2 && i < iArr.length) {
            int i5 = iArr[i];
            if (i5 != this.indiceActual && ((!z || i5 != this.indiceSolicitado) && i5 != i3 && i5 != i4)) {
                Long l = this.cuarentena.get(Integer.valueOf(i5));
                if (l != null) {
                    if (l.longValue() > SystemClock.elapsedRealtime()) {
                        continue;
                    } else {
                        this.cuarentena.remove(Integer.valueOf(i5));
                    }
                }
                if (!ficheroCache(i5, intensidadPara(i5, intensidadManual()), objetivoPara(i5, objetivoManual())).exists()) {
                    return i5;
                }
            }
            i++;
        }
        return -1;
    }

    private void servicioCalculo(boolean z) {
        try {
            Intent intent = new Intent(this, (Class<?>) ServicioPrecalculado.class);
            if (z) {
                startForegroundService(intent);
            } else {
                stopService(intent);
            }
        } catch (Throwable th) {
            Registro.escribir("servicio de cálculo: " + th);
        }
    }

    void supervisarCola() {
        int siguientePendiente;
        int siguientePendiente2;
        if (this.colaBloqueada) {
            if (SystemClock.elapsedRealtime() - this.colaBloqueadaMs <= 300000) {
                return;
            } else {
                this.colaBloqueada = false;
            }
        }
        if (this.datos == null || this.perfil == null) {
            return;
        }
        if (!hayMemoria()) {
            int i = this.esperasMemoria + 1;
            this.esperasMemoria = i;
            if (i >= 100) {
                this.esperasMemoria = 0;
                Registro.escribir("Precalculado: el aparato no deja 1 GB libre, se suelta la cola");
                soltarPrecalculados();
                return;
            }
            return;
        }
        this.esperasMemoria = 0;
        if (!hayHeap()) {
            System.gc();
            return;
        }
        long memoriaLibreSistema = memoriaLibreSistema();
        String motorRapido = Acelerador.motorRapido(this);
        String motorLento = Acelerador.motorLento(this);
        if (siguientePendiente() < 0 && !this.trabajandoSecundario && !this.trabajandoPrincipal) {
            servicioCalculo(false);
            return;
        }
        servicioCalculo(true);
        if (!this.trabajandoSecundario && (siguientePendiente2 = siguientePendiente()) >= 0) {
            this.trabajandoSecundario = true;
            this.indiceSecundario = siguientePendiente2;
            Registro.escribir(String.format(Locale.US, "Precalculando %s (%s) · libre en el aparato %d MB", Presets.NOMBRES[siguientePendiente2], motorLento, Long.valueOf(memoriaLibreSistema / 1048576)));
            new Thread(new TrabajoPrecalculado(this, siguientePendiente2, intensidadPara(siguientePendiente2, intensidadManual()), objetivoPara(siguientePendiente2, objetivoManual()), motorLento, false), "precalculado-secundario").start();
        }
        if (this.interactivoEnMarcha || this.trabajandoPrincipal || (siguientePendiente = siguientePendiente()) < 0) {
            return;
        }
        this.trabajandoPrincipal = true;
        this.indicePrincipal = siguientePendiente;
        new Thread(new TrabajoPrecalculado(this, siguientePendiente, intensidadPara(siguientePendiente, intensidadManual()), objetivoPara(siguientePendiente, objetivoManual()), motorRapido, true), "precalculado-principal").start();
    }

    void soltarPrecalculados() {
        this.hilo.post(new SoltarPrecalculados(this));
    }

    /* JADX INFO: Access modifiers changed from: private */
    /* loaded from: classes.dex */
    public static class SoltarPrecalculados implements Runnable {
        private final MainActivity a;

        SoltarPrecalculados(MainActivity mainActivity) {
            this.a = mainActivity;
        }

        @Override // java.lang.Runnable
        public void run() {
            ArrayList<String> arrayList;
            String absolutePath = this.a.ficheroMaster == null ? null : this.a.ficheroMaster.getAbsolutePath();
            synchronized (this.a.precalculados) {
                arrayList = new ArrayList(this.a.precalculados);
                this.a.precalculados.clear();
            }
            int i = 0;
            for (String str : arrayList) {
                if (!str.equals(absolutePath)) {
                    File file = new File(str);
                    if (file.exists() && file.delete()) {
                        i++;
                    }
                    File file2 = new File(str + ".txt");
                    if (file2.exists()) {
                        file2.delete();
                    }
                }
            }
            Registro.escribir("Precalculado: memoria justa, se borran " + i + " audios automáticos");
            this.a.colaBloqueada = true;
            this.a.colaBloqueadaMs = SystemClock.elapsedRealtime();
            this.a.actualizarMarcas();
        }
    }

    void precalculadoListo(int i) {
        this.hilo.post(new RefrescarMarcas(this));
    }

    void marcarCalculando(int i, boolean z) {
        this.hilo.post(new MarcarCalculando(this, i, z));
    }

    /* JADX INFO: Access modifiers changed from: private */
    /* loaded from: classes.dex */
    public static class MarcarCalculando implements Runnable {
        private final MainActivity a;
        private final boolean activo;
        private final int indice;

        MarcarCalculando(MainActivity mainActivity, int i, boolean z) {
            this.a = mainActivity;
            this.indice = i;
            this.activo = z;
        }

        @Override // java.lang.Runnable
        public void run() {
            if (this.activo) {
                this.a.calculando.add(Integer.valueOf(this.indice));
            } else {
                this.a.calculando.remove(Integer.valueOf(this.indice));
            }
            this.a.refrescarIconos();
        }
    }



    /** Memoria disponible del aparato en bytes (MemAvailable), -1 si no se puede leer. */
    long memoriaLibreSistema() {
        java.io.BufferedReader lector = null;
        try {
            lector = new java.io.BufferedReader(new java.io.FileReader("/proc/meminfo"));
            String linea = lector.readLine();
            while (linea != null) {
                if (linea.startsWith("MemAvailable:")) {
                    return Long.parseLong(linea.trim().split("\\s+")[1]) * 1024L;
                }
                linea = lector.readLine();
            }
        } catch (Throwable e) {
            Registro.escribir("no se pudo leer /proc/meminfo: " + e);
        } finally {
            if (lector != null) {
                try {
                    lector.close();
                } catch (Exception ignorado) {
                }
            }
        }
        return -1L;
    }

    boolean hayMemoria() {
        long memoriaLibreSistema = memoriaLibreSistema();
        return memoriaLibreSistema <= 0 || memoriaLibreSistema >= LIBRE_MINIMO_SISTEMA;
    }

    boolean hayHeap() {
        Runtime runtime = Runtime.getRuntime();
        return runtime.maxMemory() - (runtime.totalMemory() - runtime.freeMemory()) > 16777216;
    }

    /* JADX INFO: Access modifiers changed from: private */
    /* loaded from: classes.dex */
    public static class RefrescarMarcas implements Runnable {
        private final MainActivity a;

        RefrescarMarcas(MainActivity mainActivity) {
            this.a = mainActivity;
        }

        @Override // java.lang.Runnable
        public void run() {
            this.a.actualizarMarcas();
        }
    }

    void masterizado(float[][] fArr, int i, File file, double d, double d2) {
        this.hilo.post(new EntregaMaster(this, fArr, i, file, d, d2));
    }

    /* JADX INFO: Access modifiers changed from: private */
    /* loaded from: classes.dex */
    public static class EntregaMaster implements Runnable {
        private final MainActivity a;
        private final File fichero;
        private final int indice;
        private final double lufs;
        private final double tp;
        private final float[][] y;

        EntregaMaster(MainActivity mainActivity, float[][] fArr, int i, File file, double d, double d2) {
            this.a = mainActivity;
            this.y = fArr;
            this.indice = i;
            this.fichero = file;
            this.lufs = d;
            this.tp = d2;
        }

        @Override // java.lang.Runnable
        public void run() {
            this.a.progreso.setVisibility(8);
            MainActivity mainActivity = this.a;
            mainActivity.posicionDeseada = mainActivity.posicionActual();
            this.a.resultado = this.y;
            this.a.indiceActual = this.indice;
            this.a.ficheroMaster = this.fichero;
            if (this.fichero != null) {
                try {
                    FileWriter fileWriter = new FileWriter(this.fichero.getAbsolutePath() + ".txt");
                    fileWriter.write(String.format("%.2f;%.2f;%d", Double.valueOf(this.lufs), Double.valueOf(this.tp), Integer.valueOf(this.indice)));
                    fileWriter.close();
                } catch (Exception e) {
                    Registro.escribir("no se pudo guardar la ficha: " + e);
                }
            }
            MainActivity mainActivity2 = this.a;
            float[][] fArr = this.y;
            mainActivity2.picosMaster = fArr == null ? mainActivity2.picosOriginal : mainActivity2.picosDe(fArr);
            this.a.prepararJugador(false);
            this.a.viendoOriginal = false;
            this.a.botonPlay.setEnabled(true);
            this.a.botonGuardar.setEnabled(true);
            this.a.etiquetaEstado.setText("");
            this.a.lufsMaster = this.lufs;
            this.a.tpMaster = this.tp;
            this.a.etiquetaSonando.setText(Double.isNaN(this.tp) ? String.format(Idioma.t("%s · %.1f LUFS · audio largo"), Idioma.t(Presets.NOMBRES[this.indice]), Double.valueOf(this.lufs)) : String.format(Idioma.t("%s · %.1f LUFS · pico %.2f dBTP"), Idioma.t(Presets.NOMBRES[this.indice]), Double.valueOf(this.lufs), Double.valueOf(this.tp)));
            this.a.viendoOriginal = false;
            this.a.marcarFuente();
            this.a.pausaManual = false;
            this.a.marcarActivo(this.indice);
            this.a.ocultarGiros();
            this.a.calculando.remove(Integer.valueOf(this.indice));
            this.a.pintarOndaDeLaVersion();
            this.a.seguirEnCaliente(true);      // suena el ajuste en cuanto está listo
            this.a.hechos.add(Integer.valueOf(this.indice));
            this.a.calculando.remove(Integer.valueOf(this.indice));
            this.a.actualizarMarcas();
            this.a.guardarSesion();
            this.a.resultado = null;
            System.gc();
            this.a.supervisarCola();
        }
    }

    private MediaPlayer preparadoUri(Uri uri) {
        MediaPlayer mediaPlayer = new MediaPlayer();
        try {
            mediaPlayer.setDataSource(this, uri);
            mediaPlayer.setLooping(true);
            mediaPlayer.prepare();
            return mediaPlayer;
        } catch (Exception e) {
            Registro.escribir("no se puede abrir el audio original: " + e);
            return null;
        }
    }

    private MediaPlayer preparado(File file) {
        if (file == null) {
            return null;
        }
        MediaPlayer mediaPlayer = new MediaPlayer();
        try {
            mediaPlayer.setDataSource(file.getAbsolutePath());
            mediaPlayer.setLooping(true);
            mediaPlayer.prepare();
            return mediaPlayer;
        } catch (Exception e) {
            Registro.escribir("No se pudo preparar el reproductor: " + e);
            try {
                mediaPlayer.release();
            } catch (Exception unused) {
            }
            return null;
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    public void prepararJugador(boolean z) {
        MediaPlayer preparado;
        Uri uri;
        File file = z ? this.ficheroOriginal : this.ficheroMaster;
        if (file != null) {
            preparado = preparado(file);
        } else if (!z || (uri = this.uriEntrada) == null) {
            return;
        } else {
            preparado = preparadoUri(uri);
        }
        if (preparado == null) {
            return;
        }
        MediaPlayer mediaPlayer = z ? this.jugadorOriginal : this.jugadorMaster;
        if (z) {
            this.jugadorOriginal = preparado;
        } else {
            this.jugadorMaster = preparado;
        }
        if (mediaPlayer == null) {
            return;
        }
        boolean enUso = this.viendoOriginal == z;
        int i = 0;
        boolean z2 = false;
        try {
            i = mediaPlayer.getCurrentPosition();
            z2 = mediaPlayer.isPlaying();
        } catch (Exception unused) {
        }
        if (!enUso || !z2) {
            try {
                if (mediaPlayer.isPlaying()) {
                    mediaPlayer.stop();
                }
            } catch (Exception unused2) {
            }
            try {
                mediaPlayer.release();
            } catch (Exception unused3) {
            }
            return;
        }
        // la versión que se está oyendo no se corta: entra la nueva por el mismo punto
        // y la anterior se apaga en un cruce de 80 ms
        try {
            preparado.seekTo(i);
        } catch (Exception unused4) {
        }
        try {
            preparado.setVolume(0.0f, 0.0f);
            preparado.start();
        } catch (Exception unused5) {
        }
        Cruce.empezar(mediaPlayer, preparado, true);
    }

    /* JADX INFO: Access modifiers changed from: private */
    public int posicionActual() {
        MediaPlayer mediaPlayer = this.viendoOriginal ? this.jugadorOriginal : this.jugadorMaster;
        if (mediaPlayer != null) {
            try {
                return mediaPlayer.getCurrentPosition();
            } catch (Exception unused) {
            }
        }
        return this.posicionDeseada;
    }

    private void pausarTodos() {
        MediaPlayer mediaPlayer = this.jugadorOriginal;
        if (mediaPlayer != null && mediaPlayer.isPlaying()) {
            try {
                this.jugadorOriginal.pause();
            } catch (Exception unused) {
            }
        }
        MediaPlayer mediaPlayer2 = this.jugadorMaster;
        if (mediaPlayer2 == null || !mediaPlayer2.isPlaying()) {
            return;
        }
        try {
            this.jugadorMaster.pause();
        } catch (Exception unused2) {
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    public void seguirEnCaliente() {
        seguirEnCaliente(this.motivoUltimo == 0);
    }

    /* JADX WARN: Code restructure failed: missing block: B:26:0x0041, code lost:
    
        if (r4.seguiaSonando != false) goto L19;
     */
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    /** Pasa a la versión nueva sin cortar: sigue por el mismo punto y solo arranca si tocaba. */
    private void seguirEnCaliente(boolean forzar) {
        MediaPlayer activo = this.jugadorMaster;
        if (activo == null) {
            return;
        }
        try {
            if (this.jugadorOriginal != null && this.jugadorOriginal.isPlaying()) {
                this.jugadorOriginal.pause();
            }
        } catch (Exception ignorado) {
        }
        try {
            int duracion = activo.getDuration();
            int posicion = Math.min(this.posicionDeseada, Math.max(0, duracion - 300));
            if (posicion > 0) {
                activo.seekTo(posicion);
            }
        } catch (Exception e) {
            Registro.escribir("seek al cambiar de ajuste: " + e);
        }
        try {
            if ((forzar || this.seguiaSonando) && !this.pausaManual) {
                activo.start();
                this.botonPlay.setText(Idioma.t("■ Parar"));
            } else {
                this.botonPlay.setText(Idioma.t("▶ Escuchar"));
            }
        } catch (Exception e) {
            Registro.escribir("no arranca: " + e);
        }
    }

    private void reproducir() {
        MediaPlayer mediaPlayer = this.viendoOriginal ? this.jugadorOriginal : this.jugadorMaster;
        if (mediaPlayer == null) {
            return;
        }
        try {
            mediaPlayer.start();
            this.pausaManual = false;
            this.botonPlay.setText(Idioma.t("■ Parar"));
        } catch (Exception e) {
            Registro.escribir("no arranca: " + e);
        }
    }

    private void alternarReproduccion() {
        MediaPlayer mediaPlayer = this.viendoOriginal ? this.jugadorOriginal : this.jugadorMaster;
        if (mediaPlayer == null) {
            return;
        }
        if (mediaPlayer.isPlaying()) {
            mediaPlayer.pause();
            this.pausaManual = true;
            this.botonPlay.setText(Idioma.t("▶ Escuchar"));
        } else {
            mediaPlayer.start();
            this.pausaManual = false;
            this.botonPlay.setText(Idioma.t("■ Parar"));
        }
    }

    private void cambiarFuente(boolean z) {
        int i;
        boolean z2;
        boolean z3 = this.viendoOriginal;
        MediaPlayer mediaPlayer = z3 ? this.jugadorOriginal : this.jugadorMaster;
        MediaPlayer mediaPlayer2 = z ? this.jugadorMaster : this.jugadorOriginal;
        if (z == (!z3)) {
            if (z) {
                mostrarInfoMaster();
                return;
            } else {
                mostrarInfoOriginal();
                return;
            }
        }
        if (mediaPlayer2 == null) {
            if (!z) {
                this.viendoOriginal = true;
                marcarFuente();
                pintarOndaDeLaVersion();
                mostrarInfoOriginal();
                return;
            }
            mostrarInfoMaster();
            return;
        }
        if (mediaPlayer != null) {
            i = mediaPlayer.getCurrentPosition();
            z2 = mediaPlayer.isPlaying();
        } else {
            i = 0;
            z2 = false;
        }
        this.viendoOriginal = !z;
        pintarOndaDeLaVersion();
        if (z2 && mediaPlayer != null) {
            // suena: la nueva versión entra por el mismo punto y la vieja se apaga
            // con un cruce de 80 ms (antes se paraba y arrancaba: se oía el corte)
            try {
                mediaPlayer2.seekTo(i);
            } catch (Exception e) {
                Registro.escribir("seek falló: " + e);
            }
            try {
                mediaPlayer2.setVolume(0.0f, 0.0f);
                mediaPlayer2.start();
            } catch (Exception e2) {
                Registro.escribir("no arranca la versión nueva: " + e2);
            }
            Cruce.empezar(mediaPlayer, mediaPlayer2, false);
            this.botonPlay.setText(Idioma.t("■ Parar"));
        } else {
            pausarTodos();
            try {
                mediaPlayer2.seekTo(i);
            } catch (Exception e3) {
                Registro.escribir("seek falló: " + e3);
            }
            this.botonPlay.setText(Idioma.t("▶ Escuchar"));
        }
        marcarFuente();
        if (this.viendoOriginal) {
            mostrarInfoOriginal();
        } else {
            mostrarInfoMaster();
        }
        StringBuilder sb = new StringBuilder("Cambio a ");
        sb.append(this.viendoOriginal ? "original" : "masterizado");
        sb.append(" @");
        sb.append(i);
        Registro.escribir(sb.toString());
    }

    /* JADX INFO: Access modifiers changed from: private */
    public void mostrarInfoOriginal() {
        if (this.perfil == null) {
            this.etiquetaSonando.setText(Idioma.t("Original"));
        } else if (Double.isNaN(this.tpOriginal)) {
            this.etiquetaSonando.setText(String.format(Locale.US, Idioma.t("Original · %.1f LUFS"), Double.valueOf(this.perfil.lufs)));
        } else {
            this.etiquetaSonando.setText(String.format(Locale.US, Idioma.t("Original · %.1f LUFS · pico %.2f dBTP"), Double.valueOf(this.perfil.lufs), Double.valueOf(this.tpOriginal)));
        }
    }

    private void mostrarInfoMaster() {
        File file;
        double[] leerFicha;
        if (this.indiceActual < 0) {
            this.etiquetaSonando.setText(Idioma.t("Masterizado"));
            return;
        }
        double d = this.lufsMaster;
        double d2 = this.tpMaster;
        if (Double.isNaN(d) && (file = this.ficheroMaster) != null && (leerFicha = leerFicha(file)) != null) {
            d = leerFicha[0];
            d2 = leerFicha[1];
            this.lufsMaster = d;
            this.tpMaster = d2;
        }
        String str = Idioma.t(Presets.NOMBRES[this.indiceActual]);
        if (Double.isNaN(d)) {
            this.etiquetaSonando.setText(str);
        } else if (Double.isNaN(d2)) {
            this.etiquetaSonando.setText(String.format(Locale.US, Idioma.t("%s · %.1f LUFS"), str, Double.valueOf(d)));
        } else {
            this.etiquetaSonando.setText(String.format(Locale.US, Idioma.t("%s · %.1f LUFS · pico %.2f dBTP"), str, Double.valueOf(d), Double.valueOf(d2)));
        }
    }

    /* loaded from: classes.dex */
    private static class MedirPico implements Runnable {
        private final MainActivity a;
        private final Wav.Datos d;

        MedirPico(MainActivity mainActivity, Wav.Datos datos) {
            this.a = mainActivity;
            this.d = datos;
        }

        @Override // java.lang.Runnable
        public void run() {
            try {
                this.a.hilo.post(new PonerPico(this.a, Sonoridad.picoReal(this.d.muestras, this.d.frecuencia)));
            } catch (Throwable th) {
                Registro.escribir("no se pudo medir el original: " + th);
            }
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    /* loaded from: classes.dex */
    public static class OcultarProgreso implements Runnable {
        private final MainActivity a;

        OcultarProgreso(MainActivity mainActivity) {
            this.a = mainActivity;
        }

        @Override // java.lang.Runnable
        public void run() {
            if (this.a.progreso != null) {
                this.a.progreso.setVisibility(8);
            }
        }
    }

    /* loaded from: classes.dex */
    private static class PonerPico implements Runnable {
        private final MainActivity a;
        private final double tp;

        PonerPico(MainActivity mainActivity, double d) {
            this.a = mainActivity;
            this.tp = d;
        }

        @Override // java.lang.Runnable
        public void run() {
            this.a.tpOriginal = this.tp;
            if (this.a.viendoOriginal) {
                this.a.mostrarInfoOriginal();
            }
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    public void marcarFuente() {
        MediaPlayer mediaPlayer = null;
        MediaPlayer mediaPlayer2;
        if (this.viendoOriginal && (mediaPlayer2 = this.jugadorMaster) != null && mediaPlayer2.isPlaying()) {
            try {
                this.jugadorMaster.pause();
            } catch (Exception unused) {
            }
        }
        if (!this.viendoOriginal && (mediaPlayer = this.jugadorOriginal) != null && mediaPlayer.isPlaying()) {
            try {
                this.jugadorOriginal.pause();
            } catch (Exception unused2) {
            }
        }
        Button button = this.botonOriginal;
        boolean z = this.viendoOriginal;
        int i = Estilo.ROSA;
        button.setBackground(Estilo.redondeado(z ? Estilo.ROSA : -14474438, Estilo.dp(this, 14.0f), 1, Estilo.BORDE));
        this.botonOriginal.setTextColor(this.viendoOriginal ? -1 : Estilo.TEXTO);
        Button button2 = this.botonMaster;
        if (this.viendoOriginal) {
            i = -14474438;
        }
        button2.setBackground(Estilo.redondeado(i, Estilo.dp(this, 14.0f), 1, Estilo.BORDE));
        this.botonMaster.setTextColor(this.viendoOriginal ? Estilo.TEXTO : -1);
        this.botonOriginal.setEnabled(this.ficheroOriginal != null);
        this.botonMaster.setEnabled(this.ficheroMaster != null);
    }

    /* JADX INFO: Access modifiers changed from: private */
    public void actualizarProgreso() {
        MediaPlayer mediaPlayer = this.viendoOriginal ? this.jugadorOriginal : this.jugadorMaster;
        if (mediaPlayer == null) {
            return;
        }
        try {
            int duration = mediaPlayer.getDuration();
            int currentPosition = mediaPlayer.getCurrentPosition();
            if (this.arrastrandoOnda) {
                return;
            }
            this.posicionDeseada = currentPosition;
            if (duration > 0) {
                // división en coma flotante: con enteros daba 0 y la onda no marcaba por dónde iba
                this.onda.setProgreso((float) currentPosition / (float) duration);
            }
            if (mediaPlayer.isPlaying()) {
                return;
            }
            this.botonPlay.setText(Idioma.t("▶ Escuchar"));
        } catch (Exception unused) {
        }
    }

    private void pararTodo() {
        MediaPlayer mediaPlayer = this.jugadorOriginal;
        if (mediaPlayer != null) {
            try {
                mediaPlayer.stop();
            } catch (Exception unused) {
            }
            this.jugadorOriginal.release();
            this.jugadorOriginal = null;
        }
        MediaPlayer mediaPlayer2 = this.jugadorMaster;
        if (mediaPlayer2 != null) {
            try {
                mediaPlayer2.stop();
            } catch (Exception unused2) {
            }
            this.jugadorMaster.release();
            this.jugadorMaster = null;
        }
        Button button = this.botonPlay;
        if (button != null) {
            button.setText(Idioma.t("▶ Escuchar"));
        }
    }

    void error(String str) {
        Registro.escribir("ERROR: " + str);
        this.hilo.post(new OcultarProgreso(this));
        this.hilo.post(new Fin(this));
        this.hilo.post(new QuitarGiros(this));
        this.hilo.post(new Aviso(this, str));
    }

    private void guardarEn(Uri uri) {
        try {
            OutputStream openOutputStream = getContentResolver().openOutputStream(uri);
            if (openOutputStream == null) {
                throw new Exception("no se pudo abrir el destino");
            }
            float[][] fArr = this.resultado;
            if (fArr == null || fArr.length == 0 || fArr[0] == null) {
                File file = this.ficheroMaster;
                if (file == null || !file.exists()) {
                    throw new Exception("todavía no hay nada masterizado");
                }
                fArr = Wav.leer(this.ficheroMaster.getAbsolutePath()).muestras;
            }
            Wav.escribirEn(openOutputStream, fArr, this.frecuencia);
            openOutputStream.close();
            Toast.makeText(this, Idioma.t("Guardado"), 1).show();
        } catch (Exception e) {
            Toast.makeText(this, Idioma.t("No se pudo guardar: ") + e.getMessage(), 1).show();
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    public void guardarSesion() {
        if (this.uriEntrada == null) {
            return;
        }
        Double objetivoManual = objetivoManual();
        Sesion.guardar(this, this.uriEntrada.toString(), this.nombreEntrada, this.indiceActual, intensidadManual(), this.modoAuto, objetivoManual == null ? 0.0d : objetivoManual.doubleValue());
    }

    private void guardarEnMemoria() {
        if (this.uriEntrada == null || this.datos == null) {
            return;
        }
        Estado estado = new Estado();
        estado.uri = this.uriEntrada;
        estado.nombre = this.nombreEntrada;
        estado.datos = this.datos;
        estado.perfil = this.perfil;
        estado.orden = this.ordenCompleto;
        estado.recomendados = this.recomendados;
        estado.entradaLarga = this.entradaLarga;
        estado.duracion = this.duracionEntrada;
        estado.indiceActual = this.indiceActual;
        estado.ficheroOriginal = this.ficheroOriginal;
        estado.ficheroMaster = this.ficheroMaster;
        estado.viendoOriginal = this.viendoOriginal;
        estado.tpOriginal = this.tpOriginal;
        estado.lufsMaster = this.lufsMaster;
        estado.tpMaster = this.tpMaster;
        estado.hechos = new HashSet(this.hechos);
        Estado.ultima = estado;
    }

    private boolean cargarDeMemoria() {
        Estado estado = Estado.ultima;
        if (estado == null || estado.datos == null) {
            return false;
        }
        this.uriEntrada = estado.uri;
        this.nombreEntrada = estado.nombre;
        this.datos = estado.datos;
        this.frecuencia = estado.datos.frecuencia;
        this.perfil = estado.perfil;
        this.ordenCompleto = estado.orden;
        this.recomendados = estado.recomendados == null ? new int[]{0, 0} : estado.recomendados;
        this.entradaLarga = estado.entradaLarga;
        this.duracionEntrada = estado.duracion;
        this.indiceActual = estado.indiceActual;
        this.ficheroOriginal = estado.ficheroOriginal;
        this.ficheroMaster = estado.ficheroMaster;
        this.viendoOriginal = estado.viendoOriginal;
        this.tpOriginal = estado.tpOriginal;
        this.lufsMaster = estado.lufsMaster;
        this.tpMaster = estado.tpMaster;
        this.hechos.clear();
        if (estado.hechos != null) {
            this.hechos.addAll(estado.hechos);
        }
        this.listaCola = null;
        return true;
    }

    private void reanudarEnMemoria() {
        String str;
        try {
            this.etiquetaArchivo.setText(this.nombreEntrada);
            boolean z = false;
            if (this.perfil != null) {
                this.etiquetaPerfil.setText(resumenPerfil(this.perfil) + String.format(Idioma.t(" · graves %+.1f dB · agudos %+.1f dB"), Double.valueOf(this.perfil.gravesDb), Double.valueOf(this.perfil.agudosDb)));
            }
            pintarOpciones();
            File file = this.ficheroMaster;
            if (file != null && file.exists()) {
                prepararJugador(false);
            }
            File file2 = this.ficheroOriginal;
            if (file2 != null && file2.exists()) {
                prepararJugador(true);
            }
            this.botonOriginal.setEnabled(true);
            Button button = this.botonMaster;
            File file3 = this.ficheroMaster;
            button.setEnabled(file3 != null && file3.exists());
            this.botonPlay.setEnabled(true);
            Button button2 = this.botonGuardar;
            File file4 = this.ficheroMaster;
            if (file4 != null && file4.exists()) {
                z = true;
            }
            button2.setEnabled(z);
            try {
                float[] calcularPicos = calcularPicos();
                this.picosOriginal = calcularPicos;
                this.picosMaster = calcularPicos;
            } catch (Throwable unused) {
                Registro.escribir("sin memoria para la onda al reanudar");
            }
            pintarOndaDeLaVersion();
            marcarFuente();
            marcarActivo(this.indiceActual);
            if (this.viendoOriginal) {
                mostrarInfoOriginal();
            } else {
                mostrarInfoMaster();
            }
            StringBuilder sb = new StringBuilder("Se retoma en memoria: ");
            sb.append(this.nombreEntrada);
            if (this.indiceActual >= 0) {
                str = " · " + Presets.NOMBRES[this.indiceActual];
            } else {
                str = "";
            }
            sb.append(str);
            Registro.escribir(sb.toString());
            supervisarCola();
        } catch (Throwable th) {
            Registro.escribir("no se pudo reanudar: " + th);
        }
    }

    private void restaurarSesion() {
        String str;
        Sesion leer = Sesion.leer(this);
        if (leer == null) {
            return;
        }
        try {
            Uri parse = Uri.parse(leer.uri);
            this.uriEntrada = parse;
            if (parse == null) {
                return;
            }
            String str2 = leer.nombre;
            this.nombreEntrada = str2;
            this.etiquetaArchivo.setText(str2);
            this.modoAuto = true;
            this.intensidadFija = true;
            pintarEstadoAuto();
            pintarEstadoIntensidad();
            this.indiceAlRestaurar = Integer.valueOf(leer.indice);
            StringBuilder sb = new StringBuilder("Se retoma la sesión: ");
            sb.append(this.nombreEntrada);
            if (leer.indice >= 0) {
                str = " · ajuste " + Presets.NOMBRES[leer.indice];
            } else {
                str = "";
            }
            sb.append(str);
            Registro.escribir(sb.toString());
            empezarAnalisis(false);
        } catch (Exception unused) {
        }
    }

    @Override // android.app.Activity
    protected void onPause() {
        guardarSesion();
        guardarEnMemoria();
        super.onPause();
    }

    @Override // android.app.Activity
    protected void onDestroy() {
        this.hilo.removeCallbacks(this.latido);
        pararTodo();
        if (isFinishing()) {
            limpiarCache();
            Sesion.borrar(this);
            Estado.limpiar();
        }
        super.onDestroy();
    }
}
