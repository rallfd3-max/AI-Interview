# START_CODEX_HERE.md

Codex：请先阅读以下文件，然后直接自动开始开发，不要等待我逐步发送“继续”。

阅读顺序：

1. `GPT项目交接上下文.md`
2. `PROJECT_PLAN_SMART_GLASSES.md`
3. `FEASIBILITY_SMART_GLASSES.md`
4. `CODEX_MASTER_PROMPT.md`

执行要求：

- 以真实仓库代码为准
- 先审计再修改
- 不重复开发已有姓名匹配
- 姓名只用于搜索
- 最终身份使用 `candidateId`
- 重名候选人全部显示，由人工选择
- 手机作为智能眼镜与 Java Server 之间的 Gateway
- 新增智能眼镜业务链路不要直连 Python
- Server 地址配置化，正式地址当前允许为空
- 保留已有智能眼镜前端，只补接口
- 真实眼镜 SDK 未确定时使用 Adapter + Mock
- 自动执行：审计 → 开发 → 构建 → 测试 → 修复 → 文档 → 最终报告
- 不要每阶段停下来问我是否继续
- 不要虚报测试、构建或硬件验证结果

现在直接读取 `CODEX_MASTER_PROMPT.md` 并开始。
