package com.superassistant.mobile.perception

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class FaceFlowPolicyTest {

    @Test
    fun `IDLE 模式下检测到人脸立即上传`() {
        val p = FaceFlowPolicy()
        assertTrue(p.onFaceDetected(1_000))
    }

    @Test
    fun `IDLE 模式下 5 秒内重复人脸不上传`() {
        val p = FaceFlowPolicy()
        assertTrue(p.onFaceDetected(1_000))
        assertFalse(p.onFaceDetected(3_000))
        assertFalse(p.onFaceDetected(5_999))
        assertTrue(p.onFaceDetected(6_000))
    }

    @Test
    fun `连续 3 次无人脸触发 person_left`() {
        val p = FaceFlowPolicy()
        p.onFaceDetected(1_000)
        p.onPersonIdentified("p001")
        assertFalse(p.onNoFace())
        assertFalse(p.onNoFace())
        assertTrue(p.onNoFace())
    }

    @Test
    fun `IDLE 态无人脸不触发 person_left`() {
        val p = FaceFlowPolicy()
        assertFalse(p.onNoFace())
        assertFalse(p.onNoFace())
        assertFalse(p.onNoFace())  // 无会话可清,不上报
    }

    @Test
    fun `检测到人脸重置无脸计数`() {
        val p = FaceFlowPolicy()
        p.onFaceDetected(1_000)
        p.onPersonIdentified("p001")
        p.onNoFace()
        p.onNoFace()
        p.onFaceDetected(2_000)
        assertFalse(p.onNoFace())
        assertFalse(p.onNoFace())
        assertTrue(p.onNoFace())
    }

    @Test
    fun `ACTIVE 模式下 30 秒周期重新上传`() {
        val p = FaceFlowPolicy()
        p.onFaceDetected(1_000)
        p.onPersonIdentified("p001")
        assertEquals(FaceFlowPolicy.Mode.ACTIVE, p.mode)
        assertFalse(p.onFaceDetected(5_000))  // ACTIVE 间隙内不上传
        assertTrue(p.onFaceDetected(31_000))  // 30s 周期到
    }

    @Test
    fun `识别后切换 ACTIVE 并锁定人物`() {
        val p = FaceFlowPolicy()
        p.onPersonIdentified("p001")
        assertEquals(FaceFlowPolicy.Mode.ACTIVE, p.mode)
        assertEquals("p001", p.currentPersonId)
    }

    @Test
    fun `clear 后回 IDLE 且节流计时清零`() {
        val p = FaceFlowPolicy()
        p.onFaceDetected(1_000)
        p.onPersonIdentified("p001")
        p.onCleared()
        assertEquals(FaceFlowPolicy.Mode.IDLE, p.mode)
        assertEquals(null, p.currentPersonId)
        assertTrue(p.onFaceDetected(2_000))
    }

    @Test
    fun `person_left 触发后 onCleared 复位不再触发`() {
        val p = FaceFlowPolicy()
        p.onFaceDetected(1_000)
        p.onPersonIdentified("p001")
        p.onNoFace(); p.onNoFace(); p.onNoFace()
        p.onCleared()  // PhotoController 触发后立即复位
        assertFalse(p.onNoFace())
    }

    @Test
    fun `识别到离开到回来循环 20 次无异常`() {
        // M4-T1 验收:识别→离开→回来→再识别循环 20 次,状态机不卡死
        val p = FaceFlowPolicy()
        var t = 0L
        repeat(20) { i ->
            // 识别:人脸出现,上传,云端回 person_info
            t += 1_000
            assertTrue(p.onFaceDetected(t))
            p.onPersonIdentified("p00$i")
            assertEquals(FaceFlowPolicy.Mode.ACTIVE, p.mode)
            assertEquals("p00$i", p.currentPersonId)

            // 离开:连续 3 次无人脸,触发 person_left
            assertFalse(p.onNoFace())
            assertFalse(p.onNoFace())
            assertTrue(p.onNoFace())
            p.onCleared()
            assertEquals(FaceFlowPolicy.Mode.IDLE, p.mode)
            assertEquals(null, p.currentPersonId)
            assertFalse(p.onNoFace())  // 复位后不再误触发
        }
    }
}
