package es.pitmasterai.masterlab.motor;

/** Filtros biquad RBJ y utilidades de filtrado (buffers planares x[canal][muestra]). */
public final class Biquad {

    public static final int PICO = 0;
    public static final int GRAVES = 1;
    public static final int AGUDOS = 2;
    public static final int PASO_ALTO = 3;
    public static final int PASO_BAJO = 4;

    public final double b0, b1, b2, a1, a2;

    public Biquad(double b0, double b1, double b2, double a1, double a2) {
        this.b0 = b0; this.b1 = b1; this.b2 = b2; this.a1 = a1; this.a2 = a2;
    }

    /** Coeficientes RBJ normalizados por a0. */
    public static Biquad disenar(int tipo, double sr, double f0, double gananciaDb, double q) {
        double A = Math.pow(10, gananciaDb / 40.0);
        double w0 = 2 * Math.PI * f0 / sr;
        double cw = Math.cos(w0), sw = Math.sin(w0);
        double al = sw / (2 * q);
        double b0, b1, b2, a0, a1, a2;
        switch (tipo) {
            case GRAVES: {
                double sq = 2 * Math.sqrt(A) * al;
                b0 = A * ((A + 1) - (A - 1) * cw + sq);
                b1 = 2 * A * ((A - 1) - (A + 1) * cw);
                b2 = A * ((A + 1) - (A - 1) * cw - sq);
                a0 = (A + 1) + (A - 1) * cw + sq;
                a1 = -2 * ((A - 1) + (A + 1) * cw);
                a2 = (A + 1) + (A - 1) * cw - sq;
                break;
            }
            case AGUDOS: {
                double sq = 2 * Math.sqrt(A) * al;
                b0 = A * ((A + 1) + (A - 1) * cw + sq);
                b1 = -2 * A * ((A - 1) + (A + 1) * cw);
                b2 = A * ((A + 1) + (A - 1) * cw - sq);
                a0 = (A + 1) - (A - 1) * cw + sq;
                a1 = 2 * ((A - 1) - (A + 1) * cw);
                a2 = (A + 1) - (A - 1) * cw - sq;
                break;
            }
            case PASO_ALTO:
                b0 = (1 + cw) / 2; b1 = -(1 + cw); b2 = (1 + cw) / 2;
                a0 = 1 + al; a1 = -2 * cw; a2 = 1 - al;
                break;
            case PASO_BAJO:
                b0 = (1 - cw) / 2; b1 = 1 - cw; b2 = (1 - cw) / 2;
                a0 = 1 + al; a1 = -2 * cw; a2 = 1 - al;
                break;
            default:
                b0 = 1 + al * A; b1 = -2 * cw; b2 = 1 - al * A;
                a0 = 1 + al / A; a1 = -2 * cw; a2 = 1 - al / A;
        }
        return new Biquad(b0 / a0, b1 / a0, b2 / a0, a1 / a0, a2 / a0);
    }

    /** Respuesta en dB a la frecuencia f. */
    public double respuestaDb(double f, double sr) {
        double w = 2 * Math.PI * f / sr;
        double cw = Math.cos(w), sw = Math.sin(w);
        double c2 = Math.cos(2 * w), s2 = Math.sin(2 * w);
        double nr = b0 + b1 * cw + b2 * c2;
        double ni = -(b1 * sw + b2 * s2);
        double dr = 1 + a1 * cw + a2 * c2;
        double di = -(a1 * sw + a2 * s2);
        double mag = Math.sqrt((nr * nr + ni * ni) / Math.max(dr * dr + di * di, 1e-20));
        return 20 * Math.log10(Math.max(mag, 1e-12));
    }

    /** Aplica el filtro en sitio a todas las muestras (una pasada por canal). */
    /**
     * Aplica el filtro canal a canal. En canciones largas cada canal va en su
     * propio hilo (los canales son independientes), que es la mejora real de
     * rendimiento en un móvil; el resultado es idéntico al de una sola hebra.
     */
    public void aplicar(float[][] x, boolean haciaAtras) {
        int nucleos = Runtime.getRuntime().availableProcessors();
        if (x.length >= 2 && x[0].length >= 200000 && nucleos > 1) {
            Obrero obrero = new Obrero(this, x, haciaAtras);
            Thread hilo = new Thread(obrero);
            hilo.start();
            try {
                procesar(x[0], haciaAtras);
                hilo.join();
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
            obrero.revisar();
            return;
        }
        for (int c = 0; c < x.length; c++) procesar(x[c], haciaAtras);
    }

    /** Trabaja los canales del 1 en adelante mientras el hilo principal hace el 0. */
    private static class Obrero implements Runnable {
        private final Biquad filtro;
        private final float[][] x;
        private final boolean haciaAtras;
        private RuntimeException fallo;

        Obrero(Biquad filtro, float[][] x, boolean haciaAtras) {
            this.filtro = filtro;
            this.x = x;
            this.haciaAtras = haciaAtras;
        }

        public void run() {
            try {
                for (int c = 1; c < x.length; c++) filtro.procesar(x[c], haciaAtras);
            } catch (RuntimeException e) {
                fallo = e;                 // se vuelve a lanzar en el hilo principal
            }
        }

        void revisar() {
            if (fallo != null) throw fallo;
        }
    }

    private void procesar(float[] t, boolean haciaAtras) {
        {
            int n = t.length;
            double z1 = 0, z2 = 0;
            for (int i = 0; i < n; i++) {
                if ((i & 0xFFFF) == 0) Trabajo.comprobar();
                int idx = haciaAtras ? (n - 1 - i) : i;
                double in = t[idx];
                double sal = b0 * in + z1;
                z1 = b1 * in - a1 * sal + z2;
                z2 = b2 * in - a2 * sal;
                t[idx] = (float) sal;
            }
        }
    }

    /** Filtrado de fase cero (adelante y atrás). */
    public static void aplicarFaseCero(float[][] x, Biquad... etapas) {
        for (Biquad b : etapas) b.aplicar(x, false);
        for (int i = etapas.length - 1; i >= 0; i--) etapas[i].aplicar(x, true);
    }

    /** Crossover Linkwitz-Riley 4 de fase cero sobre una copia. */
    public static float[][] pasoBajoFaseCero(float[][] x, double sr, double f) {
        float[][] copia = Copia.de(x);
        double q = 1.0 / Math.sqrt(2.0);
        aplicarFaseCero(copia, disenar(PASO_BAJO, sr, f, 0, q), disenar(PASO_BAJO, sr, f, 0, q));
        return copia;
    }
}
