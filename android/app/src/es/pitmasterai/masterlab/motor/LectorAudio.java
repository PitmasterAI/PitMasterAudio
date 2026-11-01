package es.pitmasterai.masterlab.motor;

import android.content.Context;
import android.media.MediaCodec;
import android.media.MediaExtractor;
import android.media.MediaFormat;
import android.net.Uri;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.ArrayList;

public final class LectorAudio {

    
    public static final class Info {
        public final int frecuencia;
        public final int canales;
        public final double segundos;

        Info(int frecuencia, int canales, double segundos) {
            this.frecuencia = frecuencia;
            this.canales = canales;
            this.segundos = segundos;
        }
    }

    private LectorAudio() {
    }

    
    public static Info info(Context ctx, Uri uri) throws Exception {
        MediaExtractor extractor = new MediaExtractor();
        try {
            extractor.setDataSource(ctx, uri, null);
            MediaFormat formato = pistaAudio(extractor);
            if (formato == null) throw new IOException("el archivo no tiene audio");
            int frecuencia = formato.getInteger(MediaFormat.KEY_SAMPLE_RATE);
            int canales = formato.containsKey(MediaFormat.KEY_CHANNEL_COUNT)
                    ? formato.getInteger(MediaFormat.KEY_CHANNEL_COUNT) : 2;
            double segundos = formato.containsKey(MediaFormat.KEY_DURATION)
                    ? formato.getLong(MediaFormat.KEY_DURATION) / 1000000.0 : 0.0;
            return new Info(frecuencia, canales, segundos);
        } finally {
            extractor.release();
        }
    }

    private static MediaFormat pistaAudio(MediaExtractor extractor) {
        for (int i = 0; i < extractor.getTrackCount(); i++) {
            MediaFormat f = extractor.getTrackFormat(i);
            String mime = f.getString(MediaFormat.KEY_MIME);
            if (mime != null && mime.startsWith("audio/")) {
                extractor.selectTrack(i);
                return f;
            }
        }
        return null;
    }

    

    public static Wav.Datos leerTramo(Context ctx, Uri uri, double desdeSeg, double hastaSeg)
            throws Exception {
        MediaExtractor extractor = new MediaExtractor();
        MediaCodec codec = null;
        try {
            extractor.setDataSource(ctx, uri, null);
            MediaFormat formato = pistaAudio(extractor);
            if (formato == null) throw new IOException("el archivo no tiene audio");
            int frecuencia = formato.getInteger(MediaFormat.KEY_SAMPLE_RATE);
            int canales = formato.containsKey(MediaFormat.KEY_CHANNEL_COUNT)
                    ? formato.getInteger(MediaFormat.KEY_CHANNEL_COUNT) : 2;
            String mime = formato.getString(MediaFormat.KEY_MIME);

            long desdeUs = (long) (Math.max(0, desdeSeg) * 1000000.0);
            long hastaUs = (long) (Math.max(desdeSeg, hastaSeg) * 1000000.0);
            extractor.seekTo(desdeUs, MediaExtractor.SEEK_TO_PREVIOUS_SYNC);

            codec = MediaCodec.createDecoderByType(mime);
            codec.configure(formato, null, null, 0);
            codec.start();

            ArrayList<float[][]> trozos = new ArrayList<float[][]>();
            int total = 0;
            MediaCodec.BufferInfo info = new MediaCodec.BufferInfo();
            boolean entradaTerminada = false;
            boolean salidaTerminada = false;
            while (!salidaTerminada) {
                if (!entradaTerminada) {
                    int entrada = codec.dequeueInputBuffer(10000);
                    if (entrada >= 0) {
                        ByteBuffer buffer = codec.getInputBuffer(entrada);
                        int tam = extractor.readSampleData(buffer, 0);
                        if (tam < 0 || extractor.getSampleTime() > hastaUs) {
                            codec.queueInputBuffer(entrada, 0, 0, 0,
                                    MediaCodec.BUFFER_FLAG_END_OF_STREAM);
                            entradaTerminada = true;
                        } else {
                            codec.queueInputBuffer(entrada, 0, tam, extractor.getSampleTime(), 0);
                            extractor.advance();
                        }
                    }
                }
                int salida = codec.dequeueOutputBuffer(info, 10000);
                if (salida >= 0) {
                    ByteBuffer buffer = codec.getOutputBuffer(salida);
                    if (buffer != null && info.size > 0) {
                        buffer.position(info.offset);
                        buffer.limit(info.offset + info.size);
                        int tramas = info.size / (2 * canales);
                        double t = info.presentationTimeUs / 1000000.0;
                        int desde = (int) Math.max(0, Math.round((desdeSeg - t) * frecuencia));
                        int hasta = (int) Math.min(tramas, Math.round((hastaSeg - t) * frecuencia));
                        if (hasta > desde) {
                            ByteBuffer leible = buffer.order(ByteOrder.LITTLE_ENDIAN);
                            leible.position(info.offset + desde * 2 * canales);
                            int cuantas = hasta - desde;
                            float[][] trozo = new float[canales][cuantas];
                            for (int i = 0; i < cuantas; i++) {
                                for (int c = 0; c < canales; c++) {
                                    trozo[c][i] = leible.getShort() / 32768.0f;
                                }
                            }
                            trozos.add(trozo);
                            total += cuantas;
                        }
                        if (t >= hastaSeg) salidaTerminada = true;
                    }
                    codec.releaseOutputBuffer(salida, false);
                    if ((info.flags & MediaCodec.BUFFER_FLAG_END_OF_STREAM) != 0) salidaTerminada = true;
                } else if (salida == MediaCodec.INFO_TRY_AGAIN_LATER) {
                    if (entradaTerminada) break;
                }
            }

            float[][] muestras = new float[canales][total];
            int pos = 0;
            for (float[][] trozo : trozos) {
                int tramas = trozo[0].length;
                for (int c = 0; c < canales; c++) {
                    System.arraycopy(trozo[c], 0, muestras[c], pos, tramas);
                }
                pos += tramas;
            }
            return new Wav.Datos(muestras, frecuencia);
        } finally {
            if (codec != null) {
                try {
                    codec.stop();
                } catch (Exception ignorado) {
                }
                codec.release();
            }
            extractor.release();
        }
    }

    
    public static Wav.Datos leer(Context ctx, Uri uri) throws Exception {
        File temporal = File.createTempFile("masterlab_entrada", ".wav", ctx.getCacheDir());
        try {
            copiar(ctx, uri, temporal);
            try {
                return Wav.leer(temporal.getAbsolutePath());
            } catch (IOException noEsWav) {
                return decodificar(ctx, uri);
            }
        } finally {
            temporal.delete();
        }
    }

    private static void copiar(Context ctx, Uri uri, File destino) throws IOException {
        InputStream in = ctx.getContentResolver().openInputStream(uri);
        if (in == null) throw new IOException("no se puede abrir el archivo");
        OutputStream out = new FileOutputStream(destino);
        byte[] buffer = new byte[1 << 16];
        int leidos;
        while ((leidos = in.read(buffer)) > 0) out.write(buffer, 0, leidos);
        in.close();
        out.close();
    }

    private static Wav.Datos decodificar(Context ctx, Uri uri) throws Exception {
        MediaExtractor extractor = new MediaExtractor();
        MediaCodec codec = null;
        try {
            extractor.setDataSource(ctx, uri, null);
            MediaFormat formato = pistaAudio(extractor);
            if (formato == null) throw new IOException("el archivo no tiene audio");
            int frecuencia = formato.getInteger(MediaFormat.KEY_SAMPLE_RATE);
            int canales = formato.containsKey(MediaFormat.KEY_CHANNEL_COUNT)
                    ? formato.getInteger(MediaFormat.KEY_CHANNEL_COUNT) : 2;
            String mime = formato.getString(MediaFormat.KEY_MIME);

            codec = MediaCodec.createDecoderByType(mime);
            codec.configure(formato, null, null, 0);
            codec.start();

            ArrayList<float[][]> trozos = new ArrayList<float[][]>();
            int total = 0;
            MediaCodec.BufferInfo info = new MediaCodec.BufferInfo();
            boolean entradaTerminada = false;
            boolean salidaTerminada = false;
            while (!salidaTerminada) {
                if (!entradaTerminada) {
                    int entrada = codec.dequeueInputBuffer(10000);
                    if (entrada >= 0) {
                        ByteBuffer buffer = codec.getInputBuffer(entrada);
                        int tam = extractor.readSampleData(buffer, 0);
                        if (tam < 0) {
                            codec.queueInputBuffer(entrada, 0, 0, 0,
                                    MediaCodec.BUFFER_FLAG_END_OF_STREAM);
                            entradaTerminada = true;
                        } else {
                            codec.queueInputBuffer(entrada, 0, tam, extractor.getSampleTime(), 0);
                            extractor.advance();
                        }
                    }
                }
                int salida = codec.dequeueOutputBuffer(info, 10000);
                if (salida >= 0) {
                    ByteBuffer buffer = codec.getOutputBuffer(salida);
                    if (buffer != null && info.size > 0) {
                        buffer.position(info.offset);
                        buffer.limit(info.offset + info.size);
                        int tramas = info.size / (2 * canales);
                        float[][] trozo = new float[canales][tramas];
                        ByteBuffer leible = buffer.order(ByteOrder.LITTLE_ENDIAN);
                        for (int i = 0; i < tramas; i++) {
                            for (int c = 0; c < canales; c++) {
                                trozo[c][i] = leible.getShort() / 32768.0f;
                            }
                        }
                        trozos.add(trozo);
                        total += tramas;
                    }
                    codec.releaseOutputBuffer(salida, false);
                    if ((info.flags & MediaCodec.BUFFER_FLAG_END_OF_STREAM) != 0) salidaTerminada = true;
                } else if (salida == MediaCodec.INFO_TRY_AGAIN_LATER) {
                    if (entradaTerminada) break;
                }
            }

            float[][] muestras = new float[canales][total];
            int pos = 0;
            for (float[][] trozo : trozos) {
                int tramas = trozo[0].length;
                for (int c = 0; c < canales; c++) {
                    System.arraycopy(trozo[c], 0, muestras[c], pos, tramas);
                }
                pos += tramas;
            }
            return new Wav.Datos(muestras, frecuencia);
        } finally {
            if (codec != null) {
                try {
                    codec.stop();
                } catch (Exception ignorado) {
                }
                codec.release();
            }
            extractor.release();
        }
    }
}
