package es.pitmasterai.masterlab;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.LinearGradient;
import android.graphics.Paint;
import android.graphics.RectF;
import android.graphics.Shader;
import android.view.MotionEvent;
import android.view.View;

/* loaded from: classes.dex */
public class OndaSonido extends View {
    private AlTocar escucha;
    private float[] picos;
    private final Paint pincelBarra;
    private final Paint pincelCero;
    private final Paint pincelFondo;
    private final Paint pincelHecho;
    private final Paint pincelMarco;
    private final Paint pincelSaturado;
    private final Paint pincelTope;
    private float progreso;

    /* loaded from: classes.dex */
    public interface AlTocar {
        void alArrastrar(float f);

        void alBuscar(float f);

        void alSoltar(float f);
    }

    public OndaSonido(Context context) {
        super(context);
        this.picos = new float[0];
        this.progreso = 0.0f;
        Paint paint = new Paint(1);
        this.pincelFondo = paint;
        Paint paint2 = new Paint(1);
        this.pincelSaturado = paint2;
        Paint paint3 = new Paint(1);
        this.pincelHecho = paint3;
        Paint paint4 = new Paint(1);
        this.pincelBarra = paint4;
        Paint paint5 = new Paint(1);
        this.pincelCero = paint5;
        Paint paint6 = new Paint(1);
        this.pincelTope = paint6;
        Paint paint7 = new Paint(1);
        this.pincelMarco = paint7;
        paint.setColor(-12961198);
        paint3.setShader(new LinearGradient(0.0f, 0.0f, 0.0f, 1.0f, Estilo.ROSA, Estilo.VIOLETA, Shader.TileMode.CLAMP));
        paint3.setColor(Estilo.ROSA);
        paint4.setColor(1728053247);
        paint2.setColor(-53931);
        paint7.setColor(1040187391);
        paint7.setStyle(Paint.Style.STROKE);
        paint7.setStrokeWidth(2.0f);
        paint5.setColor(1442840575);
        paint5.setStrokeWidth(1.5f);
        paint6.setColor(872415231);
        paint6.setStrokeWidth(1.0f);
    }

    public void setEscucha(AlTocar alTocar) {
        this.escucha = alTocar;
    }

    public void setPicos(float[] fArr) {
        if (fArr == null) {
            fArr = new float[0];
        }
        this.picos = fArr;
        invalidate();
    }

    public void setProgreso(float f) {
        this.progreso = Math.max(0.0f, Math.min(1.0f, f));
        invalidate();
    }

    @Override // android.view.View
    protected void onDraw(Canvas canvas) {
        int i;
        float max;
        super.onDraw(canvas);
        int width = getWidth();
        int height = getHeight();
        if (width <= 0 || height <= 0) {
            return;
        }
        float f = height;
        float f2 = f / 2.0f;
        float f3 = f2 - 6.0f;
        if (f3 < 4.0f) {
            f3 = 4.0f;
        }
        float f4 = f3 / 1.25f;
        float f5 = width;
        canvas.drawRect(0.0f, f2 - 1.0f, f5, f2 + 1.0f, this.pincelCero);
        canvas.drawRoundRect(1.0f, 1.0f, f5 - 1.0f, f - 1.0f, 10.0f, 10.0f, this.pincelMarco);
        float[] fArr = this.picos;
        int max2 = Math.max(24, Math.min(fArr.length == 0 ? 64 : fArr.length, width / 2));
        float f6 = max2;
        float f7 = f5 / f6;
        float max3 = Math.max(1.2f, 0.62f * f7);
        float f8 = max3 / 2.0f;
        float f9 = f5 * this.progreso;
        RectF rectF = new RectF();
        int i2 = 0;
        while (i2 < max2) {
            if (this.picos.length == 0) {
                max = 0.15f;
                i = max2;
            } else {
                int length = (int) ((i2 / f6) * this.picos.length);
                int max4 = Math.max(length + 1, (int) (((i2 + 1) / f6) * this.picos.length));
                float f10 = 0.0f;
                while (true) {
                    if (length >= max4) {
                        i = max2;
                        break;
                    }
                    float[] fArr2 = this.picos;
                    i = max2;
                    if (length >= fArr2.length) {
                        break;
                    }
                    float f11 = fArr2[length];
                    if (f11 > f10) {
                        f10 = f11;
                    }
                    length++;
                    max2 = i;
                }
                max = Math.max(0.01f, Math.min(1.6f, f10));
            }
            float f12 = max * f4;
            if (f12 < 1.0f) {
                f12 = 1.0f;
            }
            if (f12 > f) {
                f12 = f;
            }
            float f13 = (i2 * f7) + ((f7 - max3) / 2.0f);
            rectF.set(f13, f2 - f12, f13 + max3, f12 + f2);
            canvas.drawRoundRect(rectF, f8, f8, ((f13 + f8) > f9 ? 1 : ((f13 + f8) == f9 ? 0 : -1)) <= 0 ? this.pincelHecho : this.pincelFondo);
            i2++;
            max2 = i;
        }
        float f14 = this.progreso;
        if (f14 <= 0.0f || f14 >= 1.0f) {
            return;
        }
        canvas.drawRect(f9 - 1.0f, 0.0f, f9 + 1.0f, f, this.pincelBarra);
    }

    @Override // android.view.View
    public boolean onTouchEvent(MotionEvent motionEvent) {
        float x = motionEvent.getX() / Math.max(1.0f, getWidth());
        if (x < 0.0f) {
            x = 0.0f;
        }
        float f = x <= 1.0f ? x : 1.0f;
        int action = motionEvent.getAction();
        if (action != 0) {
            if (action != 1) {
                if (action != 2) {
                    if (action != 3) {
                        return super.onTouchEvent(motionEvent);
                    }
                }
            }
            setProgreso(f);
            AlTocar alTocar = this.escucha;
            if (alTocar != null) {
                alTocar.alSoltar(f);
            }
            return true;
        }
        setProgreso(f);
        AlTocar alTocar2 = this.escucha;
        if (alTocar2 != null) {
            alTocar2.alArrastrar(f);
        }
        return true;
    }
}
