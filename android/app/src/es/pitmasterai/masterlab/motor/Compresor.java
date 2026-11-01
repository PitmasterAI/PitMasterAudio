package es.pitmasterai.masterlab.motor;

/* loaded from: classes.dex */
public final class Compresor {

    /* loaded from: classes.dex */
    public static final class Ajuste {
        public final float ataqueMs;
        public final float liberacionMs;
        public final float ratio;
        public final float rodillaDb;
        public final float umbral;

        public Ajuste(float f, float f2, float f3, float f4, float f5) {
            this.umbral = f;
            this.ratio = f2;
            this.ataqueMs = f3;
            this.liberacionMs = f4;
            this.rodillaDb = f5;
        }
    }

    public static void comprimir(float[][] fArr, double d, Ajuste ajuste) {
        double d2;
        int length = fArr.length;
        int length2 = fArr[0].length;
        int max = Math.max(1, (int) ((d * 10.0d) / 1000.0d));
        double[] dArr = new double[max];
        double exp = Math.exp((-1.0d) / ((Math.max(ajuste.ataqueMs, 0.1d) * 0.001d) * d));
        double exp2 = Math.exp((-1.0d) / ((Math.max(ajuste.liberacionMs, 0.1d) * 0.001d) * d));
        double d3 = ajuste.ratio;
        Double.isNaN(d3);
        double d4 = (1.0d / d3) - 1.0d;
        double d5 = ajuste.umbral;
        double d6 = ajuste.rodillaDb;
        Double.isNaN(d6);
        Double.isNaN(d5);
        double d7 = d5 - (d6 / 2.0d);
        double d8 = ajuste.umbral;
        double d9 = ajuste.rodillaDb;
        Double.isNaN(d9);
        Double.isNaN(d8);
        double d10 = d8 + (d9 / 2.0d);
        int i = 0;
        double d11 = 0.0d;
        int i2 = 0;
        double d12 = 0.0d;
        double d13 = 0.0d;
        boolean z = false;
        while (i < length2) {
            int i3 = 0;
            double d14 = 0.0d;
            while (i3 < length) {
                int i4 = i;
                int i5 = length2;
                double abs = Math.abs(fArr[i3][i]);
                if (abs > d14) {
                    d14 = abs;
                }
                i3++;
                length2 = i5;
                i = i4;
            }
            int i6 = i;
            int i7 = length2;
            double d15 = d14 * d14;
            d11 += d15 - dArr[i2];
            dArr[i2] = d15;
            i2 = (i2 + 1) % max;
            double d16 = max;
            Double.isNaN(d16);
            double log10 = Math.log10(Math.max(Math.sqrt(Math.max(d11 / d16, 1.0E-20d)), 1.0E-9d)) * 20.0d;
            if (!z) {
                d12 = log10;
                d13 = d12;
                z = true;
            }
            d12 = ((1.0d - exp) * log10) + (d12 * exp);
            double d17 = ((1.0d - exp2) * d12) + (d13 * exp2);
            d13 = d17 < d12 ? d12 : d17;
            if (ajuste.rodillaDb <= 0.0f || d13 < d7) {
                d2 = 0.0d;
            } else if (d13 > d10) {
                double d18 = ajuste.umbral;
                Double.isNaN(d18);
                d2 = (d13 - d18) * d4;
            } else {
                double d19 = d13 - d7;
                double d20 = d4 * d19 * d19;
                double d21 = ajuste.rodillaDb * 2.0f;
                Double.isNaN(d21);
                d2 = d20 / d21;
            }
            if (d2 > 0.0d) {
                d2 = 0.0d;
            }
            float pow = (float) Math.pow(10.0d, d2 / 20.0d);
            for (float[] fArr2 : fArr) {
                fArr2[i6] = fArr2[i6] * pow;
            }
            i = i6 + 1;
            length2 = i7;
        }
    }
}
