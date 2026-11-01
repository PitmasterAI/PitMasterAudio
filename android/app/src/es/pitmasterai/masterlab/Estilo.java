package es.pitmasterai.masterlab;

import android.content.Context;
import android.graphics.drawable.GradientDrawable;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

/* loaded from: classes.dex */
public final class Estilo {
    public static final int BORDE = -14013894;
    public static final int CIAN = -14494738;
    public static final int FONDO = -16119280;
    public static final int NARANJA = -429290;
    public static final int ROSA = -1897635;
    public static final int SUAVE = -6643532;
    public static final int TARJETA = -15395553;
    public static final int TEXTO = -723718;
    public static final int VERDE = -15681151;
    public static final int VIOLETA = -8635667;

    public static GradientDrawable redondeado(int i, float f, int i2, int i3) {
        GradientDrawable gradientDrawable = new GradientDrawable();
        gradientDrawable.setColor(i);
        gradientDrawable.setCornerRadius(f);
        if (i2 > 0) {
            gradientDrawable.setStroke(i2, i3);
        }
        return gradientDrawable;
    }

    public static LinearLayout tarjeta(Context context) {
        LinearLayout linearLayout = new LinearLayout(context);
        linearLayout.setOrientation(1);
        int dp = dp(context, 16.0f);
        linearLayout.setPadding(dp, dp, dp, dp);
        linearLayout.setBackground(redondeado(TARJETA, dp(context, 20.0f), dp(context, 1.0f), BORDE));
        LinearLayout.LayoutParams layoutParams = new LinearLayout.LayoutParams(-1, -2);
        layoutParams.setMargins(0, dp(context, 10.0f), 0, 0);
        linearLayout.setLayoutParams(layoutParams);
        return linearLayout;
    }

    public static int dp(Context context, float f) {
        return (int) (f * context.getResources().getDisplayMetrics().density);
    }

    public static TextView titulo(Context context, String str, int i, int i2) {
        TextView textView = new TextView(context);
        textView.setText(str);
        textView.setTextSize(i);
        textView.setTextColor(i2);
        return textView;
    }

    public static TextView detalle(Context context, String str) {
        TextView textView = new TextView(context);
        textView.setText(str);
        textView.setTextSize(12.0f);
        textView.setTextColor(SUAVE);
        textView.setPadding(0, dp(context, 4.0f), 0, 0);
        return textView;
    }

    public static Button boton(Context context, String str, int i, int i2, float f) {
        Button button = new Button(context);
        button.setText(str);
        button.setTextColor(i2);
        button.setTextSize(13.0f);
        button.setAllCaps(false);
        button.setBackground(redondeado(i, dp(context, (float) ((int) f)) != 0 ? dp(context, 14.0f) : 14.0f, 0, 0));
        button.setPadding(dp(context, 10.0f), dp(context, 10.0f), dp(context, 10.0f), dp(context, 10.0f));
        button.setGravity(17);
        return button;
    }

    public static Button principal(Context context, String str) {
        return boton(context, str, ROSA, -1, 16.0f);
    }

    public static Button secundario(Context context, String str) {
        Button boton = boton(context, str, -14474438, TEXTO, 14.0f);
        boton.setBackground(redondeado(-14474438, dp(context, 14.0f), dp(context, 1.0f), BORDE));
        return boton;
    }

    public static LinearLayout fila(Context context) {
        LinearLayout linearLayout = new LinearLayout(context);
        linearLayout.setOrientation(0);
        return linearLayout;
    }

    public static LinearLayout.LayoutParams peso(Context context, float f) {
        LinearLayout.LayoutParams layoutParams = new LinearLayout.LayoutParams(0, -2, f);
        int dp = dp(context, 5.0f);
        layoutParams.setMargins(dp, 0, dp, 0);
        return layoutParams;
    }

    public static LinearLayout.LayoutParams ancho(Context context) {
        LinearLayout.LayoutParams layoutParams = new LinearLayout.LayoutParams(-1, -2);
        layoutParams.setMargins(0, dp(context, 8.0f), 0, 0);
        return layoutParams;
    }
}
