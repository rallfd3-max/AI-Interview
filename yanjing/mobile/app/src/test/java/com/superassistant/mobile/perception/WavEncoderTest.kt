package com.superassistant.mobile.perception

import org.junit.Assert.assertEquals
import org.junit.Test

class WavEncoderTest {

    @Test
    fun `标准44字节头字段正确`() {
        val samples = ShortArray(1600) { it.toShort() }  // 100ms
        val wav = WavEncoder.encode(samples)
        assertEquals(44 + 3200, wav.size)

        fun str(at: Int, len: Int) = wav.copyOfRange(at, at + len).toString(Charsets.US_ASCII)
        fun i32(at: Int) = (wav[at].toInt() and 0xFF) or
                ((wav[at + 1].toInt() and 0xFF) shl 8) or
                ((wav[at + 2].toInt() and 0xFF) shl 16) or
                ((wav[at + 3].toInt() and 0xFF) shl 24)

        assertEquals("RIFF", str(0, 4))
        assertEquals(36 + 3200, i32(4))
        assertEquals("WAVE", str(8, 4))
        assertEquals("fmt ", str(12, 4))
        assertEquals(16, i32(16))          // fmt size
        assertEquals(1, wav[20].toInt())   // PCM
        assertEquals(1, wav[22].toInt())   // mono
        assertEquals(16_000, i32(24))      // sample rate
        assertEquals(32_000, i32(28))      // byte rate
        assertEquals(2, wav[32].toInt())   // block align
        assertEquals(16, wav[34].toInt())  // bits
        assertEquals("data", str(36, 4))
        assertEquals(3200, i32(40))
    }

    @Test
    fun `小端样本字节序正确`() {
        val wav = WavEncoder.encode(shortArrayOf(0x1234.toShort(), (-2).toShort()))
        assertEquals(0x34, wav[44].toInt() and 0xFF)
        assertEquals(0x12, wav[45].toInt() and 0xFF)
        assertEquals(0xFE, wav[46].toInt() and 0xFF)
        assertEquals(0xFF, wav[47].toInt() and 0xFF)
    }

    @Test
    fun `空样本输出仅头`() {
        assertEquals(44, WavEncoder.encode(ShortArray(0)).size)
    }
}
