package com.superassistant.mobile.perception

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class VadStateMachineTest {

    private val frame = ShortArray(VadStateMachine.FRAME_SIZE) { 1000 }

    private fun feed(
        p: VadStateMachine,
        speechFrames: Int,
        silenceFrames: Int,
    ): List<VadStateMachine.VadSentence> {
        val out = ArrayList<VadStateMachine.VadSentence>()
        repeat(speechFrames) { p.onFrame(0.9f, frame)?.let { out.add(it) } }
        repeat(silenceFrames) { p.onFrame(0.1f, frame)?.let { out.add(it) } }
        return out
    }

    @Test
    fun `静音流不产生片段`() {
        val p = VadStateMachine()
        repeat(100) { assertNull(p.onFrame(0.1f, frame)) }
        assertEquals(0, p.sentencesEmitted)
    }

    @Test
    fun `两句话切出两个片段`() {
        val p = VadStateMachine()
        // 句1: 1s 语音 + 1s 静音
        val s1 = feed(p, speechFrames = 31, silenceFrames = 31)
        // 句2: 0.5s 语音 + 1s 静音
        val s2 = feed(p, speechFrames = 16, silenceFrames = 31)
        val all = s1 + s2
        assertEquals(2, all.size)
        assertEquals(2, p.sentencesEmitted)
    }

    @Test
    fun `断句静音阈值不足不断句`() {
        val p = VadStateMachine()
        val out = feed(p, speechFrames = 31, silenceFrames = 21)  // 672ms < 700ms
        assertEquals(0, out.size)
    }

    @Test
    fun `短于300ms的语音被丢弃`() {
        val p = VadStateMachine()
        // 9 帧 ≈ 288ms 语音 + 长静音
        val out = feed(p, speechFrames = 9, silenceFrames = 31)
        assertEquals(0, out.size)
        assertEquals(0, p.sentencesEmitted)
    }

    @Test
    fun `片段时长与样本数一致且含尾部保留`() {
        val p = VadStateMachine()
        val out = feed(p, speechFrames = 31, silenceFrames = 25)
        assertEquals(1, out.size)
        val s = out[0]
        // 31 帧语音 + 5 帧尾部(160ms/32ms) = 36 帧
        assertEquals(36 * VadStateMachine.FRAME_SIZE, s.samples.size)
        assertEquals(s.samples.size * 1000L / 16_000, s.durationMs)
        assertTrue(s.durationMs in 1000..1300)
    }

    @Test
    fun `超长句15秒强制截断`() {
        val p = VadStateMachine()
        var cut: VadStateMachine.VadSentence? = null
        var frames = 0
        while (cut == null && frames < 2000) {
            cut = p.onFrame(0.9f, frame)
            frames++
        }
        assertNotNull(cut)
        assertEquals(15_000 / 32 + 1, frames)  // 469 帧处截断
        assertTrue(cut!!.durationMs <= 15_100)
    }

    @Test
    fun `连续静音不重复断句`() {
        val p = VadStateMachine()
        repeat(31) { p.onFrame(0.9f, frame) }
        // 40 帧静音: 第 22 帧断句一次,后续静音不再产出
        val out = ArrayList<VadStateMachine.VadSentence>()
        repeat(40) { p.onFrame(0.1f, frame)?.let { out.add(it) } }
        assertEquals(1, out.size)
    }

    @Test
    fun `forceFlush 冲刷未断句语音`() {
        val p = VadStateMachine()
        repeat(31) { p.onFrame(0.9f, frame) }  // 1s 语音未静音
        val s = p.forceFlush()
        assertNotNull(s)
        // flush 时无尾部静音可裁,保留全部已缓冲语音
        assertEquals(31 * VadStateMachine.FRAME_SIZE, s!!.samples.size)
        assertNull(p.forceFlush())  // 已复位,再 flush 无产出
    }

    @Test
    fun `forceFlush 对静音态无产出`() {
        val p = VadStateMachine()
        repeat(50) { p.onFrame(0.1f, frame) }
        assertNull(p.forceFlush())
    }
}
