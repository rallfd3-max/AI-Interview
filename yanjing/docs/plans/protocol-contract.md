# 超级助手 · 手机端 ↔ 云端 WebSocket 协议契约

| 项 | 内容 |
|----|------|
| 版本 | v1.0 |
| 日期 | 2026-08-26 |
| 状态 | 已定稿（手机端已实现，mock 服务器已按此实现） |
| 适用对象 | 云端服务器开发方 |
| 关联文档 | [总体设计](2026-06-27-super-assistant-design.md) 第 6 节 · [实现计划](2026-08-26-v2-implementation-plan.md) |
| 手机端实现 | `mobile/app/src/main/java/com/superassistant/mobile/net/MessageProtocol.kt` |
| 参考实现 | `mock/mock-server.js`（可直接作为云端骨架改造） |

---

## 1. 传输层与连接管理

### 1.1 基本参数

| 项 | 值 |
|----|----|
| 协议 | WebSocket（RFC 6455） |
| URL（开发） | `ws://<服务器IP>:9000/ws` |
| URL（生产） | `wss://<域名>/ws`（必须 TLS，手机端届时移除明文许可） |
| 子协议 | 无 |
| 握手 Header | `X-Device-Id: <设备唯一ID>`（首次安装生成，卸载重装才变化） |

### 1.2 心跳

- 手机端每 **30 秒** 发送 `{"type":"ping"}`，云端必须回 `{"type":"pong"}`
- 手机端若 **45 秒**（30s 间隔 + 15s 容忍）内未收到 pong，判定连接死亡并主动断开重连
- 云端也可主动发 ping（可选），手机端会回 pong

### 1.3 断线重连

手机端自动重连，指数退避：**1s → 2s → 4s → 8s → 16s → 30s（封顶）**，直至成功。

### 1.4 离线缓存与重传

断线期间的上行消息缓存 **最近 3 条**（FIFO，超出丢弃最旧）。重连成功后按原顺序重传。
> 注意：缓存消息的 `ts` 是**采集时刻**的时间戳，云端消费时应以 ts 而非到达顺序判断时效。

### 1.5 消息格式约定

- 所有消息均为 UTF-8 JSON 文本帧，顶层必有 `"type"` 字段
- 字段命名统一 **snake_case**
- 时间戳 `ts`：Unix 毫秒
- 手机端解码 `ignoreUnknownKeys = true`：**云端可以增加新字段，手机端向后兼容**；但已有字段改名会破坏兼容
- 手机端解析失败的消息会被静默丢弃（不影响后续消息），云端应保证 JSON 合法

---

## 2. 上行消息（手机 → 云端）

### 2.1 `face` — 人脸图片

本地 BlazeFace 检测到人脸后触发上传。IDLE 状态同 5 秒内只传 1 张；会话激活后每 30 秒刷新 1 张。

```json
{
  "type": "face",
  "img": "<base64 编码的完整 JPEG>",
  "ts": 1700000000123,
  "face_count": 1,
  "face_box": [120, 80, 200, 160]
}
```

| 字段 | 类型 | 必有 | 说明 |
|------|------|------|------|
| type | string | ✓ | 固定 `"face"` |
| img | string | ✓ | base64(JPEG)，原图 1024×768、质量 80，典型 40–60KB（base64 后约 55–80KB） |
| ts | long | ✓ | 拍摄时刻 Unix 毫秒 |
| face_count | int | ✓ | 手机本地检测到的人脸数（当前恒为 1，只上传最大的一张） |
| face_box | int[4] | 可选 | 本地检测的最大人脸框 `[left, top, right, bottom]`，原图像素坐标。云端可直接用于裁剪，也可自行检测 |

**云端应答要求**：收到 `face` 后必须在 **3 秒内** 回 `person_info`（识别成功）或 `error{code:"unknown_face"}`（识别失败）。超时手机端不重发，人物卡保持上一状态。

### 2.2 `audio` — 对话音频片段（M3 接入）

手机端 VAD 判定一句话结束（静音 700ms）后上传。

```json
{
  "type": "audio",
  "data": "<base64 编码的 WAV>",
  "ts": 1700000001234,
  "duration_ms": 2500
}
```

| 字段 | 类型 | 必有 | 说明 |
|------|------|------|------|
| type | string | ✓ | 固定 `"audio"` |
| data | string | ✓ | base64(WAV)，PCM 16kHz / 16bit / 单声道 |
| ts | long | ✓ | 片段结束时刻 Unix 毫秒 |
| duration_ms | long | ✓ | 片段时长 |

**云端应答要求**：`audio` **不要求应答**。云端 ASR + RAG 判断后，若需要补充信息则推 `hint`，否则静默。

### 2.3 `event` — 生命周期事件

```json
{
  "type": "event",
  "event": "person_left",
  "ts": 1700000001234
}
```

| event 值 | 触发条件 |
|----------|---------|
| `person_left` | 会话激活状态下连续 3 次拍照（约 9 秒）无人脸 |
| `person_back` | （预留）人重新入镜，M4 接入 |

**云端应答要求**：收到 `person_left` 应回 `clear` 结束会话（手机端本地也会先行复位，云端 clear 用于同步自身会话状态）。

### 2.4 `ping` — 心跳

```json
{"type": "ping"}
```

云端必须立即回 `pong`（见 3.5）。

---

## 3. 下行消息（云端 → 手机）

### 3.1 `person_info` — 人物识别成功

驱动眼镜端人物卡：姓名大字 + 正文行，常驻显示。

```json
{
  "type": "person_info",
  "id": "p001",
  "name": "张三",
  "role": "前公司CTO",
  "relation": "5年老朋友",
  "last_met": "2026-03-15",
  "notes": "对技术细节敏感",
  "display_lines": [
    "张三",
    "前公司CTO / 5年老朋友",
    "上次见面:2026-03-15",
    "注意:对技术细节敏感"
  ],
  "ts": 1700000001234
}
```

| 字段 | 类型 | 必有 | 说明 |
|------|------|------|------|
| type | string | ✓ | 固定 `"person_info"` |
| id | string | ✓ | 人物唯一 ID。**同一人重复识别必须返回相同 id**（手机端据此锁定会话、抑制重复弹卡） |
| name | string | ✓ | 姓名，人物卡主标题（最长建议 12 汉字，超出眼镜端换行） |
| role | string | 可选 | 职务/身份 |
| relation | string | 可选 | 关系标签 |
| last_met | string | 可选 | 上次见面日期（自由格式，建议 `YYYY-MM-DD`） |
| notes | string | 可选 | 备注要点 |
| display_lines | string[] | 可选 | **推荐**。眼镜卡正文行，非空时手机端直接显示；为空时手机端自动用 role/relation/last_met/notes 拼装。上限 5 行，每行建议 ≤18 汉字 |
| ts | long | 可选 | 消息生成时刻 |

**推荐做法**：由云端 LLM 生成 `display_lines`（控制在 3–5 行），结构化字段同时下发供手机端日志与后续扩展使用。

### 3.2 `hint` — 对话补充提示（M3 接入）

显示在人物卡下方的提示浮层，按 `display_ms` 自动消失。

```json
{
  "type": "hint",
  "text": "他上周提到项目延期",
  "priority": "high",
  "topic": "project_delay",
  "display_ms": 5000,
  "ts": 1700000001234
}
```

| 字段 | 类型 | 必有 | 默认 | 说明 |
|------|------|------|------|------|
| type | string | ✓ | — | 固定 `"hint"` |
| text | string | ✓ | — | 提示正文（建议 ≤40 汉字） |
| priority | string | | `"medium"` | `high`=高亮反色显示；`medium`/`low`=常规 |
| topic | string | 可选 | — | 提示主题键。手机端按 topic 去重，避免同一话题反复推送 |
| display_ms | long | | `5000` | 自动隐藏时长（毫秒） |
| ts | long | 可选 | — | 消息生成时刻 |

**云端可随时主动推送** `hint`（不限于收到 audio 后），例如基于人脸识别结果的补充提醒。

### 3.3 `clear` — 清除人物卡

```json
{
  "type": "clear",
  "reason": "person_left",
  "ts": 1700000001234
}
```

| 字段 | 类型 | 必有 | 说明 |
|------|------|------|------|
| type | string | ✓ | 固定 `"clear"` |
| reason | string | 可选 | `person_left` / `timeout` / `manual`，仅用于日志 |
| ts | long | 可选 | 消息生成时刻 |

手机端收到后：眼镜回待机界面、感知状态机复位 IDLE。

### 3.4 `error` — 错误

```json
{
  "type": "error",
  "code": "unknown_face",
  "msg": "未识别此人",
  "ts": 1700000001234
}
```

| 字段 | 类型 | 必有 | 说明 |
|------|------|------|------|
| type | string | ✓ | 固定 `"error"` |
| code | string | ✓ | 错误码，见第 5 节 |
| msg | string | 可选 | 人类可读描述，仅入手机端日志 |
| ts | long | 可选 | 消息生成时刻 |

`unknown_face` 的手机端行为：眼镜显示「未识别」卡 2 秒 → 回待机。

### 3.5 `pong` — 心跳应答

```json
{"type": "pong"}
```

---

## 4. 端到端时序（含性能预算）

### 4.1 人脸识别流

```
手机                    云端
 │ │
 │──── face(img) ───────▶│  t=600ms   base64 解码 → 人脸特征提取 → 档案比对
 │                       │             → LLM 生成 display_lines
 │◀─── person_info ──────│  t≈1450ms  （云端预算 ≤850ms）
 │
 眼镜渲染人物卡           t≈1650ms  端到端目标 ≤2s
```

**超时策略**：手机端对 `face` 不设硬超时等待，但云端若 3 秒未应答，该帧信息即视为过期（下一帧 5s/30s 周期会重新评估）。

### 4.2 对话提示流（M3）

```
手机                    云端
 │──── audio(data) ─────▶│  ASR(SenseVoiceSmall) → RAG 检索 → LLM 判定
 │◀─── hint(可选) ───────│  云端预算 ≤1s，端到端目标 ≤1.5s
```

### 4.3 人离开流

```
手机                    云端
 │ 连续3帧无人脸(≈9s)
 │──── event(person_left)▶│
 │◀─── clear ────────────│  手机端已先本地复位,clear 幂等
```

---

## 5. 错误码表

| code | 语义 | 手机端行为 |
|------|------|-----------|
| `unknown_face` | 知识库无此人 | 陌生人卡 2s → 待机 |
| `bad_image` | 图片损坏/无法解码 | 记日志，静默 |
| `rate_limited` | 云端限流 | 记日志，静默（手机端会自动按周期重试） |
| `internal` | 云端内部错误 | 记日志，静默 |

未知 code 一律记日志静默，不影响连接。

---

## 6. 云端实现清单（验收标准）

1. ☐ WebSocket 服务监听 `/ws` 任意路径（以 `/ws` 为主），接受 `X-Device-Id` header
2. ☐ 收 `ping` 回 `pong`（30s 周期，45s 无 pong 手机端会断开重连）
3. ☐ 收 `face` 3 秒内回 `person_info` 或 `error{unknown_face}`
4. ☐ `person_info.id` 同人恒定；`display_lines` 3–5 行、每行 ≤18 汉字
5. ☐ 收 `audio`：ASR + 检索 + LLM，需要时推 `hint`（≤1s），不需要时静默
6. ☐ 收 `event{person_left}` 回 `clear`
7. ☐ 可主动推送 `hint` / `clear`
8. ☐ 生产环境必须 `wss://` + 合法证书
9. ☐ 并发：单设备消息速率峰值 = 1 face/5s + 1 audio/句话 + 心跳，带宽预估 ≤ 100KB/s/设备
10. ☐ 图片/音频落库策略由云端自定（注意隐私合规，人脸数据属敏感个人信息）

## 7. 联调指南

**第一阶段：用 mock 打通**
mock 已按本契约实现（`mock/mock-server.js`），收图回「张三」，随机回 hint，落盘 `mock/captures/` 供检查真实采集效果。

**第二阶段：切真实云端**
1. 云端起服务后，手机 App「状态面板 → 云端连接」把地址改为 `ws://<云IP>:9000/ws`，点「保存并连接」
2. 验证顺序：心跳（日志出现 pong）→ 对脸拍照（云端收到 face）→ 收 person_info（眼镜出卡）
3. 常见问题：
   - 连不上 → 检查防火墙放行端口 + 手机与服务器同网段/公网可达
   - `not permit by network security policy` → 这是 Android 明文限制，确认开发期配置（当前仅放行开发地址）或改 `wss://`

**第三阶段：压测与调优**
- 用 mock 的 captures 样本重放压测 ASR/识别链路时延
- 验证 4.1 节性能预算（识别 ≤2s、提示 ≤1.5s 端到端）

## 8. 变更记录

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-08-26 | v1.0 | 定稿：统一 snake_case 字段名；新增 `face_box` 字段；明确心跳/重连/离线缓存参数与时序预算 |
