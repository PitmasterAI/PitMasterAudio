package es.pitmasterai.masterlab;

import android.R;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.Intent;
import android.os.Build;
import android.os.IBinder;

public class ServicioPrecalculado extends Service {
    public static final String CANAL = "precalculado";
    private static final int ID_AVISO = 42;

    @Override 
    public IBinder onBind(Intent intent) {
        return null;
    }

    @Override 
    public void onCreate() {
        super.onCreate();
        Idioma.iniciar(this);       
        NotificationManager notificationManager = (NotificationManager) getSystemService(NotificationManager.class);
        if (notificationManager != null) {
            NotificationChannel notificationChannel = new NotificationChannel(CANAL, Idioma.t("Preparando versiones"), 2);
            notificationChannel.setDescription(Idioma.t("Se muestra mientras se calculan los ajustes por detrás"));
            notificationManager.createNotificationChannel(notificationChannel);
        }
    }

    @Override 
    public int onStartCommand(Intent intent, int i, int i2) {
        Notification.Builder builder;
        Idioma.iniciar(this);
        if (Build.VERSION.SDK_INT >= 26) {
            builder = new Notification.Builder(this, CANAL);
        } else {
            builder = new Notification.Builder(this);
        }
        builder.setContentTitle("PitMasterAudio").setContentText(Idioma.t("Preparando los ajustes de la canción…")).setSmallIcon(R.drawable.ic_media_play).setOngoing(true);
        startForeground(ID_AVISO, builder.build());
        return 2;
    }

    @Override 
    public void onDestroy() {
        stopForeground(true);
        super.onDestroy();
    }
}
