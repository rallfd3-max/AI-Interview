package com.superassistant.mobile.net

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class MessageProtocolTest {

    @Test
    fun nestedServerPersonBecomesGlassesCard() {
        val raw = """{"type":"recognition_result","success":true,"matched":true,"person":{"person_id":"student_001","name":"测试同学","school":"测试大学","major":"软件工程","description":"测试人员","created_at":"2026-10-09"},"stability":{"confirmed":true,"consistent_frames":3},"error":null}"""
        val result = MessageProtocol.decode(raw) as RecognitionResultMessage
        val card = result.toPersonInfo()!!
        assertEquals("student_001", card.id)
        assertEquals("测试同学", card.name)
        assertEquals(listOf("测试大学", "软件工程", "测试人员"), card.displayLines)
    }

    @Test
    fun unmatchedFailedOrUnconfirmedResultsNeverBecomeCards() {
        for (flags in listOf(
            "\"matched\":false",
            "\"matched\":true,\"success\":false",
            "\"matched\":true,\"stability\":{\"confirmed\":false}"
        )) {
            val result = MessageProtocol.decode("""{"type":"recognition_result",$flags,"person":{"person_id":"p1","name":"测试"}}""") as RecognitionResultMessage
            assertNull(result.toPersonInfo())
        }
    }

    @Test
    fun pendingConfirmationErrorIsAvailableToRouter() {
        val result = MessageProtocol.decode("""{"type":"recognition_result","matched":false,"person":null,"error":{"code":"PENDING_CONFIRMATION","message":"wait"}}""") as RecognitionResultMessage
        assertEquals("PENDING_CONFIRMATION", result.error?.code)
        assertNull(result.toPersonInfo())
    }

    @Test
    fun recognizeMessageEncodesWithTypeDiscriminator() {
        val json = MessageProtocol.encode(
            UplinkMessage.RecognizeMessage(
                requestId = "photo-001",
                imageBase64 = "abc123",
                deviceId = "phone-001",
                sessionId = "session-001",
            )
        )
        assertTrue(json.contains("\"type\":\"recognize\""))
        assertTrue(json.contains("\"request_id\":\"photo-001\""))
        assertTrue(json.contains("\"image_base64\":\"abc123\""))
        assertTrue(json.contains("\"device_id\":\"phone-001\""))
        assertTrue(json.contains("\"session_id\":\"session-001\""))
        assertTrue(json.contains("\"image_format\":\"jpeg\""))
        assertTrue(json.contains("\"stable_frames\":1"))
    }

    @Test
    fun recognizeMessageEncodesFaceBoxObject() {
        val json = MessageProtocol.encode(
            UplinkMessage.RecognizeMessage(
                requestId = "photo-002",
                imageBase64 = "abc",
                deviceId = "phone-001",
                sessionId = "session-001",
                faceBox = UplinkMessage.FaceBox(x = 120, y = 80, w = 260, h = 260),
            )
        )
        assertTrue(json.contains("\"face_box\":{\"x\":120,\"y\":80,\"w\":260,\"h\":260}"))
    }

    @Test
    fun recognizeWithoutFaceBoxOmitsField() {
        val json = MessageProtocol.encode(
            UplinkMessage.RecognizeMessage(
                requestId = "photo-003",
                imageBase64 = "abc",
                deviceId = "phone-001",
                sessionId = "session-001",
            )
        )
        assertTrue(!json.contains("face_box"))
    }

    @Test
    fun audioMessageEncodesDuration() {
        val json = MessageProtocol.encode(
            UplinkMessage.AudioMessage(data = "wav-bytes", durationMs = 2500)
        )
        assertTrue(json.contains("\"type\":\"audio\""))
        assertTrue(json.contains("\"duration_ms\":2500"))
    }

    @Test
    fun personLeftEncodesAsTopLevelType() {
        val json = MessageProtocol.encode(
            UplinkMessage.PersonLeftMessage(
                requestId = "leave-001",
                deviceId = "phone-001",
                sessionId = "session-001",
            )
        )
        assertTrue(json.contains("\"type\":\"person_left\""))
        assertTrue(json.contains("\"request_id\":\"leave-001\""))
    }

    @Test
    fun uplinkTypeReadsEncodedUplinkMessages() {
        // 回归:decode() 只认下行类型,上行 type 提取必须走原始 JSON
        assertEquals(
            "recognize",
            MessageProtocol.uplinkType(
                MessageProtocol.encode(
                    UplinkMessage.RecognizeMessage("r1", "x", "d1", "s1")
                )
            )
        )
        assertEquals("audio", MessageProtocol.uplinkType(MessageProtocol.encode(UplinkMessage.AudioMessage(data = "x", durationMs = 1))))
        assertEquals(
            "person_left",
            MessageProtocol.uplinkType(
                MessageProtocol.encode(UplinkMessage.PersonLeftMessage("l1", "d1", "s1"))
            )
        )
    }

    @Test
    fun uplinkTypeHandlesBadInput() {
        assertEquals("other", MessageProtocol.uplinkType("not json"))
        assertEquals("other", MessageProtocol.uplinkType("{\"no_type\":1}"))
        assertEquals("other", MessageProtocol.uplinkType("{\"type\":[1,2]}"))
    }

    @Test
    fun personInfoDecodes() {
        val raw = """
            {"type":"person_info","id":"p001","name":"张三","role":"前公司CTO",
             "relation":"5年老朋友","last_met":"2026-03-15","notes":"对技术细节敏感",
             "display_lines":["张三","前公司CTO / 5年老朋友"],"ts":1700000000}
        """.trimIndent()
        val msg = MessageProtocol.decode(raw) as PersonInfoMessage
        assertEquals("张三", msg.name)
        assertEquals("前公司CTO", msg.role)
        assertEquals("2026-03-15", msg.lastMet)
        assertEquals(2, msg.displayLines.size)
    }

    @Test
    fun personInfoToleratesCamelCaseLegacy() {
        // 兼容旧 mock 版本的 camelCase 字段,云端按 snake_case 为准
        val raw = """{"type":"person_info","id":"p1","name":"李四","lastMet":"2026-01-01","displayLines":["x"]}"""
        val msg = MessageProtocol.decode(raw) as PersonInfoMessage
        assertEquals("李四", msg.name)
    }

    @Test
    fun recognitionResultDecodes() {
        val raw = """
            {"type":"recognition_result","matched":true,"id":"202","name":"张三",
             "role":"Java 开发工程师","notes":"上次面试已完成","display_lines":["张三","Java 开发工程师"]}
        """.trimIndent()
        val msg = MessageProtocol.decode(raw) as RecognitionResultMessage
        assertEquals(true, msg.matched)
        assertEquals("张三", msg.name)
        assertEquals(2, msg.displayLines.size)
    }

    @Test
    fun recognitionResultToleratesUnknownFields() {
        // 服务端未给出 recognition_result 字段说明,未知键必须被忽略而不是解析失败
        val raw = """{"type":"recognition_result","matched":false,"similarity":0.12,"face_box":{"x":1,"y":2,"w":3,"h":4}}"""
        val msg = MessageProtocol.decode(raw) as RecognitionResultMessage
        assertEquals(false, msg.matched)
        assertNull(msg.name)
    }

    @Test
    fun hintDecodesWithDefaults() {
        val raw = """{"type":"hint","text":"他上周提到项目延期"}"""
        val msg = MessageProtocol.decode(raw) as HintMessage
        assertEquals("他上周提到项目延期", msg.text)
        assertEquals("medium", msg.priority)
        assertEquals(5000, msg.displayMs)
    }

    @Test
    fun hintDecodesSnakeCaseDisplayMs() {
        val raw = """{"type":"hint","text":"hi","priority":"high","display_ms":8000,"ts":1}"""
        val msg = MessageProtocol.decode(raw) as HintMessage
        assertEquals("high", msg.priority)
        assertEquals(8000, msg.displayMs)
    }

    @Test
    fun hintTextWithQuotesAndNewlinesSurvivesRoundTrip() {
        val tricky = "他说: \"项目\" 下周\n上线\"了\""
        val raw = """{"type":"hint","text":"${tricky.replace("\n", "\\n").replace("\"", "\\\"")}"}"""
        val msg = MessageProtocol.decode(raw) as HintMessage
        assertEquals(tricky, msg.text)
    }

    @Test
    fun clearAndErrorDecode() {
        val clear = MessageProtocol.decode("""{"type":"clear","reason":"person_left"}""") as ClearMessage
        assertEquals("person_left", clear.reason)

        val error = MessageProtocol.decode(
            """{"type":"error","code":"unknown_face","msg":"未识别此人"}"""
        ) as ErrorMessage
        assertEquals(ErrorMessage.UNKNOWN_FACE, error.code)
        assertEquals("未识别此人", error.msg)
    }

    @Test
    fun pongDecodes() {
        val msg = MessageProtocol.decode("""{"type":"pong"}""")
        assertEquals(PongMessage, msg)
    }

    @Test
    fun unknownTypeReturnsNull() {
        assertNull(MessageProtocol.decode("""{"type":"mystery"}"""))
    }

    @Test
    fun malformedJsonReturnsNull() {
        assertNull(MessageProtocol.decode("not json at all"))
        assertNull(MessageProtocol.decode("{\"type\":"))
    }
}
