package com.superassistant.mobile

import android.app.Application
import android.util.Log
import com.rokid.cxr.link.CXRLink
import com.superassistant.mobile.cxr.CustomViewRenderer
import com.superassistant.mobile.cxr.PhotoController
import com.superassistant.mobile.net.CloudClient
import com.superassistant.mobile.net.ClearMessage
import com.superassistant.mobile.net.DownlinkMessage
import com.superassistant.mobile.net.ErrorMessage
import com.superassistant.mobile.net.HintMessage
import com.superassistant.mobile.net.PersonInfoMessage
import com.superassistant.mobile.net.PongMessage
import com.superassistant.mobile.net.RecognitionResultMessage

class App : Application() {

    companion object {
        lateinit var instance: App
            private set
    }

    var sharedLink: CXRLink? = null
    var isSessionReady: Boolean = false

    fun requireReadyLink(): CXRLink {
        check(sharedLink != null && isSessionReady) {
            "CXRLink session not ready: complete authorization and connect first"
        }
        return sharedLink!!
    }

    fun resetSession() {
        sharedLink = null
        isSessionReady = false
    }

    override fun onCreate() {
        super.onCreate()
        instance = this
        CloudClient.setOnMessage(::routeDownlink)
        PhotoController.onPersonLeft = {
            // 本地判定人已离开:立即回待机,云端 clear 到达后幂等复位
            CustomViewRenderer.showIdle()
        }
        CloudClient.loadSavedConfig()
        CloudClient.connect()
    }

    /**
     * 下行消息统一路由:云端应答 -> 感知调度 + 眼镜界面。
     */
    private fun routeDownlink(msg: DownlinkMessage) {
        CloudClient.log("下行: ${msg::class.simpleName}")
        when (msg) {
            is RecognitionResultMessage -> {
                Log.i(TAG, "route: recognition_result matched=${msg.matched} id=${msg.id} name=${msg.name}")
                val personInfo = msg.toPersonInfo()
                if (personInfo != null) {
                    PhotoController.onPersonIdentified(personInfo.id)
                    CustomViewRenderer.showPersonCard(personInfo.name, personInfo.displayLines)
                } else if (msg.error?.code == "PENDING_CONFIRMATION") {
                    // 新人物尚未确认，保留上一张已确认卡片。
                    CloudClient.log("等待连续帧确认")
                } else if (!msg.success) {
                    CloudClient.log("识别失败: ${msg.error?.code} ${msg.error?.message.orEmpty()}")
                } else {
                    PhotoController.onCleared()
                    CustomViewRenderer.showIdle()
                }
            }

            is PersonInfoMessage -> {
                Log.i(TAG, "route: person_info id=${msg.id} name=${msg.name}")
                PhotoController.onPersonIdentified(msg.id)
                CustomViewRenderer.showPersonCard(
                    msg.name,
                    cardLines(msg.displayLines, msg.role, msg.relation, msg.lastMet, msg.notes),
                )
            }

            is ClearMessage -> {
                Log.i(TAG, "route: clear reason=${msg.reason}")
                PhotoController.onCleared()
                CustomViewRenderer.showIdle()
            }

            is ErrorMessage -> {
                Log.w(TAG, "route: error code=${msg.code} msg=${msg.msg}")
                if (msg.code == ErrorMessage.UNKNOWN_FACE) {
                    // 协议约定:unknown_face 需清除当前人物卡,避免残留上一个人的信息
                    CustomViewRenderer.showIdle()
                }
            }

            is HintMessage -> {
                Log.i(TAG, "route: hint priority=${msg.priority} text=${msg.text}")
                CustomViewRenderer.showHint(msg.text, msg.priority, msg.displayMs)
            }

            is PongMessage -> Unit
        }
    }

    /**
     * 人物卡正文行:云端 displayLines 优先,否则本地从结构化字段拼装。
     */
    private fun cardLines(
        displayLines: List<String>,
        role: String?,
        relation: String?,
        lastMet: String?,
        notes: String?,
    ): List<String> {
        if (displayLines.isNotEmpty()) return displayLines
        return buildList {
            listOfNotNull(
                listOfNotNull(role, relation).joinToString(" / ").ifEmpty { null },
                lastMet?.let { "上次见面:$it" },
                notes?.let { "注意:$it" },
            ).forEach { add(it) }
        }
    }
}

private const val TAG = "SuperApp"
