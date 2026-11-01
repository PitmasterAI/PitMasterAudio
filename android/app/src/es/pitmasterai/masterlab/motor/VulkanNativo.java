package es.pitmasterai.masterlab.motor;

public final class VulkanNativo {
    private static boolean activo = false;
    private static boolean cargada = false;
    private static String error = "";
    private static boolean listo = false;
    private static double msCpu = 0.0d;
    private static double msVulkan = 0.0d;
    private static String nombre = "";
    private static boolean probado = false;

    private static native boolean nativoAbrir();

    private static native boolean nativoEscalar(float[] fArr, float f);

    private static native String nativoNombre();

    private static native boolean nativoPorGanancia(float[] fArr, float[] fArr2);

    private static native boolean nativoSaturar(float[] fArr, float f);

    static {
        try {
            System.loadLibrary("masterlabvk");
            cargada = true;
        } catch (Throwable th) {
            cargada = false;
            error = th.getClass().getSimpleName() + ": " + th.getMessage();
        }
        activo = false;
        msCpu = -1.0d;
        msVulkan = -1.0d;
    }

    private VulkanNativo() {
    }

    public static synchronized boolean abrir() {
        synchronized (VulkanNativo.class) {
            if (probado) {
                return listo;
            }
            probado = true;
            if (!cargada) {
                listo = false;
                return false;
            }
            try {
                boolean nativoAbrir = nativoAbrir();
                listo = nativoAbrir;
                if (nativoAbrir) {
                    nombre = nativoNombre();
                }
            } catch (Throwable th) {
                listo = false;
                error = th.getClass().getSimpleName() + ": " + th.getMessage();
            }
            return listo;
        }
    }

    public static boolean cargada() {
        return cargada;
    }

    public static double milisegundosCpu() {
        return msCpu;
    }

    public static double milisegundosVulkan() {
        return msVulkan;
    }

    public static synchronized boolean activo() {
        boolean z = false;
        synchronized (VulkanNativo.class) {
            if (activo) {
                z = abrir();
            }
        }
        return z;
    }

    

    

    public static synchronized void preparar(boolean z) {
        synchronized (VulkanNativo.class) {
            boolean z2 = false;
            if (!abrir()) {
                activo = false;
                return;
            }
            if (msCpu < 0.0d) {
                medir();
            }
            if (!z) {
                double d = msVulkan;
                if (d > 0.0d) {
                }
                activo = z2;
            }
            z2 = true;
            activo = z2;
        }
    }

    private static void medir() {
        double d;
        try {
            float[] fArr = new float[1048576];
            for (int i = 0; i < 1048576; i++) {
                double d2 = i;
                Double.isNaN(d2);
                fArr[i] = ((float) Math.sin(d2 * 0.001d)) * 0.25f;
            }
            float[] copiar = copiar(fArr);
            long nanoTime = System.nanoTime();
            for (int i2 = 0; i2 < 1048576; i2++) {
                copiar[i2] = copiar[i2] * 0.5f;
            }
            double nanoTime2 = System.nanoTime() - nanoTime;
            Double.isNaN(nanoTime2);
            msCpu = nanoTime2 / 1000000.0d;
            System.gc();
            float[] copiar2 = copiar(fArr);
            long nanoTime3 = System.nanoTime();
            if (nativoEscalar(copiar2, 0.5f)) {
                double nanoTime4 = System.nanoTime() - nanoTime3;
                Double.isNaN(nanoTime4);
                d = nanoTime4 / 1000000.0d;
            } else {
                d = -1.0d;
            }
            msVulkan = d;
        } catch (Throwable unused) {
            msCpu = -1.0d;
            msVulkan = -1.0d;
        }
    }

    private static float[] copiar(float[] fArr) {
        float[] fArr2 = new float[fArr.length];
        System.arraycopy(fArr, 0, fArr2, 0, fArr.length);
        return fArr2;
    }

    public static boolean listo() {
        return abrir();
    }

    public static String nombre() {
        abrir();
        String str = nombre;
        return str == null ? "" : str;
    }

    public static String error() {
        return error;
    }

    public static boolean escalar(float[] fArr, float f) {
        if (fArr != null && abrir()) {
            try {
                return nativoEscalar(fArr, f);
            } catch (Throwable unused) {
            }
        }
        return false;
    }

    public static boolean saturar(float[] fArr, float f) {
        if (abrir() && fArr != null) {
            try {
                return nativoSaturar(fArr, f);
            } catch (Throwable unused) {
            }
        }
        return false;
    }

    public static boolean porGanancia(float[] fArr, float[] fArr2) {
        if (abrir() && fArr != null && fArr2 != null) {
            try {
                return nativoPorGanancia(fArr, fArr2);
            } catch (Throwable unused) {
            }
        }
        return false;
    }
}
