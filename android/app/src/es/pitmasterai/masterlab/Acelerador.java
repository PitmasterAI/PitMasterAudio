package es.pitmasterai.masterlab;

import android.content.Context;
import android.content.pm.PackageManager;
import android.provider.Settings;
import es.pitmasterai.masterlab.motor.Gpu;
import es.pitmasterai.masterlab.motor.VulkanNativo;

/* loaded from: classes.dex */
public final class Acelerador {
    public static final String CLAVE_FORZAR = "masterlab_forzar_gpu";
    public static final String CPU = "CPU";
    public static final String GPU = "GPU";
    private static final ThreadLocal<String> MOTOR_HILO = new ThreadLocal<>();
    public static final String NPU = "NPU";
    public static final String VULKAN = "VULKAN";

    private Acelerador() {
    }

    public static boolean hayNpu(Context context) {
        try {
            PackageManager packageManager = context.getPackageManager();
            if (!packageManager.hasSystemFeature("android.hardware.neuralnetworks")) {
                if (!packageManager.hasSystemFeature("android.software.neuralnetworks")) {
                    return false;
                }
            }
            return true;
        } catch (Exception unused) {
            return false;
        }
    }

    public static boolean hayGpu(Context context) {
        try {
            PackageManager packageManager = context.getPackageManager();
            if (!packageManager.hasSystemFeature("android.hardware.vulkan.level") && !packageManager.hasSystemFeature("android.hardware.vulkan.version")) {
                if (!packageManager.hasSystemFeature("android.hardware.opengles.aep")) {
                    return false;
                }
            }
            return true;
        } catch (Exception unused) {
            return false;
        }
    }

    public static boolean pedidoForzado(Context context) {
        try {
            return Settings.Global.getInt(context.getContentResolver(), CLAVE_FORZAR, 0) == 1;
        } catch (Throwable unused) {
            return false;
        }
    }

    public static void aplicarForzado(Context context) {
        boolean pedidoForzado = pedidoForzado(context);
        Gpu.forzar(pedidoForzado);
        VulkanNativo.preparar(pedidoForzado);
    }

    public static String enUso(Context context) {
        try {
            if (VulkanNativo.activo()) {
                return VULKAN;
            }
        } catch (Throwable unused) {
        }
        try {
            return Gpu.sirve() ? GPU : CPU;
        } catch (Throwable unused2) {
            return CPU;
        }
    }

    public static void fijarMotorHilo(String str) {
        MOTOR_HILO.set(str);
    }

    public static void limpiarMotorHilo() {
        MOTOR_HILO.remove();
    }

    public static String motorHilo() {
        return MOTOR_HILO.get();
    }

    public static String motorRapido(Context context) {
        aplicarForzado(context);
        double milisegundosCpu = VulkanNativo.milisegundosCpu();
        double milisegundosVulkan = VulkanNativo.milisegundosVulkan();
        return (milisegundosVulkan <= 0.0d || milisegundosCpu <= 0.0d || milisegundosVulkan >= milisegundosCpu) ? CPU : VULKAN;
    }

    public static String motorLento(Context context) {
        if (VULKAN.equals(motorRapido(context))) {
            return CPU;
        }
        try {
            if (VulkanNativo.activo()) {
                return VULKAN;
            }
        } catch (Throwable unused) {
        }
        return Gpu.sirve() ? GPU : CPU;
    }

    public static String detalleDoble(Context context) {
        return Idioma.t("Motor principal: ") + nombre(motorRapido(context)) + "\n" + Idioma.t("Motor secundario: ") + nombre(motorLento(context));
    }

    public static String detalleLinea(Context context) {
        return detalleDoble(context).replace(String.valueOf('\n'), " | ");
    }

    private static String nombre(String str) {
        return (VULKAN.equals(str) || GPU.equals(str)) ? GPU : CPU;
    }

    public static String detalle(Context context) {
        aplicarForzado(context);
        if (VulkanNativo.activo()) {
            return Idioma.t("Motor: ") + "Vulkan (" + VulkanNativo.nombre() + ")";
        }
        return Idioma.t("Motor: ") + Idioma.t(Gpu.detalle());
    }
}
