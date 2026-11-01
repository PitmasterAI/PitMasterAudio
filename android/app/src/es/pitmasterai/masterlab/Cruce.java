package es.pitmasterai.masterlab;

import android.media.MediaPlayer;
import android.os.Handler;
import android.os.Looper;

/**
 * Cruce corto entre dos versiones del mismo audio: la nueva entra subiendo su volumen
 * mientras la anterior baja y se para. Sin este cruce se oía un corte al cambiar de
 * ajuste o al llegar la versión masterizada.
 */
final class Cruce implements Runnable {
    private static final int PASOS = 4;
    private static final long MS_PASO = 20L;

    private final MediaPlayer anterior;
    private final MediaPlayer nueva;
    private final int paso;
    private final boolean soltarAnterior;

    static void empezar(MediaPlayer anterior, MediaPlayer nueva, boolean soltarAnterior) {
        if (nueva == null) {
            return;
        }
        new Handler(Looper.getMainLooper()).post(new Cruce(anterior, nueva, 0, soltarAnterior));
    }

    private Cruce(MediaPlayer anterior, MediaPlayer nueva, int paso, boolean soltarAnterior) {
        this.anterior = anterior;
        this.nueva = nueva;
        this.paso = paso;
        this.soltarAnterior = soltarAnterior;
    }

    @Override // java.lang.Runnable
    public void run() {
        float f = Math.min(1.0f, (this.paso + 1) / (float) PASOS);
        try {
            this.nueva.setVolume(f, f);
            if (this.anterior != null && this.anterior != this.nueva) {
                this.anterior.setVolume(1.0f - f, 1.0f - f);
            }
        } catch (Exception unused) {
        }
        if (this.paso < PASOS - 1) {
            new Handler(Looper.getMainLooper()).postDelayed(
                    new Cruce(this.anterior, this.nueva, this.paso + 1, this.soltarAnterior), MS_PASO);
            return;
        }
        if (this.anterior == null || this.anterior == this.nueva) {
            return;
        }
        try {
            this.anterior.pause();
            this.anterior.setVolume(1.0f, 1.0f);
        } catch (Exception unused2) {
        }
        if (this.soltarAnterior) {
            try {
                this.anterior.release();
            } catch (Exception unused3) {
            }
        }
    }
}
