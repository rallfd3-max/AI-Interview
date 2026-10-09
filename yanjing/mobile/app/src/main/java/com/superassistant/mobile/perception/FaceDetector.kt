package com.superassistant.mobile.perception

import android.content.Context
import android.graphics.Bitmap
import android.util.Log
import com.google.mediapipe.framework.image.BitmapImageBuilder
import com.google.mediapipe.tasks.core.BaseOptions
import com.google.mediapipe.tasks.vision.core.RunningMode
import com.google.mediapipe.tasks.vision.facedetector.FaceDetector
import com.google.mediapipe.tasks.vision.facedetector.FaceDetectorResult

/**
 * BlazeFace 人脸检测封装(MediaPipe Tasks, 模型 assets/blazeface_short_range.tflite)。
 *
 * 用途:判断拍照帧中是否存在人脸(供上传决策),不做人脸识别。
 * 线程安全性:内部无锁,调用方(PhotoController)保证串行调用。
 */
class FaceDetector(context: Context, private val minConfidence: Float = 0.6f) {

    companion object {
        private const val TAG = "FaceDetector"
        private const val MODEL_ASSET = "blazeface_short_range.tflite"
    }

    /** left/top/right/bottom 为原图像素坐标 */
    data class FaceBox(
        val score: Float,
        val left: Int,
        val top: Int,
        val right: Int,
        val bottom: Int,
    ) {
        val width: Int get() = right - left
        val height: Int get() = bottom - top

        /** 日志用简写: [x, y, w, h] */
        fun toList(): List<Int> = listOf(left, top, width, height)
    }

    private val detector: FaceDetector

    init {
        val options = FaceDetector.FaceDetectorOptions.builder()
            .setBaseOptions(
                BaseOptions.builder().setModelAssetPath(MODEL_ASSET).build()
            )
            .setRunningMode(RunningMode.IMAGE)
            .setMinDetectionConfidence(minConfidence)
            .build()
        detector = FaceDetector.createFromOptions(context, options)
        Log.i(TAG, "init: model=$MODEL_ASSET threshold=$minConfidence")
    }

    /**
     * 检测一帧,返回置信度最高的人脸框;无脸返回 null。
     */
    fun detect(frame: Bitmap): FaceBox? {
        val result: FaceDetectorResult = detector.detect(BitmapImageBuilder(frame).build())
        val best = result.detections().maxByOrNull { it.categories().firstOrNull()?.score() ?: 0f }
            ?: return null
        val score = best.categories().firstOrNull()?.score() ?: 0f
        if (score < minConfidence) return null
        val box = best.boundingBox()
        return FaceBox(
            score,
            box.left.toInt(),
            box.top.toInt(),
            box.right.toInt(),
            box.bottom.toInt(),
        )
    }

    fun close() {
        runCatching { detector.close() }
        Log.i(TAG, "closed")
    }
}
