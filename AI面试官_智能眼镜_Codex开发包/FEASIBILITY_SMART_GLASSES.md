# AI 面试官智能眼镜接入——可行性分析

> 建议放置位置：仓库根目录 `/FEASIBILITY_SMART_GLASSES.md`

---

## 1. 结论

本次需求总体判断：

# 技术可行性：高

主要原因：

1. 候选人数据已经存在于 MySQL
2. Java 后端已有候选人管理能力
3. 姓名精确匹配和同名多结果已经实现
4. `candidateId` 已可作为唯一候选人标识
5. 手机作为智能眼镜与互联网之间的 Gateway 是合理架构
6. 智能眼镜前端已经完成，本次主要工作集中在通信和后端 API
7. 正式服务器地址尚未确定并不会阻止开发，只要进行配置化
8. 在真实眼镜 SDK 尚未确定的情况下，可以用 Adapter + Mock 完成绝大多数业务开发和测试

当前最大不确定性不是数据库或业务逻辑，而是：

```text
真实智能眼镜具体品牌
SDK
手机与眼镜实际通信方式
操作系统
权限模型
数据传输能力
```

因此正确做法不是等待硬件再开发，而是：

```text
先完成协议层和业务层
        +
MockGlassesBridge
        +
VendorGlassesBridge 接口
```

以后只替换厂商适配层。

---

## 2. 现有项目对本需求的支持度

### 2.1 Java 后端

现有 Spring Boot 后端已经承担：

- 候选人
- 岗位
- 题库
- 面试记录
- 上传
- 基础业务逻辑

因此它天然适合作为：

```text
手机端统一 Server API
```

可行性：

```text
高
```

不建议手机：

```text
Java + Python 双直连
```

新增智能眼镜链路应统一经过 Java。

---

## 3. 姓名搜索可行性

项目已经有：

```text
GET /candidate/match
```

并支持：

```text
0
1
N
```

结果。

这意味着：

```text
姓名搜索 → 同名列表 → 人工选择
```

无需重新设计底层机制。

可行性：

```text
非常高
```

---

## 4. 同名处理可行性

数据库允许：

```text
real_name 重复
```

所以同名属于正常业务情况。

通过：

```text
candidateId
```

可彻底解决最终身份冲突。

正确流程：

```text
name
 ↓
candidate[]
 ↓
human selection
 ↓
candidateId
```

因此业务和技术均可行。

---

## 5. 候选人完整信息展示可行性

相关数据已经分布在：

```text
candidate
job
interview_record
answer_record
reexamine_record
reexamine_summary
```

等表。

可以由 Java Service 聚合成：

```text
GlassesCandidateContextVO
```

风险：

当前数据模型中存在部分含义接近字段，例如：

```text
job_id
job
job_can
job_name
```

所以 Codex 不能简单猜测字段语义。

应先检查当前 Mapper / Service 实际使用方式。

可行性：

```text
高
```

工程复杂度：

```text
中
```

---

## 6. 手机连接服务器可行性

推荐：

```text
HTTPS REST
```

用于：

- 搜索
- 详情
- context

未来：

```text
WebSocket
```

用于：

- AI 提示
- 面试状态
- 实时消息

技术成熟，无明显阻碍。

可行性：

```text
非常高
```

---

## 7. 智能眼镜连接手机可行性

理论路径可能包括：

```text
Bluetooth
BLE
Wi-Fi
Wi-Fi Direct
Local WebSocket
厂商 SDK
Android Companion API
局域网 Socket
```

但目前没有提供真实眼镜型号，因此不能确认最终实现方式。

因此：

### 当前阶段

可实现：

```text
100% 的业务接口
100% 的服务器链路
100% 的状态机
100% 的 Mock Glasses
80%~95% 的手机侧集成结构
```

暂时不能保证：

```text
真实眼镜物理通信 100% 可直接运行
```

直到拿到：

```text
品牌 + 型号 + SDK + 开发文档
```

可行性判断：

```text
架构可行性：高
厂商最终接入可行性：待硬件 SDK 验证
```

---

## 8. Server 地址未确定

不会阻塞开发。

应该使用：

```text
AI_INTERVIEWER_SERVER_BASE_URL
```

实现。

当前：

```text
empty
```

生产时注入。

优点：

- 不需要重新编译业务代码
- 可切换局域网服务器
- 可切换测试服务器
- 可切换生产服务器
- 避免继续出现大量硬编码 IP

可行性：

```text
非常高
```

---

## 9. 性能

候选人姓名搜索属于传统 MySQL 查询。

如果：

```text
candidate.real_name
```

存在索引，则一般可以满足实时交互。

智能眼镜操作对搜索响应要求预计：

```text
< 1s 理想
< 2s 可接受
```

真实性能需以实际部署测试为准。

候选人 context 可能关联多表，但数据量通常有限。

推荐：

```text
按需聚合
避免 N+1
只返回眼镜需要字段
```

---

## 10. 网络风险

智能眼镜依赖：

```text
Glasses ↔ Phone
```

手机依赖：

```text
Phone ↔ Server
```

因此存在两段网络。

必须处理：

```text
眼镜断开
手机无网络
服务器离线
请求超时
服务器地址为空
重复请求
慢响应
JSON 错误
```

建议：

```text
Request Timeout
Retry（仅安全 GET）
Connection State
Request ID
Error Code
```

---

## 11. 安全可行性

系统涉及：

- 姓名
- 手机号
- 身份信息
- 面试回答
- 录音
- 视频
- 面试评价

属于高敏感招聘信息。

从技术上可通过：

```text
HTTPS
认证
权限控制
脱敏
日志审计
最小字段
Server-side secrets
```

降低风险。

但当前项目已有一些硬编码凭据和敏感数据管理问题。

因此：

```text
功能演示可行
生产化需要先完成安全整改
```

---

## 12. 是否需要 RAG

本需求：

```text
不需要
```

人员身份属于结构化数据库查询。

RAG 仅适合：

- 企业知识
- 岗位资料
- 面试知识
- 语义检索

禁止使用：

```text
向量搜索确认候选人身份
```

---

## 13. 是否需要 AI 自动判断同名候选人

不建议。

原因：

1. 身份误判风险
2. AI 不具备可靠身份认证能力
3. 当前有人工操作员
4. 摘要字段足够让人工判断

因此：

```text
人工确认
```

是正确方案。

---

## 14. 开发难度评估

### 后端

```text
难度：低~中
```

主要工作：

- Context API
- DTO / VO
- Service 聚合
- 测试
- 配置

### 手机 Server Client

```text
难度：中
```

主要工作：

- API Client
- 状态机
- 错误处理
- 数据转发

### 智能眼镜 Bridge

```text
Mock：低
真实 SDK：未知
```

### 测试

```text
难度：中
```

因为需要覆盖：

```text
同名
断网
错误
candidateId
```

---

## 15. 主要风险

### Risk 1：真实智能眼镜 SDK 未确定

等级：

```text
高
```

解决：

```text
Adapter + Mock
```

---

### Risk 2：现有项目硬编码网络地址

等级：

```text
高
```

解决：

```text
统一配置层
```

---

### Risk 3：PII 泄露

等级：

```text
高
```

解决：

```text
DTO 最小化 + 脱敏 + 日志治理
```

---

### Risk 4：candidateId / 手机号身份逻辑混用

等级：

```text
中~高
```

解决：

```text
新增链路全部 candidateId
```

---

### Risk 5：同名错误选择

等级：

```text
中
```

解决：

```text
禁止自动选择
必须人工确认
```

---

### Risk 6：前端/项目当前构建方式不标准

等级：

```text
中
```

解决：

```text
Codex 先审计真实构建方式
不要为本需求大规模重构 UI
```

---

## 16. 推荐实施策略

采用：

# 业务先行 + 硬件解耦

即：

```text
数据库
 ↓
Java
 ↓
REST
 ↓
Phone Gateway
 ↓
Mock Glasses
```

先全部跑通。

真实智能眼镜到位后：

```text
MockGlassesBridge
        ↓ replace
VendorGlassesBridge
```

业务代码不需要重新开发。

---

## 17. 最终可行性结论

### 用于比赛/毕业设计/演示

```text
完全可行
```

### 用于内部试用

```text
可行
```

前提：

- Server 配置统一
- 网络稳定
- 基础认证
- PII 脱敏

### 用于正式招聘生产环境

```text
可行，但需要额外安全和工程治理
```

至少需要：

- 完整认证授权
- HTTPS
- 密钥轮换
- 数据生命周期
- 日志审计
- 自动化测试
- 部署标准化
- 真实眼镜 SDK 验证

---

# 总体评分

| 项目 | 判断 |
|---|---|
| Java API | 高可行 |
| MySQL 查询 | 高可行 |
| 同名处理 | 高可行 |
| candidateId 确认 | 高可行 |
| 手机连接 Server | 高可行 |
| Server 地址配置 | 高可行 |
| Mock Glasses | 高可行 |
| 真实 Glasses SDK | 待型号验证 |
| AI 面试后续扩展 | 高可行 |
| 生产级安全 | 当前需要整改 |

综合结论：

# 建议立即进入开发
