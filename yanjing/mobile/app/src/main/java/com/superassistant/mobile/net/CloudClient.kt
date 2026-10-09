package com.superassistant.mobile.net

import android.content.Context
import android.content.SharedPreferences
import android.util.Log
import com.superassistant.mobile.App
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.WebSocket
import okhttp3.WebSocketListener
import okio.ByteString
import okio.ByteString.Companion.toByteString
import java.util.concurrent.TimeUnit

object CloudClient {

    private const val TAG = "CloudClient"
    private const val PREFS_NAME = "cloud_client"
    private const val KEY_SERVER_URL = "server_url"
    private const val DEFAULT_SERVER_URL = "ws://172.20.10.5:18081/ws/recognition"
    private const val KEY_DEVICE_ID = "device_id"

    /** 开发期用过的旧服务器地址:启动时命中的旧值会被迁移到当前默认,避免旧地址覆盖新默认 */
    private val LEGACY_SERVER_URLS = setOf(
        "ws://localhost:8080/ws",
        "ws://127.0.0.1:8080/ws",
        "ws://192.168.1.100:9000/ws",
        "ws://192.168.1.2:8080/ws",
        "ws://172.20.10.5:8080/ws",
        "ws://172.20.10.5:18081/ws",
    )

    /** 本次识别会话 ID:进程内保持不变,服务端用于关联同一次识别会话 */
    val sessionId: String = "session-" + java.lang.Long.toHexString(System.currentTimeMillis())

    private const val HEARTBEAT_INTERVAL_MS = 30_000L
    private const val HEARTBEAT_TIMEOUT_MS = 15_000L
    private const val RECONNECT_BASE_MS = 1_000L
    private const val RECONNECT_MAX_MS = 30_000L
    private const val OFFLINE_AUDIO_MAX = 3   // M4-T3: 最近 3 条音频
    private const val OFFLINE_FACE_MAX = 1    // M4-T3: 最近 1 张人脸图
    private const val QUEUE_FILE = "offline_queue.json"

    /** 离线缓存条目:类型标记 + 原始消息 JSON(落盘用) */
    private data class QueuedItem(val type: String, val json: String)

    enum class ConnState { DISCONNECTED, CONNECTING, CONNECTED }

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    private val client = OkHttpClient.Builder()
        .pingInterval(0, TimeUnit.MILLISECONDS)
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(0, TimeUnit.MILLISECONDS)
        .build()

    private var webSocket: WebSocket? = null
    private var heartbeatJob: Job? = null
    private var reconnectJob: Job? = null
    private var reconnectAttempts = 0
    private var lastPongTs = 0L
    private var manuallyClosed = false
    private val pingSeq = java.util.concurrent.atomic.AtomicInteger(0)

    private val offlineQueue = ArrayDeque<QueuedItem>()
    private var listener: ((DownlinkMessage) -> Unit)? = null

    private val _state = MutableStateFlow(ConnState.DISCONNECTED)
    val state: StateFlow<ConnState> = _state.asStateFlow()

    private val _serverUrl = MutableStateFlow(DEFAULT_SERVER_URL)
    val serverUrl: StateFlow<String> = _serverUrl.asStateFlow()

    private val _queuedCount = MutableStateFlow(0)
    val queuedCount: StateFlow<Int> = _queuedCount.asStateFlow()

    private val _lastError = MutableStateFlow("")
    val lastError: StateFlow<String> = _lastError.asStateFlow()

    private val _logLines = MutableStateFlow<List<String>>(emptyList())
    val logLines: StateFlow<List<String>> = _logLines.asStateFlow()

    fun setOnMessage(l: (DownlinkMessage) -> Unit) {
        listener = l
    }

    fun setServerUrl(url: String) {
        _serverUrl.value = url.trim().ifEmpty { DEFAULT_SERVER_URL }
        prefs(App.instance).edit().putString(KEY_SERVER_URL, _serverUrl.value).apply()
        log("服务器地址已保存: ${_serverUrl.value}")
    }

    fun loadSavedConfig() {
        val saved = prefs(App.instance).getString(KEY_SERVER_URL, null)
        // 开发期旧地址(mock 的 localhost / 之前的服务器 IP)已废弃,迁移到当前默认
        val url = if (saved.isNullOrBlank() ||
            saved.trim() in LEGACY_SERVER_URLS
        ) {
            DEFAULT_SERVER_URL
        } else {
            saved
        }
        _serverUrl.value = url
        prefs(App.instance).edit().putString(KEY_SERVER_URL, url).apply()
        loadQueue()
    }

    fun connect() {
        if (_state.value == ConnState.CONNECTED || _state.value == ConnState.CONNECTING) return
        manuallyClosed = false
        reconnectJob?.cancel()
        _state.value = ConnState.CONNECTING
        log("连接 ${_serverUrl.value}")
        val deviceId = deviceId()
        val request = Request.Builder()
            .url(_serverUrl.value)
            .header("X-Device-Id", deviceId)
            .build()
        webSocket = client.newWebSocket(request, socketListener)
    }

    fun disconnect(manual: Boolean = true) {
        manuallyClosed = manual
        heartbeatJob?.cancel()
        reconnectJob?.cancel()
        webSocket?.close(1000, "client close")
        webSocket = null
        _state.value = ConnState.DISCONNECTED
        if (manual) log("已断开连接")
    }

    fun send(message: UplinkMessage) {
        val json = MessageProtocol.encode(message)
        if (_state.value == ConnState.CONNECTED) {
            val sent = webSocket?.send(json) ?: false
            if (!sent) enqueue(json)
        } else {
            enqueue(json)
        }
    }

    fun clearQueue() {
        offlineQueue.clear()
        _queuedCount.value = 0
        persistQueue()
    }

    /**
     * M4-T3 离线缓存:按消息类型限额——
     * audio 最多 3 条(挤掉最老),recognize 仅留最新 1 帧,person_left 等时效性消息直接丢弃
     * (离线期间 person_left 已过时,重传反而误导云端)。
     * 队列变化即落盘,进程重启后恢复。
     */
    private fun enqueue(json: String) {
        val type = extractType(json)
        when (type) {
            "audio" -> {
                while (offlineQueue.count { it.type == "audio" } >= OFFLINE_AUDIO_MAX) {
                    val oldest = offlineQueue.indexOfFirst { it.type == "audio" }
                    if (oldest < 0) break
                    offlineQueue.removeAt(oldest)
                }
            }

            "recognize" -> {
                // 只保留最新一帧待识别照片
                while (offlineQueue.count { it.type == "recognize" } >= OFFLINE_FACE_MAX) {
                    val oldest = offlineQueue.indexOfFirst { it.type == "recognize" }
                    if (oldest < 0) break
                    offlineQueue.removeAt(oldest)
                }
            }

            else -> return  // person_left 等时效性消息不缓存
        }
        offlineQueue.addLast(QueuedItem(type, json))
        _queuedCount.value = offlineQueue.size
        persistQueue()
        log("离线缓存 +1 ${type} (共${offlineQueue.size}条)")
    }

    private fun extractType(json: String): String = MessageProtocol.uplinkType(json)

    private fun flushQueue() {
        while (offlineQueue.isNotEmpty()) {
            val item = offlineQueue.removeFirst()
            val sent = webSocket?.send(item.json) ?: false
            if (!sent) {
                offlineQueue.addFirst(item)
                break
            }
        }
        _queuedCount.value = offlineQueue.size
        persistQueue()
        if (offlineQueue.isEmpty()) log("离线缓存已全部重传")
    }

    /** 队列落盘:进程被杀后重启仍可恢复未重传的数据 */
    private fun persistQueue() {
        runCatching {
            val arr = buildJsonArray {
                offlineQueue.forEach {
                    add(
                        buildJsonObject {
                            put("type", it.type)
                            put("json", it.json)
                        }
                    )
                }
            }
            queueFile().writeText(arr.toString())
        }.onFailure { Log.w(TAG, "persistQueue failed: ${it.message}") }
    }

    private fun loadQueue() {
        runCatching {
            val f = queueFile()
            if (!f.exists()) return
            val arr = Json.parseToJsonElement(f.readText())
            (arr as? JsonArray)?.forEach { el ->
                val obj = el as? JsonObject ?: return@forEach
                val t = (obj["type"] as? JsonPrimitive)?.content ?: return@forEach
                val j = (obj["json"] as? JsonPrimitive)?.content ?: return@forEach
                offlineQueue.addLast(QueuedItem(t, j))
            }
            _queuedCount.value = offlineQueue.size
            if (offlineQueue.isNotEmpty()) log("从磁盘恢复离线缓存 ${offlineQueue.size} 条")
        }.onFailure { Log.w(TAG, "loadQueue failed: ${it.message}") }
    }

    private fun queueFile() = java.io.File(App.instance.filesDir, QUEUE_FILE)

    private fun scheduleReconnect() {
        if (manuallyClosed) return
        val delayMs = minOf(
            RECONNECT_BASE_MS * (1L shl reconnectAttempts.coerceAtMost(5)),
            RECONNECT_MAX_MS
        )
        reconnectAttempts++
        log("${delayMs / 1000.0}s 后重连 (第${reconnectAttempts}次)")
        reconnectJob = scope.launch {
            delay(delayMs)
            connect()
        }
    }

    private fun startHeartbeat() {
        heartbeatJob?.cancel()
        lastPongTs = System.currentTimeMillis()
        heartbeatJob = scope.launch {
            while (true) {
                delay(HEARTBEAT_INTERVAL_MS)
                if (System.currentTimeMillis() - lastPongTs > HEARTBEAT_INTERVAL_MS + HEARTBEAT_TIMEOUT_MS) {
                    log("心跳超时,主动断开重连")
                    webSocket?.cancel()
                    break
                }
                webSocket?.send("""{"type":"ping","request_id":"ping-${pingSeq.incrementAndGet()}"}""")
            }
        }
    }

    private val socketListener = object : WebSocketListener() {
        override fun onOpen(webSocket: WebSocket, response: Response) {
            log("已连接")
            _state.value = ConnState.CONNECTED
            _lastError.value = ""
            reconnectAttempts = 0
            startHeartbeat()
            flushQueue()
        }

        override fun onMessage(webSocket: WebSocket, text: String) {
            // 记录原始下行,便于核对服务端 recognition_result 的实际字段结构
            log("下行原始: ${text.take(300)}")
            val msg = MessageProtocol.decode(text)
            if (msg == null) {
                log("收到无法解析的消息: ${text.take(80)}")
                return
            }
            when (msg) {
                is PongMessage -> lastPongTs = System.currentTimeMillis()
                else -> listener?.invoke(msg)
            }
        }

        override fun onMessage(webSocket: WebSocket, bytes: ByteString) {}

        override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
            log("连接关闭: code=$code")
            _state.value = ConnState.DISCONNECTED
            heartbeatJob?.cancel()
            scheduleReconnect()
        }

        override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
            log("连接失败: ${t.message ?: t.javaClass.simpleName}")
            _state.value = ConnState.DISCONNECTED
            _lastError.value = t.message ?: "连接失败"
            heartbeatJob?.cancel()
            scheduleReconnect()
        }
    }

    /** 稳定的设备标识:握手的 X-Device-Id 与 recognize.device_id 共用 */
    fun deviceId(): String {
        val p = prefs(App.instance)
        var id = p.getString(KEY_DEVICE_ID, null)
        if (id.isNullOrBlank()) {
            id = "dev-" + android.util.Base64.encodeToString(
                android.os.Build.FINGERPRINT.toByteArray(),
                android.util.Base64.NO_WRAP
            ).replace("=", "").take(12)
            p.edit().putString(KEY_DEVICE_ID, id).apply()
        }
        return id
    }

    private fun prefs(context: Context): SharedPreferences =
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    fun log(line: String) {
        Log.i(TAG, line)
        _logLines.value = (_logLines.value + "${timeNow()} $line").takeLast(100)
    }

    private fun timeNow(): String {
        val fmt = java.text.SimpleDateFormat("HH:mm:ss", java.util.Locale.US)
        return fmt.format(java.util.Date())
    }
}
