# 智能眼镜手机端 WebSocket 接口文档

版本：v1.0（已按 `protocol-contract(1).md` 接入）  
服务端：AI 面试官 Java API

## 1. 连接配置

开发环境连接地址：

```text
ws://<Java服务IP或域名>:8080/ws
```

生产环境必须由 HTTPS/WSS 反向代理提供 TLS：

```text
wss://<业务域名>/ws
```

`9000` 是原协议的示例端口；本项目当前 Java 服务端口为 `8080`，因此眼镜手机端应配置为上述 `:8080/ws`。如部署时修改了 Spring Boot 的 `server.port`，连接端口也需同步修改。

握手必须带设备标识；缺失、空值或超过 128 个字符时服务端以 HTTP 400 拒绝连接。

```http
X-Device-Id: glasses-001
```

服务端配置位于 `ai-interviewer-master/api/src/main/resources/application-dev.yml`：

```yaml
smart-glasses:
  websocket:
    path: /ws
    max-text-message-size: 262144
```

所有消息均为 UTF-8 JSON 文本帧，字段命名遵循 `snake_case`。建议手机端每 30 秒发送一次 `ping`。

## 2. 手机端发送

### 心跳

```json
{"type":"ping","ts":1780000000000}
```

服务端立即返回：

```json
{"type":"pong"}
```

### 人脸帧

```json
{
  "type":"face",
  "img":"<完整 JPEG 的 Base64，不含 data:image/... 前缀>",
  "ts":1780000000000,
  "face_count":1,
  "face_box":[120,80,260,260]
}
```

字段说明：

| 字段 | 必填 | 说明 |
|---|---:|---|
| `img` | 是 | 完整图片的 Base64；解码后最大 1 MiB |
| `ts` | 否 | Unix 毫秒；未传时使用服务端当前时间 |
| `face_count` | 否 | 当前检测到的人脸数量 |
| `face_box` | 否 | `[x,y,w,h]`，仅接受四个整数 |

服务端会在识别成功时返回 `person_info`，未匹配返回 `unknown_face`，图片无效或超限返回 `bad_image`。协议目标为 3 秒内响应。

### 音频帧

```json
{
  "type":"audio",
  "data":"<WAV Base64>",
  "ts":1780000000000,
  "duration_ms":2600
}
```

当前服务端接受但不回包；ASR 和 `hint` 推送属于后续能力，手机端不应等待此消息的同步响应。

### 人员离开

```json
{"type":"event","event":"person_left","ts":1780000000000}
```

服务端返回：

```json
{"type":"clear","reason":"person_left","ts":1780000000100}
```

## 3. 服务端发送

### 候选人信息卡 `person_info`

当人脸解析器识别到已登记候选人后，服务端用稳定的 `candidateId` 查询现有 Candidate、Job 和最近一次 InterviewRecord，并返回：

```json
{
  "type":"person_info",
  "id":"202",
  "name":"张三",
  "role":"Java 开发工程师",
  "notes":"上次面试已完成，待复评",
  "display_lines":[
    "张三",
    "Java 开发工程师",
    "某大学 / 软件工程",
    "面试:COMPLETED",
    "备注:上次面试已完成，待复评"
  ],
  "ts":1780000000100
}
```

| 字段 | 说明 |
|---|---|
| `id` | 稳定的候选人 ID，即 `candidateId`；同一人必须保持一致 |
| `name` | 候选人姓名 |
| `role` | 应聘岗位名；无数据时省略 |
| `notes` | 最近一次面试摘要；无数据时省略 |
| `display_lines` | 最多 5 行；每行按 18 个字符截断，适合眼镜端显示 |
| `ts` | 服务端生成时间（Unix 毫秒） |

为避免在眼镜上泄露敏感信息，卡片不会返回身份证、手机号、邮箱、住址、人脸/媒体 URL、密码、令牌或任何模型与存储凭据。

### 清屏 `clear`

收到 `event/person_left` 时发送。眼镜端应清除当前人物卡片。

### 错误 `error`

```json
{
  "type":"error",
  "code":"unknown_face",
  "msg":"No enrolled candidate matched this face",
  "ts":1780000000100
}
```

| 错误码 | 当前行为 |
|---|---|
| `unknown_face` | 没有匹配到登记候选人，或匹配的候选人已不可用 |
| `bad_image` | `img` 为空、不是合法 Base64，或解码图片大于 1 MiB |
| `internal` | 服务端处理异常；客户端可稍后重试 |

`rate_limited` 和服务端主动 `hint` 为协议预留项，当前版本尚未发送。

## 4. 当前识别接入状态

WebSocket 协议、候选人信息聚合和返回卡片已接入 Java 服务端；但仓库中尚未提供人脸特征提取/比对 SDK。因此默认的 `UnknownFaceCandidateResolver` 会安全返回 `unknown_face`，不会按姓名或任意候选人进行猜测。

接入真实人脸服务时，实现 `FaceCandidateResolver` 并返回已验证的 `candidateId`，注册为 Spring Bean，同时设置 `smart-glasses.face.default-resolver-enabled=false` 关闭默认解析器；无需修改 WebSocket 协议或候选人信息查询逻辑。

## 5. 客户端处理约定

1. 连接失败或断开时按原协议进行退避重连；服务端不保存人脸和音频原始内容。
2. 收到 `person_info` 后按 `id` 更新/覆盖当前人物卡片。
3. 收到 `clear` 或 `unknown_face` 时清除当前人物卡片，避免显示上一个人的信息。
4. `audio` 当前无同步回包，不能以“未收到消息”判断网络异常。
5. 非 JSON、未知 `type`、未知 `event` 会被服务端静默忽略，客户端应自行记录诊断日志。

## 6. 联调前检查

1. 启动 Java 服务：在 `ai-interviewer-master` 下运行 `mvn -pl api -am spring-boot:run`。
2. 确认手机能访问服务端 IP 和 `8080` 端口，再使用 `ws://<IP>:8080/ws`。
3. 握手中带入唯一的 `X-Device-Id`。
4. 先发送 `ping` 验证得到 `pong`，再发送 `event/person_left` 验证得到 `clear`。
5. 当前未部署真实人脸解析器时，发送合法 `face` 会得到 `unknown_face`，这是预期的安全行为。
