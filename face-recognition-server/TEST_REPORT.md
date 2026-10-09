# Test Summary

- 日期：2026-10-09，Asia/Shanghai；最终测试执行于 15:31～15:34，报告于测试结束后整理。
- 最终结论：**PASS WITH LIMITATIONS**。
- 完整 pytest：**73 passed / 0 failed / 0 skipped / 0 xfailed，27.06 秒，3 warnings**。
- 独立 Uvicorn 实际联调：**56 项 PASS、0 项 FAIL**；另有 1 组独立身份识别/陌生人/合照/真实标定测试为 **SKIPPED / NEED_USER_DATA**。
- 找到并修复产品 Bug **3 个**，仅修改 `app/main.py` 的错误关联与响应头处理，未新增业务功能或重构项目。
- 用户提供的 1 张照片：真实单脸检测、ArcFace embedding、注册、SQLite 持久化、热更新索引结构、reload 和删除验证均通过。没有把该注册照片用作独立身份识别准确率样本。
- 测试使用 `test_artifacts/api/测试数据库_f81d7340.db`，pytest 使用自己的临时数据库；正式 `data/database/face.db` SHA-256 前后相同。
- 18081 已完成三轮启动/优雅关闭，最后额外用原始 `run.py` 启动、验证 health、Ctrl+C 关闭；没有遗留测试服务器，未停止或修改 8000 上的未知服务。
- 仓库 HEAD：`da4630db4a32d9ea42cacd5fd9955be43ee0c2ac`。服务器目录当前为未提交文件，HEAD 不能单独标识此次代码；具体 Python 文件哈希见 `test_artifacts/reports/code_sha256.json`。

证据入口：[最终 pytest 日志](test_artifacts/logs/pytest_full.txt)、[JUnit XML](test_artifacts/reports/pytest_final.xml)、[独立联调结果](test_artifacts/reports/live_results.json)、[完整联调输出](test_artifacts/logs/live_validation.txt)。

# Environment

| 项目 | 实际值 |
|---|---|
| Python | 项目 `.venv/Scripts/python.exe`，3.11.15，64 位 |
| pip | 24.0 |
| OS | Windows build 26200；platform 输出 Windows-10-10.0.26200-SP0 |
| CPU | AMD Ryzen 7 7840H with Radeon 780M Graphics，16 个逻辑 CPU |
| GPU 硬件 | NVIDIA GeForce RTX 4060 Laptop GPU，驱动 560.94，nvidia-smi 可运行 |
| ONNX providers | AzureExecutionProvider、CPUExecutionProvider；当前安装没有 CUDAExecutionProvider |
| 实际推理设备 | CPUExecutionProvider，未执行 GPU 推理 |
| InsightFace / ONNX Runtime | 0.7.3 / 1.21.1 |
| OpenCV / NumPy | 4.11.0.86 / 1.26.4 |
| FastAPI / Uvicorn | 0.115.12 / 0.34.2 |
| SQLAlchemy / Pydantic | 2.0.40 / 2.11.3 |
| pytest / Pillow | 8.3.5 / 11.2.1 |

完整版本清单见 `test_artifacts/logs/pip_list.txt`，硬件、模型文件、数据集盘点和原图哈希见 `test_artifacts/reports/environment.json`。`pip check` 通过，`pip install --dry-run --no-index -r requirements-model.txt` 确认当前安装满足 README 的依赖命令，未升级任何依赖。

# Automated Tests

先重新运行原有测试，结果为 46 passed、3 skipped；这是未开启集成环境变量的基线，不能代替最终验收。随后增加有明确测试目标的边界/回归测试，先复现 Bug，再局部修复并执行针对性回归，最后开启真实模型及用户图片测试完成完整 pytest。

最终命令：

```powershell
cd D:\ai面试官\face-recognition-server
$env:PYTHONUTF8="1"
$env:FACE_RUN_MODEL_SMOKE="1"
$env:FACE_INTEGRATION_IMAGE="D:\xwechat_files\wxid_iy03ox51v6ad22_a5fb\temp\RWTemp\2026-10\9e20f478899dc29eb19741386f9343c8\4b45c430f64d35da655bde693d33c8e3.jpg"
.\.venv\Scripts\python.exe -m pytest -v -ra --junitxml=test_artifacts/reports/pytest_final.xml 2>&1 |
  Tee-Object -FilePath test_artifacts/logs/pytest_full.txt
```

73 项全部通过。普通 `pytest` 不设置这两个环境变量时会跳过真实模型/用户图片测试，因此不能直接与上述 0 skipped 比较。原始图片来自微信临时目录，若文件被清理，复现前应由用户重新提供或将路径指向自己保存的授权照片。

3 条 warning：1 条为 Starlette TestClient 引用已弃用的 AnyIO BlockingPortal 别名，2 条为 InsightFace 调用 scikit-image 已弃用的 `estimate`。实际调用仍正常；没有为消除警告升级或修改第三方库。

## Coverage

**SKIPPED / NOT INSTALLED**：项目未安装 pytest-cov，requirements 也未要求，按本轮要求没有强制安装。总体覆盖率与 face_matcher、recognition_service、routes_recognition、websocket、person_repository、session_service 的行覆盖率均为 N/A；未生成虚假的覆盖率数字或 htmlcov。相关业务均有测试，但测试通过不等于行覆盖率 100%。

## Import Smoke

实际执行 `import app.main; print('IMPORT_OK')` 成功；FaceEngine、FaceMatcher、SQLAlchemy database、embedding model、recognition/person schemas 和 WebSocket 模块均可导入。compileall 与最终 pip check 也通过。

# Database Tests

- 使用独立 Unicode 路径测试数据库运行 `scripts/init_db.py`，正式数据库未参与 CRUD。
- 验证实际表 `persons`、`face_embeddings`，字段、索引、唯一 person_id、外键及 ON DELETE CASCADE；保存结果见 `test_artifacts/reports/database_schema.json`。
- `PRAGMA integrity_check` 在初始化、两次重新启动及最终清理后均为 ok。
- float32 embedding 经过 serialize → SQLite BLOB → deserialize 后 dtype/shape/数值一致；损坏 BLOB 有明确 AppError；未使用 eval。
- 用户照片注册产生 1 条样本和 1 条 centroid，均为 buffalo_l、512 维、L2 norm 约等于 1。health 的 registered_embeddings 仅统计样本，为 1。
- 删除测试人物后关联向量数为 0；真实模型集成测试同时确认内存 matrix 从 `(1,512)` 变为 `(0,512)`，person_ids/embedding_ids 清空。
- 正式库前后 SHA-256 都为 `aa6d7d514118127465a22147a062998d148d58742b8bda7508475f0aa9678918`；用户原图哈希也未变化。

# Model Tests

实际从项目本地 `data/face_models/models/buffalo_l/` 加载 SCRFD 与 ArcFace ONNX，无首次下载、无网络真人照片。真实模型启动的三轮初始化耗时分别为 **5335.29 / 5327.48 / 5922.37 ms**，均为 CPUExecutionProvider、512 维。

提供的照片成功检测为单脸并经过五点对齐与 ArcFace 特征提取。直接模型测试验证向量形状与归一化，HTTP/WebSocket 在注册前完成真实推理后返回 **NO_REGISTERED_FACES**，符合空库语义，不是 UNKNOWN_FACE。

缺失模型路径场景通过专门测试验证：health 可访问、database_ready=true、model_ready=false，识别返回 MODEL_NOT_READY，应用不崩溃。

真实模型注册、持久化和内存索引测试见 `tests/test_real_registration.py`。本次未声称验证了真人身份识别准确率或 GPU 性能。

# HTTP API Tests

在 `http://127.0.0.1:18081` 实际联调，完整 status、Content-Type、响应 header 和 JSON 见 `test_artifacts/api/responses.json`。

| 场景 | 实际结果 |
|---|---|
| health / docs / openapi.json | HTTP 200；model_ready/database_ready=true；recognition schema 可生成 |
| 创建 test_student_001、列表、按 ID 查询 | 201/200，人物字段一致，request_id 可关联 |
| 重复 person_id | 409 / PERSON_ALREADY_EXISTS |
| 查询或删除不存在的人物 | 404 / PERSON_NOT_FOUND |
| 删除测试人物 | 200，随后计数为 0 |
| JPEG/PNG/纯色/几何/随机噪声/1×1 图片 | NO_FACE，无 500 |
| 空文件、损坏 JPEG、文本冒充 jpg | INVALID_IMAGE / IMAGE_DECODE_FAILED，无 500 |
| 非法 Base64 | 400 / INVALID_BASE64 |
| 缺少或空 image_base64 | 422 / INVALID_REQUEST，符合实际 Pydantic Schema |
| 缺少 request_id | 自动生成 ID，正常处理 |
| GIF 文件名 | 400 / INVALID_IMAGE_FORMAT |
| >8 MiB 文件、24MP 小压缩图片 | IMAGE_TOO_LARGE，无模型崩溃 |
| data URL | 正常解码并返回 NO_FACE |
| 中文、换行 request_id | JSON 原样返回；header 百分号编码，无编码或 header 注入异常 |
| face_box | 正常 ROI 可处理；负值、零宽高、越界、部分越界、超大框明确 INVALID_FACE_BOX |
| EXIF 90°/180°/270° | 形状及空间标记旋转均符合预期 |

当前接口保留原实现的 HTTP 语义：部分进入识别 pipeline 的业务失败用 HTTP 200 + success/error 表示，进入前的校验失败用 400/413/422/429 等。客户端必须同时检查 JSON，不应只依赖 HTTP status。本轮未为统一状态码改动业务协议。

注册 CLI 已用用户图片实际执行并成功；HTTP multipart/Base64 和 WebSocket 示例客户端也都实际运行。日志见 `register_user_photo.txt`、`example_http.txt`、`example_base64.txt`、`example_websocket.txt`。

# WebSocket Tests

实际连接 `ws://127.0.0.1:18081/ws/recognition`：ping→pong、recognize→recognition_result、person_left→clear 均通过。错误 JSON、未知 type、空消息不导致退出；断线后可重连。用户照片注册前的 WebSocket 请求真实完成检测/embedding，得到 NO_REGISTERED_FACES，字段可由 RecognitionResponse 校验。

请求/响应记录在 `test_artifacts/websocket/responses.json`，其中不保存 Base64 图片。成功身份、多帧切换与两个 session 的人物隔离使用已有/新增 MockFaceEngine 测试验证，不冒充独立真人识别结果。

# Recognition Tests

- 向量 `[3,4]` 归一化得到 `[0.6,0.8]`，norm≈1；相同/正交/相反向量的 cosine 分别≈1/0/-1。
- Top-K 按分数降序、每人去重，max/mean/top_n_mean 正常。
- 阈值低于/等于/高于分数、UNKNOWN_FACE、NO_FACE、MULTIPLE_FACES、空索引均有自动测试。
- 真实照片验证了提取、注册、存储与索引结构，没有用注册图重复识别来计算准确率。
- 独立识别尝试数为 **0**。`real_face_recognition_results.csv` 只有表头；Correct/Wrong Identification、False Acceptance/False Rejection、Accuracy/Precision/Recall/FAR/FRR 均为 **N/A**。

# Session Tests

验证连续三帧才确认、确认后单帧出现另一候选人不切换、原候选人恢复时仍保持、另一候选人连续达到三帧后才切换。person_left 清空 session 和相关请求缓存，随后重新从第一帧累计。

新增双 WebSocket 测试使用相同 device、不同 session_A/session_B 交错发送：帧数分别累计，A 的 clear 不清除 B。session 超时通过 TTLCache 可控时间验证，无长时间等待；显式 session 可跨重连，连接临时 session 会关闭清理。

# Rate Limit Tests

HTTP/WS 的 RATE_LIMITED 和恢复均已验证；默认 5 RPS，来自同一 peer 的并发请求按预期限流。10 请求中 5 个接受、5 个限流；20 请求中 5 个接受、15 个限流。全部返回有效协议，无 500、崩溃或 request_id 错位。

| 并发数 | 协议/传输成功率 | 接受 | 预期限流 | 全部响应平均延迟 |
|---|---|---|---|---|
| 10 | 100% | 5 | 5 | 471.82 ms |
| 20 | 100% | 5 | 15 | 432.79 ms |

“协议成功率”包含预期的 429，不是识别成功率。已验证时间窗口后恢复。worker 队列有界及请求取消后占用直到实际工作结束的测试通过。数据见 `test_artifacts/benchmark/concurrency_10.json` 和 `concurrency_20.json`。

# Cache Tests

同 peer/device/session/request_id 和相同内容返回完全相同响应，live stats 确认只增加一次模型推理；并发重试同样只执行一次。不同内容复用 ID 返回 INVALID_REQUEST。缓存过期后重新处理，由可控时间测试验证。重复请求不重复累计稳定帧；注册、删除、reload、clear 后相关缓存失效。

# Performance

CPU，串行请求，脚本间隔 0.21 秒；小样本功能 benchmark，不是生产容量承诺。

| 测试 | iterations | Mean | P50 | P95 | P99 | 实测 throughput |
|---|---|---|---|---|---|---|
| API NO_FACE | 20 | 125.26 ms | 111.00 ms | 225.48 ms | 259.50 ms | 2.98 req/s，含间隔 |
| 用户人脸，空索引 | 10 | 197.20 ms | 176.83 ms | 292.36 ms | 342.68 ms | 2.46 req/s，含间隔 |
| Matcher：500 人×5 个合成向量，512 维 | 100 | 0.708 ms | 0.641 ms | 1.180 ms | 1.389 ms | 1413.23 queries/s，仅 matcher |

用户人脸的服务阶段均值：decode=13.06 ms、detection=108.88 ms、embedding=52.07 ms、matching=0.024 ms、database=0 ms、total=174.18 ms。此时索引为空，未匹配人物，也未查询人物档案；不能把此数值称为完整 1:N 身份识别性能。

NO_FACE 的服务 total 均值 112.32 ms，未执行 embedding/matching。脚本中“不含间隔”的 service_rps 是用平均响应时间倒数计算的串行估计，不是实测并发吞吐。

原始文件：`test_artifacts/benchmark/benchmark_results.txt`、`benchmark_results.json`、`user_face_empty_index.json`、`matcher_benchmark.json`。

# Threshold Calibration

标定脚本、混淆矩阵、CSV 列、阈值推荐机制已用明确标记的合成分数验证；CSV 为 `test_artifacts/calibration/synthetic_threshold_results.csv`，不是实际人脸评估。

真实标定：**NOT ENOUGH DATA FOR RELIABLE CALIBRATION**。只有 1 人的 1 张照片，没有独立同人/异人比较。没有产生真实 threshold_results.csv，也没有更改 FACE_MATCH_THRESHOLD；现有 0.65 仍是示例配置，不能当作已验证阈值。数据要求见 `REAL_FACE_TEST_REQUIRED.md`。

# Bugs Found

| ID | Severity | 复现和根因 |
|---|---|---|
| FRS-TEST-001 | Medium | 中文 request_id 在 JSON 中合法，写入 latin-1 HTTP header 时 UnicodeEncodeError，导致响应失败 |
| FRS-TEST-002 | Medium | multipart/form 缺 file 时，路由未执行，原 request_id 未进入 request state，422 丢失关联 |
| FRS-TEST-003 | Low | 请求体超限的 middleware 提前 return，绕过 X-Request-ID header 赋值 |

每个 Bug 的 Steps/Expected/Actual/Root Cause/Fix/Regression 和修复前失败日志见 `test_artifacts/reports/BUGS.md`。此外修正 QA runner 对 GIF 的错误 HTTP status 预期（200→400），以及日志审计辅助脚本初次父目录定位错误；两者均为测试工具问题，未计为产品 Bug，失败历史分别保留在 initial 日志中。

# Bugs Fixed

3/3 已修复并通过针对性测试和完整 73 项回归：JSON 保持原 ID，header 使用百分号编码；validation handler 从实际表单 body 恢复合法 ID；error_response 同样附加安全 header。扩展验证中文、CR/LF、表单缺字段和 body limit。

只修改相关生产代码、文档说明和隐私忽略规则；新增内容是 QA 测试与复现脚本。没有升级第三方包、修改既有 Java/客户端或改变识别算法。

# Known Limitations

1. 独立真人身份识别、未知参与者拒识、真实合照和真实阈值尚未验证；一个人一张照片不足以统计准确率。
2. GPU 硬件存在，但当前 ONNX Runtime 没有 CUDA provider；仅验证 CPU。Docker/Linux 和真实眼镜设备未实测。
3. 无账号鉴权/TLS/活体检测，单 worker 内存状态；沿用可信课程测试网络的现有限制。
4. Coverage 工具缺失，行覆盖率未知；第三方弃用警告仍存在。
5. 真实身份确认与会话隔离的业务语义已由 mock 测试覆盖，仍需多人的独立照片完成真实数据验收。
6. 用户原图目前位于微信 temp，可能被微信清理；复现命令需有效路径。正式人脸测试数据不得进 Git。

# Skipped Tests

最终 pytest 在提供照片并开启 smoke 后 **0 skipped**；独立联调中明确跳过以下数据驱动验收，不能与 pytest 通过数混淆：

- 至少 A/B/C 三人、独立 test 图片的身份识别。
- 经过同意但未注册人员的 UNKNOWN_FACE。
- 同意参与人员的多人合照 MULTIPLE_FACES。
- 可靠阈值与 Accuracy/Precision/Recall/FAR/FRR。
- 有实际注册库并查询人物信息的完整识别 benchmark。

# Logs and Resource Release

三轮后台服务器日志均包含 Application shutdown complete，退出码 0，没有 Traceback/ERROR/CRITICAL、database locked、ONNX/OpenCV 异常或 HTTP 500。异常输入产生的 WARNING 是预期拒绝，不是隐藏异常。初始复现日志保留的失败与 traceback 已在 Bug ledger 解释；最终联调不包含这些失败。

原始 run.py 最终启动 health HTTP 200，model_ready/database_ready=true，之后 Ctrl+C 正常关闭应用。终端 PowerShell 包装层中断退出码为 1，这是 Ctrl+C 中断状态；日志明确 Application shutdown complete，无 shutdown traceback。见 `test_artifacts/api/final_run_py_health.json`、`logs/final_run_py_shutdown.txt`、`reports/final_port_state.json`。18081 连接已拒绝，测试进程已结束。

正式数据库与原图只读校验均通过，临时人物/向量已逻辑删除。测试产物目录被 Git 忽略。SQLite connection、executor 和 WebSocket 通过应用正常 shutdown 路径关闭，模型所在测试进程退出；未测试 GPU VRAM 释放。

# Final Verdict

**PASS WITH LIMITATIONS**：所有已执行自动化测试和最终独立联调通过，实际模型、用户照片提取/注册、数据库、HTTP/WebSocket、缓存、限流及会话逻辑正常；3 个已复现 Bug 完成修复与完整回归。但缺少独立多人人脸数据，不能验收最终识别准确率、未知人员拒识能力和正式阈值。

完整联调复现：

```powershell
.\.venv\Scripts\python.exe tests/qa_validation.py --face-image $env:FACE_INTEGRATION_IMAGE
.\.venv\Scripts\python.exe test_artifacts/reports/audit_logs.py
```

runner 自动选 18081，若占用则选 18082，不停止其他服务；每次新建独立测试库，启动并优雅关闭三次服务器。生成图片和向量 benchmark 明确标为合成测试，不与真人准确率混用。

之后正常手动启动（不要覆盖已有 `.env`；若要继续隔离，设置独立 DATABASE_URL）：

```powershell
cd D:\ai面试官\face-recognition-server
$env:APP_PORT="18081"
.\.venv\Scripts\python.exe run.py
```
