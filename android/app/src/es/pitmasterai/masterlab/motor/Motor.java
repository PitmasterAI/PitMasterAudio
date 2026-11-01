package es.pitmasterai.masterlab.motor;

import es.pitmasterai.masterlab.motor.Compresor;

/* loaded from: classes.dex */
public final class Motor {
    static Biquad[] compensar(double[] dArr, double[] dArr2, double d, double d2, int i) {
        int length = dArr.length;
        double[] dArr3 = new double[length];
        double[] dArr4 = new double[length];
        for (int i2 = 0; i2 < length; i2++) {
            double max = Math.max(-15.0d, Math.min(15.0d, dArr2[i2])) * d2;
            dArr4[i2] = max;
            dArr3[i2] = max;
        }
        Biquad[] biquadArr = new Biquad[length];
        int i3 = 0;
        while (i3 <= i) {
            for (int i4 = 0; i4 < length; i4++) {
                biquadArr[i4] = reconstruir(dArr[i4], dArr3[i4], d, 4.32d);
            }
            if (i3 == i) {
                break;
            }
            int i5 = 0;
            while (i5 < length) {
                double d3 = 0.0d;
                int i6 = 0;
                while (i6 < length) {
                    d3 += biquadArr[i6].respuestaDb(dArr[i5], d);
                    i6++;
                    biquadArr = biquadArr;
                }
                dArr3[i5] = Math.max(-18.0d, Math.min(18.0d, dArr3[i5] + (dArr4[i5] - d3)));
                i5++;
                biquadArr = biquadArr;
            }
            i3++;
            biquadArr = biquadArr;
        }
        return biquadArr;
    }

    private static Biquad reconstruir(double d, double d2, double d3, double d4) {
        if (d <= 25.0d) {
            return Biquad.disenar(1, d3, Math.min(1.4d * d, 200.0d), d2, 0.707d);
        }
        if (d >= 16000.0d) {
            return Biquad.disenar(2, d3, Math.min(d * 0.8d, (d3 / 2.0d) * 0.8d), d2, 0.707d);
        }
        return Biquad.disenar(0, d3, d, d2, d4);
    }

    public static float[][] masterizar(float[][] fArr, double d, Preset preset, float f, Double d2, Double d3) {
        float[][] de = Copia.de(fArr);
        if (preset.hpfHz > 0.0f) {
            Biquad.disenar(3, d, preset.hpfHz, 0.0d, 0.707d).aplicar(de, false);
            Copia.quitarDc(de);
        }
        Trabajo.comprobar();
        for (Biquad biquad : compensar(preset.eqFreqs, preset.eqGains, d, f, 2)) {
            biquad.aplicar(de, false);
        }
        Trabajo.comprobar();
        if (preset.compBajo != null || preset.compMedio != null || preset.compAlto != null) {
            float[][] pasoBajoFaseCero = Biquad.pasoBajoFaseCero(de, d, preset.crossBajo);
            comprimirBanda(pasoBajoFaseCero, d, preset.compBajo, f, preset.compScale);
            Copia.restar(de, pasoBajoFaseCero);
            float[][] pasoBajoFaseCero2 = Biquad.pasoBajoFaseCero(de, d, preset.crossAlto);
            comprimirBanda(pasoBajoFaseCero2, d, preset.compMedio, f, preset.compScale);
            Copia.restar(de, pasoBajoFaseCero2);
            comprimirBanda(de, d, preset.compAlto, f, preset.compScale);
            Copia.sumar(de, pasoBajoFaseCero);
            Copia.sumar(de, pasoBajoFaseCero2);
        }
        Trabajo.comprobar();
        if (preset.satMix > 0.0f) {
            saturar(de, d, preset.satDrive * f, Math.min(1.0f, preset.satMix * f), preset.satEven, preset.satTone);
        }
        Trabajo.comprobar();
        if (preset.sideDb != 0.0f || preset.midDb != 0.0f) {
            anchoEstereo(de, preset.sideDb * f, preset.midDb * f);
        }
        Trabajo.comprobar();
        double doubleValue = d2 != null ? d2.doubleValue() : preset.lufs;
        double doubleValue2 = d3 != null ? d3.doubleValue() : preset.techoDb;
        System.gc();
        double lufs = Sonoridad.lufs(de, d);
        for (int i = 0; i < 3; i++) {
            Trabajo.comprobar();
            Copia.ganancia(de, (doubleValue - lufs) * 0.9d);
            Limitador.limitar(de, d, doubleValue2, preset.lookaheadMs, preset.releaseMs);
            lufs = Sonoridad.lufs(de, d);
            if (Math.abs(lufs - doubleValue) < 0.15d) {
                break;
            }
        }
        return de;
    }

    private static void comprimirBanda(float[][] fArr, double d, Compresor.Ajuste ajuste, float f, float f2) {
        if (ajuste == null) {
            return;
        }
        Compresor.comprimir(fArr, d, new Compresor.Ajuste(ajuste.umbral, ((ajuste.ratio - 1.0f) * f * f2) + 1.0f, ajuste.ataqueMs, ajuste.liberacionMs, ajuste.rodillaDb));
    }

    private static void saturar(float[][] fArr, double d, double d2, double d3, double d4, double d5) {
        double d6;
        double pow = Math.pow(10.0d, d2 / 20.0d);
        float pico = Copia.pico(fArr);
        int length = fArr.length;
        float f = 0.0f;
        int i = 0;
        while (true) {
            d6 = 0.0d;
            if (i >= length) {
                break;
            }
            for (double d7 : fArr[i]) {
                Double.isNaN(d7);
                double tanh = Math.tanh(d7 * pow);
                if (d4 != 0.0d) {
                    tanh += tanh * tanh * d4;
                }
                float abs = (float) Math.abs(tanh);
                if (abs > f) {
                    f = abs;
                }
            }
            i++;
        }
        double d8 = pico;
        double max = Math.max(f, 1.0E-9d);
        Double.isNaN(d8);
        float f2 = (float) (d8 / max);
        int i2 = 0;
        while (i2 < length) {
            float[] fArr2 = fArr[i2];
            int i3 = 0;
            while (i3 < fArr2.length) {
                double d9 = fArr2[i3];
                Double.isNaN(d9);
                double tanh2 = Math.tanh(d9 * pow);
                if (d4 != d6) {
                    tanh2 += tanh2 * tanh2 * d4;
                }
                double d10 = fArr2[i3];
                Double.isNaN(d10);
                double d11 = (1.0d - d3) * d10;
                double d12 = d3 * tanh2;
                double d13 = f2;
                Double.isNaN(d13);
                fArr2[i3] = (float) (d11 + (d12 * d13));
                i3++;
                d6 = 0.0d;
            }
            i2++;
            d6 = 0.0d;
        }
    }

    private static void anchoEstereo(float[][] fArr, double d, double d2) {
        if (fArr.length < 2) {
            return;
        }
        double pow = Math.pow(10.0d, d / 20.0d);
        double pow2 = Math.pow(10.0d, d2 / 20.0d);
        float[] fArr2 = fArr[0];
        float[] fArr3 = fArr[1];
        for (int i = 0; i < fArr2.length; i++) {
            float f = fArr2[i];
            float f2 = fArr3[i];
            double d3 = f + f2;
            Double.isNaN(d3);
            double d4 = (d3 / 2.0d) * pow2;
            double d5 = f - f2;
            Double.isNaN(d5);
            double d6 = (d5 / 2.0d) * pow;
            fArr2[i] = (float) (d4 + d6);
            fArr3[i] = (float) (d4 - d6);
        }
    }
}
