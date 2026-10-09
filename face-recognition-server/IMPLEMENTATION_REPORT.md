# 实施与验收记录

日期：2026-10-09（Asia/Shanghai）

项目位置：`face-recognition-server/`。只新增此服务器项目，未修改现有 Java、前端或眼镜客户端。完整目录、架构 Mermaid、数据库结构、API、注册/识别、启动、标定、性能测试和客户端适配说明见 [README.md](README.md)。

## 已实际执行

| 项目 | 结果 |
|---|---|
| Python | 已使用现有 .venv，Python 3.11.15；已补装 pip |
| 服务与测试依赖 | 已安装，pip check 无损坏依赖 |
| InsightFace 0.7.3 | 已实际编译安装，核对本地 prepare/get 和 ArcFace 对齐调用 |
| ONNX Runtime 1.21.1 | 已安装，CPUExecutionProvider 可用 |
| buffalo_l 模型 | 已从官方发布地址下载，在 CPU 成功初始化，512 维 |
| SQLite 初始化 | scripts/init_db.py 已执行成功；未导入真人数据 |
| FastAPI import | 成功，包含 HTTP 与 WebSocket 共 15 条路由（含文档路由） |
| 独立 matcher | 实际执行归一化向量匹配，分数断言通过 |
| pytest 最终 | **48 passed, 1 skipped, 1 warning in 20.97s** |
| 真实检测器 | 本地真实模型初始化、重复 initialize 幂等、空白图 NO_FACE 测试通过 |
| 独立 Uvicorn | 实际启动临时端口，HTTP health/NO_FACE、WebSocket ping/NO_FACE/person_left 通过，之后关闭测试进程 |
| benchmark CLI | 对真实检测器执行 3 次空白图请求，阶段计时与报告断言通过 |
| calibration CLI | 用测试分数对验证指标、CSV 和推荐值输出；并非真人阈值标定 |
| 隐私 Git 忽略 | 已验证数据库、模型和虚拟环境被忽略；照片/调试图/数据集同样加入忽略 |

最终测试命令：

```powershell
$env:FACE_RUN_MODEL_SMOKE="1"
.\.venv\Scripts\python.exe -m pytest -q -ra
```

唯一跳过项：`test_real_model`，缺少 `FACE_INTEGRATION_IMAGE` 指向知情参与者的单人照片。唯一 warning 来自 Starlette TestClient 使用已弃用的 AnyIO BlockingPortal 别名，不影响上述测试通过。

普通 `pytest` 不设置环境变量时会另外跳过两项真实模型 smoke 测试；业务测试仍可只安装 requirements.txt 执行。

## 业务测试覆盖

归一化、零向量/非有限值、BLOB 安全转换、cosine、人物去重 Top-K、max/mean/top_n_mean、阈值等号、unknown、空库、Person repository/CRUD、三照片注册与平均向量、批次失败回滚、五照片上限、删除级联与缓存失效、非法 Base64/图片/格式/尺寸/ROI、EXIF、无脸、多脸、模型不可用、HTTP multipart/data URL、WebSocket、连续帧确认/切换防抖/超时/清理、重复请求/不同内容冲突/并发去重、HTTP/WS 限流、worker 队列上限及取消、标定指标和命令行输出。

API 中的“成功识别、陌生人、多脸、三照片注册”等路径使用测试注入的 MockFaceEngine 验证业务逻辑；正常服务器始终调用真实模型。真实模型部分只确认启动与无脸检测，尚未验证真人 embedding 与身份识别准确率。

## 尚未执行与限制

1. 未提供知情参与者照片，因此未实测真人场景 A/B/C/E、真实多帧身份稳定性、真实数据集阈值和单人完整 pipeline 性能。可先注册自己的测试照片，再使用 examples/ 和 calibration 工具执行。
2. GPU 和 Docker 未在目标环境运行；已提供 CPU 回退与容器配置。
3. 本课程原型无鉴权、TLS、活体检测；只用于可信测试网络。仅支持单 Uvicorn worker，内存状态不跨进程。
4. 现有 Java `/ws` 协议与 Python `/ws/recognition` 不同；尚未实现 Java 网关适配或绑定 Candidate ID。Python 数据为通用课程人物档案。
5. 本机 8000 端口已被现有进程占用，未停止该进程。启动本项目可改用 18081。测试 Uvicorn 使用自动选择的临时端口，测试结束已关闭，没有遗留后台服务器。

## 客户端最少字段

HTTP JSON schema 的唯一必填图片字段是 `image_base64`；实际联调应同时传 `request_id`，便于原样关联响应。WebSocket 识别还需 `type=recognize`。建议连续帧统一使用以下完整元数据：

```json
{"type":"recognize","request_id":"每帧唯一ID","device_id":"glass_001","session_id":"本次会话ID","image_base64":"JPEG或PNG Base64"}
```

单帧设置 `stable_frames=1`；连续帧保持 device/session 不变，每帧换 request_id；重试同一帧保留原 request_id。HTTP multipart 最少 `file`，建议也传相同元数据。

识别响应：`type/request_id/timestamp/success/error/face_detected/matched/person/match/stability/top_k/processing`。未匹配 person=null；待确认时不切换卡片，按 stability.confirmed_person_id 保留已确认卡片。person_left/clear 使用相同 device/session，响应 type=clear。

## 最新完整 QA 验证（2026-10-09，保留上文首次验收记录）

后续完整验证及用户本轮提供的 1 张照片测试已完成，详细证据与复现步骤见 [TEST_REPORT.md](TEST_REPORT.md)。

- 最终 pytest：**73 passed，0 failed，0 skipped，3 warnings，27.06s**。开启 FACE_RUN_MODEL_SMOKE 和 FACE_INTEGRATION_IMAGE，真实特征提取/注册集成测试实际执行。
- 独立 Uvicorn 联调：**56 PASS、0 FAIL**；1 组独立身份识别/未知人物/合照/标定验收为 SKIPPED / NEED_USER_DATA。
- 用户图片真实检测、512 维 ArcFace、单照片注册、SQLite BLOB/centroid、索引结构更新/reload 与删除均通过；只在独立测试数据库操作，没有将注册图当作独立身份识别准确率样本。
- 发现并修复 FRS-TEST-001/002/003：Unicode 请求 ID 导致 HTTP header 编码失败、表单校验时 ID 丢失、body-limit 响应缺 ID header。相关边界和全量回归均通过。
- 18081 三轮实际启动/优雅停止，10/20 HTTP 并发、双 WebSocket session 隔离、cache TTL、限流恢复、EXIF 和 ROI 边界测试通过；最后 run.py 正常启动及 health 验证后关闭，无遗留测试服务器。
- CPU 用户图片空库推理 benchmark：10 次，HTTP mean=197.20ms、P95=292.36ms；包含真实 detection/embedding，但不是已注册库的完整身份识别性能。
- 原正式数据库和用户图片 SHA-256 不变，测试人物/向量清理；pytest-cov 未安装，因此 coverage 未执行。
- 当前只有 1 人 1 照，没有独立测试照片和多参与者数据，可靠准确率与 threshold 仍无法验证；最终结论 **PASS WITH LIMITATIONS**。上文“没有用户图片、48 passed/1 skipped”是首次实现阶段记录，已被本节最新状态补充。
