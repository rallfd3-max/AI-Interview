package com.superassistant.mobile.cxr

import android.util.Base64
import android.util.Log
import com.rokid.cxr.link.CXRLink
import com.rokid.cxr.link.callbacks.IAudioStreamCbk
import com.rokid.sprite.aiapp.externalapp.auth.AuthorizationHelper
import com.rokid.sprite.aiapp.externalapp.auth.GlassPermission
import com.superassistant.mobile.App
import com.superassistant.mobile.net.CloudClient
import com.superassistant.mobile.net.UplinkMessage
import com.superassistant.mobile.perception.VadDetector
import com.superassistant.mobile.perception.WavEncoder
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/**
 * 音频监听:会话就绪后开启 CXR-L 音频流(PCM 16kHz/16bit/mono),
 * Silero VAD 断句后封装 WAV 上传 {type:"audio", data, duration_ms}。
 */
object AudioMonitor {

    private const val TAG = "AudioMonitor"
    private const val CODEC_PCM = 1

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)

    private val _segmentsUploaded = MutableStateFlow(0)
    val segmentsUploaded: StateFlow<Int> = _segmentsUploaded.asStateFlow()

    private val _running = MutableStateFlow(false)
    val running: StateFlow<Boolean> = _running.asStateFlow()

    private var started = false
    private var startJob: Job? = null

    /** 记录实际开启音频流的 link,会话重建后仍能对旧 link 正确 stopAudioStream */
    private var activeLink: CXRLink? = null
    private var vad: VadDetector? = null

    // 流量诊断:chunk/字节计数,每 5s 汇总一次
    private var chunkCount = 0L
    private var byteCount = 0L
    private var lastStatAt = 0L

    // 诊断用滚动缓冲:最近 15s 原始 PCM,可导出为 WAV 分析
    private val debugBuf = ShortArray(16_000 * 15)
    private var debugLen = 0
    private var debugWrapped = false

    private val audioCallback = object : IAudioStreamCbk {
        override fun onAudioReceived(data: ByteArray?, offset: Int, length: Int) {
            if (data == null || length <= 0) return
            // SDK 偶发越界 offset/length,按示例做边界保护
            val safeOffset = if (offset in 0 until data.size) offset else 0
            val maxAvailable = data.size - safeOffset
            val safeLength = when {
                length in 1..maxAvailable -> length
                maxAvailable > 0 -> maxAvailable
                else -> data.size
            }
            if (safeLength <= 0) return
            chunkCount++
            byteCount += safeLength
            logFlowStats()
            appendDebug(data, safeOffset, safeLength)
            if (!firstChunkLogged) {
                firstChunkLogged = true
                Log.i(TAG, "first audio chunk: len=$safeLength offset=$safeOffset (16kHz/16bit/mono 假设下=${safeLength * 1000 / 32_000}ms)")
                CloudClient.log("音频流已收到数据 (首块 ${safeLength} 字节)")
            }
            val detector = vad ?: return
            val sentences = runCatching {
                detector.feedPcm(data, safeOffset, safeLength)
            }.onFailure { Log.e(TAG, "feedPcm failed: ${it.message}") }.getOrNull() ?: return
            for (s in sentences) upload(s.samples, s.durationMs)
        }

        override fun onAudioError(errorCode: Int, errorInfo: String?) {
            Log.e(TAG, "onAudioError: code=$errorCode info=$errorInfo")
            CloudClient.log("音频错误: code=$errorCode ${errorInfo ?: ""}")
        }

        override fun onAudioStreamStateChanged(started: Boolean) {
            Log.i(TAG, "onAudioStreamStateChanged: started=$started")
        }
    }

    private var firstChunkLogged = false

    fun start() {
        if (started || startJob?.isActive == true) return
        val link = readyLink() ?: run {
            Log.w(TAG, "start: session not ready")
            return
        }
        if (!AuthorizationHelper.hasGlassPermission(GlassPermission.MICROPHONE)) {
            Log.w(TAG, "start: microphone permission missing")
            return
        }
        startJob = scope.launch {
            // ONNX 模型加载放 IO 线程,避免阻塞主线程
            val detector = vad ?: withContext(Dispatchers.IO) {
                runCatching { VadDetector(App.instance) }
                    .onFailure { Log.e(TAG, "VAD init failed: ${it.message}") }
                    .getOrNull()
            } ?: return@launch
            // 流重启时清空LSTM状态/64样本上文/半句缓冲,防止跨流残留
            detector.reset()
            vad = detector
            activeLink = link
            link.setCXRAudioCbk(audioCallback)
            val ok = link.startAudioStream(CODEC_PCM)
            started = true
            _running.value = true
            Log.i(TAG, "start: audio stream requested result=$ok")
            CloudClient.log("音频监听已开启 (Silero VAD 断句)")
        }
    }

    fun stop() {
        startJob?.cancel()
        val link = activeLink
        if (!started && link == null) return
        started = false
        activeLink = null
        _running.value = false
        link?.let {
            runCatching { it.stopAudioStream() }
                .onFailure { Log.w(TAG, "stopAudioStream failed: ${it.message}") }
        }
        Log.i(TAG, "stop: audio stream stopped (segments=${_segmentsUploaded.value})")
    }

    private fun upload(samples: ShortArray, durationMs: Long) {
        val wav = WavEncoder.encode(samples)
        val b64 = Base64.encodeToString(wav, Base64.NO_WRAP)
        CloudClient.send(UplinkMessage.AudioMessage(data = b64, durationMs = durationMs))
        _segmentsUploaded.value++
        CloudClient.log("已上传音频片段 ${durationMs}ms (${wav.size / 1024}KB)")
    }

    private fun logFlowStats() {
        val now = System.currentTimeMillis()
        if (lastStatAt == 0L) {
            lastStatAt = now
            return
        }
        if (now - lastStatAt >= 5_000) {
            val secs = (now - lastStatAt) / 1000.0
            val wearing = CxrSessionManager.wearing.value
            val mic = AuthorizationHelper.hasGlassPermission(GlassPermission.MICROPHONE)
            Log.i(
                TAG,
                "flow 5s: chunks=$chunkCount bytes=$byteCount (${"%.0f".format(byteCount / 32000.0)}s@16kHz, %.1f chunks/s), wearing=$wearing micPerm=$mic"
                    .format(chunkCount / secs)
            )
            chunkCount = 0
            byteCount = 0
            lastStatAt = now
        }
    }

    private fun appendDebug(data: ByteArray, offset: Int, length: Int) {
        var i = offset
        val end = offset + length
        while (i + 1 < end && debugLen < debugBuf.size) {
            debugBuf[debugLen++] =
                (((data[i + 1].toInt() shl 8) or (data[i].toInt() and 0xFF)).toShort())
            i += 2
        }
        if (debugLen >= debugBuf.size) {
            debugLen = 0
            debugWrapped = true
        }
    }

    /** 导出最近 15s 原始音频为 WAV,用于诊断采样率/内容问题 */
    fun dumpDebugAudio(): String? {
        if (debugLen == 0 && !debugWrapped) return null
        return runCatching {
            val samples = if (debugWrapped) {
                val out = ShortArray(debugBuf.size)
                System.arraycopy(debugBuf, debugLen, out, 0, debugBuf.size - debugLen)
                System.arraycopy(debugBuf, 0, out, debugBuf.size - debugLen, debugLen)
                out
            } else {
                debugBuf.copyOf(debugLen)
            }
            val dir = App.instance.getExternalFilesDir(null) ?: return null
            val file = java.io.File(dir, "debug_audio_${System.currentTimeMillis()}.wav")
            file.writeBytes(WavEncoder.encode(samples))
            Log.i(TAG, "debug audio dumped: ${file.absolutePath} (${samples.size / 16_000}s@16kHz)")
            CloudClient.log("已导出诊断音频: ${file.name}")
            file.absolutePath
        }.onFailure {
            Log.e(TAG, "dumpDebugAudio failed: ${it.message}")
        }.getOrNull()
    }

    private fun readyLink(): CXRLink? {
        val app = App.instance
        return if (app.sharedLink != null && app.isSessionReady) app.sharedLink else null
    }
}
