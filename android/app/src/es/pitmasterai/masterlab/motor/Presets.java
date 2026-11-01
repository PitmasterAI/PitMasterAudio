package es.pitmasterai.masterlab.motor;

import es.pitmasterai.masterlab.motor.Compresor;

/* loaded from: classes.dex */
public final class Presets {
    public static final String[] CLAVES = {"alt_high_bright", "alt_high_brighter", "alt_high_neutral", "alt_high_warm", "alt_high_warmer", "alt_low_bright", "alt_low_brighter", "alt_low_neutral", "alt_low_warm", "alt_low_warmer", "alt_medium_bright", "alt_medium_brighter", "alt_medium_neutral", "alt_medium_warm", "alt_medium_warmer", "base_amplia", "base_caliente", "base_claro", "base_equilibrado", "base_film", "base_neutra", "base_potente", "base_retro", "voz_clara", "podcast"};
    public static final String[] NOMBRES = {"Radiante", "Deslumbrante", "Firme", "Densa", "Oscura", "Luminosa", "Aire", "Sencilla", "Suave", "Terciopelo", "Viva", "Chispa", "Habitual", "Calida", "Sedosa", "Amplia", "Caliente", "Claro", "Amplificador", "Film", "Neutra", "Potente", "Retro", "Audiolibro", "Podcast"};
    public static final String[] DESCRIPCIONES = {"Mucha compresion, timbre brillante", "Mucha compresion, timbre muy brillante", "Mucha compresion, timbre neutro", "Mucha compresion, timbre calido", "Mucha compresion, timbre muy calido", "Poca compresion, timbre brillante", "Poca compresion, timbre muy brillante", "Poca compresion, timbre neutro", "Poca compresion, timbre calido", "Poca compresion, timbre muy calido", "Compresion media, timbre brillante", "Compresion media, timbre muy brillante", "Compresion media, timbre neutro", "Compresion media, timbre calido", "Compresion media, timbre muy calido", "Escena estereo abierta", "Bajos con cuerpo y medios claros", "Agudos abiertos, mas aire arriba", "Balance tonal neutro, no toca el color", "Saturacion intensa, sonido grande", "Compresion suave, casi no se nota", "Graves y agudos con mas pegada", "Saturacion calida de cinta", "Audiolibro: quita retumbe y suciedad, aclara la diccion sin saturar", "Podcast: voz al frente, compresion firme y nivel -16 LUFS"};

    public static Preset crear(int i) {
        switch (i) {
            case Trabajo.INTERACTIVO /* 0 */:
                return alt_high_bright();
            case 1:
                return alt_high_brighter();
            case 2:
                return alt_high_neutral();
            case Biquad.PASO_ALTO /* 3 */:
                return alt_high_warm();
            case Biquad.PASO_BAJO /* 4 */:
                return alt_high_warmer();
            case 5:
                return alt_low_bright();
            case 6:
                return alt_low_brighter();
            case 7:
                return alt_low_neutral();
            case 8:
                return alt_low_warm();
            case 9:
                return alt_low_warmer();
            case 10:
                return alt_medium_bright();
            case 11:
                return alt_medium_brighter();
            case 12:
                return alt_medium_neutral();
            case 13:
                return alt_medium_warm();
            case 14:
                return alt_medium_warmer();
            case 15:
                return base_amplia();
            case 16:
                return base_caliente();
            case 17:
                return base_claro();
            case 18:
                return base_equilibrado();
            case 19:
                return base_film();
            case 20:
                return base_neutra();
            case 21:
                return base_potente();
            case 22:
                return base_retro();
            case 23:
                return voz_clara();
            case 24:
                return podcast();
            default:
                return null;
        }
    }

    private static Preset alt_high_bright() {
        return new Preset("alt_high_bright", new double[]{22.4d, 28.3d, 35.6d, 44.9d, 56.6d, 71.3d, 89.8d, 113.1d, 142.5d, 179.6d, 226.3d, 285.1d, 359.2d, 452.5d, 570.2d, 718.4d, 905.1d, 1140.4d, 1436.8d, 1810.2d, 2280.7d, 2873.5d, 3620.4d, 4561.4d, 5747.0d, 7240.8d, 9122.8d, 11494.0d, 14481.5d}, new double[]{9.62d, 9.41d, 7.54d, 6.33d, 5.09d, 4.22d, 4.98d, 5.47d, 5.58d, 4.66d, 2.7d, 1.0d, 0.36d, 0.47d, 0.97d, 0.05d, 0.0d, 2.05d, 2.81d, 4.44d, 5.48d, 6.97d, 8.51d, 10.24d, 12.71d, 13.85d, 14.04d, 14.39d, 15.78d}, 45.0f, 1.2f, 250.0f, 3000.0f, new Compresor.Ajuste(-28.4f, 1.2f, 15.0f, 180.0f, 6.0f), new Compresor.Ajuste(-25.6f, 1.32f, 8.0f, 120.0f, 6.0f), new Compresor.Ajuste(-39.0f, 1.28f, 3.0f, 70.0f, 6.0f), 6.0f, 0.13f, 0.05f, 16000.0f, 6.0f, 0.0f, 0.0f, -7.33f, -0.3f, 5.0f, 60.0f);
    }

    private static Preset alt_high_brighter() {
        return new Preset("alt_high_brighter", new double[]{22.4d, 28.3d, 35.6d, 44.9d, 56.6d, 71.3d, 89.8d, 113.1d, 142.5d, 179.6d, 226.3d, 285.1d, 359.2d, 452.5d, 570.2d, 718.4d, 905.1d, 1140.4d, 1436.8d, 1810.2d, 2280.7d, 2873.5d, 3620.4d, 4561.4d, 5747.0d, 7240.8d, 9122.8d, 11494.0d, 14481.5d}, new double[]{12.71d, 8.4d, 5.28d, 4.09d, 2.84d, 2.23d, 2.83d, 3.15d, 3.39d, 2.23d, 0.53d, -0.91d, -1.38d, -1.01d, 0.14d, -0.07d, 0.0d, 2.14d, 3.11d, 4.71d, 5.85d, 7.16d, 8.82d, 10.5d, 12.77d, 14.28d, 14.67d, 14.99d, 16.38d}, 45.0f, 1.2f, 250.0f, 3000.0f, new Compresor.Ajuste(-28.4f, 1.2f, 15.0f, 180.0f, 6.0f), new Compresor.Ajuste(-25.6f, 1.32f, 8.0f, 120.0f, 6.0f), new Compresor.Ajuste(-39.0f, 1.28f, 3.0f, 70.0f, 6.0f), 6.0f, 0.13f, 0.05f, 16000.0f, 6.0f, 0.0f, 0.0f, -8.44f, -0.3f, 5.0f, 60.0f);
    }

    private static Preset alt_high_neutral() {
        return new Preset("alt_high_neutral", new double[]{22.4d, 28.3d, 35.6d, 44.9d, 56.6d, 71.3d, 89.8d, 113.1d, 142.5d, 179.6d, 226.3d, 285.1d, 359.2d, 452.5d, 570.2d, 718.4d, 905.1d, 1140.4d, 1436.8d, 1810.2d, 2280.7d, 2873.5d, 3620.4d, 4561.4d, 5747.0d, 7240.8d, 9122.8d, 11494.0d, 14481.5d}, new double[]{14.79d, 10.44d, 7.34d, 6.17d, 4.95d, 4.39d, 5.04d, 5.55d, 5.69d, 4.51d, 2.98d, 1.4d, 0.55d, 0.63d, 1.18d, 0.25d, 0.0d, 2.5d, 3.34d, 4.99d, 6.2d, 7.49d, 9.1d, 10.33d, 11.88d, 12.42d, 12.41d, 12.56d, 13.56d}, 45.0f, 1.2f, 250.0f, 3000.0f, new Compresor.Ajuste(-28.4f, 1.2f, 15.0f, 180.0f, 6.0f), new Compresor.Ajuste(-25.6f, 1.32f, 8.0f, 120.0f, 6.0f), new Compresor.Ajuste(-39.0f, 1.28f, 3.0f, 70.0f, 6.0f), 6.0f, 0.13f, 0.05f, 16000.0f, 6.0f, 0.0f, 0.0f, -8.72f, -0.3f, 5.0f, 60.0f);
    }

    private static Preset alt_high_warm() {
        return new Preset("alt_high_warm", new double[]{22.4d, 28.3d, 35.6d, 44.9d, 56.6d, 71.3d, 89.8d, 113.1d, 142.5d, 179.6d, 226.3d, 285.1d, 359.2d, 452.5d, 570.2d, 718.4d, 905.1d, 1140.4d, 1436.8d, 1810.2d, 2280.7d, 2873.5d, 3620.4d, 4561.4d, 5747.0d, 7240.8d, 9122.8d, 11494.0d, 14481.5d}, new double[]{14.66d, 10.49d, 7.39d, 6.19d, 4.95d, 4.41d, 5.05d, 5.57d, 5.72d, 4.54d, 3.03d, 1.45d, 0.6d, 0.68d, 1.24d, 0.27d, 0.0d, 2.52d, 3.37d, 5.02d, 6.25d, 7.53d, 9.14d, 9.94d, 10.74d, 10.35d, 9.91d, 9.88d, 10.55d}, 45.0f, 1.2f, 250.0f, 3000.0f, new Compresor.Ajuste(-28.4f, 1.2f, 15.0f, 180.0f, 6.0f), new Compresor.Ajuste(-25.6f, 1.32f, 8.0f, 120.0f, 6.0f), new Compresor.Ajuste(-39.0f, 1.28f, 3.0f, 70.0f, 6.0f), 6.0f, 0.13f, 0.05f, 16000.0f, 6.0f, 0.0f, 0.0f, -9.0f, -0.3f, 5.0f, 60.0f);
    }

    private static Preset alt_high_warmer() {
        return new Preset("alt_high_warmer", new double[]{22.4d, 28.3d, 35.6d, 44.9d, 56.6d, 71.3d, 89.8d, 113.1d, 142.5d, 179.6d, 226.3d, 285.1d, 359.2d, 452.5d, 570.2d, 718.4d, 905.1d, 1140.4d, 1436.8d, 1810.2d, 2280.7d, 2873.5d, 3620.4d, 4561.4d, 5747.0d, 7240.8d, 9122.8d, 11494.0d, 14481.5d}, new double[]{16.28d, 12.12d, 9.04d, 7.74d, 6.4d, 5.79d, 6.21d, 6.57d, 6.4d, 4.89d, 3.28d, 1.6d, 0.67d, 0.74d, 1.3d, 0.31d, 0.0d, 2.57d, 3.41d, 5.05d, 6.31d, 7.57d, 9.13d, 9.44d, 9.33d, 7.66d, 6.28d, 5.51d, 5.5d}, 45.0f, 1.2f, 250.0f, 3000.0f, new Compresor.Ajuste(-28.4f, 1.2f, 15.0f, 180.0f, 6.0f), new Compresor.Ajuste(-25.6f, 1.32f, 8.0f, 120.0f, 6.0f), new Compresor.Ajuste(-39.0f, 1.28f, 3.0f, 70.0f, 6.0f), 6.0f, 0.13f, 0.05f, 16000.0f, 6.0f, 0.0f, 0.0f, -9.35f, -0.3f, 5.0f, 60.0f);
    }

    private static Preset alt_low_bright() {
        return new Preset("alt_low_bright", new double[]{22.4d, 28.3d, 35.6d, 44.9d, 56.6d, 71.3d, 89.8d, 113.1d, 142.5d, 179.6d, 226.3d, 285.1d, 359.2d, 452.5d, 570.2d, 718.4d, 905.1d, 1140.4d, 1436.8d, 1810.2d, 2280.7d, 2873.5d, 3620.4d, 4561.4d, 5747.0d, 7240.8d, 9122.8d, 11494.0d, 14481.5d}, new double[]{16.61d, 12.2d, 9.51d, 7.98d, 6.76d, 5.99d, 6.41d, 6.49d, 5.86d, 5.0d, 3.88d, 2.33d, 1.4d, 1.58d, 2.02d, 0.62d, 0.0d, 2.0d, 2.39d, 4.12d, 4.97d, 6.12d, 7.57d, 8.92d, 10.64d, 12.11d, 12.37d, 12.3d, 12.75d}, 45.0f, 0.815f, 250.0f, 3000.0f, new Compresor.Ajuste(-28.4f, 1.2f, 15.0f, 180.0f, 6.0f), new Compresor.Ajuste(-25.6f, 1.32f, 8.0f, 120.0f, 6.0f), new Compresor.Ajuste(-39.0f, 1.28f, 3.0f, 70.0f, 6.0f), 3.25f, 0.081f, 0.05f, 16000.0f, 3.8f, 0.0f, 0.0f, -13.39f, -0.3f, 5.0f, 60.0f);
    }

    private static Preset alt_low_brighter() {
        return new Preset("alt_low_brighter", new double[]{22.4d, 28.3d, 35.6d, 44.9d, 56.6d, 71.3d, 89.8d, 113.1d, 142.5d, 179.6d, 226.3d, 285.1d, 359.2d, 452.5d, 570.2d, 718.4d, 905.1d, 1140.4d, 1436.8d, 1810.2d, 2280.7d, 2873.5d, 3620.4d, 4561.4d, 5747.0d, 7240.8d, 9122.8d, 11494.0d, 14481.5d}, new double[]{13.27d, 9.64d, 7.25d, 5.87d, 4.73d, 3.97d, 4.39d, 4.28d, 3.75d, 2.83d, 1.57d, 0.17d, -0.42d, 0.05d, 1.05d, 0.35d, 0.0d, 1.68d, 2.18d, 3.85d, 4.68d, 5.85d, 7.35d, 8.7d, 10.45d, 11.92d, 12.16d, 12.07d, 12.51d}, 45.0f, 0.815f, 250.0f, 3000.0f, new Compresor.Ajuste(-28.4f, 1.2f, 15.0f, 180.0f, 6.0f), new Compresor.Ajuste(-25.6f, 1.32f, 8.0f, 120.0f, 6.0f), new Compresor.Ajuste(-39.0f, 1.28f, 3.0f, 70.0f, 6.0f), 3.25f, 0.081f, 0.05f, 16000.0f, 3.8f, 0.0f, 0.0f, -13.85f, -0.3f, 5.0f, 60.0f);
    }

    private static Preset alt_low_neutral() {
        return new Preset("alt_low_neutral", new double[]{22.4d, 28.3d, 35.6d, 44.9d, 56.6d, 71.3d, 89.8d, 113.1d, 142.5d, 179.6d, 226.3d, 285.1d, 359.2d, 452.5d, 570.2d, 718.4d, 905.1d, 1140.4d, 1436.8d, 1810.2d, 2280.7d, 2873.5d, 3620.4d, 4561.4d, 5747.0d, 7240.8d, 9122.8d, 11494.0d, 14481.5d}, new double[]{16.52d, 12.17d, 9.47d, 7.94d, 6.74d, 5.97d, 6.39d, 6.48d, 5.85d, 5.01d, 3.86d, 2.3d, 1.38d, 1.56d, 2.01d, 0.61d, 0.0d, 1.99d, 2.39d, 4.13d, 4.98d, 6.14d, 7.59d, 8.55d, 9.53d, 10.05d, 9.92d, 9.67d, 9.84d}, 45.0f, 0.815f, 250.0f, 3000.0f, new Compresor.Ajuste(-28.4f, 1.2f, 15.0f, 180.0f, 6.0f), new Compresor.Ajuste(-25.6f, 1.32f, 8.0f, 120.0f, 6.0f), new Compresor.Ajuste(-39.0f, 1.28f, 3.0f, 70.0f, 6.0f), 3.25f, 0.081f, 0.05f, 16000.0f, 3.8f, 0.0f, 0.0f, -13.59f, -0.3f, 5.0f, 60.0f);
    }

    private static Preset alt_low_warm() {
        return new Preset("alt_low_warm", new double[]{22.4d, 28.3d, 35.6d, 44.9d, 56.6d, 71.3d, 89.8d, 113.1d, 142.5d, 179.6d, 226.3d, 285.1d, 359.2d, 452.5d, 570.2d, 718.4d, 905.1d, 1140.4d, 1436.8d, 1810.2d, 2280.7d, 2873.5d, 3620.4d, 4561.4d, 5747.0d, 7240.8d, 9122.8d, 11494.0d, 14481.5d}, new double[]{17.56d, 12.88d, 10.15d, 8.54d, 7.27d, 6.45d, 6.77d, 6.79d, 6.03d, 5.11d, 3.9d, 2.32d, 1.37d, 1.55d, 2.01d, 0.6d, 0.0d, 2.01d, 2.4d, 4.15d, 5.01d, 6.17d, 7.61d, 8.16d, 8.39d, 7.99d, 7.44d, 7.04d, 6.94d}, 45.0f, 0.815f, 250.0f, 3000.0f, new Compresor.Ajuste(-28.4f, 1.2f, 15.0f, 180.0f, 6.0f), new Compresor.Ajuste(-25.6f, 1.32f, 8.0f, 120.0f, 6.0f), new Compresor.Ajuste(-39.0f, 1.28f, 3.0f, 70.0f, 6.0f), 3.25f, 0.081f, 0.05f, 16000.0f, 3.8f, 0.0f, 0.0f, -13.55f, -0.3f, 5.0f, 60.0f);
    }

    private static Preset alt_low_warmer() {
        return new Preset("alt_low_warmer", new double[]{22.4d, 28.3d, 35.6d, 44.9d, 56.6d, 71.3d, 89.8d, 113.1d, 142.5d, 179.6d, 226.3d, 285.1d, 359.2d, 452.5d, 570.2d, 718.4d, 905.1d, 1140.4d, 1436.8d, 1810.2d, 2280.7d, 2873.5d, 3620.4d, 4561.4d, 5747.0d, 7240.8d, 9122.8d, 11494.0d, 14481.5d}, new double[]{21.18d, 15.24d, 12.3d, 10.45d, 8.92d, 7.85d, 7.93d, 7.75d, 6.59d, 5.39d, 4.02d, 2.34d, 1.35d, 1.53d, 1.99d, 0.58d, 0.0d, 2.01d, 2.43d, 4.18d, 5.04d, 6.17d, 7.6d, 7.66d, 7.02d, 5.31d, 3.78d, 2.61d, 1.75d}, 45.0f, 0.815f, 250.0f, 3000.0f, new Compresor.Ajuste(-28.4f, 1.2f, 15.0f, 180.0f, 6.0f), new Compresor.Ajuste(-25.6f, 1.32f, 8.0f, 120.0f, 6.0f), new Compresor.Ajuste(-39.0f, 1.28f, 3.0f, 70.0f, 6.0f), 3.25f, 0.081f, 0.05f, 16000.0f, 3.8f, 0.0f, 0.0f, -13.54f, -0.3f, 5.0f, 60.0f);
    }

    private static Preset alt_medium_bright() {
        return new Preset("alt_medium_bright", new double[]{22.4d, 28.3d, 35.6d, 44.9d, 56.6d, 71.3d, 89.8d, 113.1d, 142.5d, 179.6d, 226.3d, 285.1d, 359.2d, 452.5d, 570.2d, 718.4d, 905.1d, 1140.4d, 1436.8d, 1810.2d, 2280.7d, 2873.5d, 3620.4d, 4561.4d, 5747.0d, 7240.8d, 9122.8d, 11494.0d, 14481.5d}, new double[]{14.41d, 11.59d, 8.52d, 7.37d, 6.0d, 5.28d, 5.91d, 6.33d, 5.97d, 4.74d, 3.54d, 1.99d, 1.12d, 1.28d, 1.76d, 0.56d, 0.0d, 2.24d, 2.83d, 4.39d, 5.56d, 6.76d, 8.23d, 9.74d, 11.77d, 13.25d, 13.55d, 13.59d, 14.41d}, 45.0f, 1.025f, 250.0f, 3000.0f, new Compresor.Ajuste(-28.4f, 1.2f, 15.0f, 180.0f, 6.0f), new Compresor.Ajuste(-25.6f, 1.32f, 8.0f, 120.0f, 6.0f), new Compresor.Ajuste(-39.0f, 1.28f, 3.0f, 70.0f, 6.0f), 4.75f, 0.108f, 0.05f, 16000.0f, 5.0f, 0.0f, 0.0f, -10.66f, -0.3f, 5.0f, 60.0f);
    }

    private static Preset alt_medium_brighter() {
        return new Preset("alt_medium_brighter", new double[]{22.4d, 28.3d, 35.6d, 44.9d, 56.6d, 71.3d, 89.8d, 113.1d, 142.5d, 179.6d, 226.3d, 285.1d, 359.2d, 452.5d, 570.2d, 718.4d, 905.1d, 1140.4d, 1436.8d, 1810.2d, 2280.7d, 2873.5d, 3620.4d, 4561.4d, 5747.0d, 7240.8d, 9122.8d, 11494.0d, 14481.5d}, new double[]{12.12d, 9.79d, 6.66d, 5.46d, 4.03d, 3.36d, 3.8d, 3.95d, 3.7d, 2.26d, 1.1d, -0.27d, -0.86d, -0.4d, 0.66d, 0.24d, 0.0d, 2.2d, 3.03d, 4.62d, 5.81d, 6.95d, 8.54d, 10.07d, 12.06d, 13.63d, 14.01d, 14.1d, 15.02d}, 45.0f, 1.025f, 250.0f, 3000.0f, new Compresor.Ajuste(-28.4f, 1.2f, 15.0f, 180.0f, 6.0f), new Compresor.Ajuste(-25.6f, 1.32f, 8.0f, 120.0f, 6.0f), new Compresor.Ajuste(-39.0f, 1.28f, 3.0f, 70.0f, 6.0f), 4.75f, 0.108f, 0.05f, 16000.0f, 5.0f, 0.0f, 0.0f, -11.33f, -0.3f, 5.0f, 60.0f);
    }

    private static Preset alt_medium_neutral() {
        return new Preset("alt_medium_neutral", new double[]{22.4d, 28.3d, 35.6d, 44.9d, 56.6d, 71.3d, 89.8d, 113.1d, 142.5d, 179.6d, 226.3d, 285.1d, 359.2d, 452.5d, 570.2d, 718.4d, 905.1d, 1140.4d, 1436.8d, 1810.2d, 2280.7d, 2873.5d, 3620.4d, 4561.4d, 5747.0d, 7240.8d, 9122.8d, 11494.0d, 14481.5d}, new double[]{14.77d, 11.66d, 8.45d, 7.27d, 5.91d, 5.32d, 5.85d, 6.22d, 5.9d, 4.54d, 3.43d, 1.9d, 0.98d, 1.12d, 1.62d, 0.49d, 0.0d, 2.52d, 3.22d, 4.9d, 6.1d, 7.27d, 8.8d, 9.91d, 11.19d, 11.78d, 11.75d, 11.67d, 12.27d}, 45.0f, 1.025f, 250.0f, 3000.0f, new Compresor.Ajuste(-28.4f, 1.2f, 15.0f, 180.0f, 6.0f), new Compresor.Ajuste(-25.6f, 1.32f, 8.0f, 120.0f, 6.0f), new Compresor.Ajuste(-39.0f, 1.28f, 3.0f, 70.0f, 6.0f), 4.75f, 0.108f, 0.05f, 16000.0f, 5.0f, 0.0f, 0.0f, -11.38f, -0.3f, 5.0f, 60.0f);
    }

    private static Preset alt_medium_warm() {
        return new Preset("alt_medium_warm", new double[]{22.4d, 28.3d, 35.6d, 44.9d, 56.6d, 71.3d, 89.8d, 113.1d, 142.5d, 179.6d, 226.3d, 285.1d, 359.2d, 452.5d, 570.2d, 718.4d, 905.1d, 1140.4d, 1436.8d, 1810.2d, 2280.7d, 2873.5d, 3620.4d, 4561.4d, 5747.0d, 7240.8d, 9122.8d, 11494.0d, 14481.5d}, new double[]{14.94d, 11.62d, 8.4d, 7.22d, 5.88d, 5.3d, 5.84d, 6.19d, 5.9d, 4.56d, 3.42d, 1.88d, 0.96d, 1.09d, 1.6d, 0.47d, 0.0d, 2.51d, 3.22d, 4.9d, 6.11d, 7.28d, 8.82d, 9.5d, 10.06d, 9.68d, 9.24d, 9.0d, 9.29d}, 45.0f, 1.025f, 250.0f, 3000.0f, new Compresor.Ajuste(-28.4f, 1.2f, 15.0f, 180.0f, 6.0f), new Compresor.Ajuste(-25.6f, 1.32f, 8.0f, 120.0f, 6.0f), new Compresor.Ajuste(-39.0f, 1.28f, 3.0f, 70.0f, 6.0f), 4.75f, 0.108f, 0.05f, 16000.0f, 5.0f, 0.0f, 0.0f, -11.56f, -0.3f, 5.0f, 60.0f);
    }

    private static Preset alt_medium_warmer() {
        return new Preset("alt_medium_warmer", new double[]{22.4d, 28.3d, 35.6d, 44.9d, 56.6d, 71.3d, 89.8d, 113.1d, 142.5d, 179.6d, 226.3d, 285.1d, 359.2d, 452.5d, 570.2d, 718.4d, 905.1d, 1140.4d, 1436.8d, 1810.2d, 2280.7d, 2873.5d, 3620.4d, 4561.4d, 5747.0d, 7240.8d, 9122.8d, 11494.0d, 14481.5d}, new double[]{18.09d, 13.8d, 10.4d, 8.98d, 7.46d, 6.72d, 7.01d, 7.18d, 6.51d, 4.93d, 3.58d, 1.91d, 0.95d, 1.08d, 1.6d, 0.46d, 0.0d, 2.51d, 3.25d, 4.92d, 6.13d, 7.32d, 8.79d, 9.02d, 8.68d, 7.03d, 5.58d, 4.62d, 4.21d}, 45.0f, 1.025f, 250.0f, 3000.0f, new Compresor.Ajuste(-28.4f, 1.2f, 15.0f, 180.0f, 6.0f), new Compresor.Ajuste(-25.6f, 1.32f, 8.0f, 120.0f, 6.0f), new Compresor.Ajuste(-39.0f, 1.28f, 3.0f, 70.0f, 6.0f), 4.75f, 0.108f, 0.05f, 16000.0f, 5.0f, 0.0f, 0.0f, -11.71f, -0.3f, 5.0f, 60.0f);
    }

    private static Preset base_amplia() {
        return new Preset("base_amplia", new double[]{22.4d, 28.3d, 35.6d, 44.9d, 56.6d, 71.3d, 89.8d, 113.1d, 142.5d, 179.6d, 226.3d, 285.1d, 359.2d, 452.5d, 570.2d, 718.4d, 905.1d, 1140.4d, 1436.8d, 1810.2d, 2280.7d, 2873.5d, 3620.4d, 4561.4d, 5747.0d, 7240.8d, 9122.8d, 11494.0d, 14481.5d}, new double[]{-1.5d, 1.1d, -2.1d, 0.1d, -1.5d, -0.6d, -0.9d, -0.8d, -0.5d, -0.7d, -0.1d, 0.1d, 0.4d, 0.7d, 0.5d, 0.7d, 0.2d, 0.4d, 0.6d, 0.1d, 0.6d, 0.6d, 1.4d, 2.7d, 3.9d, 5.1d, 5.8d, 6.9d, 8.9d}, 0.0f, 1.0f, 250.0f, 3000.0f, new Compresor.Ajuste(-23.4f, 1.06f, 15.0f, 180.0f, 6.0f), new Compresor.Ajuste(-31.4f, 1.1f, 8.0f, 120.0f, 6.0f), new Compresor.Ajuste(-36.5f, 1.2f, 3.0f, 70.0f, 6.0f), 3.0f, 0.04f, 0.0f, 16000.0f, 5.7f, 0.0f, 0.1f, -12.62f, -0.3f, 5.0f, 60.0f);
    }

    private static Preset base_caliente() {
        return new Preset("base_caliente", new double[]{22.4d, 28.3d, 35.6d, 44.9d, 56.6d, 71.3d, 89.8d, 113.1d, 142.5d, 179.6d, 226.3d, 285.1d, 359.2d, 452.5d, 570.2d, 718.4d, 905.1d, 1140.4d, 1436.8d, 1810.2d, 2280.7d, 2873.5d, 3620.4d, 4561.4d, 5747.0d, 7240.8d, 9122.8d, 11494.0d, 14481.5d}, new double[]{18.0d, 18.0d, 18.0d, 13.3d, 9.1d, 7.2d, 5.7d, 5.5d, 3.7d, 1.2d, -1.2d, -0.8d, 0.2d, 0.3d, 0.4d, 0.6d, 0.2d, 0.5d, 1.1d, 0.4d, 0.9d, 2.2d, 4.1d, 5.8d, 7.8d, 9.2d, 9.5d, 9.2d, 8.4d}, 45.0f, 1.0f, 250.0f, 3000.0f, new Compresor.Ajuste(-20.5f, 1.35f, 15.0f, 180.0f, 6.0f), new Compresor.Ajuste(-27.7f, 1.26f, 8.0f, 120.0f, 6.0f), new Compresor.Ajuste(-35.8f, 1.34f, 3.0f, 70.0f, 6.0f), 5.0f, 0.1f, 0.1f, 15000.0f, -2.0f, 0.0f, 0.0f, -12.77f, -0.3f, 5.0f, 60.0f);
    }

    private static Preset base_claro() {
        return new Preset("base_claro", new double[]{22.4d, 28.3d, 35.6d, 44.9d, 56.6d, 71.3d, 89.8d, 113.1d, 142.5d, 179.6d, 226.3d, 285.1d, 359.2d, 452.5d, 570.2d, 718.4d, 905.1d, 1140.4d, 1436.8d, 1810.2d, 2280.7d, 2873.5d, 3620.4d, 4561.4d, 5747.0d, 7240.8d, 9122.8d, 11494.0d, 14481.5d}, new double[]{1.9d, 1.4d, 1.8d, 1.5d, 0.9d, 1.0d, 0.4d, -0.8d, -0.4d, 0.1d, 0.4d, -0.0d, -0.1d, -0.8d, -0.2d, 0.0d, -0.2d, -0.9d, -0.8d, -0.9d, 0.1d, 1.2d, 2.8d, 4.9d, 6.5d, 7.4d, 7.7d, 8.4d, 12.8d}, 0.0f, 1.0f, 250.0f, 3000.0f, new Compresor.Ajuste(-12.1f, 1.15f, 15.0f, 180.0f, 6.0f), new Compresor.Ajuste(-18.6f, 1.12f, 8.0f, 120.0f, 6.0f), new Compresor.Ajuste(-37.1f, 1.3f, 3.0f, 70.0f, 6.0f), 2.0f, 0.03f, 0.0f, 18000.0f, 0.3f, 0.0f, 0.0f, -12.49f, -0.3f, 5.0f, 60.0f);
    }

    private static Preset base_equilibrado() {
        return new Preset("base_equilibrado", new double[]{22.4d, 28.3d, 35.6d, 44.9d, 56.6d, 71.3d, 89.8d, 113.1d, 142.5d, 179.6d, 226.3d, 285.1d, 359.2d, 452.5d, 570.2d, 718.4d, 905.1d, 1140.4d, 1436.8d, 1810.2d, 2280.7d, 2873.5d, 3620.4d, 4561.4d, 5747.0d, 7240.8d, 9122.8d, 11494.0d, 14481.5d}, new double[]{12.8d, 6.2d, 3.2d, 0.6d, -0.6d, -1.3d, -1.7d, -1.2d, -0.9d, -0.7d, -1.5d, -0.9d, -1.3d, -1.4d, -0.7d, -0.6d, -0.4d, -0.4d, 0.1d, 0.1d, -1.1d, -0.1d, 0.6d, 1.6d, 2.8d, 3.6d, 4.2d, 4.9d, 5.5d}, 45.0f, 1.0f, 250.0f, 3000.0f, new Compresor.Ajuste(-20.3f, 1.1f, 15.0f, 180.0f, 6.0f), new Compresor.Ajuste(-23.3f, 1.4f, 8.0f, 120.0f, 6.0f), new Compresor.Ajuste(-33.2f, 1.5f, 3.0f, 70.0f, 6.0f), 3.0f, 0.06f, 0.0f, 17000.0f, 0.5f, 0.0f, 0.0f, -13.02f, -0.3f, 5.0f, 60.0f);
    }

    private static Preset base_film() {
        return new Preset("base_film", new double[]{22.4d, 28.3d, 35.6d, 44.9d, 56.6d, 71.3d, 89.8d, 113.1d, 142.5d, 179.6d, 226.3d, 285.1d, 359.2d, 452.5d, 570.2d, 718.4d, 905.1d, 1140.4d, 1436.8d, 1810.2d, 2280.7d, 2873.5d, 3620.4d, 4561.4d, 5747.0d, 7240.8d, 9122.8d, 11494.0d, 14481.5d}, new double[]{-18.0d, -18.0d, -5.5d, -1.6d, 1.0d, 2.3d, 1.5d, 1.1d, 1.0d, 0.7d, 0.6d, 0.5d, 0.5d, 0.4d, 0.4d, 0.4d, 0.1d, 0.2d, 0.3d, 0.2d, 0.5d, 1.0d, 1.8d, 2.9d, 4.2d, 6.2d, 9.0d, 13.5d, 17.0d}, 0.0f, 1.0f, 250.0f, 3000.0f, new Compresor.Ajuste(-23.1f, 1.05f, 15.0f, 180.0f, 6.0f), new Compresor.Ajuste(-25.0f, 1.11f, 8.0f, 120.0f, 6.0f), new Compresor.Ajuste(-50.2f, 1.05f, 3.0f, 70.0f, 6.0f), 10.0f, 0.3f, 0.2f, 9000.0f, 0.0f, 0.0f, 0.0f, -14.09f, -0.3f, 5.0f, 60.0f);
    }

    private static Preset base_neutra() {
        return new Preset("base_neutra", new double[]{22.4d, 28.3d, 35.6d, 44.9d, 56.6d, 71.3d, 89.8d, 113.1d, 142.5d, 179.6d, 226.3d, 285.1d, 359.2d, 452.5d, 570.2d, 718.4d, 905.1d, 1140.4d, 1436.8d, 1810.2d, 2280.7d, 2873.5d, 3620.4d, 4561.4d, 5747.0d, 7240.8d, 9122.8d, 11494.0d, 14481.5d}, new double[]{0.4d, -0.5d, -0.3d, -1.2d, -0.2d, -0.7d, 0.0d, -0.1d, 0.4d, 0.7d, 1.0d, 0.6d, -0.3d, -0.9d, 0.2d, 0.5d, -0.0d, -0.1d, -0.3d, -1.2d, -1.1d, -1.5d, -1.5d, -2.2d, -0.6d, -0.3d, -0.0d, 0.3d, 0.8d}, 0.0f, 1.0f, 250.0f, 3000.0f, new Compresor.Ajuste(-25.8f, 1.19f, 15.0f, 180.0f, 6.0f), new Compresor.Ajuste(-26.9f, 1.23f, 8.0f, 120.0f, 6.0f), new Compresor.Ajuste(-39.9f, 1.14f, 3.0f, 70.0f, 6.0f), 2.0f, 0.05f, 0.0f, 16000.0f, 0.0f, 0.0f, 0.0f, -12.06f, -0.3f, 5.0f, 60.0f);
    }

    private static Preset base_potente() {
        return new Preset("base_potente", new double[]{22.4d, 28.3d, 35.6d, 44.9d, 56.6d, 71.3d, 89.8d, 113.1d, 142.5d, 179.6d, 226.3d, 285.1d, 359.2d, 452.5d, 570.2d, 718.4d, 905.1d, 1140.4d, 1436.8d, 1810.2d, 2280.7d, 2873.5d, 3620.4d, 4561.4d, 5747.0d, 7240.8d, 9122.8d, 11494.0d, 14481.5d}, new double[]{18.0d, 16.7d, 12.0d, 8.1d, 5.4d, 4.6d, 3.9d, 3.0d, 1.5d, 1.0d, -1.8d, -0.5d, -0.6d, -0.8d, -0.2d, 0.1d, 0.1d, 1.2d, 2.6d, 2.4d, 4.5d, 6.0d, 8.2d, 10.2d, 12.4d, 14.1d, 15.5d, 18.0d, 18.0d}, 45.0f, 1.0f, 250.0f, 3000.0f, new Compresor.Ajuste(-28.4f, 1.2f, 15.0f, 180.0f, 6.0f), new Compresor.Ajuste(-25.6f, 1.32f, 8.0f, 120.0f, 6.0f), new Compresor.Ajuste(-39.0f, 1.28f, 3.0f, 70.0f, 6.0f), 6.0f, 0.12f, 0.05f, 16000.0f, 6.5f, 0.0f, 0.0f, -10.76f, -0.3f, 5.0f, 60.0f);
    }

    private static Preset base_retro() {
        return new Preset("base_retro", new double[]{22.4d, 28.3d, 35.6d, 44.9d, 56.6d, 71.3d, 89.8d, 113.1d, 142.5d, 179.6d, 226.3d, 285.1d, 359.2d, 452.5d, 570.2d, 718.4d, 905.1d, 1140.4d, 1436.8d, 1810.2d, 2280.7d, 2873.5d, 3620.4d, 4561.4d, 5747.0d, 7240.8d, 9122.8d, 11494.0d, 14481.5d}, new double[]{-2.0d, -1.2d, -1.0d, -1.3d, -2.0d, -1.8d, -1.5d, -1.2d, -1.1d, -1.0d, -0.3d, 0.2d, 0.5d, 0.6d, 0.6d, 0.4d, 0.0d, -0.4d, -0.7d, -1.4d, -1.5d, -0.7d, 1.3d, 4.8d, 8.8d, 11.7d, 13.7d, 17.1d, 18.0d}, 0.0f, 1.0f, 250.0f, 3000.0f, new Compresor.Ajuste(-15.9f, 1.17f, 15.0f, 180.0f, 6.0f), new Compresor.Ajuste(-27.0f, 1.26f, 8.0f, 120.0f, 6.0f), new Compresor.Ajuste(-44.1f, 1.47f, 3.0f, 70.0f, 6.0f), 6.0f, 0.18f, 0.15f, 12500.0f, 0.2f, 0.0f, 0.0f, -12.41f, -0.3f, 5.0f, 60.0f);
    }

    private static Preset voz_clara() {
        return new Preset("voz_clara", new double[]{22.4d, 28.3d, 35.6d, 44.9d, 56.6d, 71.3d, 89.8d, 113.1d, 142.5d, 179.6d, 226.3d, 285.1d, 359.2d, 452.5d, 570.2d, 718.4d, 905.1d, 1140.4d, 1436.8d, 1810.2d, 2280.7d, 2873.5d, 3620.4d, 4561.4d, 5747.0d, 7240.8d, 9122.8d, 11494.0d, 14481.5d}, new double[]{-18.0d, -18.0d, -12.0d, -8.0d, -4.0d, -2.0d, -1.0d, -0.5d, 0.0d, -0.5d, -1.5d, -1.5d, -1.0d, -0.5d, 0.0d, 0.2d, 0.3d, 0.5d, 0.8d, 1.2d, 1.8d, 2.2d, 2.2d, 2.0d, 1.5d, 0.8d, -0.5d, -2.0d, -3.0d}, 90.0f, 0.65f, 250.0f, 3000.0f, new Compresor.Ajuste(-30.0f, 1.6f, 20.0f, 200.0f, 6.0f), new Compresor.Ajuste(-26.0f, 1.9f, 10.0f, 150.0f, 6.0f), new Compresor.Ajuste(-34.0f, 1.7f, 5.0f, 90.0f, 6.0f), 1.0f, 0.0f, 0.0f, 16000.0f, 0.0f, 0.0f, 0.0f, -16.0f, -1.0f, 5.0f, 60.0f);
    }

    private static Preset podcast() {
        return new Preset("podcast", new double[]{22.4d, 28.3d, 35.6d, 44.9d, 56.6d, 71.3d, 89.8d, 113.1d, 142.5d, 179.6d, 226.3d, 285.1d, 359.2d, 452.5d, 570.2d, 718.4d, 905.1d, 1140.4d, 1436.8d, 1810.2d, 2280.7d, 2873.5d, 3620.4d, 4561.4d, 5747.0d, 7240.8d, 9122.8d, 11494.0d, 14481.5d}, new double[]{-18.0d, -18.0d, -14.0d, -9.0d, -5.0d, -2.5d, -1.2d, -0.5d, 0.0d, -0.8d, -2.0d, -2.2d, -1.6d, -1.0d, -0.2d, 0.4d, 0.8d, 1.2d, 1.6d, 2.2d, 2.8d, 3.2d, 3.0d, 2.6d, 2.0d, 1.2d, -0.5d, -2.5d, -4.0d}, 80.0f, 0.8f, 250.0f, 3000.0f, new Compresor.Ajuste(-30.0f, 1.7f, 20.0f, 180.0f, 6.0f), new Compresor.Ajuste(-24.0f, 2.6f, 8.0f, 120.0f, 6.0f), new Compresor.Ajuste(-32.0f, 2.2f, 4.0f, 80.0f, 6.0f), 1.5f, 0.05f, 0.05f, 15000.0f, 0.0f, 0.0f, 0.0f, -16.0f, -1.0f, 5.0f, 60.0f);
    }
}
