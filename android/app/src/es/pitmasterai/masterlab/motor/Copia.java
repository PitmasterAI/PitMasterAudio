package es.pitmasterai.masterlab.motor;

import es.pitmasterai.masterlab.Acelerador;

public final class Copia {
    public static int tramas(float[][] fArr) {
        return fArr[0].length;
    }

    public static int canales(float[][] fArr) {
        return fArr.length;
    }

    public static float[][] de(float[][] fArr) {
        float[][] fArr2 = new float[fArr.length][];
        for (int i = 0; i < fArr.length; i++) {
            float[] fArr3 = new float[fArr[i].length];
            fArr2[i] = fArr3;
            float[] fArr4 = fArr[i];
            System.arraycopy(fArr4, 0, fArr3, 0, fArr4.length);
        }
        return fArr2;
    }

    public static float[][] vacio(int i, int i2) {
        float[][] fArr = new float[i2][];
        for (int i3 = 0; i3 < i2; i3++) {
            fArr[i3] = new float[i];
        }
        return fArr;
    }

    public static void copiarEn(float[][] fArr, float[][] fArr2) {
        for (int i = 0; i < fArr.length; i++) {
            float[] fArr3 = fArr2[i];
            float[] fArr4 = fArr[i];
            System.arraycopy(fArr3, 0, fArr4, 0, fArr4.length);
        }
    }

    public static void sumar(float[][] fArr, float[][] fArr2) {
        for (int i = 0; i < fArr.length; i++) {
            float[] fArr3 = fArr[i];
            float[] fArr4 = fArr2[i];
            for (int i2 = 0; i2 < fArr3.length; i2++) {
                fArr3[i2] = fArr3[i2] + fArr4[i2];
            }
        }
    }

    public static void restar(float[][] fArr, float[][] fArr2) {
        for (int i = 0; i < fArr.length; i++) {
            float[] fArr3 = fArr[i];
            float[] fArr4 = fArr2[i];
            for (int i2 = 0; i2 < fArr3.length; i2++) {
                fArr3[i2] = fArr3[i2] - fArr4[i2];
            }
        }
    }

    public static void ganancia(float[][] fArr, double d) {
        float pow = (float) Math.pow(10.0d, d / 20.0d);
        if (Math.abs(d) <= 1.0E-4d) {
            return;
        }
        int i = 0;
        if (!(fArr.length >= 1 && fArr[0].length > 100000)) {
            while (i < fArr.length) {
                escalarCpu(fArr[i], pow);
                i++;
            }
            return;
        }
        String motorHilo = Acelerador.motorHilo();
        if (motorHilo == null) {
            if (VulkanNativo.activo()) {
                motorHilo = Acelerador.VULKAN;
            } else {
                motorHilo = Gpu.sirve() ? Acelerador.GPU : Acelerador.CPU;
            }
        }
        if (Acelerador.VULKAN.equals(motorHilo) && VulkanNativo.activo()) {
            while (i < fArr.length) {
                if (!VulkanNativo.escalar(fArr[i], pow)) {
                    while (i < fArr.length) {
                        escalarCpu(fArr[i], pow);
                        i++;
                    }
                    return;
                }
                i++;
            }
            return;
        }
        if (Acelerador.GPU.equals(motorHilo) && fArr.length >= 2 && Gpu.sirve() && Gpu.multiplicar(fArr, pow)) {
            return;
        }
        while (i < fArr.length) {
            escalarCpu(fArr[i], pow);
            i++;
        }
    }

    private static void escalarCpu(float[] fArr, float f) {
        for (int i = 0; i < fArr.length; i++) {
            fArr[i] = fArr[i] * f;
        }
    }

    public static void porGanancia(float[][] fArr, float[] fArr2) {
        for (float[] fArr3 : fArr) {
            for (int i = 0; i < fArr3.length; i++) {
                fArr3[i] = fArr3[i] * fArr2[i];
            }
        }
    }

    public static float pico(float[][] fArr) {
        float f = 0.0f;
        for (float[] fArr2 : fArr) {
            for (float f2 : fArr2) {
                float abs = Math.abs(f2);
                if (abs > f) {
                    f = abs;
                }
            }
        }
        return f;
    }

    public static void quitarDc(float[][] fArr) {
        for (float[] fArr2 : fArr) {
            double d = 0.0d;
            for (double d2 : fArr2) {
                Double.isNaN(d2);
                d += d2;
            }
            double length = fArr2.length;
            Double.isNaN(length);
            float f = (float) (d / length);
            for (int i = 0; i < fArr2.length; i++) {
                fArr2[i] = fArr2[i] - f;
            }
        }
    }
}
