# Rokid 眼镜超级助手 - 设计文档

> 日期:2026-08-26
> 状态:已确认,待实现

## 1. 项目定位

通过 Rokid AI 眼镜构建一个实时社交超级助手:
- 摄像头实时识别面前的人是谁
- 识别结果发送云端,从知识库检索人物档案和相关文档
- 眼镜常驻显示人物关键信息
- 持续监听双方对话,根据谈话内容动态推送补充信息

## 2. 核心决策

| 决策项 | 选择 | 理由 |
|--------|------|------|
| 开发路线 | **CXR-L SDK 手机端方案,CustomView 会话** | 眼镜端零代码,开发调试只需手机+云端,无需专用开发线/眼镜 ADB |
| 会话模式 | CustomView(手机下发布局 JSON,眼镜渲染) | 核心需求(拍照/音频/显示)全覆盖;未来可平滑升级 CustomApp |
| 人脸识别 | 混合模式(手机本地检测 + 云端识别) | 手机算力充裕,只上传有人的照片,精度交云端 |
| 语音识别 | VAD 手机本地检测 + 云端 ASR | 眼镜麦克风经 CXR-L 传到手机,手机做轻量 VAD,ASR 交云端 |
| 端云架构 | 轻眼镜 + 手机调度 + 重云端 | 眼镜只作感知外设+显示载体,手机做调度,智能全在云端 |
| 对话语言 | 中文为主 | ASR/LLM 选型以中文能力为核心 |
| 知识库 | 人物档案库(结构化)+ 文档知识库(非结构化) | 双路 RAG 检索 |
| ASR 模型 | FunAudioLLM/SenseVoiceSmall(硅基流动) | 延迟优先,专为实时交互设计 |
| LLM 模型 | deepseek-ai/DeepSeek-V3.2(硅基流动) | 中文理解强,OpenAI 兼容 API |
| 向量模型 | BAAI/bge-m3(硅基流动) | 中英双语嵌入 |
| 人脸识别 | InsightFace buffalo_l(自建本地 GPU) | 中文场景准确率高,开源 |

**CustomView 会话能力边界**(依据 CXR-L 官方文档能力矩阵):自定义 View 打开后,音频 ✓、拍照 ✓、自定义指令 ✗(MVP 无需指令,够用)。

## 3. 整体架构

```
┌────────────────────────────────────────────────┐
│         手机端 App (Android / Kotlin)            │
│    集成 CXR-L SDK + Rokid AI App ≥ 1.7.14        │
│                                                │
│  ┌──────────┐  ┌───────────┐  ┌────────────┐  │
│  │ 会话管理  │  │ 感知调度   │  │ CustomView │  │
│  │ 授权/token│  │ 定时拍照   │  │ JSON布局   │  │
│  │ Session  │  │ 手机本地   │  │ 推送/更新  │  │
│  │ 建立保活  │  │ 人脸检测   │  │ 人物卡/提示│  │
│  └──────────┘  │ 手机本地VAD│  └────────────┘  │
│                └───────────┘                  │
└──────┬──────────────┬─────────────────┬───────┘
       │ CXR-L 链路     │                 │ WebSocket(互联网)
       │(经 Rokid AI App)│                 │
       ▼               │                 ▼
┌──────────────┐       │        ┌─────────────────────┐
│  Rokid 眼镜   │       │        │      云端服务器      │
│  (零代码外设)  │◄──────┘        │  FastAPI + WebSocket │
│  摄像头/麦克风 │                  │  ├─ InsightFace(GPU)│
│  显示CustomView│                  │  ├─ 硅基流动三件套   │
└──────────────┘                  │  │  ASR/LLM/Embedding│
                                  │  ├─ pgvector 检索    │
                                  │  └─ Redis 会话缓存   │
                                  └─────────────────────┘
```

**三端职责**:
- **眼镜**:感知外设(摄像头拍照、麦克风拾音)+ 显示载体(CustomView 渲染),零代码
- **手机**:调度中枢 —— CXR-L 会话管理、定时触发拍照、本地人脸检测、本地 VAD、与云端 WebSocket 通信、下发布局 JSON
- **云端**:智能中枢 —— 人脸识别、ASR、RAG 检索、LLM 生成、推送决策

## 4. 手机端详细设计(CXR-L SDK)

### 4.1 应用架构

```
com.superassistant.mobile/
├── App.kt                          # Application 入口
├── MainActivity.kt                 # 唯一 Activity,状态面板 + 会话控制
├── cxr/
│   ├── CxrSessionManager.kt        # CXR-L 会话生命周期(授权→token→会话→保活)
│   ├── PhotoController.kt          # 拍照控制(定时触发,取回结果)
│   ├── AudioMonitor.kt             # 音频监听(眼镜麦克风 → 手机)
│   └── CustomViewRenderer.kt       # CustomView JSON 组装/推送/更新
├── perception/
│   ├── FaceDetector.kt             # 手机本地人脸检测(BlazeFace TFLite)
│   └── VadDetector.kt              # 手机本地 VAD(Silero ONNX)
├── net/
│   ├── CloudClient.kt              # WebSocket 客户端(手机↔云端)
│   └── MessageProtocol.kt          # 消息协议定义
├── state/
│   ├── AppViewModel.kt             # 全局状态
│   └── SessionStateMachine.kt      # 会话状态机
└── ui/
    ├── StatusPanel.kt              # 手机侧状态面板(调试/运维用)
    └── theme/
```

### 4.2 CXR-L 会话生命周期

依据 CXR-L 官方文档,会话建立是所有能力的前提:

```
1. 引导依赖:检测/引导安装 Rokid AI App(≥1.7.14),唤起授权
2. 授权流程:走 CXR-L 授权 → 获取 token
3. 建立 CustomView 会话:下发初始布局 JSON(待机界面)
4. 等待会话构建完成(眼镜端已实际呈现界面)→ 链路就绪
5. 此后可用能力:音频监听 ✓、拍照 ✓
6. 保活:监听会话断开事件 → 自动重授权/重建会话
```

**关键约束**:拍照和音频能力仅在"会话构建完成且自定义 View 已打开"后可用。会话未就绪时所有感知调度必须挂起。

### 4.3 视觉感知模块(定时拍照 + 手机本地检测)

```
PhotoController(定时器)
  ├─ IDLE 态:每 3 秒触发一次拍照(找人模式)
  ├─ ACTIVE 态:每 30 秒触发一次拍照(确认同一人/人还在)
  └─ 拍照参数:面向使用场景的分辨率,取回 JPEG
       ↓
眼镜拍照 → 图片经 CXR-L 链路回传手机
       ↓
FaceDetector 手机本地检测(BlazeFace TFLite, ~10-30ms/张)
  ├─ 无人脸 → 丢弃,不发云端
  ├─ 检测到人脸:
  │    ├─ 距上次上传 < 5秒 且同一人 → 跳过(节流)
  │    └─ 新人 / 超过30秒 → 上传云端 {type:"face", img}
  └─ 多人脸 → 取最大人脸框(最近的人)
```

**人离开判定**:连续 3 次(约 10 秒)拍照无人脸 → 发送 person_left 事件 → 云端推送 clear → 眼镜回待机界面。

**模型选型**:BlazeFace(短距版)TFLite,约 1MB。手机端推理 10-30ms,远快于眼镜端方案。

### 4.4 音频感知模块(眼镜音频监听 + 手机本地 VAD)

```
AudioMonitor(CXR-L 音频监听)
  ↓ 眼镜麦克风音频流持续到手机(16kHz 采样)
VadDetector 手机本地检测(Silero VAD ONNX, ~2MB)
  ├─ 静音 → 丢弃
  ├─ 语音开始 → 开启缓冲区
  ├─ 语音持续 → 持续缓冲
  └─ 静音 > 700ms → 判定一句话结束
       → 封装音频片段(WAV, 16kHz)
       → WebSocket 发送 {type:"audio", data: base64, ts}
       → 清空缓冲区,等下一句
```

注:VAD 只需单声道;眼镜 8 通道能力经 CXR-L 链路后按 SDK 提供的格式消费,MVP 不做声源定位。

### 4.5 CustomView 显示层(JSON 布局)

显示由手机端组装 JSON 布局,经 CXR-L 推送到眼镜渲染。全部使用绿色系(单绿显示),组件支持 RelativeLayout / LinearLayout / TextView / ImageView / Lottie。

**三态界面**:

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  待机界面        │      │ 人物卡(常驻)    │      │ 人物卡(常驻)     │
│                 │      │                 │      │ + 提示区(更新)   │
│   · · · ·       │      │ 张三            │      │ 张三            │
│  (呼吸点)       │ ──→  │ CTO / 老朋友    │ ──→  │ CTO / 老朋友    │
│                 │      │                 │      │ 上次见面:3月15日 │
│                 │      │ 上次见面:3月15日 │      │ ┌────────────┐ │
│                 │      │                 │      │ │他上周提到   │ │
│                 │      │                 │      │ │项目延期     │ │
│                 │      │                 │      │ └────────────┘ │
└─────────────────┘      └─────────────────┘      └─────────────────┘
  IDLE                    人物卡常驻显示             提示区动态更新
                          (人在就一直显示)           (5秒后清空,人物卡不动)
```

**布局 JSON 结构(示意)**:

```json
{
  "root": {
    "type": "LinearLayout",
    "orientation": "vertical",
    "children": [
      {"type": "TextView", "id": "tv_name", "text": "张三", "textSize": 32, "textColor": "#00FF00"},
      {"type": "TextView", "id": "tv_role", "text": "前公司CTO / 5年老朋友", "textSize": 20},
      {"type": "TextView", "id": "tv_last_met", "text": "上次见面:2026-03-15", "textSize": 20},
      {"type": "TextView", "id": "tv_notes", "text": "注意:对技术细节敏感", "textSize": 20},
      {"type": "View", "id": "divider", "height": 2, "background": "#00FF00"},
      {"type": "TextView", "id": "tv_hint", "text": "", "textSize": 22, "visibility": "gone"}
    ]
  }
}
```

**更新策略**:
- 人物卡:初次识别后整体下发(常驻,不重复推送)
- 提示:仅调用 updateCustomView 更新 `tv_hint` 文本 + visibility,5 秒后清空(不动人物卡)
- 高优先级提示:用反色样式表达(绿底黑字),因单绿无法用颜色区分
- 字号:姓名 32sp+,正文 20sp+,信息密度人物卡 ≤5 行、提示 ≤3 行

### 4.6 手机端状态机

```
              ┌──────┐
              │ IDLE │←──────────────────────┐
              └──┬───┘                        │
                 │ 拍照检测到人脸 + 云端返回身份  │ 连续3次拍照无人脸(≈10秒)
                 ▼                            │
     ┌───────────────────┐    VAD检测到语音    │
     │ ACTIVE            │──────────────┐    │
     │ (人物卡常驻)       │              │    │
     └───────────────────┘              ▼    │
     │  ↑                    ┌──────────────┐│
     │  │ 提示超时清空         │ACTIVE        ││
     │  └────────────────────│ + 提示显示中   ││
     │                       │(人物卡仍在)   ││
     │                       └──────────────┘│
     │                                        │
     └────────────────────────────────────────┘
```

- IDLE:待机界面,每 3 秒拍照找人
- ACTIVE:人物卡常驻,每 30 秒拍照确认,提示按需叠加

### 4.7 手机端资源占用预估

| 组件 | CPU | 内存 |
|------|-----|------|
| CXR-L SDK(会话+蓝牙/WiFi链路) | ~4% | ~40MB |
| BlazeFace 推理(每3秒一张) | ~2% | ~20MB |
| Silero VAD 推理 | ~3% | ~10MB |
| WebSocket + 协程 | ~2% | ~15MB |
| UI 状态面板 | ~3% | ~40MB |
| **合计** | **~14%** | **~125MB** |

现代手机轻松承受。眼镜端零自研代码,功耗与官方链路一致。

## 5. 云端服务器详细设计

### 5.1 技术栈

| 组件 | 选型 | 理由 |
|------|------|------|
| Web 框架 | FastAPI | 原生 async,WebSocket 支持好 |
| 人脸识别 | InsightFace (buffalo_l) | 中文场景准确率高,开源 |
| ASR | FunAudioLLM/SenseVoiceSmall | 硅基流动,延迟低,实时交互优化 |
| LLM | deepseek-ai/DeepSeek-V3.2 | 硅基流动,中文理解强 |
| 向量数据库 | pgvector(PostgreSQL 扩展) | 与人物档案同库,运维简单 |
| 向量模型 | bge-m3 | 硅基流动,中英双语嵌入 |
| 缓存 | Redis | 对话上下文、会话状态 |
| 部署 | Docker Compose | 单机起步 |

注:云端不感知客户端是手机还是眼镜,WebSocket 客户端为手机 App;device_id 用手机标识。

### 5.2 API 网关层

```
FastAPI + WebSocket

路由:
├── GET  /ws                    # WebSocket 长连接(手机 App 接入)
├── POST /api/face/register     # 注册人脸(管理用)
├── POST /api/knowledge/upload  # 上传文档到知识库
├── GET  /api/persons           # 查询人物列表(管理用)
└── GET  /health                # 健康检查
```

### 5.3 会话编排层

```python
class SessionState(Enum):
    IDLE = "idle"                          # 无人在前
    WAITING_IDENTIFY = "waiting_identify"  # 已收到人脸,识别中
    IDENTIFIED = "identified"              # 已识别,人物卡已推送
    IN_CONVERSATION = "in_conversation"    # 对话进行中

class SessionManager:
    device_id: str
    state: SessionState
    current_person: Person | None
    conversation_buffer: list[Utterance]   # 对话历史(最近10轮)
    last_face_ts: float
    pushed_topics: set[str]                # 本轮已推送的话题(去重)
```

状态流转:
```
收到 face 消息:
  ├─ state == IDLE
  │    → state = WAITING_IDENTIFY → 调用 FaceRecognizer
  │    → 识别成功 → 推送 person_info, state = IDENTIFIED
  │    → 识别失败 → 推送 error, state = IDLE
  ├─ state == IDENTIFIED / IN_CONVERSATION
  │    → 更新 last_face_ts → 距上次上传 > 30s → 重新识别

收到 audio 消息:
  ├─ state == IDENTIFIED → state = IN_CONVERSATION → 进入对话流
  ├─ state == IN_CONVERSATION → 追加到 buffer → 触发增量推送

收到 person_left:
  → 推送 clear → state = IDLE → 清空 buffer, pushed_topics
```

注:人离开的宽限期(连续 3 次拍照无人脸)由手机端判定后上报,云端直接响应。

### 5.4 智能处理层

#### 5.4.1 人脸识别引擎

```python
class FaceRecognizer:
    async def recognize(self, img_bytes: bytes) -> Person | None:
        faces = app.get(img_array)
        if len(faces) == 0:
            return None
        embedding = faces[0].normed_embedding  # 512维
        # pgvector 余弦相似度检索
        match = await db.execute("""
            SELECT person_id, 1 - (embedding <=> :emb) AS sim
            FROM face_embeddings
            WHERE 1 - (embedding <=> :emb) > 0.5
            ORDER BY embedding <=> :emb LIMIT 1
        """, emb=embedding.tolist())
        if match.sim < 0.5:
            return None  # 陌生人
        return await Person.get(match.person_id)
```

性能:InsightFace buffalo_l,GPU 80-150ms。

#### 5.4.2 ASR 引擎

```python
class AsrEngine:
    """SenseVoiceSmall via 硅基流动 API"""
    async def transcribe(self, audio_wav: bytes) -> str:
        url = "https://api.siliconflow.cn/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {SILICONFLOW_KEY}"}
        files = {"file": ("audio.wav", audio_wav, "audio/wav")}
        data = {"model": "FunAudioLLM/SenseVoiceSmall"}
        resp = await httpx.post(url, headers=headers, files=files, data=data)
        return resp.json()["text"]
```

#### 5.4.3 知识检索引擎(双路 RAG)

```python
class KnowledgeRetriever:
    async def retrieve(self, person: Person, query: str = None) -> str:
        # 路径1:结构化人物档案
        profile = await self.get_person_profile(person.id)
        # 路径2:非结构化文档(语义检索)
        if query:
            query_embedding = await bge_m3.encode(query)  # 硅基流动 API
            docs = await db.execute("""
                SELECT content, metadata, 1 - (embedding <=> :q) AS sim
                FROM documents
                WHERE 1 - (embedding <=> :q) > 0.6
                  AND (metadata->>'person_id') = :pid
                   OR metadata->>'tags' @> profile.tags
                ORDER BY embedding <=> :q LIMIT 3
            """)
        else:
            docs = await self.get_person_docs(person.id, limit=3)
        return profile, docs
```

#### 5.4.4 LLM 生成引擎

```python
class LlmGenerator:
    async def generate_person_summary(self, person, profile, docs) -> dict:
        """初次识别:生成人物卡显示内容(5行以内)"""
        prompt = f"""你是社交助手。根据以下信息,为用户生成简短的人物卡。
要求:总共不超过5行,每行简短,适合眼镜小屏阅读。
人物:{person.name} 职位:{person.role} 关系:{person.relation}
标签:{person.tags} 备注:{person.notes} 上次见面:{person.last_met}
相关文档:{docs}
输出JSON:{{"display_lines": [...], "talking_points": [...]}}"""
        return await siliconflow_chat("deepseek-ai/DeepSeek-V3.2", prompt)

    async def generate_conversation_hint(
        self, person, conversation, new_utterance, pushed_topics
    ) -> dict | None:
        """对话中:判断是否推送 + 生成提示"""
        prompt = f"""你是社交助手。用户正在和 {person.name} 交谈。
人物档案:{person.profile} 对话历史:{conversation[-6:]}
新发言:{new_utterance} 已推送话题:{pushed_topics}
判断规则:
1. 新发言是否涉及需要提醒用户的信息?
2. 是否有高价值补充信息值得推送?
3. 不要重复已推送的话题
4. 宁可不推,不要刷屏
如果有价值,输出JSON:{{"should_push": true, "text": "简短提示(<30字)", "topic": "话题标识"}}
如果没必要,输出:{{"should_push": false}}"""
        return await siliconflow_chat("deepseek-ai/DeepSeek-V3.2", prompt)
```

### 5.5 推送决策引擎

```python
class PushDecisionEngine:
    MIN_PUSH_INTERVAL = 8.0      # 两次推送最少间隔8秒
    MAX_HINTS_PER_PERSON = 10    # 单人单次会话最多推10条提示
    SAME_TOPIC_COOLDOWN = 60.0   # 同一话题60秒内不重复

    async def should_push(self, hint: dict, session: SessionManager) -> bool:
        now = time.time()
        if now - session.last_push_ts < self.MIN_PUSH_INTERVAL:
            return False
        if len(session.pushed_topics) >= self.MAX_HINTS_PER_PERSON:
            return False
        if hint["topic"] in session.pushed_topics:
            return False
        return True
```

### 5.6 数据库表结构

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE persons (
    id          VARCHAR(36) PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    role        VARCHAR(200),
    relation    VARCHAR(200),
    tags        TEXT[] DEFAULT '{}',
    notes       TEXT,
    last_met    DATE,
    created_at  TIMESTAMP DEFAULT NOW(),
    updated_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE face_embeddings (
    id          SERIAL PRIMARY KEY,
    person_id   VARCHAR(36) REFERENCES persons(id) ON DELETE CASCADE,
    embedding   vector(512),
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE interactions (
    id          SERIAL PRIMARY KEY,
    person_id   VARCHAR(36) REFERENCES persons(id) ON DELETE CASCADE,
    met_at      DATE NOT NULL,
    summary     TEXT,
    topics      TEXT[] DEFAULT '{}',
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE documents (
    id          SERIAL PRIMARY KEY,
    content     TEXT NOT NULL,
    embedding   vector(1024),
    metadata    JSONB DEFAULT '{}',
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_face_emb ON face_embeddings USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_doc_emb ON documents USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_person_tags ON persons USING gin (tags);
CREATE INDEX idx_doc_meta ON documents USING gin (metadata);
```

## 6. 数据流与接口协议

### 6.1 WebSocket 消息协议(手机 ↔ 云端)

手机 → 云端(上行):
```json
{"type": "face", "img": "<base64 JPEG>", "ts": 1700000000123, "face_count": 1, "face_box": [120,80,200,160]}
{"type": "audio", "data": "<base64 WAV>", "ts": 1700000001234, "duration_ms": 2500}
{"type": "event", "event": "person_left", "ts": 1700000001234}
```

云端 → 手机(下行):
```json
{"type": "person_info", "id": "p001", "name": "张三", "role": "前公司CTO", "relation": "5年老朋友", "last_met": "2026-03-15", "notes": "对技术细节敏感", "display_lines": ["张三","前公司CTO / 5年老朋友","上次见面:2026-03-15","注意:对技术细节敏感"], "ts": 1700000001234}
{"type": "hint", "text": "他上周提到项目延期", "priority": "high", "topic": "project_delay", "display_ms": 5000, "ts": 1700000001234}
{"type": "clear", "reason": "person_left"}
{"type": "error", "code": "unknown_face", "msg": "未识别此人"}
{"type": "pong"}
```

手机收到下行消息后,由 CustomViewRenderer 翻译为布局 JSON 推送/更新到眼镜。

### 6.2 端到端时序

人脸识别流(初次,经手机中转):
```
t=0ms     手机触发拍照
t=400ms   眼镜完成拍摄,图片经 CXR-L 链路回传手机
t=450ms   手机本地 BlazeFace 检测(有人)
t=600ms   图片上传云端
t=800ms   InsightFace 识别完成(GPU)
t=850ms   查人物档案 + 相关文档
t=1250ms  LLM 生成人物卡摘要
t=1450ms  person_info 回手机 → CustomView 布局下发
t=1650ms  眼镜渲染人物卡
端到端:~1.7s(含眼镜拍摄与 CXR-L 链路回传开销)
```

对话增量提示流:
```
t=0ms     VAD 判定一句话结束(静音700ms后)
t=100ms   音频片段上传云端
t=400ms   SenseVoiceSmall ASR 转写完成
t=450ms   RAG 检索 + LLM 判断
t=1050ms  LLM 生成提示(若需要)
t=1150ms  hint 回手机 → updateCustomView 更新提示区
t=1350ms  眼镜显示提示
端到端:~1.4s(音频链路开销小)
```

### 6.3 错误处理与降级

| 场景 | 处理 |
|------|------|
| CXR-L 会话断开 | 手机自动重授权/重建会话;期间感知调度挂起,面板提示"眼镜连接中" |
| 网络断开(手机↔云端) | 手机本地缓存最近3条音频+1张人脸图,恢复后重传;面板显示"离线" |
| 陌生人 | 推送 {error, unknown_face};眼镜显示"未识别"卡片(2秒)后回待机 |
| ASR 失败 | 云端记录日志,静默失败,继续等下一句 |
| LLM 超时(>5秒) | 跳过本次推送,不阻塞后续流程,日志告警 |
| WebSocket 重连 | 指数退避(1s→2s→…→30s 封顶);重连后重发当前状态;云端从 Redis 恢复会话 |

### 6.4 数据量估算

单次会话(5分钟):人脸图片 ~440KB + 音频片段 ~750KB + 下行消息 ~10KB ≈ 1.2MB(手机侧流量)

## 7. 技术选型与部署

### 7.1 手机端依赖

```kotlin
// CXR-L SDK(核心)
implementation("com.rokid.cxr:client-l:1.0.3")
// 前置条件:手机安装 Rokid AI App ≥ 1.7.14

// Android 基础 + Compose(状态面板)
implementation(platform("androidx.compose:compose-bom:2024.06.00"))

// TFLite(人脸检测)
implementation("org.tensorflow:tensorflow-lite:2.14.0")
implementation("org.tensorflow:tensorflow-lite-support:0.4.4")

// ONNX Runtime(VAD)
implementation("com.microsoft.onnxruntime:onnxruntime-android:1.16.3")

// WebSocket
implementation("com.squareup.okhttp3:okhttp:4.12.0")

// JSON + 协程
implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.6.3")
implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.8.0")
```

参考工程:RenewCXRLSample(com.rokid.renewcxrlsample)。

### 7.2 云端依赖

```txt
fastapi==0.111.0
uvicorn[standard]==0.30.1
httpx==0.27.0
insightface==0.7.3
onnxruntime-gpu==1.18.1
sqlalchemy[asyncio]==2.0.30
asyncpg==0.29.0
pgvector==0.3.0
redis==5.0.4
```

### 7.3 Docker Compose 部署

```yaml
version: '3.8'
services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: superassistant
      POSTGRES_USER: sa
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
  redis:
    image: redis:7-alpine
  server:
    build: .
    environment:
      - SILICONFLOW_API_KEY=${SILICONFLOW_API_KEY}
      - DATABASE_URL=postgresql+asyncpg://sa:${DB_PASSWORD}@postgres:5432/superassistant
      - REDIS_URL=redis://redis:6379/0
    depends_on: [postgres, redis]
    ports: ["8000:8000"]
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
volumes:
  pgdata:
```

### 7.4 部署资源

RTX 5070 Ti (12GB VRAM):
| 组件 | VRAM | RAM |
|------|------|-----|
| InsightFace | ~2GB | ~1GB |
| PostgreSQL | - | ~512MB |
| Redis | - | ~128MB |
| FastAPI | - | ~256MB |
| **合计** | **~2GB / 12GB** | **~2GB** |

## 8. MVP 开发里程碑

| 阶段 | 周期 | 内容 | 里程碑 |
|------|------|------|--------|
| 1. 基础设施 | 1周 | 云端 Docker 搭建+数据库初始化;手机项目骨架;CXR-L 会话打通(授权→CustomView 待机界面);硅基流动三个 API 验证 | 眼镜显示手机下发的待机界面 |
| 2. 人脸识别链路 | 1周 | 定时拍照+回传;手机 BlazeFace 检测;云端 InsightFace+pgvector;person_info→CustomView 人物卡常驻 | 能识别面前的人并常驻显示 |
| 3. 对话补充链路 | 1.5周 | 音频监听+手机 VAD;SenseVoiceSmall ASR;DeepSeek 判断+生成;RAG 检索;hint→updateCustomView 提示区 | 对话中能推送补充信息 |
| 4. 会话编排与节流 | 1周 | 状态机完整流转;推送决策引擎;错误降级;人离开判定与清除;CXR-L 断线重连 | 完整流程可用 |
| 5. 优化与测试 | 1周 | 延迟优化;真实场景测试;人物/文档管理后台 | 可日常使用 |

总计:约 5-5.5 周。

## 9. 参考来源

- Rokid Glasses 裸机开发简介(官方文档,480×640 单绿显示等硬件约束)
- CXR-M SDK 简介(官方文档,自定义界面组件含 Lottie)
- CXR-L SDK 简介(官方文档,会话生命周期、CustomView/CustomApp 双模式、能力可用矩阵、RenewCXRLSample 示例工程)
- 硅基流动 SiliconCloud 平台(SenseVoiceSmall / DeepSeek-V3.2 / bge-m3)
- InsightFace 开源人脸识别框架
- Silero VAD 开源语音活动检测模型
