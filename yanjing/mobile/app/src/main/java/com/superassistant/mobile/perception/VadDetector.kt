package com.superassistant.mobile.perception

import android.content.Context
import android.util.Log
import ai.onnxruntime.OnnxTensor
import ai.onnxruntime.OrtEnvironment
import ai.onnxruntime.OrtSession
import java.nio.FloatBuffer
import java.nio.LongBuffer

/**
 * Silero VAD 封装(ONNX Runtime, 模型 assets/silero_vad.onnx)。
 *
 * 输入流:CXR-L 回传的 PCM 字节流(16kHz/16bit/mono LE)。
 * 内部按 512 样本/帧推理,喂 VadStateMachine 断句。
 *
 * 官方协议(OnnxWrapper): 每帧模型输入 = 64样本上文 + 512新样本 = 576。
 * 上文取自上一帧尾部64样本,首帧为全零。只喂512裸样本时模型不报错
 * (输入形状动态)但输出恒为~0.001,等同于失效。
 */
class VadDetector(
    context: Context,
    private val machine: VadStateMachine = VadStateMachine(),
) {

    companion object {
        private const val TAG = "VadDetector"
        private const val MODEL_ASSET = "silero_vad.onnx"
        private const val STATE_SIZE = 2 * 1 * 128
        private const val CONTEXT_SIZE = 64
    }

    private val env: OrtEnvironment = OrtEnvironment.getEnvironment()
    private val session: OrtSession

    private val inputName: String
    private val stateName: String
    private val srName: String
    private val inputShape: LongArray
    private val srShape: LongArray

    private val rnnState = FloatArray(STATE_SIZE)
    private val context = FloatArray(CONTEXT_SIZE)

    private val pcmBuf = ShortArray(VadStateMachine.FRAME_SIZE * 4)
    private var pcmLen = 0

    // 诊断统计:每 ~1s 汇总一次,排查"没识别到说话"
    private var statFrames = 0
    private var statMaxProb = 0f
    private var statSumProb = 0f
    private var statPeak = 0
    private var lastSpeaking = false

    init {
        val bytes = context.assets.open(MODEL_ASSET).use { it.readBytes() }
        session = env.createSession(bytes)

        var inName = "input"; var stName = "state"; var srNameLocal = "sr"
        var inShape = longArrayOf(VadStateMachine.FRAME_SIZE.toLong())
        var srShapeLocal = longArrayOf()
        for ((name, info) in session.inputInfo) {
            val shape = (info.info as? ai.onnxruntime.TensorInfo)?.shape ?: continue
            when {
                name == "input" || shape.size <= 2 && name != "state" && name != "sr" -> {
                    inName = name
                    // 模型输入 = 64上文 + 512新样本; 2-D 喂 [1,576], 1-D 喂 [576]
                    inShape = if (shape.size >= 2) {
                        longArrayOf(1, (CONTEXT_SIZE + VadStateMachine.FRAME_SIZE).toLong())
                    } else {
                        longArrayOf((CONTEXT_SIZE + VadStateMachine.FRAME_SIZE).toLong())
                    }
                }

                name == "state" -> stName = name

                name == "sr" -> {
                    srNameLocal = name
                    srShapeLocal = if (shape.isEmpty()) longArrayOf() else longArrayOf(1)
                }
            }
        }
        inputName = inName
        stateName = stName
        srName = srNameLocal
        inputShape = inShape
        srShape = srShapeLocal
        Log.i(TAG, "init: inputs=$inName/$stName/$srNameLocal shape=${inShape.toList()} sr=${srShapeLocal.toList()}")
    }

    /**
     * 喂入 PCM 字节,返回本次断出的句子片段(通常 0 或 1 条)。
     */
    fun feedPcm(data: ByteArray, offset: Int, length: Int): List<VadStateMachine.VadSentence> {
        val out = ArrayList<VadStateMachine.VadSentence>(1)
        var i = offset
        val end = offset + length
        while (i + 1 < end) {
            val lo = data[i].toInt() and 0xFF
            val hi = data[i + 1].toInt()
            val sample = ((hi shl 8) or lo).toShort()
            pcmBuf[pcmLen++] = sample
            i += 2
            if (pcmLen == VadStateMachine.FRAME_SIZE) {
                val frame = pcmBuf.copyOf(VadStateMachine.FRAME_SIZE)
                pcmLen = 0
                val prob = infer(frame)
                machine.onFrame(prob, frame)?.let { out.add(it) }
                trackStats(prob, frame)
            }
        }
        return out
    }

    private fun trackStats(prob: Float, frame: ShortArray) {
        statFrames++
        if (prob > statMaxProb) statMaxProb = prob
        statSumProb += prob
        for (s in frame) {
            val a = if (s < 0) -s.toInt() else s.toInt()
            if (a > statPeak) statPeak = a
        }
        val speaking = machine.isSpeaking
        if (speaking != lastSpeaking) {
            Log.i(TAG, "state -> ${if (speaking) "SPEAKING" else "SILENCE"} (prob=%.3f)".format(prob))
            lastSpeaking = speaking
        }
        if (statFrames >= 31) {
            Log.i(
                TAG,
                "vad 1s: maxProb=%.3f avgProb=%.3f peak=%d speaking=%b emitted=%d"
                    .format(statMaxProb, statSumProb / statFrames, statPeak, machine.isSpeaking, machine.sentencesEmitted)
            )
            statFrames = 0
            statMaxProb = 0f
            statSumProb = 0f
            statPeak = 0
        }
    }

    fun forceFlush(): VadStateMachine.VadSentence? = machine.forceFlush()

    fun close() {
        runCatching { session.close() }
        Log.i(TAG, "closed")
    }

    /** 音频流重启时清空推理状态(LSTM状态/上文/断句缓冲),防止跨流残留 */
    fun reset() {
        rnnState.fill(0f)
        context.fill(0f)
        machine.reset()
        Log.i(TAG, "reset")
    }

    private fun infer(frame: ShortArray): Float {
        val input = FloatArray(CONTEXT_SIZE + frame.size)
        System.arraycopy(context, 0, input, 0, CONTEXT_SIZE)
        for (i in frame.indices) input[CONTEXT_SIZE + i] = frame[i] / 32768f

        val prob = OnnxTensor.createTensor(env, FloatBuffer.wrap(input), inputShape).use { t ->
            OnnxTensor.createTensor(env, FloatBuffer.wrap(rnnState), longArrayOf(2, 1, 128)).use { s ->
                OnnxTensor.createTensor(env, LongBuffer.wrap(longArrayOf(VadStateMachine.SAMPLE_RATE.toLong())), srShape).use { sr ->
                    session.run(
                        mapOf(inputName to t, stateName to s, srName to sr)
                    ).use { res ->
                        val p = (res[0] as OnnxTensor).floatBuffer.get(0)
                        val newState = (res[1] as OnnxTensor).floatBuffer
                        newState.get(rnnState)
                        newState.rewind()
                        p
                    }
                }
            }
        }

        // 官方协议: 下一帧上文 = 当前输入的尾部64样本(即当前帧尾部)
        for (i in 0 until CONTEXT_SIZE) {
            context[i] = input[input.size - CONTEXT_SIZE + i]
        }
        return prob
    }
}
