package com.superassistant.mobile

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.ui.platform.LocalContext
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.superassistant.mobile.cxr.AudioMonitor
import com.superassistant.mobile.cxr.CustomViewRenderer
import com.superassistant.mobile.cxr.CxrSessionManager
import com.superassistant.mobile.cxr.PhotoController
import com.superassistant.mobile.net.CloudClient
import com.superassistant.mobile.net.UplinkMessage
import com.superassistant.mobile.perception.FaceFlowPolicy
import com.superassistant.mobile.service.KeepAliveService
import kotlinx.coroutines.flow.map

class MainActivity : ComponentActivity() {

    private val notifPermLauncher =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) { }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        requestNotifPermission()
        CxrSessionManager.checkCompanionInstalled(this)
        CxrSessionManager.restoreSession(this)
        setContent {
            MaterialTheme {
                PermissionAutoRequest()
                Scaffold { padding ->
                    StatusPanel(
                        modifier = Modifier.padding(padding),
                        onRequestAuth = { CxrSessionManager.requestAuthorization(this) },
                        onReconnect = { CxrSessionManager.startSession(this) },
                        onShowIdle = { CustomViewRenderer.showIdle() },
                        onCloseView = { CustomViewRenderer.close() },
                    )
                }
            }
        }
    }

    /** Android 13+ 需运行时申请通知权限,前台服务通知才可见(拒绝不影响保活) */
    private fun requestNotifPermission() {
        if (Build.VERSION.SDK_INT >= 33 &&
            checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED
        ) {
            notifPermLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
        }
    }

    override fun onResume() {
        super.onResume()
        // MIUI 在 Application.onCreate 阶段(Activity 未 resume)会拒绝 FGS 启动,故在 resume 后启动
        KeepAliveService.start(this)
    }

    @Deprecated("Deprecated in Java")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == CxrSessionManager.REQUEST_CODE_AUTH) {
            CxrSessionManager.handleAuthResult(resultCode, data)
            if (CxrSessionManager.authenticated.value && !CxrSessionManager.glassPermissionsReady()) {
                CloudClient.log("警告: 眼镜端相机/麦克风权限未授予,拍照与音频不可用")
            }
        }
    }

    private var authRequestedOnce = false

    /** 会话就绪后若设备权限缺失,自动重新请求授权(每次启动至多一次) */
    @Composable
    private fun PermissionAutoRequest() {
        val ready by CxrSessionManager.sessionReady.collectAsState()
        LaunchedEffect(ready) {
            if (ready && !authRequestedOnce && !CxrSessionManager.glassPermissionsReady()) {
                authRequestedOnce = true
                CloudClient.log("检测到眼镜权限缺失,重新请求授权")
                CxrSessionManager.requestAuthorization(this@MainActivity)
            }
        }
    }
}

@Composable
private fun StatusPanel(
    modifier: Modifier = Modifier,
    onRequestAuth: () -> Unit,
    onReconnect: () -> Unit,
    onShowIdle: () -> Unit,
    onCloseView: () -> Unit,
) {
    val scroll = rememberScrollState()
    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(scroll)
            .padding(16.dp),
    ) {
        Text("超级助手 · 状态面板", fontSize = 22.sp)
        Spacer(Modifier.height(16.dp))

        CxrSection(onRequestAuth, onReconnect, onShowIdle, onCloseView)
        Spacer(Modifier.height(24.dp))
        CloudSection()
        Spacer(Modifier.height(24.dp))
        PerceptionSection()
        Spacer(Modifier.height(24.dp))
        LogSection()
    }
}

@Composable
private fun SectionTitle(text: String) {
    Text(text, fontSize = 16.sp, color = MaterialTheme.colorScheme.primary)
    Spacer(Modifier.height(8.dp))
}

@Composable
private fun StatusRow(label: String, ok: Boolean) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 3.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
    ) {
        Text(text = label, fontSize = 14.sp)
        Text(
            text = if (ok) "✓" else "✗",
            fontSize = 14.sp,
            color = if (ok) Color(0xFF1B9E4B) else Color(0xFF888888),
        )
    }
}

@Composable
private fun CxrSection(
    onRequestAuth: () -> Unit,
    onReconnect: () -> Unit,
    onShowIdle: () -> Unit,
    onCloseView: () -> Unit,
) {
    val companionInstalled by CxrSessionManager.companionInstalled.collectAsState()
    val authenticated by CxrSessionManager.authenticated.collectAsState()
    val cxrlConnected by CxrSessionManager.cxrlConnected.collectAsState()
    val btConnected by CxrSessionManager.btConnected.collectAsState()
    val sessionReady by CxrSessionManager.sessionReady.collectAsState()
    val wearing by CxrSessionManager.wearing.collectAsState()
    val viewOpened by CustomViewRenderer.viewOpened.collectAsState()
    val sessionError by CxrSessionManager.lastError.collectAsState()
    val viewError by CustomViewRenderer.lastError.collectAsState()

    SectionTitle("眼镜链路 (CXR-L)")
    StatusRow("Rokid AI App 已安装", companionInstalled)
    StatusRow("已授权 (token)", authenticated)
    StatusRow("CXR-L 链路", cxrlConnected)
    StatusRow("眼镜蓝牙", btConnected)
    StatusRow("会话就绪", sessionReady)
    StatusRow("眼镜界面已打开", viewOpened)
    Text(
        text = "佩戴: ${wearing?.let { if (it) "已佩戴" else "未佩戴" } ?: "未知"}",
        fontSize = 12.sp,
        color = Color(0xFF666666),
    )
    if (sessionError.isNotEmpty()) Text("会话错误: $sessionError", fontSize = 12.sp, color = Color(0xFFB00020))
    if (viewError.isNotEmpty()) Text("界面错误: $viewError", fontSize = 12.sp, color = Color(0xFFB00020))
    Spacer(Modifier.height(10.dp))
    Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
        Button(onClick = onRequestAuth) { Text("授权") }
        Button(onClick = onReconnect) { Text("重连") }
    }
    Spacer(Modifier.height(8.dp))
    Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
        Button(onClick = onShowIdle) { Text("显示待机界面") }
        Button(onClick = onCloseView) { Text("关闭界面") }
    }
}

@Composable
private fun CloudSection() {
    val state by CloudClient.state.collectAsState()
    val serverUrl by CloudClient.serverUrl.collectAsState()
    val queued by CloudClient.queuedCount.collectAsState()
    val error by CloudClient.lastError.collectAsState()
    var urlInput by remember(serverUrl) { mutableStateOf(serverUrl) }

    SectionTitle("云端连接")
    val stateText = when (state) {
        CloudClient.ConnState.CONNECTED -> "已连接"
        CloudClient.ConnState.CONNECTING -> "连接中…"
        CloudClient.ConnState.DISCONNECTED -> "未连接"
    }
    Text(text = "状态: $stateText   离线缓存: ${queued}条", fontSize = 14.sp)
    if (error.isNotEmpty()) Text("错误: $error", fontSize = 12.sp, color = Color(0xFFB00020))
    Spacer(Modifier.height(8.dp))
    OutlinedTextField(
        value = urlInput,
        onValueChange = { urlInput = it },
        label = { Text("服务器地址") },
        modifier = Modifier.fillMaxWidth(),
        singleLine = true,
        textStyle = MaterialTheme.typography.bodySmall,
    )
    Spacer(Modifier.height(8.dp))
    Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
        Button(onClick = {
            CloudClient.setServerUrl(urlInput)
            CloudClient.disconnect(false)
            CloudClient.connect()
        }) { Text("保存并连接") }
        Button(onClick = { CloudClient.connect() }) { Text("连接") }
        Button(onClick = { CloudClient.disconnect() }) { Text("断开") }
    }
    Spacer(Modifier.height(8.dp))
    Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
        Button(onClick = {
            CloudClient.send(
                UplinkMessage.RecognizeMessage(
                    requestId = "photo-test",
                    imageBase64 = TEST_FACE_IMG,
                    deviceId = CloudClient.deviceId(),
                    sessionId = CloudClient.sessionId,
                )
            )
        }) { Text("发测试识别消息") }
        Button(onClick = {
            CloudClient.send(
                UplinkMessage.PersonLeftMessage(
                    requestId = "leave-test",
                    deviceId = CloudClient.deviceId(),
                    sessionId = CloudClient.sessionId,
                )
            )
        }) { Text("发 person_left") }
        Button(onClick = {
            CustomViewRenderer.showHint("测试提示 · 高优先级反色", "high", 5000)
        }) { Text("测试提示区") }
        val ctx = LocalContext.current
        Button(onClick = {
            AudioMonitor.dumpDebugAudio() ?: Toast.makeText(ctx, "暂无音频数据", Toast.LENGTH_SHORT).show()
        }) { Text("导出原始音频") }
    }
}

@Composable
private fun PerceptionSection() {
    val mode by PhotoController.mode.collectAsState()
    val detected by PhotoController.framesDetected.collectAsState()
    val sessionReady by CxrSessionManager.sessionReady.collectAsState()
    val rebuilding by CxrSessionManager.rebuilding.collectAsState()
    val audioRunning by AudioMonitor.running.collectAsState()
    val segments by AudioMonitor.segmentsUploaded.collectAsState()

    SectionTitle("感知链路 (M2/M3)")
    val modeText = when (mode) {
        FaceFlowPolicy.Mode.IDLE -> "IDLE · 每3s快扫"
        FaceFlowPolicy.Mode.ACTIVE -> "ACTIVE · 每30s刷新"
    }
    Text(text = "拍照模式: $modeText", fontSize = 14.sp)
    Text(text = "检测到人脸帧数: $detected", fontSize = 14.sp)
    StatusRow("拍照循环运行中", sessionReady)
    StatusRow("音频监听 (VAD 断句)", audioRunning)
    Text(text = "已上传音频片段: $segments", fontSize = 14.sp)
    if (rebuilding) {
        Text(text = "眼镜连接中,自动重连…", fontSize = 13.sp, color = Color(0xFFB8860B))
    }
}

@Composable
private fun LogSection() {
    val lines by CloudClient.logLines.collectAsState()
    val scroll = rememberScrollState()
    LaunchedEffect(lines.size) { scroll.animateScrollTo(0) }

    SectionTitle("事件日志")
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .height(200.dp)
            .verticalScroll(scroll)
            .padding(8.dp),
    ) {
        if (lines.isEmpty()) {
            Text("暂无日志", fontSize = 12.sp, color = Color(0xFF999999))
        }
        lines.asReversed().forEach { line ->
            Text(
                text = line,
                fontSize = 11.sp,
                fontFamily = FontFamily.Monospace,
                color = Color(0xFF444444),
            )
        }
    }
}

private const val TEST_FACE_IMG =
    "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwcJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPDQ0NP/AABEIAAEAAQMBIgACEQEDEQH/xAAfAAABBQEBAQEBAQAAAAAAAAABAgMEBQYHCAkKC//EALUQAAIBAwMCBAMFBQQEAAABfQECAwAEEQUSITFBBhNRYQcicRQygZGhCCNCscEVUtHwJDNicoIJChYXGBkaJSYnKCkqNDU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6g4SFhoeIiYqSk5SVlpeYmZqio6Slpqeoqaqys7S1tre4ubrCw8TFxsfIycrS09TV1tfY2drh4uPk5ebn6Onq8fLz9PX29/j5+v/aAAwDAQACEQMRAD8A9/ooooA"
