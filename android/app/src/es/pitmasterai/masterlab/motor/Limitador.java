package es.pitmasterai.masterlab.motor;

import java.util.ArrayDeque;

/* loaded from: classes.dex */
public final class Limitador {
    private static final int BLOQUE = 8192;
    private static final double[] H = filtroInterpolador();
    private static final int TAPS = 8;

    private static double[] filtroInterpolador() {
        double sin;
        double[] dArr = new double[32];
        for (int i = 0; i < 32; i++) {
            int i2 = i - 16;
            if (i2 == 0) {
                sin = 1.0d;
            } else {
                double d = i2;
                Double.isNaN(d);
                double d2 = d * 0.7853981633974483d;
                sin = Math.sin(d2) / d2;
            }
            double d3 = i;
            Double.isNaN(d3);
            double d4 = 31;
            Double.isNaN(d4);
            dArr[i] = sin * 0.25d * (0.54d - (Math.cos((d3 * 6.283185307179586d) / d4) * 0.46d));
        }
        for (int i3 = 0; i3 < 4; i3++) {
            double d5 = 0.0d;
            for (int i4 = 0; i4 < TAPS; i4++) {
                d5 += dArr[(i4 * 4) + i3];
            }
            if (Math.abs(d5) > 1.0E-12d) {
                for (int i5 = 0; i5 < TAPS; i5++) {
                    int i6 = (i5 * 4) + i3;
                    dArr[i6] = dArr[i6] / d5;
                }
            }
        }
        return dArr;
    }

    /* JADX INFO: Access modifiers changed from: package-private */
    public static double picoRealEn(float[] fArr, int i) {
        int length = fArr.length;
        double abs = Math.abs(fArr[i]);
        for (int i2 = 0; i2 < 4; i2++) {
            double d = 0.0d;
            for (int i3 = 0; i3 < TAPS; i3++) {
                int i4 = (i - i3) + 4;
                if (i4 >= 0 && i4 < length) {
                    double d2 = H[(i3 * 4) + i2];
                    double d3 = fArr[i4];
                    Double.isNaN(d3);
                    d += d2 * d3;
                }
            }
            double abs2 = Math.abs(d);
            if (abs2 > abs) {
                abs = abs2;
            }
        }
        return abs;
    }

    static float[] maxDeslizante(float[] fArr, int i) {
        int length = fArr.length;
        float[] fArr2 = new float[length];
        ArrayDeque arrayDeque = new ArrayDeque();
        int i2 = 0;
        for (int i3 = 0; i3 < length; i3++) {
            while (i2 < length && i2 <= i3 + i) {
                while (!arrayDeque.isEmpty() && fArr[((Integer) arrayDeque.peekLast()).intValue()] <= fArr[i2]) {
                    arrayDeque.pollLast();
                }
                arrayDeque.addLast(Integer.valueOf(i2));
                i2++;
            }
            while (!arrayDeque.isEmpty() && ((Integer) arrayDeque.peekFirst()).intValue() < i3 - i) {
                arrayDeque.pollFirst();
            }
            fArr2[i3] = arrayDeque.isEmpty() ? fArr[i3] : fArr[((Integer) arrayDeque.peekFirst()).intValue()];
        }
        return fArr2;
    }

    public static double limitar(float[][] fArr, double d, double d2, double d3, double d4) {
        int length = fArr.length;
        int i = 0;
        int length2 = fArr[0].length;
        double pow = Math.pow(10.0d, d2 / 20.0d);
        int max = Math.max(1, (int) ((d * d3) / 1000.0d));
        double d5 = -1.0d;
        double exp = Math.exp((-1.0d) / ((Math.max(d4, 1.0d) * 0.001d) * d));
        int i2 = 0;
        double d6 = 0.0d;
        while (i2 < length2) {
            int i3 = i2 + BLOQUE;
            int min = Math.min(length2, i3);
            int max2 = Math.max(i, i2 - max);
            int min2 = Math.min(length2, min + max);
            float[] fArr2 = new float[min2 - max2];
            int i4 = length2;
            int i5 = max2;
            while (i5 < min2) {
                int i6 = i2;
                double d7 = d5;
                int i7 = 0;
                double d8 = 0.0d;
                while (i7 < length) {
                    int i8 = i3;
                    double d9 = exp;
                    int i9 = min2;
                    double abs = Math.abs(fArr[i7][i5]);
                    if (abs > d8) {
                        d8 = abs;
                    }
                    double picoRealEn = picoRealEn(fArr[i7], i5);
                    if (picoRealEn > d8) {
                        d8 = picoRealEn;
                    }
                    i7++;
                    i3 = i8;
                    min2 = i9;
                    exp = d9;
                }
                fArr2[i5 - max2] = (float) d8;
                i5++;
                i2 = i6;
                i3 = i3;
                d5 = d7;
                exp = exp;
            }
            int i10 = i3;
            double d10 = exp;
            float[] maxDeslizante = maxDeslizante(fArr2, max);
            while (i2 < min) {
                float[] fArr3 = maxDeslizante;
                double min3 = Math.min(1.0d, pow / Math.max(maxDeslizante[i2 - max2], 1.0E-9d));
                if (d5 < 0.0d) {
                    d5 = min3;
                }
                double d11 = ((1.0d - d10) * min3) + (d10 * d5);
                d5 = d11 > min3 ? min3 : d11;
                float f = (float) d5;
                for (float[] fArr4 : fArr) {
                    float f2 = fArr4[i2] * f;
                    fArr4[i2] = f2;
                    double abs2 = Math.abs(f2);
                    if (abs2 > d6) {
                        d6 = abs2;
                    }
                }
                i2++;
                maxDeslizante = fArr3;
            }
            i2 = i10;
            length2 = i4;
            exp = d10;
            i = 0;
        }
        return Math.log10(Math.max(d6, 1.0E-9d)) * 20.0d;
    }
}
