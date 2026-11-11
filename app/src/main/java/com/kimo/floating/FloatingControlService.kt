package com.kimo.floating

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Context
import android.content.Intent
import android.graphics.PixelFormat
import android.media.AudioManager
import android.os.Build
import android.os.IBinder
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.TextView
import kotlin.math.abs

class FloatingControlService : Service() {
    companion object {
        const val ACTION_START = "com.kimo.floating.START"
        private const val CHANNEL = "kimo_controls"
        private const val NOTIFICATION_ID = 71
    }
    private lateinit var wm: WindowManager
    private var bubble: TextView? = null
    private var params: WindowManager.LayoutParams? = null
    private var downX = 0f
    private var downY = 0f
    private var originX = 0
    private var originY = 0
    private var moved = false

    override fun onCreate() {
        super.onCreate()
        wm = getSystemService(WINDOW_SERVICE) as WindowManager
        createChannel()
        val notification = if (Build.VERSION.SDK_INT >= 26) {
            Notification.Builder(this, CHANNEL).setSmallIcon(android.R.drawable.ic_media_play)
                .setContentTitle("كيمو يعمل").setContentText("زر التحكم العائم بالوسائط نشط")
                .setOngoing(true).build()
        } else {
            @Suppress("DEPRECATION")
            Notification.Builder(this).setSmallIcon(android.R.drawable.ic_media_play)
                .setContentTitle("كيمو يعمل").setContentText("زر التحكم العائم بالوسائط نشط")
                .setOngoing(true).build()
        }
        if (Build.VERSION.SDK_INT >= 34) {
            startForeground(NOTIFICATION_ID, notification,
                android.content.pm.ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE)
        } else startForeground(NOTIFICATION_ID, notification)
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == ACTION_START) showBubble()
        return START_STICKY
    }

    private fun showBubble() {
        if (bubble != null) return
        val size = (58 * resources.displayMetrics.density).toInt()
        val view = TextView(this).apply {
            text = "▶"
            textSize = 22f
            gravity = Gravity.CENTER
            setTextColor(0xffffffff.toInt())
            background = android.graphics.drawable.GradientDrawable().apply {
                shape = android.graphics.drawable.GradientDrawable.OVAL
                setColor(0xff28736c.toInt())
                setStroke((2 * resources.displayMetrics.density).toInt(), 0xffb5ded6.toInt())
            }
            elevation = 8f
            contentDescription = "كيمو: تشغيل أو إيقاف الوسائط"
            setOnClickListener { sendMediaToggle() }
            setOnTouchListener { v, e ->
                when (e.actionMasked) {
                    MotionEvent.ACTION_DOWN -> {
                        downX = e.rawX; downY = e.rawY
                        originX = params?.x ?: 0; originY = params?.y ?: 0
                        moved = false; true
                    }
                    MotionEvent.ACTION_MOVE -> {
                        val dx = (e.rawX - downX).toInt()
                        val dy = (e.rawY - downY).toInt()
                        if (abs(dx) + abs(dy) > 6) moved = true
                        params?.let { p ->
                            p.x = (originX + dx).coerceIn(0, (resources.displayMetrics.widthPixels - p.width).coerceAtLeast(0))
                            p.y = (originY + dy).coerceIn(0, (resources.displayMetrics.heightPixels - p.height).coerceAtLeast(0))
                            try { wm.updateViewLayout(v, p) } catch (_: Exception) {}
                        }
                        true
                    }
                    MotionEvent.ACTION_UP -> { if (!moved) v.performClick(); true }
                    else -> true
                }
            }
        }
        val type = if (Build.VERSION.SDK_INT >= 26) WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
            else WindowManager.LayoutParams.TYPE_PHONE
        val lp = WindowManager.LayoutParams(size, size, type,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL,
            PixelFormat.TRANSLUCENT).apply {
            gravity = Gravity.TOP or Gravity.START
            x = (12 * resources.displayMetrics.density).toInt()
            y = (180 * resources.displayMetrics.density).toInt()
        }
        try { wm.addView(view, lp); bubble = view; params = lp }
        catch (_: Exception) { stopSelf() }
    }

    private fun sendMediaToggle() {
        try {
            val audio = getSystemService(Context.AUDIO_SERVICE) as AudioManager
            val key = android.view.KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE
            audio.dispatchMediaKeyEvent(android.view.KeyEvent(android.view.KeyEvent.ACTION_DOWN, key))
            audio.dispatchMediaKeyEvent(android.view.KeyEvent(android.view.KeyEvent.ACTION_UP, key))
        } catch (_: Exception) {}
    }

    private fun createChannel() {
        if (Build.VERSION.SDK_INT >= 26) {
            val channel = NotificationChannel(CHANNEL, "كيمو", NotificationManager.IMPORTANCE_LOW)
            (getSystemService(NOTIFICATION_SERVICE) as NotificationManager).createNotificationChannel(channel)
        }
    }

    override fun onDestroy() {
        try { bubble?.let { wm.removeView(it) } } catch (_: Exception) {}
        bubble = null
        getSharedPreferences("kimo", MODE_PRIVATE).edit().putBoolean("running", false).apply()
        if (Build.VERSION.SDK_INT >= 24) stopForeground(STOP_FOREGROUND_REMOVE) else stopForeground(true)
        super.onDestroy()
    }
    override fun onBind(intent: Intent?): IBinder? = null
}
