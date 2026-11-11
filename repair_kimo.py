from pathlib import Path
p=Path('app/src/main/java/com/kimo/floating/MainActivity.kt')
s=p.read_text()
s=s.replace('import androidx.activity.result.contract.ActivityResultContracts\n','import androidx.activity.result.contract.ActivityResultContracts\nimport androidx.core.view.WindowCompat\nimport androidx.core.view.ViewCompat\nimport androidx.core.view.WindowInsetsCompat\n')
s=s.replace('    private var instructionsExpanded = false\n','    private var instructionsExpanded = false\n    private var pendingStart = false\n    private val notificationPermission = registerForActivityResult(ActivityResultContracts.RequestPermission()) { startBubbleNow() }\n')
s=s.replace('        super.onCreate(savedInstanceState)\n        running = prefs.getBoolean("running", false)\n','        super.onCreate(savedInstanceState)\n        WindowCompat.setDecorFitsSystemWindows(window, false)\n        running = prefs.getBoolean("running", false)\n')
s=s.replace('''                    } else {
                        pickVideo.launch("video/*")
                    }''','''                    } else {
                        requestKimoStart()
                    }''',1)
s=s.replace('''        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            layoutDirection = if (english) View.LAYOUT_DIRECTION_LTR else View.LAYOUT_DIRECTION_RTL
            setBackgroundColor(bg)
        }''','''        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            layoutDirection = if (english) View.LAYOUT_DIRECTION_LTR else View.LAYOUT_DIRECTION_RTL
            setBackgroundColor(bg)
        }
        ViewCompat.setOnApplyWindowInsetsListener(root) { v, insets ->
            val bars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
            v.setPadding(bars.left, bars.top, bars.right, bars.bottom)
            insets
        }''')
s=s.replace('''        setContentView(root)
    }

    private fun section''','''        setContentView(root)
        ViewCompat.requestApplyInsets(root)
    }

    private fun requestKimoStart() {
        pendingStart = true
        if (Build.VERSION.SDK_INT >= 23 && !Settings.canDrawOverlays(this)) {
            startActivity(Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:$packageName")))
            return
        }
        startBubbleNow()
    }

    private fun startBubbleNow() {
        if (!pendingStart) return
        if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS) != android.content.pm.PackageManager.PERMISSION_GRANTED) {
            notificationPermission.launch(android.Manifest.permission.POST_NOTIFICATIONS)
            return
        }
        pendingStart = false
        val service = Intent(this, FloatingVideoService::class.java).setAction("com.kimo.floating.SHOW_BUBBLE")
        if (Build.VERSION.SDK_INT >= 26) startForegroundService(service) else startService(service)
        running = true
        prefs.edit().putBoolean("running", true).apply()
        render()
    }

    override fun onResume() {
        super.onResume()
        if (pendingStart && (Build.VERSION.SDK_INT < 23 || Settings.canDrawOverlays(this))) startBubbleNow()
    }

    private fun section''')
p.write_text(s)

p=Path('app/src/main/java/com/kimo/floating/FloatingVideoService.kt')
s=p.read_text()
s=s.replace('import android.graphics.PixelFormat\n','import android.graphics.PixelFormat\nimport android.media.AudioManager\n')
s=s.replace('''    private var endControls: LinearLayout? = null
''','''    private var endControls: LinearLayout? = null
    private var bubbleView: TextView? = null
    private var bubbleParams: WindowManager.LayoutParams? = null
    private var bubbleDownX = 0f
    private var bubbleDownY = 0f
    private var bubbleBaseX = 0
    private var bubbleBaseY = 0
    private var bubbleMoved = false
    private var expanded = false
    private var normalWidth = 0
    private var normalHeight = 0
''')
s=s.replace('''        val uri = intent?.data ?: return START_NOT_STICKY
        showPlayer(uri)
        return START_NOT_STICKY''','''        if (intent?.action == "com.kimo.floating.SHOW_BUBBLE") {
            showBubble()
            return START_NOT_STICKY
        }
        val uri = intent?.data ?: return START_NOT_STICKY
        showPlayer(uri)
        return START_NOT_STICKY''')
insert = '''
    private fun showBubble() {
        if (bubbleView != null) return
        val size = dp(58)
        val view = TextView(this).apply {
            text = "▶"; textSize = 23f; gravity = Gravity.CENTER
            setTextColor(0xffffffff.toInt())
            background = android.graphics.drawable.GradientDrawable().apply {
                shape = android.graphics.drawable.GradientDrawable.OVAL
                setColor(0xff28736c.toInt()); setStroke(dp(2), 0xffb5ded6.toInt())
            }
            elevation = dp(8).toFloat()
            contentDescription = "زر كيمو للتحكم بالوسائط"
            setOnClickListener {
                if (!bubbleMoved) {
                    val audio = getSystemService(Context.AUDIO_SERVICE) as AudioManager
                    val key = android.view.KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE
                    audio.dispatchMediaKeyEvent(android.view.KeyEvent(android.view.KeyEvent.ACTION_DOWN, key))
                    audio.dispatchMediaKeyEvent(android.view.KeyEvent(android.view.KeyEvent.ACTION_UP, key))
                }
            }
            setOnTouchListener { v, e ->
                when (e.actionMasked) {
                    MotionEvent.ACTION_DOWN -> { bubbleDownX=e.rawX; bubbleDownY=e.rawY; bubbleBaseX=bubbleParams?.x ?: 0; bubbleBaseY=bubbleParams?.y ?: 0; bubbleMoved=false; true }
                    MotionEvent.ACTION_MOVE -> {
                        val dx=(e.rawX-bubbleDownX).toInt(); val dy=(e.rawY-bubbleDownY).toInt()
                        if (kotlin.math.abs(dx)+kotlin.math.abs(dy)>dp(5)) bubbleMoved=true
                        bubbleParams?.let { lp -> lp.x=(bubbleBaseX+dx).coerceIn(0, max(0, resources.displayMetrics.widthPixels-lp.width)); lp.y=(bubbleBaseY+dy).coerceIn(dp(28), max(dp(28), resources.displayMetrics.heightPixels-lp.height-dp(24))); try { wm.updateViewLayout(v,lp) } catch (_: Exception) {} }
                        true
                    }
                    MotionEvent.ACTION_UP -> { if (!bubbleMoved) v.performClick(); true }
                    else -> true
                }
            }
        }
        val lp=WindowManager.LayoutParams(size,size,type,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL,
            PixelFormat.TRANSLUCENT).apply { gravity=Gravity.TOP or Gravity.START; x=dp(12); y=dp(180) }
        try { wm.addView(view,lp); bubbleView=view; bubbleParams=lp } catch (_: Exception) { stopSelf() }
    }

    private fun removeBubble() {
        try { bubbleView?.let { wm.removeView(it) } } catch (_: Exception) {}
        bubbleView=null; bubbleParams=null
    }
'''
s=s.replace('''        val lp=WindowManager.LayoutParams(size,size,type,''','''        val type = if (Build.VERSION.SDK_INT >= 26) WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY else WindowManager.LayoutParams.TYPE_PHONE\n        val lp=WindowManager.LayoutParams(size,size,type,''')
s=s.replace('''    private fun showPlayer(uri: Uri) {''',insert+'''
    private fun showPlayer(uri: Uri) {
        removeBubble()''')
s=s.replace('''        controls.addView(control("◀|", "السابق") { }.apply { isEnabled = false; alpha = 0.35f })
        controls.addView(control("⟳", "إعادة") { player?.seekTo(0); player?.play(); controls.visibility = View.GONE })
        controls.addView(control("|▶", "التالي") { }.apply { isEnabled = false; alpha = 0.35f })''','''        controls.addView(control("◀|", "السابق") { Toast.makeText(this, "لا توجد قائمة تشغيل", Toast.LENGTH_SHORT).show() }.apply { isEnabled = false; alpha = 0.35f })
        val playPause = control("Ⅱ", "تشغيل أو إيقاف") { player?.let { if (it.isPlaying) it.pause() else it.play() } }
        controls.addView(playPause)
        controls.addView(control("⟳", "إعادة") { player?.seekTo(0); player?.play(); controls.visibility = View.GONE })
        controls.addView(control("|▶", "التالي") { Toast.makeText(this, "لا توجد قائمة تشغيل", Toast.LENGTH_SHORT).show() }.apply { isEnabled = false; alpha = 0.35f })
        controls.addView(control("□", "تكبير أو عودة") { toggleExpand() })''')
s=s.replace('''        exo.addListener(object : Player.Listener {
            override fun onPlaybackStateChanged(playbackState: Int) {''','''        exo.addListener(object : Player.Listener {
            override fun onIsPlayingChanged(isPlaying: Boolean) { playPause.text = if (isPlaying) "Ⅱ" else "▶" }
            override fun onPlaybackStateChanged(playbackState: Int) {''')
insert2 = '''
    private fun toggleExpand() {
        val lp=params ?: return
        if (!expanded) {
            normalWidth=lp.width; normalHeight=lp.height
            lp.width=resources.displayMetrics.widthPixels-dp(16)
            lp.height=resources.displayMetrics.heightPixels-dp(72)
            lp.x=dp(8); lp.y=dp(28); expanded=true
        } else {
            lp.width=normalWidth; lp.height=normalHeight
            lp.x=((resources.displayMetrics.widthPixels-lp.width)/2).coerceAtLeast(0)
            lp.y=dp(90); expanded=false
        }
        clamp(lp)
        try { wm.updateViewLayout(root,lp) } catch (_: Exception) {}
    }
'''
s=s.replace('''    private fun handleTouch(e: MotionEvent): Boolean {''',insert2+'''
    private fun handleTouch(e: MotionEvent): Boolean {''')
s=s.replace('''    override fun onDestroy() { removeOverlay(); super.onDestroy() }''','''    override fun onDestroy() { removeOverlay(); removeBubble(); getSharedPreferences("kimo_settings", Context.MODE_PRIVATE).edit().putBoolean("running", false).apply(); super.onDestroy() }''')
p.write_text(s)
