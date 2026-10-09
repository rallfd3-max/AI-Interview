package com.superassistant.mobile.cxr

import android.app.Activity
import android.content.Context
import android.content.Intent
import android.content.SharedPreferences
import android.util.Log
import com.rokid.cxr.link.CXRLink
import com.rokid.cxr.link.callbacks.ICXRLinkCbk
import com.rokid.cxr.link.utils.CxrDefs
import com.rokid.cxr.link.utils.GlassInfo
import com.rokid.sprite.aiapp.externalapp.auth.AuthResult
import com.rokid.sprite.aiapp.externalapp.auth.AuthorizationHelper
import com.rokid.sprite.aiapp.externalapp.auth.GlassPermission
import com.superassistant.mobile.App
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

object CxrSessionManager {

    private const val TAG = "CxrSessionManager"
    private const val PREFS_NAME = "cxr_session"
    private const val KEY_TOKEN = "token"

    const val REQUEST_CODE_AUTH = 1001

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)

    private val _companionInstalled = MutableStateFlow(false)
    val companionInstalled: StateFlow<Boolean> = _companionInstalled.asStateFlow()

    private val _authenticated = MutableStateFlow(false)
    val authenticated: StateFlow<Boolean> = _authenticated.asStateFlow()

    private val _cxrlConnected = MutableStateFlow(false)
    val cxrlConnected: StateFlow<Boolean> = _cxrlConnected.asStateFlow()

    private val _btConnected = MutableStateFlow(false)
    val btConnected: StateFlow<Boolean> = _btConnected.asStateFlow()

    private val _sessionReady = MutableStateFlow(false)
    val sessionReady: StateFlow<Boolean> = _sessionReady.asStateFlow()

    private val _wearing = MutableStateFlow<Boolean?>(null)
    val wearing: StateFlow<Boolean?> = _wearing.asStateFlow()

    private val _deviceInfo = MutableStateFlow("")
    val deviceInfo: StateFlow<String> = _deviceInfo.asStateFlow()

    private val _lastError = MutableStateFlow("")
    val lastError: StateFlow<String> = _lastError.asStateFlow()

    // M4-T2: 断线自动重建(眼镜关机/蓝牙断开后自动恢复会话)
    private var rebuildJob: Job? = null
    private var rebuildAttempts = 0

    /** 面板展示用:是否处于自动重连中 */
    private val _rebuilding = MutableStateFlow(false)
    val rebuilding: StateFlow<Boolean> = _rebuilding.asStateFlow()

    private fun prefs(context: Context): SharedPreferences =
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    fun checkCompanionInstalled(activity: Activity): Boolean {
        val installed = AuthorizationHelper.isRequiredRokidAppInstalled(activity) ||
            AuthorizationHelper.isRequiredHiRokidInstalled(activity)
        _companionInstalled.value = installed
        Log.i(TAG, "checkCompanionInstalled: installed=$installed")
        return installed
    }

    fun requestAuthorization(activity: Activity) {
        Log.i(TAG, "requestAuthorization")
        AuthorizationHelper.requestAuthorization(
            activity,
            arrayOf(GlassPermission.MICROPHONE, GlassPermission.CAMERA),
            REQUEST_CODE_AUTH
        )?.let { restored ->
            Log.i(TAG, "requestAuthorization: restored from history")
            handleAuthResult(restored.first, restored.second)
        }
    }

    /** 眼镜端设备权限是否齐备(拍照/音频前置条件) */
    fun glassPermissionsReady(): Boolean {
        val cam = AuthorizationHelper.hasGlassPermission(GlassPermission.CAMERA)
        val mic = AuthorizationHelper.hasGlassPermission(GlassPermission.MICROPHONE)
        Log.i(TAG, "glassPermissionsReady: camera=$cam mic=$mic")
        return cam && mic
    }

    fun handleAuthResult(resultCode: Int, data: Intent?) {
        when (val result = AuthorizationHelper.parseAuthorizationResult(resultCode, data)) {
            is AuthResult.AuthSuccess -> {
                val token = result.token
                if (token.isNotBlank()) {
                    Log.i(TAG, "auth success, token length=${token.length}")
                    prefs(App.instance).edit().putString(KEY_TOKEN, token).apply()
                    _authenticated.value = true
                    _lastError.value = ""
                    startSession(App.instance)
                } else {
                    Log.w(TAG, "auth success but token blank")
                    _authenticated.value = false
                    _lastError.value = "授权成功但 token 为空"
                }
            }
            is AuthResult.AuthFail -> {
                Log.w(TAG, "auth fail")
                _authenticated.value = false
                _lastError.value = "授权失败"
            }
            is AuthResult.AuthCancel -> {
                Log.w(TAG, "auth cancel")
                _authenticated.value = false
                _lastError.value = "授权已取消"
            }
        }
    }

    fun restoreSession(context: Context): Boolean {
        val token = prefs(context).getString(KEY_TOKEN, null)
        if (token.isNullOrBlank()) {
            Log.i(TAG, "restoreSession: no stored token")
            return false
        }
        Log.i(TAG, "restoreSession: stored token found, starting session")
        _authenticated.value = true
        startSession(context)
        return true
    }

    fun startSession(context: Context) {
        val token = prefs(context).getString(KEY_TOKEN, null)
        if (token.isNullOrBlank()) {
            _authenticated.value = false
            _lastError.value = "无 token,请先授权"
            return
        }
        val app = context.applicationContext as? App ?: run {
            Log.e(TAG, "startSession: App context not found")
            return
        }
        // 会话重建前先停掉旧链路上的音频流(拍照循环随 ready 状态自行复位)
        AudioMonitor.stop()
        // 旧 link 主动断开,防止重建后残留回调干扰新会话
        app.sharedLink?.let { old -> runCatching { old.disconnect() } }
        app.resetSession()
        CustomViewRenderer.reset()
        resetFlows()
        val link = CXRLink(context).apply {
            configCXRSession(CxrDefs.CXRSession(CxrDefs.CXRSessionType.CUSTOMVIEW))
            setCXRLinkCbk(linkCallback)
        }
        app.sharedLink = link
        CustomViewRenderer.bind(link)
        Log.i(TAG, "startSession: CUSTOMVIEW session created, connect()")
        link.connect(token)
    }

    private fun resetFlows() {
        _cxrlConnected.value = false
        _btConnected.value = false
        _sessionReady.value = false
        _wearing.value = null
    }

    private val linkCallback = object : ICXRLinkCbk {
        override fun onCXRLConnected(connected: Boolean) {
            Log.i(TAG, "onCXRLConnected: connected=$connected (bt=${_btConnected.value})")
            _cxrlConnected.value = connected
            syncSessionReady()
        }

        override fun onGlassBtConnected(connected: Boolean) {
            Log.i(TAG, "onGlassBtConnected: connected=$connected (cxr=${_cxrlConnected.value})")
            _btConnected.value = connected
            syncSessionReady()
        }

        override fun onGlassAiAssistStart() {}

        override fun onGlassAiAssistStop() {}

        override fun onGlassAiInterrupt(interruptWake: Boolean) {
            Log.d(TAG, "onGlassAiInterrupt: interruptWake=$interruptWake")
        }

        override fun onGlassDeviceInfo(deviceInfo: GlassInfo) {
            Log.d(TAG, "onGlassDeviceInfo: $deviceInfo")
            _deviceInfo.value = deviceInfo.toString()
        }

        override fun onGlassWearingStatus(wearing: Boolean) {
            Log.d(TAG, "onGlassWearingStatus: wearing=$wearing")
            _wearing.value = wearing
        }
    }

    private fun syncSessionReady() {
        val ready = _cxrlConnected.value && _btConnected.value
        App.instance.isSessionReady = ready
        _sessionReady.value = ready
        Log.i(TAG, "syncSessionReady: ready=$ready")
        if (ready) {
            rebuildJob?.cancel()
            rebuildAttempts = 0
            _rebuilding.value = false
            PhotoController.start()
            AudioMonitor.start()
            scope.launch {
                delay(1000)
                if (sessionReady.value && !CustomViewRenderer.viewOpened.value) {
                    Log.i(TAG, "session ready, showing idle screen")
                    CustomViewRenderer.showIdle()
                }
            }
        } else {
            PhotoController.stop()
            AudioMonitor.stop()
            scheduleRebuild()
        }
    }

    /**
     * M4-T2: 会话断开后自动重建(5s→10s→20s→30s 退避)。
     * 前提:曾经授权成功(token 有效);蓝牙瞬断时给 SDK 5s 自恢复窗口,
     * 到点仍未就绪才重建 CXRLink 会话。
     */
    private fun scheduleRebuild() {
        if (!_authenticated.value) return          // 从未授权,等用户手动操作
        if (rebuildJob?.isActive == true) return   // 已有重建在排队
        val delayMs = minOf(5_000L shl rebuildAttempts.coerceAtMost(2), 30_000L)
        rebuildAttempts++
        _rebuilding.value = true
        Log.i(TAG, "scheduleRebuild: attempt=$rebuildAttempts in ${delayMs / 1000}s")
        rebuildJob = scope.launch {
            delay(delayMs)
            _rebuilding.value = sessionReady.value.not()
            if (!sessionReady.value && _authenticated.value) {
                Log.i(TAG, "rebuild: recreating session (attempt=$rebuildAttempts)")
                startSession(App.instance)
            }
        }
    }
}
