package com.superassistant.mobile.net

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.jsonObject
/**
 * 眼镜手机端 <-> 云端 WebSocket 消息协议。
 * 当前对接 face-recognition-server /ws/recognition。
 * 当前契约见 docs/plans/face-server-integration.md，旧 mock 使用 v1 协议。
 */
object MessageProtocol {

    val json: Json = Json {
        ignoreUnknownKeys = true
        encodeDefaults = true
        explicitNulls = false
    }

    fun decode(raw: String): DownlinkMessage? = runCatching {
        val obj = json.parseToJsonElement(raw) as? JsonObject ?: return null
        when (obj["type"]?.toString()?.trim('"')) {
            "recognition_result" -> json.decodeFromJsonElement(RecognitionResultMessage.serializer(), obj)
            "person_info" -> json.decodeFromJsonElement(PersonInfoMessage.serializer(), obj)
            "hint" -> json.decodeFromJsonElement(HintMessage.serializer(), obj)
            "clear" -> json.decodeFromJsonElement(ClearMessage.serializer(), obj)
            "error" -> json.decodeFromJsonElement(ErrorMessage.serializer(), obj)
            "pong" -> PongMessage
            else -> null
        }
    }.getOrNull()

    /**
     * 从已编码的上行消息 JSON 中提取 type 字段(recognize/audio/person_left)。
     * 直接读原始 JSON 而非 decode()——后者只认下行类型,上行消息会得到 null。
     * 解析失败返回 "other"(调用方按未知类型丢弃)。
     */
    fun uplinkType(raw: String): String = runCatching {
        val obj = json.parseToJsonElement(raw) as? JsonObject ?: return@runCatching null
        (obj["type"] as? JsonPrimitive)?.content
    }.getOrNull() ?: "other"

    fun encode(message: UplinkMessage): String {
        val (type, body) = when (message) {
            is UplinkMessage.RecognizeMessage -> "recognize" to json.encodeToString(UplinkMessage.RecognizeMessage.serializer(), message)
            is UplinkMessage.AudioMessage -> "audio" to json.encodeToString(UplinkMessage.AudioMessage.serializer(), message)
            is UplinkMessage.PersonLeftMessage -> "person_left" to json.encodeToString(UplinkMessage.PersonLeftMessage.serializer(), message)
        }
        val obj = MessageProtocol.json.parseToJsonElement(body).jsonObject.toMutableMap()
        obj["type"] = kotlinx.serialization.json.JsonPrimitive(type)
        return JsonObject(obj).toString()
    }
}

sealed interface UplinkMessage {
    @Serializable
    @SerialName("recognize")
    data class RecognizeMessage(
        /** 每帧唯一,用于关联 recognition_result 响应 */
        @SerialName("request_id") val requestId: String,
        /** 完整 JPEG 的 Base64(640x480, 质量70),不含 data:image 前缀 */
        @SerialName("image_base64") val imageBase64: String,
        /** 设备标识 */
        @SerialName("device_id") val deviceId: String,
        /** 同一次识别会话保持一致 */
        @SerialName("session_id") val sessionId: String,
        @SerialName("image_format") val imageFormat: String = "jpeg",
        /** 周期拍照不是连续视频帧，单张照片独立确认。 */
        @SerialName("stable_frames") val stableFrames: Int = 1,
        /** 本地检测到的人脸框(原图像素);服务端契约:不传则由服务端自行检测 */
        @SerialName("face_box") val faceBox: FaceBox? = null,
    ) : UplinkMessage

    /** 人脸框(原图像素):x/y 非负,w/h 为正 */
    @Serializable
    data class FaceBox(val x: Int, val y: Int, val w: Int, val h: Int)

    @Serializable
    @SerialName("audio")
    data class AudioMessage(
        /** base64 编码的 WAV(16kHz/16bit/mono) */
        val data: String,
        val ts: Long = System.currentTimeMillis(),
        @SerialName("duration_ms") val durationMs: Long,
    ) : UplinkMessage

    @Serializable
    @SerialName("person_left")
    data class PersonLeftMessage(
        @SerialName("request_id") val requestId: String,
        @SerialName("device_id") val deviceId: String,
        @SerialName("session_id") val sessionId: String,
    ) : UplinkMessage
}

sealed interface DownlinkMessage {
    val ts: Long
}

/**
 * 支持人脸服务的嵌套 person 结构，同时兼容旧 mock 的顶层人物字段。
 */
@Serializable
data class RecognitionResultMessage(
    val success: Boolean = true,
    val person: RecognizedPerson? = null,
    val stability: RecognitionStability? = null,
    val error: RecognitionError? = null,
    val matched: Boolean? = null,
    val id: String? = null,
    val name: String? = null,
    val role: String? = null,
    val notes: String? = null,
    /** 眼镜人物卡正文行,非空时优先于结构化字段拼装 */
    @SerialName("display_lines") val displayLines: List<String> = emptyList(),
    override val ts: Long = 0,
) : DownlinkMessage {
    fun toPersonInfo(): PersonInfoMessage? {
        if (!success || matched != true || stability?.confirmed == false) return null
        val resolvedId = person?.personId ?: id
        val resolvedName = person?.name ?: name
        if (resolvedId.isNullOrBlank() || resolvedName.isNullOrBlank()) return null
        return PersonInfoMessage(
            id = resolvedId,
            name = resolvedName,
            role = role,
            notes = person?.description ?: notes,
            displayLines = if (displayLines.isNotEmpty()) displayLines else buildList {
                listOfNotNull(person?.school, person?.major, role, person?.description ?: notes)
                    .filter { it.isNotBlank() }.forEach { add(it) }
            },
            ts = ts,
        )
    }
}

@Serializable
data class RecognizedPerson(
    @SerialName("person_id") val personId: String,
    val name: String,
    val school: String? = null,
    val major: String? = null,
    val description: String? = null,
)

@Serializable
data class RecognitionStability(val confirmed: Boolean = false)

@Serializable
data class RecognitionError(val code: String, val message: String? = null)

@Serializable
data class PersonInfoMessage(
    /** 人物唯一 ID,同一人重复识别时不变 */
    val id: String,
    /** 姓名,人物卡主标题 */
    val name: String,
    val role: String? = null,
    val relation: String? = null,
    @SerialName("last_met") val lastMet: String? = null,
    val notes: String? = null,
    /** 眼镜人物卡正文行,非空时优先于结构化字段拼装 */
    @SerialName("display_lines") val displayLines: List<String> = emptyList(),
    override val ts: Long = 0,
) : DownlinkMessage

@Serializable
data class HintMessage(
    val text: String,
    /** high:绿底黑字反色;medium/low:常规 */
    val priority: String = "medium",
    val topic: String? = null,
    @SerialName("display_ms") val displayMs: Long = 5000,
    override val ts: Long = 0,
) : DownlinkMessage

@Serializable
data class ClearMessage(
    val reason: String = "",
    override val ts: Long = 0,
) : DownlinkMessage

@Serializable
data class ErrorMessage(
    val code: String,
    val msg: String? = null,
    override val ts: Long = 0,
) : DownlinkMessage {
    companion object {
        const val UNKNOWN_FACE = "unknown_face"
        const val ASR_FAILED = "asr_failed"
        const val SERVER_ERROR = "server_error"
    }
}

@Serializable
object PongMessage : DownlinkMessage {
    override val ts: Long = 0
}
