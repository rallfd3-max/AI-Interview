package com.superassistant.mobile.cxr

import android.util.Log
import com.rokid.cxr.link.CXRLink
import com.rokid.cxr.link.callbacks.ICustomViewCbk
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put

/**
 * 眼镜界面渲染器。
 *
 * SDK 约束:customViewOpen 仅在视图关闭状态下生效,已打开时再次调用会被静默忽略。
 * 因此界面切换统一走 close -> onCustomViewClosed -> open 时序;
 * 上行消息竞争(如 clear/person_info 快速交替)由 250ms 防抖合并。
 */
object CustomViewRenderer {

    private const val TAG = "CustomViewRenderer"

    private const val GREEN = "#00FF00"
    private const val GREEN_MID = "#00C000"
    private const val GREEN_DIM = "#009000"
    private const val BLACK = "#FF000000"

    private const val OPEN_RETRY_MAX = 3
    private const val DOT_INTERVAL_MS = 800L
    private const val CARD_MAX_LINES = 5

    /** 提示区节点 id(协议契约:仅局部更新 tv_hint,人物卡不动) */
    private const val HINT_BOX_ID = "hint_box"
    private const val HINT_TEXT_ID = "tv_hint"
    private const val HINT_DEFAULT_MS = 5_000L

    /** 切换防抖:合并短时间内的多次界面切换请求 */
    private const val SWITCH_DEBOUNCE_MS = 250L

    /** close 后等待 onCustomViewClosed 的兜底超时,超时则直接 open */
    private const val CLOSE_TIMEOUT_MS = 1_500L

    private enum class Screen { NONE, IDLE, PERSON }

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)

    private var link: CXRLink? = null
    private var screen = Screen.NONE

    /** 当前目标界面的 JSON,open 失败重试时重发 */
    private var currentJson: String = ""

    /** close 完成后待 open 的 JSON(切换中转态) */
    private var pendingJson: String? = null

    private var dotJob: Job? = null
    private var debounceJob: Job? = null
    private var closeTimeoutJob: Job? = null
    private var hintJob: Job? = null
    private var openRetries = 0

    private val _viewOpened = MutableStateFlow(false)
    val viewOpened: StateFlow<Boolean> = _viewOpened.asStateFlow()

    private val _lastError = MutableStateFlow("")
    val lastError: StateFlow<String> = _lastError.asStateFlow()

    private val customViewCallback = object : ICustomViewCbk {
        override fun onCustomViewOpened() {
            Log.i(TAG, "onCustomViewOpened: screen=$screen")
            openRetries = 0
            _viewOpened.value = true
            _lastError.value = ""
            if (screen == Screen.IDLE) startDotAnimation()
        }

        override fun onCustomViewUpdated() {
            Log.d(TAG, "onCustomViewUpdated")
        }

        override fun onCustomViewClosed() {
            Log.i(TAG, "onCustomViewClosed: pending=${pendingJson != null}")
            _viewOpened.value = false
            stopDotAnimation()
            closeTimeoutJob?.cancel()
            val json = pendingJson
            pendingJson = null
            // 主动切换触发的关闭:立即打开目标界面(确保主线程调用 SDK)
            if (json != null) {
                scope.launch { link?.customViewOpen(json) }
            }
        }

        override fun onCustomViewIconsSent() {}

        override fun onCustomViewError(code: Int, msg: String?) {
            Log.e(TAG, "onCustomViewError: code=$code msg=$msg (opened=${_viewOpened.value})")
            if (!_viewOpened.value) {
                _lastError.value = "界面打开失败 code=$code ${msg ?: ""}"
                retryOpen()
            }
        }
    }

    fun bind(link: CXRLink) {
        this.link = link
        screen = Screen.NONE
        stopAllJobs()
        link.setCXRCustomViewCbk(customViewCallback)
        Log.i(TAG, "bind: callback registered")
    }

    fun showIdle() {
        Log.i(TAG, "showIdle (requested)")
        scheduleSwitch(Screen.IDLE) { idleViewJson() }
    }

    /**
     * 人物信息卡:姓名大字 + 正文行(≤5 行),常驻显示,不自动消失。
     */
    fun showPersonCard(name: String, lines: List<String>) {
        Log.i(TAG, "showPersonCard: $name (${lines.size} lines)")
        scheduleSwitch(Screen.PERSON) { personCardJson(name, lines) }
    }

    /**
     * 提示区:仅局部更新 tv_hint/hint_box,人物卡不动。
     * 高优先级反色(绿底黑字),displayMs 后自动清空。
     */
    fun showHint(text: String, priority: String = "medium", displayMs: Long = HINT_DEFAULT_MS) {
        Log.i(TAG, "showHint: \"$text\" (priority=$priority displayMs=${displayMs}ms screen=$screen)")
        hintJob?.cancel()
        if (!_viewOpened.value) {
            Log.w(TAG, "showHint: view not open, hint dropped")
            return
        }
        val high = priority == "high"
        updateNodes(
            updateNode(HINT_BOX_ID, "backgroundColor" to if (high) GREEN else BLACK),
            updateNode(HINT_TEXT_ID, "text" to text, "textColor" to if (high) BLACK else GREEN),
        )
        hintJob = scope.launch {
            delay(displayMs.coerceIn(1_000L, 30_000L))
            clearHint()
        }
    }

    fun clearHint() {
        hintJob?.cancel()
        updateNodes(
            updateNode(HINT_BOX_ID, "backgroundColor" to BLACK),
            updateNode(HINT_TEXT_ID, "text" to "", "textColor" to GREEN),
        )
    }

    fun close() {
        Log.i(TAG, "close")
        screen = Screen.NONE
        stopAllJobs()
        pendingJson = null
        link?.customViewClose()
    }

    fun reset() {
        screen = Screen.NONE
        stopAllJobs()
        pendingJson = null
        openRetries = 0
        _viewOpened.value = false
        _lastError.value = ""
    }

    private fun stopAllJobs() {
        stopDotAnimation()
        debounceJob?.cancel()
        closeTimeoutJob?.cancel()
        hintJob?.cancel()
    }

    /**
     * 防抖入口:短时间内的多次切换只保留最后一次。
     * 所有状态变更收敛到主线程协程,避免多线程并发竞争。
     */
    private fun scheduleSwitch(target: Screen, buildJson: () -> String) {
        val json = buildJson()
        // 目标界面与当前一致且已打开:跳过重建,避免周期性消息触发反复 close/open 闪切
        if (target == screen && _viewOpened.value && json == currentJson) {
            Log.d(TAG, "scheduleSwitch: $target already shown, skip")
            return
        }
        scope.launch {
            debounceJob?.cancel()
            debounceJob = scope.launch {
                delay(SWITCH_DEBOUNCE_MS)
                doSwitch(target, json)
            }
        }
    }

    private fun doSwitch(target: Screen, json: String) {
        val l = link ?: run {
            Log.w(TAG, "doSwitch: no link bound")
            return
        }
        stopDotAnimation()
        hintJob?.cancel()
        screen = target
        currentJson = json
        if (_viewOpened.value) {
            // 视图已打开:必须先 close 再 open(open 对已打开视图是静默 no-op)
            pendingJson = json
            l.customViewClose()
            closeTimeoutJob?.cancel()
            closeTimeoutJob = scope.launch {
                delay(CLOSE_TIMEOUT_MS)
                if (pendingJson != null) {
                    Log.w(TAG, "close timeout, force open")
                    pendingJson = null
                    l.customViewOpen(json)
                }
            }
        } else {
            l.customViewOpen(json)
        }
    }

    private fun retryOpen() {
        if (screen == Screen.NONE || currentJson.isEmpty()) return
        if (openRetries >= OPEN_RETRY_MAX) {
            Log.e(TAG, "retryOpen: giving up after $openRetries attempts")
            return
        }
        openRetries++
        Log.w(TAG, "retryOpen: attempt $openRetries/$OPEN_RETRY_MAX in 2s")
        scope.launch {
            delay(2000)
            if (!_viewOpened.value && screen != Screen.NONE) {
                link?.customViewOpen(currentJson)
            }
        }
    }

    private fun startDotAnimation() {
        stopDotAnimation()
        dotJob = scope.launch {
            val frames = listOf("·", "· ·", "· · ·")
            var i = 0
            while (true) {
                updateText("idle_dots", frames[i % frames.size])
                i++
                delay(DOT_INTERVAL_MS)
            }
        }
    }

    private fun stopDotAnimation() {
        dotJob?.cancel()
        dotJob = null
    }

    private fun updateText(id: String, text: String) {
        updateNodes(updateNode(id, "text" to text))
    }

    private fun updateNodes(vararg nodes: JsonObject) {
        if (nodes.isEmpty()) return
        link?.customViewUpdate(
            buildJsonArray { nodes.forEach { add(it) } }.toString()
        )
    }

    private fun updateNode(id: String, vararg props: Pair<String, String>): JsonObject = buildJsonObject {
        put("action", "update")
        put("id", id)
        put("props", buildJsonObject { props.forEach { (k, v) -> put(k, v) } })
    }

    private fun idleViewJson(): String = buildJsonObject {
        put("type", "LinearLayout")
        put(
            "props",
            buildJsonObject {
                put("id", "root")
                put("layout_width", "match_parent")
                put("layout_height", "match_parent")
                put("orientation", "vertical")
                put("gravity", "center")
                put("backgroundColor", BLACK)
            }
        )
        put(
            "children",
            buildJsonArray {
                add(textNode("idle_title", "超级助手", 28, GREEN, bold = true))
                add(textNode("idle_dots", "· · ·", 22, GREEN_MID))
                add(textNode("idle_status", "待机中 · 等待识别", 14, GREEN_DIM))
                add(hintBoxJson())
            }
        )
    }.toString()

    private fun personCardJson(name: String, lines: List<String>): String = buildJsonObject {
        put("type", "LinearLayout")
        put(
            "props",
            buildJsonObject {
                put("id", "root")
                put("layout_width", "match_parent")
                put("layout_height", "match_parent")
                put("orientation", "vertical")
                put("gravity", "center")
                put("backgroundColor", BLACK)
            }
        )
        put(
            "children",
            buildJsonArray {
                add(textNode("card_name", name, 32, GREEN, bold = true))
                lines.take(CARD_MAX_LINES).forEachIndexed { i, line ->
                    add(textNode("card_line_$i", line, 20, GREEN_MID))
                }
                add(hintBoxJson())
            }
        )
    }.toString()

    /**
     * 提示区容器:常规状态空文本不可见,高优先级时整条反色(绿底黑字)。
     * 待机界面与人物卡均携带,布局重建后提示自然复位。
     */
    private fun hintBoxJson(): JsonObject = buildJsonObject {
        put("type", "LinearLayout")
        put(
            "props",
            buildJsonObject {
                put("id", HINT_BOX_ID)
                put("layout_width", "match_parent")
                put("layout_height", "wrap_content")
                put("orientation", "vertical")
                put("gravity", "center")
                put("backgroundColor", BLACK)
                put("marginTop", "24dp")
            }
        )
        put(
            "children",
            buildJsonArray {
                add(textNode(HINT_TEXT_ID, "", 22, GREEN))
            }
        )
    }

    private fun textNode(
        id: String,
        text: String,
        sizeSp: Int,
        color: String,
        bold: Boolean = false,
    ): JsonObject = buildJsonObject {
        put("type", "TextView")
        put(
            "props",
            buildJsonObject {
                put("id", id)
                put("layout_width", "wrap_content")
                put("layout_height", "wrap_content")
                put("text", text)
                put("textColor", color)
                put("textSize", "${sizeSp}sp")
                put("gravity", "center")
                if (bold) put("textStyle", "bold")
                put("marginTop", "10dp")
            }
        )
    }
}
