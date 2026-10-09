package com.superassistant.mobile.cxr

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.util.Base64
import android.util.Log
import com.rokid.cxr.link.CXRLink
import com.rokid.cxr.link.callbacks.IImageStreamCbk
import com.rokid.sprite.aiapp.externalapp.auth.AuthorizationHelper
import com.rokid.sprite.aiapp.externalapp.auth.GlassPermission
import com.superassistant.mobile.App
import com.superassistant.mobile.net.CloudClient
import com.superassistant.mobile.net.UplinkMessage
import com.superassistant.mobile.perception.FaceDetector
import com.superassistant.mobile.perception.FaceFlowPolicy
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

/**
 * 定时拍照调度:IDLE 每 3s / ACTIVE 每 30s 拍一帧,
 * 本地 BlazeFace 检测后按 FaceFlowPolicy 决策上传,person_left 时回调通知界面复位。
 */
object PhotoController {

    private const val TAG = "PhotoController"
    private const val IDLE_INTERVAL_MS = 3_000L
    private const val ACTIVE_INTERVAL_MS = 30_000L
    // 服务端文本帧上限 256KiB(max-text-message-size: 262144),Base64 膨胀 4/3
    // ⇒ 原图需 <~192KB。640x480@70 通常 <60KB,稳定满足上限。
    private const val PHOTO_W = 640
    private const val PHOTO_H = 480
    private const val PHOTO_JPEG_QUALITY = 70

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)

    private val policy = FaceFlowPolicy()
    private var loopJob: Job? = null
    private var faceDetector: FaceDetector? = null

    private val _mode = MutableStateFlow(FaceFlowPolicy.Mode.IDLE)
    val mode: StateFlow<FaceFlowPolicy.Mode> = _mode.asStateFlow()

    private val _framesDetected = MutableStateFlow(0)
    val framesDetected: StateFlow<Int> = _framesDetected.asStateFlow()

    /** request_id 序号:每帧/每次事件唯一,便于与服务端响应关联 */
    private val reqSeq = java.util.concurrent.atomic.AtomicInteger(0)

    /** 本地判定 person_left(界面复位用,由路由层注册) */
    var onPersonLeft: (() -> Unit)? = null

    private val imageCallback = object : IImageStreamCbk {
        override fun onImageReceived(data: ByteArray?) {
            if (data == null || data.isEmpty()) return
            CloudClient.log("收到眼镜照片 ${data.size / 1024}KB")
            val jpeg = data
            scope.launch(Dispatchers.Default) {
                handleFrame(jpeg)
            }
        }

        override fun onImageError(code: Int, msg: String?) {
            Log.w(TAG, "onImageError: code=$code msg=$msg")
            CloudClient.log("眼镜拍照失败: $code ${msg.orEmpty()}")
        }
    }

    fun start() {
        if (loopJob?.isActive == true) return
        val link = readyLink() ?: run {
            Log.w(TAG, "start: session not ready")
            return
        }
        link.setCXRImageCbk(imageCallback)
        Log.i(TAG, "start: photo loop begin (mode=${_mode.value})")
        loopJob = scope.launch {
            while (isActive) {
                // 会话构建完成后(自定义界面已打开)且相机权限就绪才可拍照
                if (CustomViewRenderer.viewOpened.value) {
                    if (AuthorizationHelper.hasGlassPermission(GlassPermission.CAMERA)) {
                        triggerPhoto()
                    } else {
                        Log.w(TAG, "camera permission missing, skip photo")
                    }
                }
                delay(
                    if (_mode.value == FaceFlowPolicy.Mode.ACTIVE) ACTIVE_INTERVAL_MS
                    else IDLE_INTERVAL_MS
                )
            }
        }
    }

    fun stop() {
        loopJob?.cancel()
        loopJob = null
        Log.i(TAG, "stop: photo loop end")
    }

    /** 云端返回 person_info:锁定人物,进入 ACTIVE */
    fun onPersonIdentified(id: String) {
        policy.onPersonIdentified(id)
        _mode.value = policy.mode
        Log.i(TAG, "onPersonIdentified: id=$id -> ACTIVE")
    }

    /** 云端返回 clear:回到 IDLE */
    fun onCleared() {
        policy.onCleared()
        _mode.value = policy.mode
        Log.i(TAG, "onCleared -> IDLE")
    }

    private fun triggerPhoto() {
        val link = readyLink() ?: run {
            stop()
            return
        }
        if (!viewOpenedForPhoto) {
            viewOpenedForPhoto = true
            val cam = AuthorizationHelper.hasGlassPermission(GlassPermission.CAMERA)
            val mic = AuthorizationHelper.hasGlassPermission(GlassPermission.MICROPHONE)
            Log.w(TAG, "triggerPhoto: glass perms camera=$cam mic=$mic viewOpened=${CustomViewRenderer.viewOpened.value}")
        }
        val ok = link.takePhoto(PHOTO_W, PHOTO_H, PHOTO_JPEG_QUALITY)
        if (!ok) Log.w(TAG, "takePhoto request rejected")
    }

    private var viewOpenedForPhoto = false
    private var frameFormatLogged = false

    /** 上传用的图片:完整文件字节 + 实际编码格式 */
    private data class UploadImage(val bytes: ByteArray, val format: String)

    /**
     * 图片文件魔数判定。SDK 的 takePhoto 回调输出的是已编码的完整图片文件
     * (官方 sample 对同一 data 直接 BitmapFactory.decodeByteArray,可解即证明非 YUV/RGBA 裸数据)。
     */
    private fun imageMagic(data: ByteArray): String = when {
        data.size >= 3 &&
            data[0] == 0xFF.toByte() && data[1] == 0xD8.toByte() && data[2] == 0xFF.toByte() -> "jpeg"
        data.size >= 8 &&
            data[0] == 0x89.toByte() && data[1] == 0x50.toByte() &&
            data[2] == 0x4E.toByte() && data[3] == 0x47.toByte() -> "png"
        else -> "unknown"
    }

    /**
     * 解码帧为位图(供本地人脸检测)。data 为 SDK 输出的图片文件字节,
     * 非图片文件(如裸 YUV/RGBA)无法被 BitmapFactory 解码,直接丢弃。
     */
    private fun decodeBitmap(data: ByteArray): Bitmap? {
        if (!frameFormatLogged) {
            frameFormatLogged = true
            Log.i(TAG, "帧格式实测: magic=${imageMagic(data)} size=${data.size}B")
        }
        return runCatching { BitmapFactory.decodeByteArray(data, 0, data.size) }.getOrNull()
            ?: run {
                Log.w(TAG, "frame decode failed (magic=${imageMagic(data)}, ${data.size}B)")
                null
            }
    }

    /**
     * 产出可直接上传的图片文件字节:JPEG/PNG 原样使用;
     * 其它格式(如 WebP)重编码为 JPEG,保证服务端拿到的始终是完整图片文件而非裸像素。
     */
    private fun toUploadableImage(data: ByteArray): UploadImage? {
        when (imageMagic(data)) {
            "jpeg" -> return UploadImage(data, "jpeg")
            "png" -> return UploadImage(data, "png")
            else -> Unit
        }
        val bmp = runCatching { BitmapFactory.decodeByteArray(data, 0, data.size) }.getOrNull()
        if (bmp == null) {
            Log.e(TAG, "非图片文件字节,已丢弃 (magic=unknown, ${data.size}B)")
            return null
        }
        val jpeg = java.io.ByteArrayOutputStream().use { out ->
            bmp.compress(Bitmap.CompressFormat.JPEG, PHOTO_JPEG_QUALITY, out)
            out.toByteArray()
        }
        bmp.recycle()
        Log.i(TAG, "非 JPEG/PNG 帧已重编码为 JPEG (${data.size}B -> ${jpeg.size}B)")
        return UploadImage(jpeg, "jpeg")
    }

    private fun readyLink(): CXRLink? {
        val app = App.instance
        return if (app.sharedLink != null && app.isSessionReady) app.sharedLink else null
    }

    private suspend fun ensureDetector(): FaceDetector? {
        faceDetector?.let { return it }
        return runCatching {
            FaceDetector(App.instance).also { faceDetector = it }
        }.onFailure { Log.e(TAG, "detector init failed: ${it.message}") }.getOrNull()
    }

    private suspend fun handleFrame(data: ByteArray) {
        val detector = ensureDetector() ?: return
        val bitmap = decodeBitmap(data) ?: return
        val face = runCatching { detector.detect(bitmap) }.getOrNull()
        bitmap.recycle()
        if (face != null) {
            _framesDetected.value++
            Log.d(TAG, "face detected score=${"%.2f".format(face.score)} box=${face.toList()}")
            if (policy.onFaceDetected(System.currentTimeMillis())) {
                // 服务端只接受完整 JPEG/PNG 文件字节,上传前校验实际格式
                val upload = toUploadableImage(data) ?: return
                CloudClient.send(
                    UplinkMessage.RecognizeMessage(
                        requestId = "photo-%03d".format(reqSeq.incrementAndGet()),
                        imageBase64 = Base64.encodeToString(upload.bytes, Base64.NO_WRAP),
                        deviceId = CloudClient.deviceId(),
                        sessionId = CloudClient.sessionId,
                        imageFormat = upload.format,
                        // 后端自行在完整图片检测，避免边缘负坐标及过紧裁剪影响对齐。
                    )
                )
                CloudClient.log("已上传待识别照片 ${upload.bytes.size / 1024}KB ${upload.format} (mode=${_mode.value})")
            }
        } else {
            if (policy.onNoFace()) {
                Log.i(TAG, "no face x3, sending person_left")
                CloudClient.send(
                    UplinkMessage.PersonLeftMessage(
                        requestId = "leave-%03d".format(reqSeq.incrementAndGet()),
                        deviceId = CloudClient.deviceId(),
                        sessionId = CloudClient.sessionId,
                    )
                )
                CloudClient.log("连续无人脸,已上报 person_left")
                policy.onCleared()
                _mode.value = policy.mode
                scope.launch { onPersonLeft?.invoke() }
            }
        }
    }
}
