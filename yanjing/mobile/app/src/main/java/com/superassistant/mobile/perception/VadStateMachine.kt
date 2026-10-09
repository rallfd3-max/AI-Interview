package com.superassistant.mobile.perception

/**
 * VAD 断句状态机(纯逻辑,与推理和 IO 解耦,可 JVM 单测)。
 *
 * 输入:每帧的语音概率(由 Silero VAD 推理产出)+ 该帧 PCM 样本。
 * 规则(依据 v2 计划 M3-T2):
 * - 概率 >= startThreshold: 语音开始,开缓冲
 * - 语音中概率 >= endThreshold 视为有效语音帧
 * - 连续静音 > 700ms: 断句,输出缓冲片段(尾部保留 160ms)
 * - 有效语音帧 < 300ms 的片段丢弃(过滤咳嗽/噪声)
 * - 片段上限 15s: 强制截断上传(超长句保护)
 */
class VadStateMachine(
    val startThreshold: Float = 0.5f,
    val endThreshold: Float = 0.35f,
    private val frameMs: Int = 32,          // 512 样本 @ 16kHz
    private val cutSilenceMs: Int = 700,    // 静音断句时长
    private val minSpeechMs: Int = 300,     // 最短有效句
    private val maxSpeechMs: Int = 15_000,  // 最长句强制截断
    private val tailMs: Int = 160,          // 断句尾部保留
) {

    data class VadSentence(val samples: ShortArray, val durationMs: Long)

    private enum class State { SILENCE, SPEAKING }

    private var state = State.SILENCE
    private var buf = ShortArray(16 * 1024)
    private var bufLen = 0
    private var speechFrames = 0     // 有效语音帧数(概率 >= endThreshold)
    private var trailingSilent = 0   // 尾部连续静音帧数
    private var totalFrames = 0      // 缓冲总帧数

    private val framesToCut = (cutSilenceMs + frameMs - 1) / frameMs
    private val minSpeechFrames = (minSpeechMs + frameMs - 1) / frameMs
    private val maxSpeechFrames = (maxSpeechMs + frameMs - 1) / frameMs
    private val tailFrames = tailMs / frameMs

    var sentencesEmitted = 0
        private set

    /** 当前是否处于语音中(诊断用) */
    val isSpeaking: Boolean get() = state == State.SPEAKING

    /**
     * 喂入一帧,若断句完成返回片段,否则 null。
     */
    fun onFrame(prob: Float, frame: ShortArray): VadSentence? {
        return when (state) {
            State.SILENCE -> {
                if (prob >= startThreshold) {
                    state = State.SPEAKING
                    bufLen = 0
                    append(frame)
                    speechFrames = 1
                    trailingSilent = 0
                    totalFrames = 1
                }
                null
            }

            State.SPEAKING -> {
                append(frame)
                totalFrames++
                if (prob >= endThreshold) {
                    speechFrames++
                    trailingSilent = 0
                } else {
                    trailingSilent++
                }
                when {
                    totalFrames >= maxSpeechFrames -> cut(trimTail = false)
                    trailingSilent >= framesToCut -> cut(trimTail = true)
                    else -> null
                }
            }
        }
    }

    /**
     * 音频流重启时复位状态,丢弃跨流残留的半句缓冲。
     */
    fun reset() {
        state = State.SILENCE
        bufLen = 0
        speechFrames = 0
        trailingSilent = 0
        totalFrames = 0
    }

    /**
     * 音频流结束时强制冲刷未断句的缓冲。
     */
    fun forceFlush(): VadSentence? {
        if (state != State.SPEAKING) return null
        return cut(trimTail = true)
    }

    private fun cut(trimTail: Boolean): VadSentence? {
        val speaking = state == State.SPEAKING
        state = State.SILENCE
        val valid = speechFrames >= minSpeechFrames
        val keepFrames = if (trimTail) {
            (speechFrames + tailFrames).coerceAtMost(totalFrames)
        } else {
            totalFrames
        }
        val samples = if (valid && speaking) buf.copyOf(keepFrames * FRAME_SIZE) else ShortArray(0)
        bufLen = 0
        speechFrames = 0
        trailingSilent = 0
        totalFrames = 0
        if (!valid) return null
        sentencesEmitted++
        return VadSentence(samples, samples.size * 1000L / SAMPLE_RATE)
    }

    private fun append(frame: ShortArray) {
        if (bufLen + frame.size > buf.size) {
            buf = buf.copyOf(maxOf(buf.size * 2, bufLen + frame.size))
        }
        System.arraycopy(frame, 0, buf, bufLen, frame.size)
        bufLen += frame.size
    }

    companion object {
        const val SAMPLE_RATE = 16_000
        const val FRAME_SIZE = 512
    }
}
