package com.kimo.floating

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.PowerManager
import android.provider.Settings
import android.webkit.JavascriptInterface
import android.webkit.WebChromeClient
import android.webkit.WebView
import android.webkit.WebViewClient

class MainActivity : Activity() {
    private lateinit var web: WebView
    private val prefs by lazy { getSharedPreferences("kimo", MODE_PRIVATE) }
    private var pendingStart = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        web = WebView(this).apply {
            settings.javaScriptEnabled = true
            settings.domStorageEnabled = true
            settings.allowFileAccess = true
            settings.allowContentAccess = false
            webViewClient = WebViewClient()
            webChromeClient = WebChromeClient()
            addJavascriptInterface(AndroidBridge(), "KimoAndroid")
        }
        setContentView(web)
        web.loadUrl("file:///android_asset/kimo_v5.html")
    }

    inner class AndroidBridge {
        @JavascriptInterface fun toggleKimo(): Boolean {
            if (prefs.getBoolean("running", false)) {
                stopService(Intent(this@MainActivity, FloatingControlService::class.java))
                prefs.edit().putBoolean("running", false).apply()
                return false
            }
            if (Build.VERSION.SDK_INT >= 23 && !Settings.canDrawOverlays(this@MainActivity)) {
                pendingStart = true
                runOnUiThread {
                    startActivity(Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                        Uri.parse("package:" + packageName)))
                }
                return false
            }
            startKimoService()
            return true
        }

        @JavascriptInterface fun isRunning(): Boolean = prefs.getBoolean("running", false)
        @JavascriptInterface fun hasOverlayPermission(): Boolean =
            Build.VERSION.SDK_INT < 23 || Settings.canDrawOverlays(this@MainActivity)
        @JavascriptInterface fun hasBatteryExemption(): Boolean {
            if (Build.VERSION.SDK_INT < 23) return true
            val pm = getSystemService(POWER_SERVICE) as PowerManager
            return pm.isIgnoringBatteryOptimizations(packageName)
        }
        @JavascriptInterface fun openOverlaySettings() {
            runOnUiThread {
                if (Build.VERSION.SDK_INT >= 23) startActivity(Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                    Uri.parse("package:" + packageName)))
            }
        }
        @JavascriptInterface fun openBatterySettings() {
            runOnUiThread {
                if (Build.VERSION.SDK_INT >= 23 && !hasBatteryExemption()) {
                    try { startActivity(Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS,
                        Uri.parse("package:" + packageName))) }
                    catch (_: Exception) { openAppSettings() }
                }
            }
        }
        @JavascriptInterface fun openAppSettings() {
            runOnUiThread { startActivity(Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
                Uri.parse("package:" + packageName))) }
        }
    }

    private fun startKimoService() {
        val i = Intent(this, FloatingControlService::class.java).setAction(FloatingControlService.ACTION_START)
        if (Build.VERSION.SDK_INT >= 26) startForegroundService(i) else startService(i)
        prefs.edit().putBoolean("running", true).apply()
    }

    override fun onResume() {
        super.onResume()
        if (pendingStart) {
            pendingStart = false
            if (Build.VERSION.SDK_INT < 23 || Settings.canDrawOverlays(this)) startKimoService()
        }
        if (::web.isInitialized) web.postDelayed({
            if (!isFinishing) web.evaluateJavascript("syncNativeState()", null)
        }, 250)
    }

    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        if (::web.isInitialized) web.evaluateJavascript("goBack()", null) else super.onBackPressed()
    }

    override fun onDestroy() {
        if (::web.isInitialized) web.destroy()
        super.onDestroy()
    }
}
