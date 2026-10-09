package com.superassistant.mobile.perception

/**
 * 人脸拍照上报策略(纯逻辑,与 IO 解耦,可 JVM 单测)。
 *
 * 规则(依据 v2 计划 M2-T3):
 * - IDLE(未识别到人): 检测到人脸后上传,同 5s 内不重复上传
 * - ACTIVE(会话中):   30s 周期重新上传刷新人物信息
 * - 连续 3 次拍照无人脸: 触发 person_left,回 IDLE
 */
class FaceFlowPolicy(
    private val idleUploadGapMs: Long = 5_000L,
    private val activeUploadGapMs: Long = 30_000L,
    private val noFaceLimit: Int = 3,
) {

    enum class Mode { IDLE, ACTIVE }

    var mode: Mode = Mode.IDLE
        private set

    var currentPersonId: String? = null
        private set

    private var lastUploadTs = -1L
    private var noFaceStreak = 0

    /**
     * 检测到人脸后的决策:是否应上传该帧。
     */
    fun onFaceDetected(now: Long): Boolean {
        noFaceStreak = 0
        val gap = if (mode == Mode.ACTIVE) activeUploadGapMs else idleUploadGapMs
        if (lastUploadTs >= 0 && now - lastUploadTs < gap) return false
        lastUploadTs = now
        return true
    }

    /**
     * 拍到无人脸帧后的决策:是否应上报 person_left。
     * 仅 ACTIVE(会话中)有意义——IDLE 态无人在镜头前本就无会话可清。
     */
    fun onNoFace(): Boolean {
        noFaceStreak++
        if (noFaceStreak < noFaceLimit) return false
        return mode == Mode.ACTIVE
    }

    /**
     * 云端返回 person_info:进入 ACTIVE,锁定当前人物。
     */
    fun onPersonIdentified(id: String) {
        mode = Mode.ACTIVE
        currentPersonId = id
        noFaceStreak = 0
    }

    /**
     * 云端返回 clear(或 person_left 已发出):回 IDLE。
     */
    fun onCleared() {
        mode = Mode.IDLE
        currentPersonId = null
        noFaceStreak = 0
        lastUploadTs = -1L
    }
}
