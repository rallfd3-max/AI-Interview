package com.superassistant.mobile.service

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.IBinder
import android.os.PowerManager
import android.util.Log
import androidx.core.app.NotificationCompat
import com.superassistant.mobile.MainActivity
import com.superassistant.mobile.R

/**
 * 前台保活服务:佩戴眼镜时手机息屏在兜里,
 * Doze 会按应用切断网络并冻结后台,导致 WebSocket/拍照/音频链路中断。
 * 前台服务 + PARTIAL_WAKE_LOCK 保证息屏下全链路持续运行。
 */
class KeepAliveService : Service() {

    companion object {
        private const val TAG = "KeepAliveService"
        private const val CHANNEL_ID = "keep_alive"
        private const val NOTIFICATION_ID = 1

        fun start(context: Context) {
            Log.i(TAG, "start requested from ${context.javaClass.simpleName}")
            runCatching {
                context.startForegroundService(Intent(context, KeepAliveService::class.java))
            }.onFailure { Log.e(TAG, "startForegroundService failed: ${it.message}") }
        }
    }

    private var wakeLock: PowerManager.WakeLock? = null

    override fun onCreate() {
        super.onCreate()
        Log.i(TAG, "onCreate")
        createChannel()
        startForeground(NOTIFICATION_ID, buildNotification(), ServiceInfo.FOREGROUND_SERVICE_TYPE_CONNECTED_DEVICE)
        acquireWakeLock()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        Log.i(TAG, "onStartCommand")
        return START_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        Log.w(TAG, "onDestroy")
        wakeLock?.let { if (it.isHeld) it.release() }
        wakeLock = null
        super.onDestroy()
    }

    private fun createChannel() {
        val nm = getSystemService(NOTIFICATION_SERVICE) as NotificationManager
        nm.createNotificationChannel(
            NotificationChannel(CHANNEL_ID, "后台保活", NotificationManager.IMPORTANCE_LOW)
        )
    }

    private fun buildNotification(): Notification {
        val pi = PendingIntent.getActivity(
            this, 0,
            Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_IMMUTABLE,
        )
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("超级助手")
            .setContentText("运行中 · 眼镜链路保活")
            .setSmallIcon(R.mipmap.ic_launcher)
            .setContentIntent(pi)
            .setOngoing(true)
            .build()
    }

    private fun acquireWakeLock() {
        val pm = getSystemService(POWER_SERVICE) as PowerManager
        wakeLock = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "SuperAssistant:KeepAlive").apply {
            setReferenceCounted(false)
            acquire()
        }
    }
}
