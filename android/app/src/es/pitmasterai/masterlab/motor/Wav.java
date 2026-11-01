package es.pitmasterai.masterlab.motor;

import java.io.Closeable;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.lang.reflect.Array;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;

public final class Wav {

    
    public static final class Datos {
        public final int frecuencia;
        public final float[][] muestras;

        public Datos(float[][] fArr, int i) {
            this.muestras = fArr;
            this.frecuencia = i;
        }

        public int canales() {
            return this.muestras.length;
        }

        public int tramas() {
            return this.muestras[0].length;
        }
    }

    
    
    

    
    public static Datos leer(String ruta) throws IOException {
        FileInputStream entrada = new FileInputStream(new File(ruta));
        try {
            byte[] cabecera = new byte[12];
            if (leerTodo(entrada, cabecera, 12) != 12) throw new IOException("archivo vacio");
            if (!"RIFF".equals(new String(cabecera, 0, 4, "US-ASCII"))
                    || !"WAVE".equals(new String(cabecera, 8, 4, "US-ASCII"))) {
                throw new IOException("no es un WAV");
            }
            int formato = 1;
            int canales = 2;
            long frecuencia = 48000;
            int bits = 16;
            long datos = -1;
            byte[] bloque = new byte[8];
            while (leerTodo(entrada, bloque, 8) == 8) {
                String id = new String(bloque, 0, 4, "US-ASCII");
                int tam = ByteBuffer.wrap(bloque, 4, 4).order(ByteOrder.LITTLE_ENDIAN).getInt();
                if ("fmt ".equals(id)) {
                    byte[] cuerpoCab = new byte[Math.min(tam, 40)];
                    int leidos = leerTodo(entrada, cuerpoCab, cuerpoCab.length);
                    ByteBuffer f = ByteBuffer.wrap(cuerpoCab, 0, leidos).order(ByteOrder.LITTLE_ENDIAN);
                    int etiqueta = f.getShort() & 0xffff;
                    canales = f.getShort() & 0xffff;
                    frecuencia = f.getInt() & 0xffffffffL;
                    f.getInt();
                    f.getShort();
                    bits = f.getShort() & 0xffff;
                    formato = etiqueta;
                    if (etiqueta == 0xFFFE && leidos >= 26) {
                        f.position(24);
                        formato = f.getShort() & 0xffff;
                    }
                    saltar(entrada, tam - leidos);
                } else if ("data".equals(id)) {
                    datos = tam & 0xffffffffL;
                    break;
                } else {
                    saltar(entrada, tam + (tam & 1));
                }
            }
            if (datos <= 0) throw new IOException("el WAV no tiene datos");
            if (canales <= 0) canales = 1;
            int marco = Math.max(1, (bits / 8) * canales);
            int tramas = (int) (datos / marco);
            float[][] muestras = new float[canales][tramas];
            byte[] trozo = new byte[marco * 4096];
            int hechas = 0;
            while (hechas < tramas) {
                int pedir = Math.min(4096, tramas - hechas) * marco;
                int leidos = leerTodo(entrada, trozo, pedir);
                if (leidos < marco) break;
                int cuantas = leidos / marco;
                ByteBuffer b = ByteBuffer.wrap(trozo, 0, leidos).order(ByteOrder.LITTLE_ENDIAN);
                for (int i2 = 0; i2 < cuantas; i2++) {
                    for (int c = 0; c < canales; c++) {
                        float v;
                        if (formato == 3 && bits == 32) {
                            v = b.getFloat();
                        } else if (formato == 3 && bits == 64) {
                            v = (float) b.getDouble();
                        } else if (bits == 8) {
                            v = ((b.get() & 0xff) - 128) / 128.0f;
                        } else if (bits == 16) {
                            v = b.getShort() / 32768.0f;
                        } else if (bits == 24) {
                            int lo = b.get() & 0xff;
                            int me = b.get() & 0xff;
                            int hi = b.get();
                            v = (lo | (me << 8) | (hi << 16)) / 8388608.0f;
                        } else {
                            v = (float) (b.getInt() / 2147483648.0);
                        }
                        muestras[c][hechas + i2] = v;
                    }
                }
                hechas += cuantas;
            }
            if (hechas < tramas) {
                float[][] recortado = new float[canales][hechas];
                for (int c = 0; c < canales; c++) {
                    System.arraycopy(muestras[c], 0, recortado[c], 0, hechas);
                }
                muestras = recortado;
            }
            return new Datos(muestras, (int) frecuencia);
        } finally {
            try {
                entrada.close();
            } catch (IOException ignored) {
            }
        }
    }

    private static int leerTodo(java.io.InputStream in, byte[] destino, int cuantos) throws IOException {
        int total = 0;
        while (total < cuantos) {
            int leidos = in.read(destino, total, cuantos - total);
            if (leidos <= 0) break;
            total += leidos;
        }
        return total;
    }

    private static void saltar(java.io.InputStream in, long cuantos) throws IOException {
        long resto = cuantos;
        while (resto > 0) {
            long saltados = in.skip(resto);
            if (saltados <= 0) {
                if (in.read() < 0) break;
                saltados = 1;
            }
            resto -= saltados;
        }
    }

    public static void escribir(String str, float[][] fArr, int i) throws IOException {
        FileOutputStream fileOutputStream = new FileOutputStream(new File(str));
        try {
            escribirEn(fileOutputStream, fArr, i);
        } finally {
            fileOutputStream.close();
        }
    }

    public static void escribirEn(OutputStream outputStream, float[][] fArr, int i) throws IOException {
        int length = fArr.length;
        int length2 = fArr[0].length;
        int i2 = length * 3;
        ByteBuffer order = ByteBuffer.allocate(44).order(ByteOrder.LITTLE_ENDIAN);
        order.put("RIFF".getBytes("US-ASCII"));
        int i3 = length2 * i2;
        order.putInt(i3 + 36);
        order.put("WAVE".getBytes("US-ASCII"));
        order.put("fmt ".getBytes("US-ASCII"));
        order.putInt(16);
        order.putShort((short) 1);
        order.putShort((short) length);
        order.putInt(i);
        order.putInt(i * i2);
        order.putShort((short) i2);
        order.putShort((short) 24);
        order.put("data".getBytes("US-ASCII"));
        order.putInt(i3);
        outputStream.write(order.array());
        ByteBuffer order2 = ByteBuffer.allocate(i2 * 4096).order(ByteOrder.LITTLE_ENDIAN);
        int i4 = 0;
        for (int i5 = 0; i5 < length2; i5++) {
            for (float[] fArr2 : fArr) {
                float f = fArr2[i5];
                if (f > 1.0f) {
                    f = 1.0f;
                }
                if (f < -1.0f) {
                    f = -1.0f;
                }
                int round = Math.round(f * 8388607.0f);
                order2.put((byte) (round & 255));
                order2.put((byte) ((round >> 8) & 255));
                order2.put((byte) ((round >> 16) & 255));
            }
            i4++;
            if (i4 == 4096) {
                outputStream.write(order2.array(), 0, order2.position());
                order2.clear();
                i4 = 0;
            }
        }
        if (order2.position() > 0) {
            outputStream.write(order2.array(), 0, order2.position());
        }
        outputStream.flush();
    }

    
    public static final class Escritor implements Closeable {
        private final ByteBuffer bloque;
        private final int canales;
        private int enBloque;
        private final OutputStream salida;

        public Escritor(String str, int i, int i2, long j) throws IOException {
            this.canales = i;
            int i3 = i * 3;
            long j2 = j * i3;
            ByteBuffer order = ByteBuffer.allocate(44).order(ByteOrder.LITTLE_ENDIAN);
            order.put("RIFF".getBytes("US-ASCII"));
            order.putInt((int) Math.min(36 + j2, 2147483647L));
            order.put("WAVE".getBytes("US-ASCII"));
            order.put("fmt ".getBytes("US-ASCII"));
            order.putInt(16);
            order.putShort((short) 1);
            order.putShort((short) i);
            order.putInt(i2);
            order.putInt(i2 * i3);
            order.putShort((short) i3);
            order.putShort((short) 24);
            order.put("data".getBytes("US-ASCII"));
            order.putInt((int) Math.min(j2, 2147483647L));
            FileOutputStream fileOutputStream = new FileOutputStream(new File(str));
            this.salida = fileOutputStream;
            fileOutputStream.write(order.array());
            this.bloque = ByteBuffer.allocate(i3 * 4096).order(ByteOrder.LITTLE_ENDIAN);
        }

        public void escribir(float[][] fArr, int i, int i2) throws IOException {
            while (i < i2) {
                for (int i3 = 0; i3 < this.canales; i3++) {
                    float f = fArr[i3][i];
                    if (f > 1.0f) {
                        f = 1.0f;
                    }
                    if (f < -1.0f) {
                        f = -1.0f;
                    }
                    int round = Math.round(f * 8388607.0f);
                    this.bloque.put((byte) (round & 255));
                    this.bloque.put((byte) ((round >> 8) & 255));
                    this.bloque.put((byte) ((round >> 16) & 255));
                }
                int i4 = this.enBloque + 1;
                this.enBloque = i4;
                if (i4 == 4096) {
                    this.salida.write(this.bloque.array(), 0, this.bloque.position());
                    this.bloque.clear();
                    this.enBloque = 0;
                }
                i++;
            }
        }

        @Override 
        public void close() throws IOException {
            if (this.bloque.position() > 0) {
                this.salida.write(this.bloque.array(), 0, this.bloque.position());
            }
            this.bloque.clear();
            this.enBloque = 0;
            this.salida.flush();
            this.salida.close();
        }
    }
}
