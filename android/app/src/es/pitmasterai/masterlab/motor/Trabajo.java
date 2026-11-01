package es.pitmasterai.masterlab.motor;

/* loaded from: classes.dex */
public final class Trabajo {
    public static final int INTERACTIVO = 0;
    private static final ThreadLocal<Integer> MODO = new ThreadLocal<>();
    public static final int PRINCIPAL = 1;
    public static final int SECUNDARIO = 2;
    private static volatile boolean canceladoInteractivo = false;
    private static volatile boolean canceladoPrincipal = false;

    private Trabajo() {
    }

    public static void marcarTipo(int i) {
        MODO.set(Integer.valueOf(i));
        if (i == 0) {
            canceladoInteractivo = false;
        }
        if (i == 1) {
            canceladoPrincipal = false;
        }
    }

    public static void soltar() {
        MODO.remove();
    }

    private static int tipo() {
        Integer num = MODO.get();
        if (num == null) {
            return 2;
        }
        return num.intValue();
    }

    public static void cancelar() {
        canceladoInteractivo = true;
    }

    public static boolean cancelado() {
        int tipo = tipo();
        if (tipo == 0) {
            return canceladoInteractivo;
        }
        if (tipo == 1) {
            return canceladoPrincipal;
        }
        return false;
    }

    public static void comprobar() {
        if (cancelado()) {
            throw new Cancelado();
        }
    }

    /* loaded from: classes.dex */
    public static class Cancelado extends RuntimeException {
        public Cancelado() {
            super("masterizado sustituido");
        }
    }
}
