package es.pitmasterai.masterlab.motor;

import android.opengl.EGL14;
import android.opengl.EGLConfig;
import android.opengl.EGLContext;
import android.opengl.EGLDisplay;
import android.opengl.EGLSurface;
import android.opengl.GLES30;
import es.pitmasterai.masterlab.Acelerador;
import java.lang.reflect.Array;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;

/* loaded from: classes.dex */
public final class Gpu {
    private static final String FRAGMENTO = "#version 300 es\nprecision highp float;\nuniform sampler2D entrada;\nuniform float ganancia;\nout vec4 color;\nvoid main() {\n  vec4 v = texelFetch(entrada, ivec2(int(gl_FragCoord.x), int(gl_FragCoord.y)), 0);\n  color = vec4(v.r * ganancia, v.g * ganancia, 0.0, 1.0);\n}\n";
    private static final String VERTICE = "#version 300 es\nvoid main() {\n  vec2 p = vec2((gl_VertexID == 1) ? 3.0 : -1.0, (gl_VertexID == 2) ? 3.0 : -1.0);\n  gl_Position = vec4(p, 0.0, 1.0);\n}\n";
    private static EGLContext contexto = null;
    private static String detalle = "CPU";
    private static boolean forzado = false;
    private static double msCpu = -1.0d;
    private static double msGpu = -1.0d;
    private static EGLDisplay pantalla = null;
    private static boolean probado = false;
    private static int programa = -1;
    private static boolean sirve = false;
    private static EGLSurface superficie;

    private Gpu() {
    }

    public static void forzar(boolean z) {
        if (forzado != z) {
            forzado = z;
            probado = false;
            sirve = false;
        }
    }

    public static boolean forzado() {
        return forzado;
    }

    public static boolean sirve() {
        if (!probado) {
            probar();
        }
        return sirve;
    }

    public static String detalle() {
        if (!probado) {
            probar();
        }
        return detalle;
    }

    public static double milisegundosCpu() {
        return msCpu;
    }

    public static double milisegundosGpu() {
        return msGpu;
    }

    public static synchronized void probar() {
        synchronized (Gpu.class) {
            if (probado) {
                return;
            }
            boolean z = true;
            probado = true;
            try {
            } catch (Throwable unused) {
                sirve = false;
                detalle = Acelerador.CPU;
            }
            if (!abrirContexto()) {
                detalle = Acelerador.CPU;
                return;
            }
            float[] fArr = new float[4000000];
            for (int i = 0; i < 4000000; i++) {
                double d = i;
                Double.isNaN(d);
                fArr[i] = (float) Math.sin(d * 0.001d);
            }
            long nanoTime = System.nanoTime();
            for (int i2 = 0; i2 < 4000000; i2++) {
                fArr[i2] = fArr[i2] * 0.5f;
            }
            double nanoTime2 = System.nanoTime() - nanoTime;
            Double.isNaN(nanoTime2);
            msCpu = nanoTime2 / 1000000.0d;
            float[][] fArr2 = (float[][]) Array.newInstance((Class<?>) Float.TYPE, 2, 2000000);
            for (int i3 = 0; i3 < 2000000; i3++) {
                int i4 = i3 * 2;
                fArr2[0][i3] = fArr[i4];
                fArr2[1][i3] = fArr[i4 + 1];
            }
            long nanoTime3 = System.nanoTime();
            boolean multiplicarEnGpu = multiplicarEnGpu(fArr2, 0.5f);
            double nanoTime4 = System.nanoTime() - nanoTime3;
            Double.isNaN(nanoTime4);
            double d2 = nanoTime4 / 1000000.0d;
            msGpu = d2;
            if (!multiplicarEnGpu) {
                detalle = Acelerador.CPU;
                return;
            }
            boolean z2 = forzado;
            if (!z2 && d2 >= msCpu) {
                z = false;
            }
            sirve = z;
            detalle = z ? z2 ? "GPU (forzada)" : Acelerador.GPU : Acelerador.CPU;
        }
    }

    public static boolean multiplicar(float[][] fArr, float f) {
        if (!sirve()) {
            return false;
        }
        try {
            return multiplicarEnGpu(fArr, f);
        } catch (Throwable unused) {
            return false;
        }
    }

    private static boolean abrirContexto() {
        String glGetString;
        EGLDisplay eglGetDisplay = EGL14.eglGetDisplay(0);
        pantalla = eglGetDisplay;
        if (eglGetDisplay == EGL14.EGL_NO_DISPLAY) {
            return false;
        }
        int[] iArr = new int[2];
        if (!EGL14.eglInitialize(pantalla, iArr, 0, iArr, 1)) {
            return false;
        }
        EGLConfig[] eGLConfigArr = new EGLConfig[1];
        int[] iArr2 = new int[1];
        if (!EGL14.eglChooseConfig(pantalla, new int[]{12339, 1, 12324, 8, 12323, 8, 12322, 8, 12352, 64, 12344}, 0, eGLConfigArr, 0, 1, iArr2, 0) || iArr2[0] == 0) {
            return false;
        }
        EGLContext eglCreateContext = EGL14.eglCreateContext(pantalla, eGLConfigArr[0], EGL14.EGL_NO_CONTEXT, new int[]{12440, 3, 12344}, 0);
        contexto = eglCreateContext;
        if (eglCreateContext == EGL14.EGL_NO_CONTEXT) {
            return false;
        }
        EGLSurface eglCreatePbufferSurface = EGL14.eglCreatePbufferSurface(pantalla, eGLConfigArr[0], new int[]{12375, 16, 12374, 16, 12344}, 0);
        superficie = eglCreatePbufferSurface;
        if (eglCreatePbufferSurface == EGL14.EGL_NO_SURFACE) {
            return false;
        }
        EGLDisplay eGLDisplay = pantalla;
        EGLSurface eGLSurface = superficie;
        if (!EGL14.eglMakeCurrent(eGLDisplay, eGLSurface, eGLSurface, contexto) || (glGetString = GLES30.glGetString(7939)) == null || !glGetString.contains("EXT_color_buffer_float")) {
            return false;
        }
        int crearPrograma = crearPrograma();
        programa = crearPrograma;
        return crearPrograma > 0;
    }

    private static int compilar(int i, String str) {
        int glCreateShader = GLES30.glCreateShader(i);
        GLES30.glShaderSource(glCreateShader, str);
        GLES30.glCompileShader(glCreateShader);
        int[] iArr = new int[1];
        GLES30.glGetShaderiv(glCreateShader, 35713, iArr, 0);
        if (iArr[0] != 0) {
            return glCreateShader;
        }
        GLES30.glDeleteShader(glCreateShader);
        return 0;
    }

    private static int crearPrograma() {
        int compilar = compilar(35633, VERTICE);
        int compilar2 = compilar(35632, FRAGMENTO);
        if (compilar == 0 || compilar2 == 0) {
            return 0;
        }
        int glCreateProgram = GLES30.glCreateProgram();
        GLES30.glAttachShader(glCreateProgram, compilar);
        GLES30.glAttachShader(glCreateProgram, compilar2);
        GLES30.glLinkProgram(glCreateProgram);
        int[] iArr = new int[1];
        GLES30.glGetProgramiv(glCreateProgram, 35714, iArr, 0);
        if (iArr[0] == 0) {
            return 0;
        }
        return glCreateProgram;
    }

    private static boolean multiplicarEnGpu(float[][] fArr, float f) {
        int min;
        int[] iArr;
        int[] iArr2;
        int i;
        int i2;
        if (programa <= 0 || fArr.length < 2 || (min = Math.min(fArr[0].length, fArr[1].length)) < 4096) {
            return false;
        }
        int i3 = ((min + 2048) - 1) / 2048;
        int i4 = i3 * 2048;
        int i5 = i4 * 4 * 4;
        FloatBuffer asFloatBuffer = ByteBuffer.allocateDirect(i5).order(ByteOrder.nativeOrder()).asFloatBuffer();
        asFloatBuffer.clear();
        for (int i6 = 0; i6 < i4; i6++) {
            if (i6 < min) {
                asFloatBuffer.put(fArr[0][i6]);
                asFloatBuffer.put(fArr[1][i6]);
            } else {
                asFloatBuffer.put(0.0f);
                asFloatBuffer.put(0.0f);
            }
        }
        asFloatBuffer.position(0);
        int[] iArr3 = new int[2];
        GLES30.glGenTextures(2, iArr3, 0);
        int[] iArr4 = new int[1];
        GLES30.glGenFramebuffers(1, iArr4, 0);
        try {
            GLES30.glBindTexture(3553, iArr3[0]);
            iArr = iArr4;
            iArr2 = iArr3;
            try {
                GLES30.glTexImage2D(3553, 0, 34836, 2048, i3, 0, 6408, 5126, asFloatBuffer);
                GLES30.glTexParameteri(3553, 10241, 9728);
                GLES30.glTexParameteri(3553, 10240, 9728);
                GLES30.glBindTexture(3553, iArr2[1]);
                GLES30.glTexImage2D(3553, 0, 34836, 2048, i3, 0, 6408, 5126, null);
                GLES30.glBindFramebuffer(36160, iArr[0]);
                GLES30.glFramebufferTexture2D(36160, 36064, 3553, iArr2[1], 0);
                if (GLES30.glCheckFramebufferStatus(36160) == 36053) {
                    GLES30.glViewport(0, 0, 2048, i3);
                    GLES30.glUseProgram(programa);
                    GLES30.glActiveTexture(33984);
                    GLES30.glBindTexture(3553, iArr2[0]);
                    GLES30.glUniform1i(GLES30.glGetUniformLocation(programa, "entrada"), 0);
                    GLES30.glUniform1f(GLES30.glGetUniformLocation(programa, "ganancia"), f);
                    GLES30.glDrawArrays(4, 0, 3);
                    FloatBuffer asFloatBuffer2 = ByteBuffer.allocateDirect(i5).order(ByteOrder.nativeOrder()).asFloatBuffer();
                    GLES30.glReadPixels(0, 0, 2048, i3, 6408, 5126, asFloatBuffer2);
                    i2 = 0;
                    try {
                        asFloatBuffer2.position(0);
                        int i7 = 0;
                        while (i7 < min) {
                            float[] fArr2 = fArr[i2];
                            int i8 = i7 * 4;
                            fArr2[i7] = asFloatBuffer2.get(i8);
                            fArr[1][i7] = asFloatBuffer2.get(i8 + 1);
                            i7++;
                            i2 = 0;
                        }
                        GLES30.glBindFramebuffer(36160, i2);
                        GLES30.glDeleteTextures(2, iArr2, i2);
                        GLES30.glDeleteFramebuffers(1, iArr, i2);
                        return true;
                    } finally {
                        GLES30.glBindFramebuffer(36160, i2);
                        GLES30.glDeleteTextures(2, iArr2, i2);
                        GLES30.glDeleteFramebuffers(1, iArr, i2);
                    }
                }
                GLES30.glBindFramebuffer(36160, 0);
                GLES30.glDeleteTextures(2, iArr2, 0);
                GLES30.glDeleteFramebuffers(1, iArr, 0);
                return false;
            } finally {
                GLES30.glBindFramebuffer(36160, 0);
                GLES30.glDeleteTextures(2, iArr2, 0);
                GLES30.glDeleteFramebuffers(1, iArr, 0);
            }
        } finally {
            iArr = iArr4;
            iArr2 = iArr3;
        }
    }
}
