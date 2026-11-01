package es.pitmasterai.masterlab.motor;

import java.util.ArrayList;
import java.util.Iterator;

public final class Sonoridad {
    private static Biquad[] filtrosK(double d) {
        double tan = Math.tan(5284.078578647628d / d);
        double pow = Math.pow(10.0d, 0.19999219269866736d);
        double d2 = tan / 0.7071752369554196d;
        double d3 = tan * tan;
        double d4 = d2 + 1.0d + d3;
        double pow2 = (Math.pow(pow, 0.4996667741545416d) * tan) / 0.7071752369554196d;
        Biquad biquad = new Biquad(((pow + pow2) + d3) / d4, ((d3 - pow) * 2.0d) / d4, ((pow - pow2) + d3) / d4, ((d3 - 1.0d) * 2.0d) / d4, ((1.0d - d2) + d3) / d4);
        double tan2 = Math.tan(119.8061151453059d / d);
        double d5 = tan2 / 0.5003270373238773d;
        double d6 = tan2 * tan2;
        double d7 = d5 + 1.0d + d6;
        return new Biquad[]{biquad, new Biquad(1.0d, -2.0d, 1.0d, ((d6 - 1.0d) * 2.0d) / d7, ((1.0d - d5) + d6) / d7)};
    }

    public static double lufs(float[][] fArr, double d) {
        float[][] fArr2 = fArr;
        int length = fArr2.length;
        int i = 0;
        int length2 = fArr2[0].length;
        Biquad[] filtrosK = filtrosK(d);
        char c = 1;
        int max = Math.max(1, (int) Math.round(0.1d * d));
        int i2 = ((length2 + max) - 1) / max;
        double[] dArr = new double[i2];
        int i3 = 0;
        while (true) {
            double d2 = 0.0d;
            if (i3 >= length) {
                break;
            }
            float[] fArr3 = fArr2[i3];
            Biquad biquad = filtrosK[i];
            Biquad biquad2 = filtrosK[c];
            double d3 = 0.0d;
            double d4 = 0.0d;
            double d5 = 0.0d;
            while (i < length2) {
                double d6 = fArr3[i];
                Biquad[] biquadArr = filtrosK;
                double d7 = biquad.b0;
                Double.isNaN(d6);
                double d8 = (d7 * d6) + d2;
                double d9 = biquad.b1;
                Double.isNaN(d6);
                int i4 = i2;
                double[] dArr2 = dArr;
                double d10 = ((d9 * d6) - (biquad.a1 * d8)) + d3;
                double d11 = biquad.b2;
                Double.isNaN(d6);
                d3 = (d11 * d6) - (biquad.a2 * d8);
                double d12 = (biquad2.b0 * d8) + d4;
                double d13 = ((biquad2.b1 * d8) - (biquad2.a1 * d12)) + d5;
                d5 = (biquad2.b2 * d8) - (biquad2.a2 * d12);
                int i5 = i / max;
                dArr2[i5] = dArr2[i5] + (d12 * d12);
                i++;
                d2 = d10;
                length = length;
                filtrosK = biquadArr;
                d4 = d13;
                dArr = dArr2;
                i2 = i4;
            }
            i3++;
            fArr2 = fArr;
            i = 0;
            c = 1;
        }
        int i6 = i2;
        double[] dArr3 = dArr;
        ArrayList arrayList = new ArrayList();
        int i7 = 0;
        while (true) {
            int i8 = i6;
            if (i7 + 4 > i8) {
                break;
            }
            double d14 = 0.0d;
            for (int i9 = 0; i9 < 4; i9++) {
                d14 += dArr3[i7 + i9];
            }
            double min = Math.min(max * 4, length2 - (i7 * max));
            if (min > 0.0d) {
                Double.isNaN(min);
                arrayList.add(Double.valueOf(d14 / min));
            }
            i7++;
            i6 = i8;
        }
        if (arrayList.isEmpty()) {
            return Double.NEGATIVE_INFINITY;
        }
        double pow = Math.pow(10.0d, -6.930899999999999d);
        Iterator it = arrayList.iterator();
        double d15 = 0.0d;
        int i10 = 0;
        while (it.hasNext()) {
            double doubleValue = ((Double) it.next()).doubleValue();
            if (doubleValue > pow) {
                d15 += doubleValue;
                i10++;
            }
        }
        if (i10 == 0) {
            return Double.NEGATIVE_INFINITY;
        }
        double d16 = i10;
        Double.isNaN(d16);
        double pow2 = (d15 / d16) * Math.pow(10.0d, -1.0d);
        Iterator it2 = arrayList.iterator();
        double d17 = 0.0d;
        int i11 = 0;
        while (it2.hasNext()) {
            double doubleValue2 = ((Double) it2.next()).doubleValue();
            if (doubleValue2 > pow && doubleValue2 > pow2) {
                d17 += doubleValue2;
                i11++;
            }
        }
        if (i11 == 0 || d17 <= 0.0d) {
            return Double.NEGATIVE_INFINITY;
        }
        Double.isNaN(i11);
        return (Math.log10(d17 / i11) * 10.0d) - 0.691d;
    }

    public static double picoReal(float[][] fArr, double d) {
        int length = fArr[0].length;
        double d2 = 0.0d;
        for (float[] fArr2 : fArr) {
            for (int i = 0; i < length; i++) {
                double picoRealEn = Limitador.picoRealEn(fArr2, i);
                if (picoRealEn > d2) {
                    d2 = picoRealEn;
                }
            }
        }
        return Math.log10(Math.max(d2, 1.0E-9d)) * 20.0d;
    }

    public static double picoMuestral(float[][] fArr) {
        return Math.log10(Math.max(Copia.pico(fArr), 1.0E-9d)) * 20.0d;
    }
}
