# SMART_GLASSES_ACCEPTANCE_CHECKLIST.md

## 核心业务

- [ ] 输入姓名可以查询候选人
- [ ] 0 条结果正确处理
- [ ] 1 条结果正确处理
- [ ] 多个同名结果全部返回
- [ ] 同名时不会默认选择第一条
- [ ] 人工选择后使用 candidateId
- [ ] candidateId 查询完整候选人 context
- [ ] context 正确回到手机
- [ ] 手机正确发送给 Glasses Bridge

## 架构

- [ ] Glasses 不连接数据库
- [ ] Phone 不连接数据库
- [ ] 新 Glasses 链路只连接 Java Server
- [ ] 没有新增 Phone → Python 直连
- [ ] 姓名匹配复用现有实现
- [ ] 人员身份没有使用 RAG

## 配置

- [ ] Server Base URL 集中配置
- [ ] 正式 Server 地址可以为空
- [ ] 空地址返回 SERVER_NOT_CONFIGURED
- [ ] 新代码没有写死 192.168 / 100.x / 10.x / localhost
- [ ] `.env.example` 或等价配置样例存在

## Glasses

- [ ] 已有 UI 保留
- [ ] IGlassesBridge 或等价接口存在
- [ ] MockGlassesBridge 可运行
- [ ] VendorGlassesBridge 扩展点存在
- [ ] SEARCH_CANDIDATE 事件存在
- [ ] SELECT_CANDIDATE 事件存在
- [ ] CANDIDATE_MATCHES 消息存在
- [ ] CANDIDATE_CONTEXT 消息存在
- [ ] ERROR / LOADING 状态存在

## 安全

- [ ] 手机号默认脱敏
- [ ] 身份证默认不返回 Glasses
- [ ] 日志不打印完整 PII
- [ ] 日志不打印 Token/Secret/API Key
- [ ] DTO/VO 而不是直接 Entity 暴露
- [ ] candidateId 参数有校验

## 测试

- [ ] 姓名为空
- [ ] 姓名 trim
- [ ] 无候选人
- [ ] 唯一候选人
- [ ] 两个同名候选人
- [ ] 选择第二个同名候选人
- [ ] 不会误加载第一个
- [ ] candidateId 不存在
- [ ] Server 未配置
- [ ] 网络超时
- [ ] HTTP 4xx
- [ ] HTTP 5xx
- [ ] Glasses 中途断开
- [ ] 重复搜索
- [ ] 重复选择

## 文档

- [ ] CODEX_REPO_AUDIT
- [ ] SMART_GLASSES_INTEGRATION
- [ ] SMART_GLASSES_API
- [ ] SMART_GLASSES_TEST_REPORT
- [ ] CODEX_FINAL_REPORT

## 最终声明

只有所有可在当前环境验证的项目均完成后，才能声明本轮开发完成。

真实智能眼镜 SDK 未提供时，最终状态应写：

```text
Business flow: implemented / verified
Mock glasses: implemented / verified
Real hardware integration: pending vendor SDK
```
