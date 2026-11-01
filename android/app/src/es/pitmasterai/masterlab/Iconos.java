package es.pitmasterai.masterlab;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import android.graphics.drawable.AnimationDrawable;
import android.graphics.drawable.BitmapDrawable;

/* loaded from: classes.dex */
public final class Iconos {
    private static int dp(Context context, float f) {
        return (int) (f * context.getResources().getDisplayMetrics().density);
    }

    public static BitmapDrawable visto(Context context, int i) {
        int dp = dp(context, 18.0f);
        Bitmap createBitmap = Bitmap.createBitmap(dp, dp, Bitmap.Config.ARGB_8888);
        Canvas canvas = new Canvas(createBitmap);
        Paint paint = new Paint(1);
        paint.setColor(i);
        paint.setStyle(Paint.Style.STROKE);
        paint.setStrokeWidth(dp(context, 2.4f));
        paint.setStrokeCap(Paint.Cap.ROUND);
        Path path = new Path();
        float f = dp;
        path.moveTo(0.16f * f, 0.55f * f);
        path.lineTo(0.42f * f, 0.8f * f);
        path.lineTo(0.86f * f, f * 0.24f);
        canvas.drawPath(path, paint);
        return new BitmapDrawable(context.getResources(), createBitmap);
    }

    public static AnimationDrawable giro(Context context, int i) {
        AnimationDrawable animationDrawable = new AnimationDrawable();
        int dp = dp(context, 18.0f);
        for (int i2 = 0; i2 < 12; i2++) {
            Bitmap createBitmap = Bitmap.createBitmap(dp, dp, Bitmap.Config.ARGB_8888);
            Canvas canvas = new Canvas(createBitmap);
            Paint paint = new Paint(1);
            paint.setStyle(Paint.Style.STROKE);
            paint.setStrokeWidth(dp(context, 2.2f));
            paint.setStrokeCap(Paint.Cap.ROUND);
            RectF rectF = new RectF(dp(context, 2.0f), dp(context, 2.0f), dp - dp(context, 2.0f), dp - dp(context, 2.0f));
            for (int i3 = 0; i3 < 4; i3++) {
                paint.setColor(Color.argb(Math.max(255 - (i3 * 55), 40), Color.red(i), Color.green(i), Color.blue(i)));
                canvas.drawArc(rectF, (((i3 * 3) + i2) % 12) * 30, 24.0f, false, paint);
            }
            animationDrawable.addFrame(new BitmapDrawable(context.getResources(), createBitmap), 70);
        }
        animationDrawable.setOneShot(false);
        return animationDrawable;
    }
}
