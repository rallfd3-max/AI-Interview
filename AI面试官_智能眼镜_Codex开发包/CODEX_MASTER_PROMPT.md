# CODEX_MASTER_PROMPT.md

> 将本文件放到仓库根目录。
>
> Codex 开始工作后必须首先阅读：
>
> 1. `GPT项目交接上下文.md`（如果仓库内存在）
> 2. `PROJECT_PLAN_SMART_GLASSES.md`
> 3. `FEASIBILITY_SMART_GLASSES.md`
> 4. 本文件
>
> 然后自动开始开发。
>
> 不要要求用户每完成一步后发送“继续”。

---

# 你的角色

你现在是该 AI 面试官项目的：

- 资深软件架构师
- Java Spring Boot 工程师
- uni-app / Vue 工程师
- 移动端通信工程师
- API 设计工程师
- 测试工程师
- DevOps 工程师
- 安全审计工程师

你的任务不是仅仅分析项目。

你的任务是：

# 在现有仓库基础上直接完成本轮智能眼镜接入开发。

你必须实际：

- 阅读代码
- 修改代码
- 新增代码
- 运行构建
- 运行测试
- 修复错误
- 更新文档
- 输出最终开发报告

---

# 一、总目标

实现：

```text
Smart Glasses
        ↓
Phone Gateway
        ↓
Java Server
        ↓
MySQL
```

的候选人信息查询链路。

业务流程：

```text
眼镜输入/选择姓名
        ↓
手机接收
        ↓
Server 搜索候选人
        ↓
0 / 1 / N 个候选人
        ↓
返回摘要
        ↓
若重名则全部显示
        ↓
人工选择
        ↓
candidateId
        ↓
Server 聚合候选人信息
        ↓
Phone
        ↓
Glasses
```

---

# 二、不可违反的项目事实

开始修改代码前，先检查仓库并验证以下事实。

当前交接信息表明：

1. Java 后端为 Spring Boot 3.3.4 / Java 17
2. Java 是主要业务服务器
3. MySQL 保存候选人、岗位、面试数据
4. Python 服务主要处理 AI / 复试 / 报告
5. 当前已有姓名匹配接口
6. 当前已有同名候选人多结果返回
7. `candidate.id` 是业务主键
8. `real_name` 可以重复
9. 当前部分旧逻辑仍使用手机号作 session 标识
10. 多个模块存在硬编码 IP
11. 智能眼镜已有前端页面，本轮不重写
12. 正式服务器地址目前未知

如果代码与上述情况存在差异：

- 以真实代码为准
- 在开发报告记录差异
- 不要擅自假设

---

# 三、最高优先级约束

## 3.1 不允许重做姓名匹配

必须寻找并复用：

```http
GET /candidate/match?name=
```

对应的：

```text
Controller
Service
Mapper
VO
SQL
```

如果现有代码存在小问题，可以修复。

禁止：

- 再写第二套 matchByName SQL
- 建新姓名搜索系统
- 用 RAG 查人
- 用向量数据库查人
- 用 LLM 判定候选人身份

---

## 3.2 candidateId 是唯一主键

搜索：

```text
name
```

最终确认：

```text
candidateId
```

从用户人工选择候选人后开始，所有新增逻辑必须使用：

```text
candidateId
```

不能新增：

```text
mobile as sessionId
```

---

## 3.3 手机不访问数据库

架构必须保持：

```text
Glasses
 ↓
Phone
 ↓
Java
 ↓
MySQL
```

禁止：

```text
Phone → MySQL
Glasses → MySQL
Glasses → Python DB Tool
```

---

## 3.4 新智能眼镜链路只通过 Java Server

即使当前候选人客户端存在：

```text
Java + Python
```

双直连遗留结构，也不要把这种模式复制到智能眼镜功能。

---

## 3.5 不重写现有 Glasses UI

如果仓库存在智能眼镜前端：

- 阅读
- 识别已有接口
- 保留 UI
- 只新增/接入通信层

除非为了接口接入必须调整少量代码，否则：

```text
NO UI REWRITE
```

---

# 四、第一阶段：仓库自动审计

开始任何大规模修改之前，自动完成仓库审计。

需要定位：

```text
Java Application
CandidateController
CandidateService
CandidateServiceImpl
CandidateMapper
Candidate Mapper XML
Candidate Entity
Candidate VO
/candidate/match
candidate detail API
job service
interview record service
uni-app 网络请求封装
智能眼镜现有前端
server URL 配置
Python API
```

检查：

```text
git status
Java build
frontend build method
Python project structure
existing tests
hard-coded URLs
credentials
```

输出：

```text
docs/CODEX_REPO_AUDIT.md
```

内容：

```text
实际模块
实际入口
现有姓名匹配代码位置
现有 Server 地址位置
眼镜前端位置
实际构建结果
本轮准备修改的文件
风险
```

完成后：

# 不要停下来询问用户。

直接继续开发。

---

# 五、第二阶段：统一 Server URL

搜索整个本次涉及模块中的：

```text
localhost
127.0.0.1
192.168.
100.
10.
http://
https://
```

识别硬编码 Server URL。

本轮涉及的 Phone / Glasses 新代码必须统一使用：

```text
AI_INTERVIEWER_SERVER_BASE_URL
```

或项目技术栈中功能等价的配置。

新增：

```text
.env.example
```

示例：

```env
AI_INTERVIEWER_SERVER_BASE_URL=
```

要求：

```text
空值 = 不配置 Server
```

运行时返回：

```text
SERVER_NOT_CONFIGURED
```

不能：

```text
fallback localhost
```

除非明确属于 dev config。

不要为了本任务一次性重构整个仓库的所有旧地址。

只治理：

```text
本轮新链路
+
与新链路直接相关的地址
```

---

# 六、第三阶段：后端 API

## 6.1 Candidate Search

优先复用现有：

```text
/candidate/match
```

如果业务边界需要，可以建立：

```http
GET /api/glasses/candidates/search
```

但它必须：

```text
delegate to existing CandidateService
```

禁止复制 Mapper SQL。

---

## 6.2 Candidate Context

新增：

```http
GET /api/glasses/candidates/{candidateId}/context
```

如果项目现有 URL 规范不同，可以遵循现有风格，但文档必须明确。

新增：

```text
GlassesCandidateContextVO
```

不要直接返回 Candidate Entity。

根据数据库真实字段组合：

```text
candidate
job
interview_record
reexamine_record
```

等已有数据。

优先展示：

```text
candidateId
realName
gender
school
major
education
job
interviewStatus
interviewSummary
```

数据库不存在的字段：

```text
不要编造
```

---

# 七、PII 最小化

搜索结果默认只返回用于人工区分候选人的字段。

手机号：

```text
masked
```

身份证：

```text
不要返回
```

家庭地址：

```text
默认不要返回
```

完整录音/视频：

```text
不要默认返回
```

日志：

禁止记录：

```text
identity_num
完整 mobile
token
password
secret
API key
```

---

# 八、第四阶段：Phone Server Client

在现有 Phone Client 中建立统一：

```text
ServerApiClient
```

或现有架构等价封装。

实现：

```text
searchCandidates(name)
getCandidateContext(candidateId)
healthCheck()
```

必须：

```text
timeout
error mapping
invalid JSON handling
server not configured handling
```

---

# 九、第五阶段：Candidate Gateway

建立业务层：

```text
CandidateGateway
```

职责：

```text
接收 Glasses search event
调用 searchCandidates
把候选人列表发送给 Glasses
接收 selected candidateId
调用 getCandidateContext
把 Context 发送给 Glasses
```

禁止把这些逻辑散落在 UI 页面。

---

# 十、第六阶段：Glasses Bridge

建立：

```text
IGlassesBridge
```

或项目语言等价接口。

必须实现：

```text
connect
disconnect
isConnected

candidate search event
candidate selected event

sendCandidateMatches
sendCandidateContext
sendLoading
sendError
```

至少实现：

```text
MockGlassesBridge
```

同时新增：

```text
VendorGlassesBridge
```

占位/适配器接口。

VendorGlassesBridge：

```text
不假设具体 SDK
不伪造 SDK 调用
```

只留下清晰扩展点和 TODO。

---

# 十一、Mock Glasses 必须能够演示

实现一个最简单但真实可运行的 Mock。

例如：

```text
输入姓名
 ↓
触发 GlassesBridge
 ↓
Phone
 ↓
Java API
 ↓
显示所有候选人
 ↓
选择 candidateId
 ↓
Java Context API
 ↓
Mock 显示最终 Context
```

真实眼镜不存在时，也必须能够证明：

```text
完整业务链路逻辑成立
```

---

# 十二、同名候选人是必须测试的 P0 场景

测试数据：

```text
Candidate A
name=张三
candidateId=101

Candidate B
name=张三
candidateId=202
```

预期：

```text
Search 张三

返回：
101
202
```

然后：

```text
人工选择 202
```

必须：

```text
只加载 candidateId=202
```

测试必须明确断言：

```text
系统没有默认加载 candidateId=101
```

---

# 十三、状态机

建立清晰状态：

```text
IDLE
SEARCHING
NO_RESULT
MATCHES_READY
WAITING_FOR_SELECTION
LOADING_CONTEXT
CANDIDATE_CONFIRMED
ERROR
```

错误：

```text
SERVER_NOT_CONFIGURED
NETWORK_ERROR
SERVER_ERROR
INVALID_RESPONSE
CANDIDATE_NOT_FOUND
GLASSES_DISCONNECTED
UNAUTHORIZED
```

若项目已有统一错误体系：

```text
复用
```

---

# 十四、测试策略

你必须真正运行测试。

## Java

增加：

```text
Service tests
Controller tests
Mapper / integration tests（视当前环境）
```

覆盖：

```text
name empty
name trim
0 match
1 match
duplicate names
candidateId valid
candidateId invalid
context
PII filtering
```

## Phone / Glasses

覆盖：

```text
search
duplicate selection
context
server not configured
timeout
network error
bad response
glasses disconnected
```

---

# 十五、构建

你必须实际运行仓库可以执行的构建命令。

Java 例如：

```bash
mvn test
mvn package
```

不要只运行：

```text
-DskipTests
```

就声称测试成功。

Phone / frontend：

先判断项目真实构建方式。

如果原有管理端构建本来就失败：

```text
不要把旧问题冒充为本次引入
```

记录：

```text
pre-existing issue
```

但新修改模块必须尽可能验证。

---

# 十六、不要大范围重构

本轮目标明确。

禁止借机：

```text
升级整个 Vue 2
迁移整个管理端 Vite
重写 Python 服务
重写 RAG
重做数据库
删除大量历史代码
```

除非某个改动是新功能正常运行的硬性前提。

优先：

```text
small
safe
testable
reversible
```

---

# 十七、数据库变更

原则：

```text
尽量零数据库结构变更
```

因为：

```text
candidate.id
real_name
job
interview records
```

已经存在。

如果确实发现 context 查询必须新增索引：

允许新增 migration。

但是：

```text
不要删除字段
不要重命名历史字段
不要破坏现有数据
```

---

# 十八、真实眼镜接入之前的接口契约

最终建立文档：

```text
docs/SMART_GLASSES_INTEGRATION.md
```

说明：

```text
Phone expects from Glasses:
- SEARCH_CANDIDATE
- SELECT_CANDIDATE

Phone sends to Glasses:
- CANDIDATE_MATCHES
- CANDIDATE_CONTEXT
- LOADING
- ERROR
```

建议 JSON：

```json
{
  "type": "SEARCH_CANDIDATE",
  "payload": {
    "name": "张三"
  }
}
```

```json
{
  "type": "SELECT_CANDIDATE",
  "payload": {
    "candidateId": 202
  }
}
```

```json
{
  "type": "CANDIDATE_MATCHES",
  "payload": {
    "count": 2,
    "candidates": []
  }
}
```

```json
{
  "type": "CANDIDATE_CONTEXT",
  "payload": {
    "candidateId": 202
  }
}
```

具体字段以项目实际 DTO 为准。

---

# 十九、开发中遇到问题如何处理

不要因为以下情况停止整个任务：

```text
数据库无法启动
外部 RAG 不可用
模型服务不可用
真实 Glasses 不存在
MinIO 不可用
```

如果这些不属于当前需求的核心依赖：

使用：

```text
mock
stub
fixture
```

继续完成本轮开发和自动测试。

只有真正无法绕过的阻塞才记录。

---

# 二十、Codex 自动执行规则

从现在开始：

# 不要等待用户发送“继续”。

自动循环：

```text
Inspect
 ↓
Plan
 ↓
Implement
 ↓
Build
 ↓
Test
 ↓
Fix
 ↓
Retest
 ↓
Document
 ↓
Final Audit
```

如果测试失败：

```text
分析失败
修复
重新运行
```

只要在权限和仓库环境内可完成，就继续推进。

---

# 二十一、禁止虚报

禁止写：

```text
测试全部通过
```

除非确实运行。

禁止写：

```text
真实眼镜已连接
```

除非真的存在硬件和 SDK 验证。

应该区分：

```text
implemented
mock verified
integration verified
hardware pending
blocked
```

---

# 二十二、最终必须生成的文件

至少：

```text
docs/CODEX_REPO_AUDIT.md
docs/SMART_GLASSES_INTEGRATION.md
docs/SMART_GLASSES_API.md
docs/SMART_GLASSES_TEST_REPORT.md
docs/CODEX_FINAL_REPORT.md
```

如果仓库已有 docs 规范：

遵循现有目录。

---

# 二十三、最终报告内容

`CODEX_FINAL_REPORT.md` 必须包含：

```text
1. 原始项目状态
2. 实际修改文件
3. 新增架构
4. API
5. Glasses Bridge
6. Mock
7. Server 配置
8. 测试
9. 构建结果
10. 同名候选人验证
11. 安全检查
12. 未解决问题
13. 真实眼镜后续需要的信息
```

---

# 二十四、最终验收条件

必须逐项检查：

```text
[ ] existing candidate match reused
[ ] candidateId is identity
[ ] duplicate names displayed
[ ] manual candidate selection
[ ] context loaded by candidateId
[ ] Java is server gateway
[ ] phone does not access DB
[ ] server URL configurable
[ ] production server can remain blank
[ ] empty server URL gives explicit error
[ ] glasses UI preserved
[ ] IGlassesBridge exists
[ ] MockGlassesBridge works
[ ] Vendor bridge extension exists
[ ] tests added
[ ] tests executed
[ ] build executed
[ ] PII minimized
[ ] docs created
[ ] final report created
```

---

# 二十五、现在立即开始

现在不要向用户复述计划。

不要询问：

```text
是否开始
是否继续
下一步要不要做
```

直接：

```text
1. 阅读上述文档
2. 审计仓库
3. 创建 docs/CODEX_REPO_AUDIT.md
4. 自动进入 Phase 1
5. 一直执行到本轮能完成的所有任务结束
6. 最后输出 CODEX_FINAL_REPORT.md
```

开始开发。
