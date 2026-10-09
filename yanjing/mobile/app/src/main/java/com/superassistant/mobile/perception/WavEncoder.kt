package com.superassistant.mobile.perception

/**
 * PCM → WAV 封装(纯逻辑,可 JVM 单测)。输出 16kHz/16bit/mono 标准 44 字节头。
 */
object WavEncoder {

    fun encode(samples: ShortArray, sampleRate: Int = 16_000): ByteArray {
        val dataSize = samples.size * 2
        val out = ByteArray(44 + dataSize)
        var p = 0

        fun str(s: String) {
            for (c in s) out[p++] = c.code.toByte()
        }

        fun i32(v: Int) {
            out[p++] = v.toByte()
            out[p++] = (v shr 8).toByte()
            out[p++] = (v shr 16).toByte()
            out[p++] = (v shr 24).toByte()
        }

        fun i16(v: Int) {
            out[p++] = v.toByte()
            out[p++] = (v shr 8).toByte()
        }

        str("RIFF")
        i32(36 + dataSize)
        str("WAVE")
        str("fmt ")
        i32(16)                    // fmt chunk size
        i16(1)                     // PCM
        i16(1)                     // mono
        i32(sampleRate)
        i32(sampleRate * 2)        // byte rate = sr * channels * bits/8
        i16(2)                     // block align
        i16(16)                    // bits per sample
        str("data")
        i32(dataSize)
        for (s in samples) i16(s.toInt())
        return out
    }
}
