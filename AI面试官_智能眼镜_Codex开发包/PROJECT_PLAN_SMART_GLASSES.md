# AI 面试官项目——智能眼镜候选人信息接入迭代计划书

> 建议放置位置：仓库根目录 `/PROJECT_PLAN_SMART_GLASSES.md`
>
> 本文档基于当前 AI 面试官项目交接上下文制定。除非仓库代码实际情况与本文不同，否则 Codex 应以“先验证现状、再最小改动实现需求”为原则执行。

---

## 1. 项目背景

当前项目已经具备一套 AI 面试系统原型，包含：

- Java 17 + Spring Boot 3.3.4 业务后端
- MySQL 候选人/岗位/题库/面试记录数据库
- Vue 2 招聘管理端
- uni-app 候选人端
- Python FastAPI AI 面试/复试服务
- Redis、MinIO 等基础设施
- 姓名精确匹配功能
- 同名候选人多结果返回能力
- 初试、复试、报告生成等已有链路

本次新增硬件形态：

```text
智能眼镜
    ↓
手机
    ↓
网络
    ↓
AI 面试官服务器
    ↓
MySQL / 现有业务数据
```

智能眼镜在手机上显示的前端页面已经完成。

**本次开发不重写该前端页面，只保留并完善通信接口。**

正式服务器地址尚未确定，因此所有服务地址必须配置化，生产地址当前保留为空，不允许继续硬编码内网 IP。

---

## 2. 本次迭代目标

实现一条稳定、可测试、可扩展的候选人识别与展示链路：

```text
眼镜端发起候选人姓名选择/搜索
        ↓
手机收到事件
        ↓
手机请求 Java 后端
        ↓
Java 后端调用现有候选人姓名匹配能力
        ↓
MySQL 查询
        ↓
返回 0 / 1 / 多名候选人
        ↓
手机把候选人摘要发送给眼镜
        ↓
若存在同名候选人，则全部展示
        ↓
面试人员人工判断并选择具体候选人
        ↓
使用 candidateId 锁定唯一身份
        ↓
Java 后端聚合候选人完整业务信息
        ↓
手机接收并转发
        ↓
智能眼镜现有前端展示
```

---

## 3. 核心原则

### 3.1 candidateId 是唯一身份主键

姓名只用于：

- 搜索
- 展示
- 人工选择

姓名禁止用于：

- 面试会话唯一标识
- 写入面试记录的最终身份
- AI 上下文主键
- 后续接口唯一定位

所有最终业务逻辑必须使用：

```text
candidateId
```

### 3.2 不重复开发姓名匹配

项目中已经存在姓名匹配能力：

```http
GET /candidate/match?name=姓名
```

已有能力包括：

- 姓名前后空格清理
- 精确姓名匹配
- 0 条结果
- 1 条结果
- 多条同名结果
- 手机号脱敏
- 返回学校、专业、岗位、性别、邮箱等候选人摘要

本次必须复用已有 Service/Mapper/SQL。

禁止：

- 新建另一套姓名匹配数据库查询
- 使用 RAG 查人
- 使用向量数据库确认候选人身份
- 用手机号代替 candidateId 作为新增链路主键

---

## 4. 本次范围

### 4.1 必须完成

1. 智能眼镜通信抽象接口
2. 手机 ↔ 智能眼镜桥接层
3. Mock 智能眼镜通信实现
4. 手机 ↔ Java Server HTTP 通信
5. 统一服务器地址配置
6. 候选人姓名搜索
7. 同名候选人完整摘要列表
8. 人工选择候选人
9. candidateId 唯一确认
10. 候选人完整上下文查询
11. 手机向眼镜发送候选人完整信息
12. 加载态/空结果/服务器错误/网络错误
13. API DTO/VO 明确定义
14. 自动化测试
15. 开发文档
16. Mock 演示链路
17. 安全与隐私最小化返回

### 4.2 本次不做

除非为了本需求必须修改，否则本次不做：

- 重写智能眼镜 UI
- 重写管理端
- 重做姓名匹配
- 重构完整 AI 面试流程
- 更换大模型
- 重做 RAG
- 重做 ASR
- 生产服务器部署
- 真实厂商智能眼镜 SDK 深度集成
- 自动根据姓名确认候选人
- 基于 AI 猜测同名候选人身份

---

## 5. 推荐架构

```text
┌─────────────────────────────┐
│       Smart Glasses         │
│  已有展示页面 / 交互页面     │
└──────────────┬──────────────┘
               │
               │ Bluetooth / Wi-Fi /
               │ Vendor SDK / Local Socket
               │
┌──────────────▼──────────────┐
│        Phone Client         │
│                             │
│  GlassesBridge              │
│  CandidateGateway           │
│  ServerApiClient            │
│  State / Error Handling     │
└──────────────┬──────────────┘
               │ HTTPS REST
               │
┌──────────────▼──────────────┐
│      Java Spring Boot       │
│                             │
│  GlassesCandidateController │
│  CandidateService           │
│  CandidateContextService    │
│  Auth / Audit / Validation  │
└──────────────┬──────────────┘
               │
               │ MyBatis / MySQL
               │
┌──────────────▼──────────────┐
│            MySQL            │
│ candidate / job / interview │
│ answer / reexamine ...      │
└─────────────────────────────┘
```

原则：

```text
智能眼镜不连接数据库
手机不连接数据库
智能眼镜不直接连接 Python 服务
手机新增链路只连接 Java Server
Java 作为统一业务入口
```

---

## 6. 智能眼镜通信层设计

由于具体智能眼镜品牌/SDK 暂未确定，必须使用适配器模式。

建议定义：

```text
IGlassesBridge
```

或项目当前技术栈对应的等价接口。

推荐能力：

```text
connect()
disconnect()
isConnected()

onCandidateSearch(callback)
onCandidateSelected(callback)

sendCandidateMatches(data)
sendCandidateContext(data)

sendLoading(state)
sendError(error)

sendConnectionState(state)
```

实现：

```text
IGlassesBridge
    ├── MockGlassesBridge
    └── VendorGlassesBridge
```

其中：

### MockGlassesBridge

必须可运行。

作用：

- 没有真实眼镜时完成开发
- 模拟眼镜输入姓名
- 模拟选择 candidateId
- 显示收到的候选人信息
- 用于自动测试和演示

### VendorGlassesBridge

当前只保留接口/占位实现。

禁止凭空假设某一厂商 SDK。

后续拿到眼镜品牌、SDK、通信协议后，只替换该适配器，不改变业务层。

---

## 7. 手机端设计

手机定位：

**通信网关 / Companion App**

职责：

1. 接收智能眼镜事件
2. 调用 Java Server
3. 维护当前查询状态
4. 将候选人摘要转发给眼镜
5. 接收人工选择的 candidateId
6. 获取完整候选人上下文
7. 将上下文发送给眼镜
8. 错误提示和重试
9. 连接状态管理

禁止手机端：

- 直接访问 MySQL
- 直接访问 Python DB Tool
- 保存数据库账号密码
- 自行通过姓名确定唯一身份
- 对同名候选人自动决策

---

## 8. 服务器地址配置

当前正式服务器地址未确定。

新增统一配置：

```env
AI_INTERVIEWER_SERVER_BASE_URL=
```

若当前客户端环境不支持 `.env`，应建立等价的集中配置层。

要求：

1. 业务代码不出现固定服务器 IP
2. localhost 只允许出现在开发配置或示例配置
3. 内网 IP 不允许散落在页面文件中
4. 服务地址为空时不能自动猜测
5. 服务地址为空应返回明确状态

推荐错误：

```text
SERVER_NOT_CONFIGURED
```

示例：

```env
# .env.example

AI_INTERVIEWER_SERVER_BASE_URL=
```

开发者本地自行填写：

```env
AI_INTERVIEWER_SERVER_BASE_URL=http://192.168.1.100:8080
```

未来生产：

```env
AI_INTERVIEWER_SERVER_BASE_URL=https://api.example.com
```

---

## 9. Java 后端 API

Codex 必须首先阅读现有 Controller、Service、Mapper 和 VO，尽量复用现有结构。

### 9.1 候选人搜索

可以直接复用现有：

```http
GET /candidate/match?name={name}
```

如果为了智能眼镜业务边界需要新增 Gateway API，可以新增：

```http
GET /api/glasses/candidates/search?name={name}
```

但是内部必须调用已有 Candidate Service。

禁止复制 SQL。

建议返回：

```json
{
  "success": true,
  "query": "张三",
  "count": 2,
  "candidates": [
    {
      "candidateId": 101,
      "realName": "张三",
      "gender": "男",
      "school": "XX大学",
      "major": "软件工程",
      "jobName": "Java开发工程师",
      "mobileMasked": "138****1234",
      "emailMasked": "z***@example.com"
    }
  ]
}
```

### 9.2 候选人上下文

新增推荐接口：

```http
GET /api/glasses/candidates/{candidateId}/context
```

用途：

在人工确认候选人后，根据 candidateId 获取眼镜需要展示的完整业务上下文。

必须避免直接序列化数据库 Entity。

使用专门 VO，例如：

```text
GlassesCandidateContextVO
```

建议字段：

```text
candidateId
realName
gender
age             // 仅数据库现有且业务需要时
school
major
education
jobId
jobName
jobDescriptionSummary
candidateProfile
skills
experience
interviewStatus
initialInterviewSummary
reviewInterviewSummary
latestInterviewResult
latestReportUrl          // 仅有权限且确实需要
```

具体字段必须以当前数据库真实存在字段为准。

不要为了满足此文档虚构数据库字段。

不存在字段：

- 不新增无意义字段
- 不返回 null 大对象
- 在 DTO 中合理省略

### 9.3 不应默认返回的数据

智能眼镜默认不得返回：

- 身份证完整号码
- 手机号完整号码
- 数据库内部密码
- 管理员信息
- MinIO 密钥
- 模型密钥
- 无业务必要的家庭地址
- 与当前面试无关的敏感信息

---

## 10. 同名候选人业务流程

### 情况 A：无结果

服务器：

```text
count = 0
```

眼镜：

```text
未找到候选人“张三”
```

允许：

```text
重新搜索
```

### 情况 B：唯一结果

眼镜展示摘要：

```text
张三
XX大学
软件工程
Java开发工程师
138****1234
```

然后要求人工确认：

```text
确认选择
```

确认后：

```text
candidateId → context API
```

### 情况 C：多个同名

必须：

```text
展示所有匹配结果
```

例如：

```text
张三 | 上海XX大学 | 软件工程 | Java开发
张三 | XX科技大学 | 计算机 | 算法工程师
张三 | XX学院     | 自动化 | 测试工程师
```

人工选择。

禁止：

- 默认选第一个
- 用 AI 自动猜
- 用数据库返回顺序判断
- 根据手机号进行隐藏自动匹配

---

## 11. 状态机

手机/眼镜候选人查询建议定义：

```text
IDLE
    ↓
SEARCHING
    ↓
NO_RESULT
    或
MATCHES_READY
    ↓
WAITING_FOR_SELECTION
    ↓
LOADING_CONTEXT
    ↓
CANDIDATE_CONFIRMED
```

错误状态：

```text
SERVER_NOT_CONFIGURED
NETWORK_ERROR
SERVER_ERROR
INVALID_RESPONSE
GLASSES_DISCONNECTED
CANDIDATE_NOT_FOUND
CANDIDATE_CHANGED
UNAUTHORIZED
```

---

## 12. 候选人上下文一致性

用户在重名列表人工选择后：

```text
candidateId
```

必须成为后续所有接口主键。

例如：

```text
currentCandidateId = 123
```

后续：

```text
获取候选人详情
获取岗位
获取初试信息
获取复试历史
AI 面试
生成报告
```

均优先围绕：

```text
candidateId
interviewId
```

设计。

不要新增依赖手机号的业务链路。

---

## 13. 安全要求

### P0

必须检查仓库中的：

- 数据库凭据
- MinIO 凭据
- 模型 API Key
- 第三方 SDK Key
- 内网 IP
- 明文密码

本次不要擅自修改真实部署环境，但必须：

1. 新代码禁止新增硬编码凭据
2. 新增 `.env.example`
3. 日志禁止输出身份证号/完整手机号/token
4. API 返回最小化
5. candidateId 参数校验
6. 禁止 SQL 拼接
7. 统一异常响应
8. 为 Glasses API 预留认证/鉴权边界
9. 不把敏感数据发到智能眼镜，除非确有展示需求

---

## 14. 测试要求

### 14.1 Java

至少覆盖：

#### 姓名搜索

```text
空姓名
无结果
唯一姓名
两个同名
姓名前后空格
特殊字符
超长姓名
```

#### candidateId

```text
存在 ID
不存在 ID
非法 ID
负数
缺失
```

#### 上下文

```text
基础候选人数据
岗位存在
岗位不存在
面试记录不存在
面试记录存在
敏感字段未返回
```

### 14.2 Phone / Glasses Bridge

Mock 测试：

```text
眼镜搜索姓名
手机收到搜索
请求 Server
Server 返回两个同名
手机向眼镜发送两个候选人
模拟人工选择第二个
手机使用第二个 candidateId 获取 context
眼镜收到第二个候选人的完整信息
```

必须保证没有：

```text
误选第一名候选人
```

### 14.3 网络异常

测试：

```text
Server 地址为空
Server 不可访问
超时
HTTP 4xx
HTTP 5xx
JSON 格式异常
眼镜中途断开
重复点击候选人
重复搜索
```

---

## 15. Mock 演示

Codex 必须提供无需真实智能眼镜即可执行的 Demo。

例如：

```text
1. 启动 Java Server
2. 启动手机/Mock Client
3. Mock Glasses 输入“张三”
4. 展示 Server 返回的候选人
5. 选择 candidateId
6. 获取 candidate context
7. 控制台或 Mock UI 显示眼镜收到的数据
```

如果数据库无法在当前环境启动：

使用：

- mock repository
- test fixture
- stub API

完成自动化链路验证。

---

## 16. 日志与诊断

建议统一：

```text
requestId
candidateId
eventType
clientType
duration
result
errorCode
```

例如：

```text
event=GLASSES_CANDIDATE_SEARCH
queryName=张*
matchCount=2
requestId=...
```

日志禁止记录：

```text
完整身份证
完整手机号
token
数据库密码
API Key
```

---

## 17. 推荐开发阶段

### Phase 0：仓库审计

先完成：

- 找到真实模块目录
- 找到已有姓名匹配代码
- 找到手机端当前网络层
- 找到智能眼镜已有前端接口
- 找到当前配置文件
- 找到 Candidate Entity/VO/Mapper
- 确认可构建模块

输出：

```text
docs/CODEX_REPO_AUDIT.md
```

### Phase 1：配置治理

完成：

```text
统一 Server Base URL
.env.example
删除本次涉及页面中的硬编码地址
```

### Phase 2：后端 Glasses Candidate API

完成：

```text
/search
/{candidateId}/context
DTO/VO
Service
测试
```

### Phase 3：Phone ↔ Server

完成：

```text
ServerApiClient
CandidateGateway
错误处理
状态管理
```

### Phase 4：Glasses Bridge

完成：

```text
IGlassesBridge
MockGlassesBridge
VendorGlassesBridge placeholder
```

### Phase 5：端到端 Mock

完成：

```text
姓名 → 多候选人 → 人工选择 → context → glasses
```

### Phase 6：测试和文档

完成：

```text
测试
README
API 文档
启动说明
验收记录
```

---

## 18. 完成定义 Definition of Done

只有满足以下条件才能声明本次开发完成：

- [ ] 没有重写现有姓名匹配
- [ ] 姓名只用于搜索
- [ ] candidateId 用于最终身份确认
- [ ] 同名候选人全部展示
- [ ] 人工选择后才加载完整资料
- [ ] 手机不直接访问数据库
- [ ] Glasses 不直接访问数据库
- [ ] 新链路只调用 Java Server
- [ ] 正式 Server 地址未写死
- [ ] Server 地址为空时有明确错误
- [ ] Mock Glasses 可运行
- [ ] 真实眼镜 SDK 有适配器接口
- [ ] candidate context API 可用
- [ ] API 不泄漏高风险 PII
- [ ] Java 测试通过
- [ ] 手机/Bridge 测试通过
- [ ] 同名 E2E 测试通过
- [ ] 网络错误有处理
- [ ] 新增代码可以构建
- [ ] README 已更新
- [ ] 输出最终开发报告

---

## 19. 最终交付物

Codex 最终必须交付：

```text
源代码修改
数据库迁移（仅确实需要时）
配置样例
自动化测试
Mock Glasses
API 文档
启动说明
测试结果
开发总结
已知限制
真实眼镜 SDK 后续接入说明
```

---

## 20. 后续扩展

本迭代完成后可继续：

```text
眼镜显示实时 AI 面试提示
        ↓
服务器 WebSocket 推送
        ↓
实时语音识别
        ↓
候选人回答分析
        ↓
面试官视野提示
```

因此本期代码必须避免把 Glasses Bridge 和候选人查询逻辑耦合死。
