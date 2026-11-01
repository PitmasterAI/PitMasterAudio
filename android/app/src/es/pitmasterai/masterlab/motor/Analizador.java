package es.pitmasterai.masterlab.motor;

public final class Analizador {
    private static double acotar(double d, double d2, double d3) {
        return d < d2 ? d2 : d > d3 ? d3 : d;
    }

    
    public static final class Perfil {
        public final double agudosDb;
        public final double correlacion;
        public final double cresta;
        public final double gravesDb;
        public final double lufs;
        public final double silencio;

        Perfil(double d, double d2, double d3, double d4, double d5, double d6) {
            this.lufs = d;
            this.cresta = d2;
            this.correlacion = d3;
            this.gravesDb = d4;
            this.agudosDb = d5;
            this.silencio = d6;
        }

        public String resumen() {
            return String.format("%.1f LUFS · cresta %.1f dB · estéreo %.2f", Double.valueOf(this.lufs), Double.valueOf(this.cresta), Double.valueOf(this.correlacion));
        }
    }

    public static Perfil analizar(float[][] fArr, int i) {
        double d;
        double d2;
        double d3;
        int i2;
        double d4;
        int length = fArr.length;
        char c = 0;
        int length2 = fArr[0].length;
        double lufs = Sonoridad.lufs(fArr, i);
        double d5 = 0.0d;
        double d6 = 0.0d;
        for (float[] fArr2 : fArr) {
            for (int i3 = 0; i3 < length2; i3++) {
                double d7 = fArr2[i3];
                if (Math.abs(d7) > d6) {
                    d6 = Math.abs(d7);
                }
                Double.isNaN(d7);
                Double.isNaN(d7);
                d5 += d7 * d7;
            }
        }
        double max = Math.max(1L, length2 * length);
        Double.isNaN(max);
        double log10 = 20.0d * Math.log10(Math.max(d6, 1.0E-9d) / Math.max(Math.sqrt(d5 / max), 1.0E-9d));
        char c2 = 1;
        if (length > 1) {
            int max2 = Math.max(1, length2 / 100000);
            int i4 = 0;
            int i5 = 0;
            double d8 = 0.0d;
            double d9 = 0.0d;
            double d10 = 0.0d;
            double d11 = 0.0d;
            double d12 = 0.0d;
            while (i4 < length2) {
                double d13 = log10;
                double d14 = fArr[c][i4];
                double d15 = fArr[c2][i4];
                Double.isNaN(d14);
                d8 += d14;
                Double.isNaN(d15);
                d9 += d15;
                Double.isNaN(d14);
                Double.isNaN(d14);
                d10 += d14 * d14;
                Double.isNaN(d15);
                Double.isNaN(d15);
                d11 += d15 * d15;
                Double.isNaN(d14);
                Double.isNaN(d15);
                d12 += d14 * d15;
                i5++;
                i4 += max2;
                log10 = d13;
                c = 0;
                c2 = 1;
            }
            d = log10;
            double d16 = i5;
            Double.isNaN(d16);
            double d17 = d8 / d16;
            Double.isNaN(d16);
            double d18 = d9 / d16;
            Double.isNaN(d16);
            Double.isNaN(d16);
            Double.isNaN(d16);
            d2 = ((d12 / d16) - (d17 * d18)) / Math.sqrt(Math.max(((d10 / d16) - (d17 * d17)) * ((d11 / d16) - (d18 * d18)), 1.0E-18d));
        } else {
            d = log10;
            d2 = 1.0d;
        }
        double energiaBanda = energiaBanda(fArr, i, 110.0d);
        double energiaBanda2 = energiaBanda(fArr, i, 1000.0d);
        double energiaBanda3 = energiaBanda(fArr, i, 8000.0d);
        int max3 = Math.max(1, i / 50);
        int i6 = length2 / max3;
        double[] dArr = new double[i6];
        int i7 = 0;
        double d19 = 0.0d;
        while (i7 < i6) {
            int i8 = i7 * max3;
            double d20 = 0.0d;
            while (true) {
                i2 = i7 + 1;
                d4 = d2;
                if (i8 >= i2 * max3) {
                    break;
                }
                double d21 = fArr[0][i8];
                Double.isNaN(d21);
                Double.isNaN(d21);
                d20 += d21 * d21;
                i8++;
                d2 = d4;
            }
            double d22 = max3;
            Double.isNaN(d22);
            double sqrt = Math.sqrt(d20 / d22);
            dArr[i7] = sqrt;
            if (sqrt > d19) {
                d19 = sqrt;
            }
            i7 = i2;
            d2 = d4;
        }
        double d23 = d2;
        double d24 = d19 * 0.0178d;
        int i9 = 0;
        for (int i10 = 0; i10 < i6; i10++) {
            if (dArr[i10] < d24) {
                i9++;
            }
        }
        if (i6 > 0) {
            double d25 = i9;
            double d26 = i6;
            Double.isNaN(d25);
            Double.isNaN(d26);
            d3 = d25 / d26;
        } else {
            d3 = 0.0d;
        }
        double max4 = Math.max(energiaBanda2, 1.0E-12d);
        return new Perfil(lufs, d, d23, Math.log10(Math.max(energiaBanda, 1.0E-12d) / max4) * 10.0d, Math.log10(Math.max(energiaBanda3, 1.0E-12d) / max4) * 10.0d, d3);
    }

    private static double energiaBanda(float[][] fArr, int i, double d) {
        float[][] de = Copia.de(fArr);
        aplicarBanda(de, i, d);
        double d2 = 0.0d;
        for (float[] fArr2 : de) {
            for (double d3 : fArr2) {
                Double.isNaN(d3);
                Double.isNaN(d3);
                d2 += d3 * d3;
            }
        }
        double max = Math.max(1L, de[0].length * de.length);
        Double.isNaN(max);
        return d2 / max;
    }

    private static void aplicarBanda(float[][] fArr, int i, double d) {
        double max = Math.max(0.7d * d, 20.0d);
        double d2 = i / 2;
        Double.isNaN(d2);
        double d3 = i;
        Biquad.aplicarFaseCero(fArr, Biquad.disenar(4, d3, Math.min(1.4d * d, d2 * 0.9d), 0.0d, 0.707d), Biquad.disenar(3, d3, max, 0.0d, 0.707d));
    }

    private static double[] perfilDelPreset(Preset preset) {
        double d;
        double d2;
        double d3 = 0.0d;
        double d4 = 0.0d;
        double d5 = 0.0d;
        double d6 = 0.0d;
        int i = 0;
        int i2 = 0;
        int i3 = 0;
        for (int i4 = 0; i4 < preset.eqFreqs.length; i4++) {
            double d7 = preset.eqFreqs[i4];
            double d8 = preset.eqGains[i4];
            if (d7 < 150.0d) {
                d4 += d8;
                i++;
            } else if (d7 < 3000.0d) {
                d6 += d8;
                i2++;
            } else {
                d5 += d8;
                i3++;
            }
        }
        double[] dArr = new double[3];
        if (i > 0) {
            double d9 = i;
            Double.isNaN(d9);
            d = d4 / d9;
        } else {
            d = 0.0d;
        }
        dArr[0] = d;
        if (i2 > 0) {
            double d10 = i2;
            Double.isNaN(d10);
            d2 = d6 / d10;
        } else {
            d2 = 0.0d;
        }
        dArr[1] = d2;
        if (i3 > 0) {
            double d11 = i3;
            Double.isNaN(d11);
            d3 = d5 / d11;
        }
        dArr[2] = d3;
        return dArr;
    }

    private static boolean esDeVoz(String str) {
        return "voz_clara".equals(str) || "podcast".equals(str);
    }

    public static double[] puntuar(Perfil perfil) {
        boolean z;
        boolean z2;
        double d;
        double d2;
        boolean z3;
        double d3;
        int length = Presets.CLAVES.length;
        double[] dArr = new double[length];
        double acotar = acotar(2.0d - perfil.gravesDb, -3.0d, 3.0d);
        double acotar2 = acotar(0.0d - perfil.agudosDb, -6.0d, 6.0d);
        boolean z4 = perfil.cresta < 10.0d;
        boolean z5 = perfil.lufs < -20.0d;
        boolean z6 = perfil.correlacion > 0.95d;
        boolean z7 = perfil.correlacion < 0.35d;
        if (perfil.silencio < 0.06d || perfil.cresta < 12.0d || perfil.lufs >= -16.0d) {
            z = z4;
            z2 = false;
        } else {
            z = z4;
            z2 = true;
        }
        boolean z8 = perfil.lufs < -28.0d || perfil.cresta < 9.0d;
        int i = 0;
        while (i < length) {
            Preset crear = Presets.crear(i);
            double[] perfilDelPreset = perfilDelPreset(crear);
            int i2 = i;
            double abs = 10.0d - ((((z2 ? 0.25d : 1.0d) * Math.abs(acotar - perfilDelPreset[0])) + (Math.abs(perfilDelPreset[1]) * 0.6d)) + ((z2 ? 0.5d : 1.0d) * Math.abs(acotar2 - perfilDelPreset[2])));
            if (z) {
                d = acotar;
                if (crear.compScale > 0.85d) {
                    abs -= 3.0d;
                }
            } else {
                d = acotar;
            }
            if (z5 && crear.compScale < 0.6d) {
                abs -= 1.5d;
            }
            if (z6 && crear.sideDb < 2.0d) {
                abs -= 1.0d;
            }
            if (z7) {
                d2 = acotar2;
                if (crear.sideDb > 5.0d) {
                    abs -= 1.0d;
                }
            } else {
                d2 = acotar2;
            }
            if (z2) {
                if (crear.satMix < 0.15d) {
                    abs += 2.0d;
                    d3 = 1.5d;
                } else {
                    d3 = 1.5d;
                    abs -= 1.5d;
                }
                if (perfilDelPreset[0] > 1.0d) {
                    abs -= d3;
                }
                if (crear.hpfHz >= 60.0f) {
                    abs += 0.5d;
                }
            }
            boolean esDeVoz = esDeVoz(crear.clave);
            if (z2 && esDeVoz) {
                abs += 5.0d;
                z3 = z8;
                if ("podcast".equals(crear.clave) == (perfil.silencio < 0.15d)) {
                    abs += 1.5d;
                }
            } else {
                z3 = z8;
            }
            if (!z2 && esDeVoz) {
                abs -= 3.0d;
            }
            if (z3) {
                abs = Math.abs(perfilDelPreset[0]) + Math.abs(perfilDelPreset[2]) < 2.0d ? abs + 1.5d : abs - 1.0d;
            }
            dArr[i2] = Math.max(0.0d, abs);
            i = i2 + 1;
            z8 = z3;
            acotar2 = d2;
            acotar = d;
        }
        return dArr;
    }

    public static int recomendar(double[] dArr) {
        int i = 0;
        for (int i2 = 1; i2 < dArr.length; i2++) {
            if (dArr[i2] > dArr[i]) {
                i = i2;
            }
        }
        return i;
    }

    public static int[] ordenar(double[] dArr) {
        int length = dArr.length;
        int[] iArr = new int[length];
        for (int i = 0; i < length; i++) {
            iArr[i] = i;
        }
        for (int i2 = 1; i2 < length; i2++) {
            for (int i3 = i2; i3 > 0; i3--) {
                int i4 = iArr[i3];
                double d = dArr[i4];
                int i5 = i3 - 1;
                int i6 = iArr[i5];
                if (d > dArr[i6]) {
                    iArr[i3] = i6;
                    iArr[i5] = i4;
                }
            }
        }
        return iArr;
    }
}
