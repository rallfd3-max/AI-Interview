# Rokid 眼镜超级助手 - 实现计划(手机端范围)

> 日期:2026-08-26
> 依据:[v2 设计文档](./2026-06-27-super-assistant-design.md)
> 路线:CXR-L SDK 手机端方案(CustomView 会话),眼镜端零代码
> **范围:仅手机端 App(信息收集 + 界面显示)。云端服务器不在本计划内,以协议契约对接。**
> 工期:约 4 周(单人)

## 0. 范围与边界

| 部分 | 是否本计划范围 | 说明 |
|------|--------------|------|
| 手机端 App | **是** | CXR-L 会话、定时拍照、本地人脸检测、音频监听+VAD、WebSocket 上报、CustomView 界面下发/更新、状态面板 |
| 眼镜 | 无代码 | 感知外设 + 显示载体,零开发 |
| 云端服务器 | **否** | 由其他方负责;本计划交付「协议契约 + 联调指南」作为对接依据 |
| Mock 服务器 | 是(工具) | 单文件 Node.js 脚本,模拟云端应答,支撑手机端独立开发与演示 |

**对云端的唯一依赖**:WebSocket 消息协议(设计文档 6.1)。手机端严格按协议实现,云端就绪后改连接地址即可切换。

## 1. 前置条件(开工前必须就绪)

| # | 条件 | 说明 |
|---|------|------|
| P0-1 | Rokid Glasses 眼镜 | 已开机,与手机通过 Rokid AI App 完成配对 |
| P0-2 | 安卓手机 | 已安装 Rokid AI App ≥ 1.7.14 |
| P0-3 | RenewCXRLSample 示例工程 | 下载 `https://rokid-ota.oss-cn-hangzhou.aliyuncs.com/toB/Document/CXR-L/v1.0.3/cxrlsampe.zip`,CXR-L 集成的唯一参考源 |
| P0-4 | Node.js ≥ 18 | 运行 mock 服务器(开发工具) |
| P0-5 | 网络互通 | 手机与开发机同一局域网,手机可访问 `ws://<PC-IP>:9000/ws` |

## 2. 目标目录结构

```
yanjing/
├── docs/plans/                       # 设计与计划(已有)
├── 官方文档/                          # 已有
├── scrcpy/                           # 已有,手机投屏调试用
├── mock/                             # 【新建】Mock 服务器(开发工具)
│   ├── mock-server.js                # 单文件,模拟云端全部应答
│   └── captures/                     # 收到的图片/音频落盘(检查数据质量)
└── mobile/                           # 【新建】手机端 App(Kotlin)
    ├── settings.gradle.kts
    ├── build.gradle.kts
    ├── gradle.properties
    └── app/
        ├── build.gradle.kts          # client-l:1.0.3 等依赖
        └── src/main/
            ├── AndroidManifest.xml
            ├── assets/
            │   ├── blazeface_short_range.tflite   # 人脸检测模型(M2 落位)
            │   └── silero_vad.onnx                # VAD 模型(M3 落位)
            └── java/com/superassistant/mobile/
                ├── App.kt
                ├── MainActivity.kt
                ├── cxr/
                │   ├── CxrSessionManager.kt      # 授权→token→会话→保活→重连
                │   ├── PhotoController.kt        # 定时拍照调度
                │   ├── AudioMonitor.kt           # 音频监听
                │   └── CustomViewRenderer.kt     # 布局 JSON 组装/推送/更新
                ├── perception/
                │   ├── FaceDetector.kt           # BlazeFace TFLite
                │   └── VadDetector.kt            # Silero ONNX
                ├── net/
                │   ├── CloudClient.kt            # WebSocket(手机↔云端/mock)
                │   └── MessageProtocol.kt        # 协议契约的代码化定义
                ├── state/
                │   ├── AppViewModel.kt
                │   └── SessionStateMachine.kt    # IDLE/ACTIVE 状态机
                └── ui/
                    ├── StatusPanel.kt            # 手机侧调试面板
                    └── theme/Theme.kt
```

任务编号:`M<阶段>-T<序号>`,标注「文件 / 内容 / 验收 / 依赖」。

---

## 3. 阶段 1:项目骨架与 CXR-L 链路(第 1 周)

目标:CXR-L 会话打通,眼镜显示手机下发的待机界面;手机与 mock 服务器协议收发正常。

| ID | 文件 | 内容 | 验收 | 依赖 |
|----|------|------|------|------|
| M1-T1 | `mobile/` 全部 gradle + `App.kt` + `MainActivity.kt` + `AndroidManifest.xml` | 项目骨架:依赖 client-l:1.0.3、Compose BOM、TFLite、ONNX Runtime、OkHttp、kotlinx-serialization;INTERNET 权限 | Android Studio 编译通过,App 可安装启动 | P0-3 |
| M1-T2 | `mobile/.../cxr/CxrSessionManager.kt` | 参照 RenewCXRLSample:全局 sharedLink 链路实例、CUSTOMVIEW 会话配置、回调注册(onCXRLConnected / onGlassBtConnected / onCustomViewOpened)、connect(token)、断开重建 | 真机运行,日志显示链路就绪、会话构建完成 | M1-T1, P0-1/2 |
| M1-T3 | `mobile/.../cxr/CustomViewRenderer.kt` | 布局 JSON 组装(LinearLayout/TextView,单绿色值 #00FF00)+ `customViewOpen` 下发待机界面 + `updateCustomView` 局部更新 | **眼镜显示待机界面(呼吸点)** | M1-T2 |
| M1-T4 | `mobile/.../net/MessageProtocol.kt` | 协议契约代码化:kotlinx-serialization 定义全部上行(face/audio/event)与下行(person_info/hint/clear/error/pong)消息,字段与设计文档 6.1 完全一致 | 序列化/反序列化单测通过 | M1-T1 |
| M1-T5 | `mobile/.../net/CloudClient.kt` | OkHttp WebSocket:连接(地址可在面板配置)、30s 心跳、指数退避重连(1s→30s 封顶)、协议消息收发分发 | 连上 mock,收发 echo 正常,断网重连生效 | M1-T4 |
| M1-T6 | `mock/mock-server.js` | 单文件 Node.js(ws 库):/ws 接入;收到 face → 落盘 captures/ 并延迟 800ms 回应 canned person_info;收到 audio → 落盘并按 30% 概率回 canned hint;收到 person_left → 回 clear;心跳应答 | 手机发消息,mock 正确应答,captures/ 有落盘 | P0-4, M1-T5 |
| M1-T7 | `mobile/.../state/AppViewModel.kt` + `ui/StatusPanel.kt` + `ui/theme/Theme.kt` | Compose 状态面板:云端连接态、CXR-L 会话态、当前识别人物(mock 数据)、最近提示、服务器地址配置 | 面板实时反映三端状态 | M1-T2/3/5 |

**阶段验收**:戴眼镜 → 开 App → 眼镜显示待机界面;面板显示「mock 已连接 / 会话就绪」。

---

## 4. 阶段 2:人脸识别链路·手机侧(第 2 周前半)

目标:完整照片采集→本地检测→上报→人物卡显示循环。

| ID | 文件 | 内容 | 验收 | 依赖 |
|----|------|------|------|------|
| M2-T1 | `mobile/app/src/main/assets/blazeface_short_range.tflite` | 从 MediaPipe 模型库获取 blaze_face_short_range(约 1MB)放入 assets | 文件存在,推理封装可加载 | M1-T1 |
| M2-T2 | `mobile/.../perception/FaceDetector.kt` | TFLite 推理:Bitmap 缩放 128×128 输入,输出人脸框+置信度;取最大框;阈值 0.6 | 单测:含人脸照片检出,无脸照片返回空 | M2-T1 |
| M2-T3 | `mobile/.../cxr/PhotoController.kt` | 定时拍照调度:IDLE 态每 3s、ACTIVE 态每 30s;调用 CXR-L 拍照 API(分辨率+JPEG 质量参数)取回字节流 → FaceDetector → 节流(同 5s 内同人跳过)→ 上传 `{type:"face", img}`;连续 3 次无人脸 → 发 `person_left` | 日志可见完整循环;无人对镜头 10s 后触发 person_left;mock captures/ 收到合法 JPEG | M1-T2, M2-T2, M1-T5 |
| M2-T4 | `CustomViewRenderer.kt` 扩展 | 人物卡布局(姓名 32sp / 正文 20sp,≤5 行,常驻下发);收到 person_info → 下发人物卡;收到 error/unknown_face → 陌生人卡 2s 后回待机 | mock 应答后眼镜 1s 内显示人物卡;人离开回待机 | M1-T3, M1-T5, M1-T6 |

**阶段验收**:对着眼镜 → 人物卡出现并常驻;离开 10s → 回待机界面。

---

## 5. 阶段 3:对话补充链路·手机侧(第 2 周后半 ~ 第 3 周前半)

目标:音频采集→VAD 断句→上报→提示显示完整循环。

| ID | 文件 | 内容 | 验收 | 依赖 |
|----|------|------|------|------|
| M3-T1 | `mobile/app/src/main/assets/silero_vad.onnx` | 从 github snakers4/silero-vad 获取 ONNX 模型放入 assets | 文件存在,封装可加载 | M1-T1 |
| M3-T2 | `mobile/.../perception/VadDetector.kt` | ONNX Runtime 推理:512 采样点/帧(32ms)状态机——语音开始开缓冲、持续追加、静音>700ms 断句;输出 WAV 片段(16kHz/16bit/mono) | 单测:含两句话的 wav 切出 2 个片段 | M3-T1 |
| M3-T3 | `mobile/.../cxr/AudioMonitor.kt` | 会话就绪后开启 CXR-L 音频流,PCM 喂 VadDetector;断句片段 base64 上传 `{type:"audio", data, duration_ms}` | 对眼镜说话,mock captures/ 出现合法 WAV,时长合理 | M1-T2, M3-T2, M1-T5 |
| M3-T4 | `CustomViewRenderer.kt` 扩展 | 提示区更新:`updateCustomView` 仅改 tv_hint 文本+visibility;收到 hint → 显示,5s 后自动清空;高优先级绿底黑字反色样式;人物卡不动 | mock 回 hint 后眼镜显示提示,5s 后消失 | M2-T4, M1-T5 |

**阶段验收**:对眼镜说几句话 → 提示区按 mock 应答显示/消失,人物卡全程不动。

---

## 6. 阶段 4:会话编排与健壮性(第 3 周后半)

目标:状态机完整流转,断线恢复,离线缓存,长时间稳定。

| ID | 文件 | 内容 | 验收 | 依赖 |
|----|------|------|------|------|
| M4-T1 | `mobile/.../state/SessionStateMachine.kt` | IDLE/ACTIVE 状态机:驱动拍照频率切换(3s/30s)、person_left 宽限(连续 3 次无人脸)、clear 后回待机布局、人回来重新触发识别 | 状态切换日志正确;识别→离开→回来→再识别循环 20 次无异常 | M2-T3, M2-T4 |
| M4-T2 | `CxrSessionManager.kt` 完善 | 断线重连:onGlassBtConnected(false)/会话断开 → 自动重授权重建会话;期间感知调度挂起,面板提示「眼镜连接中」 | 关闭眼镜再开机,App 自动恢复会话与待机界面 | M1-T2 |
| M4-T3 | `CloudClient.kt` 完善 | 离线缓存:最近 3 条音频 + 1 张人脸图落盘,网络恢复后按序重传;面板离线角标 | 断 mock 30s 再恢复,缓存数据被重传且 mock 收到 | M1-T5 |
| M4-T4 | 全链路稳定性测试 | 连续 30 分钟佩戴(mock 环境):多人进出、遮挡、噪声 | 无崩溃、无内存泄漏、状态不卡死 | 全部 |

**阶段验收**:完整循环(识别→对话提示→人离开→复位)稳定运行。

---

## 7. 阶段 5:优化与交付(第 4 周)

| ID | 文件 | 内容 | 验收 | 依赖 |
|----|------|------|------|------|
| M5-T1 | 各模块埋点日志 | 延迟打点:拍照→回传、检测→上传、下行→眼镜渲染,面板显示各段耗时 | 采集→上报 ≤600ms、下行→显示 ≤200ms(80 分位) | M4-T4 |
| M5-T2 | 真实场景调参 | 多人同框、逆光/暗光、噪声、距离 0.5-1.5m 实测;调 VAD 静音阈值(700ms→1000ms)、JPEG 质量/分辨率、人脸置信度阈值 | 参数定型,记录问题清单并修复关键项 | M4-T4 |
| M5-T3 | `mobile/README.md` + `docs/plans/protocol-contract.md` | **交付物**:① App 构建/安装/配置说明;② **协议契约文档**(消息全字段、时序、错误码,交云端开发方);③ 联调指南(云端接入步骤:改地址、按契约应答) | 云端开发方仅凭契约文档即可开始对接 | M5-T2 |

**阶段验收**:手机端独立可演示(mock 全流程);协议契约可交付。

---

## 8. 依赖关系与关键路径

```
关键路径:
M1-T1 → M1-T2 → M1-T3 → M2-T3 → M2-T4 → M3-T3 → M3-T4 → M4-T1 → M5-T2
(骨架)  (会话)  (待机屏) (拍照链) (人物卡) (音频链) (提示区) (状态机) (调参)

可并行支线:
· M1-T4/T5(协议+WS)与 M1-T2/T3(CXR-L)互不依赖,可并行
· M2-T2(FaceDetector)与 M3-T2(VadDetector)单测可先行,模型就位即写
· M1-T6(mock)在 M1-T5 完成后随时补
```

**与云端的切换点**:手机端所有逻辑仅依赖 WebSocket 协议。云端就绪后,在 StatusPanel 把地址从 `ws://<PC>:9000/ws` 改为真实云端 `ws://<server>:8000/ws`,其余零改动。云端必须按 `protocol-contract.md` 应答。

## 9. 风险与应对

| 风险 | 概率 | 影响 | 应对 |
|------|------|------|------|
| CXR-L SDK API 细节与设计假设不符(官方文档为简介级) | 中 | 手机端返工 | M1-T2 严格参照 RenewCXRLSample 源码;阶段 1 打通即暴露问题 |
| 眼镜拍照回传延迟高于 400ms 假设 | 中 | 人脸链路超标 | M5-T1 实测后调低 JPEG 质量/分辨率 |
| VAD 断句在嘈杂环境误触发 | 高 | 音频碎片段多 | M5-T2 调静音阈值;上报前过滤 <1s 片段 |
| CXR-L 音频流格式(采样率/声道)与 16kHz 假设不符 | 中 | VAD 需重采样适配 | M3-T3 首先打印实际格式,封装重采样层 |
| 云端契约理解偏差 | 中 | 联调返工 | M5-T3 契约文档含完整消息示例与时序图,双方评审确认 |

## 10. 执行约定

1. 每任务完成即过验收项,通过才进入下一个
2. 每阶段结束做真机验收,不通过不进入下一阶段
3. 协议字段如需变更,先改 `MessageProtocol.kt` 与 `protocol-contract.md`,再改 mock,保持三方一致
4. mock 的 canned 应答数据放 mock-server.js 顶部常量区,便于调整演示效果
