# Research: 智影口播 · AI数字人视频助手（Windows版）V1.3

> Phase 0 output of `/speckit.plan` for `specs/001-ai-dubber-prd/spec.md`

本文件沉淀 V1.3 的关键技术决策，目标是消除实现阶段的关键不确定性，并确保与 `.specify/memory/constitution.md` 的门禁一致。

## 1) IPC 通信方式（Electron ↔ Python Local Engine）

### Decision
- 采用 **HTTP/1.1 REST + SSE** 作为本地 IPC。
- Python 引擎仅监听 `127.0.0.1:{random_port}`，基础路径为 `http://127.0.0.1:{port}/api`。
- 引擎启动就绪后通过 stdout 输出 JSON：`{"status":"ready","port":18432}`，Electron 主进程读取后开始发起 HTTP 调用。

### Rationale
- REST 适合一次性请求/响应（CRUD、设置、任务发起），SSE 适合长任务单向进度流（低开销、浏览器/Node 生态成熟）。
- 绑定 127.0.0.1 可避免触发 Windows 防火墙弹窗，降低用户困扰。
- stdout 握手能在随机端口下完成端口发现，无需固定端口或系统级服务注册。

### Alternatives considered
- Electron 原生 IPC（ipcMain/ipcRenderer）：进度流与断线重连不如 HTTP/SSE 直观；且难以用 curl/HTTP 工具调试。
- WebSocket：双向能力用不上，连接管理与心跳更复杂。

## 2) 作业模型、稳定 ID 与断点续传

### Decision
- 每个生成任务都必须有稳定的 `job_id`（单条与批量均如此）。
- 任务进度以 SSE 提供：`GET /api/pipeline/progress/{job_id}`。
- 断线重连/恢复 UI 通过快照查询：`GET /api/jobs/{job_id}/state`。
- 批量任务严格串行执行；断点续传粒度为“按条目续跑”：
  - 异常退出时正在执行的条目视为**未完成**。
  - 恢复时从**第一条非 succeeded** 的条目开始继续；未完成条目从头重跑。
  - 批量恢复时输出目录固定为批次创建时的输出目录。
- 批量中单条失败不阻塞后续条目：标记失败并继续；最终汇总成功/失败；允许对失败条目单独重试。

### Rationale
- `job_id` + 快照接口是 UI 断线/重启后的“事实来源”，避免仅靠内存状态。
- “按条目续跑”能覆盖断电/崩溃等主要故障场景，同时避免实现“单条推理中途续传”的复杂度。
- 串行执行符合显存/内存受限场景，符合 PRD（FR-072）。

### Alternatives considered
- 单条任务阶段内续传：需要为每阶段引入可重入/可恢复的中间产物与校验，复杂度高，收益小。
- 批量并行：资源争用明显，易触发 OOM / 显存爆。

## 3) 进度与资源监控（可观测性最小闭环）

### Decision
- SSE 进度事件包含：
  - `stage`: `script | tts | lipsync | mux | subtitles`
  - `progress`: 0-100
  - `message`: 人类可读阶段说明
  - `resource`: `cpu`（%）、`mem`（%）、`vram`（% 或 `N/A`）
- 资源状态更新频率：不低于 **2s/次**（FR-080）。
- 仅 CPU 推理时：显存展示为 `N/A`（未使用 GPU）。
- 达到预警阈值（例如显存 ≥ 90%）时给出提示，且提示不遮挡核心操作区（FR-081）。

### Rationale
- 进度 + 资源是用户“可控感”的核心来源，特别是批量场景。
- CPU 模式不应误导用户显示显存数值，明确 N/A 更可理解。

### Alternatives considered
- 更细粒度阶段（拆分到模型加载/音频重采样等）：对用户价值有限，先保留为内部日志。

## 4) 离线优先与授权/联网动作解耦

### Decision
- 核心生成闭环（单条/批量、字幕、作品访问）必须在断网环境可用（FR-001）。
- 授权激活、解绑等需要联网的动作仅在用户主动触发时执行，且不得阻塞离线生成流程。
- 授权接口通过 `/api/license/*` 提供；消费试用次数为内部调用：`POST /api/license/consume-trial`。

### Rationale
- 断网可用是产品核心承诺；授权联网验证必须是“增量能力”，不能成为运行前置条件。

### Alternatives considered
- 每次生成都联网校验：违反离线门禁与用户预期。

## 5) 批量导入格式与编码策略

### Decision
- TXT 导入：自动识别 `UTF-8` / `UTF-8 BOM` / `GBK`。
- Excel 导入：仅支持 `.xlsx`。
- 单批上限：最多保留前 30 条用于本次批量（FR-071）。

### Rationale
- GBK 仍是 Windows 环境常见编码；自动识别能降低导入失败率。
- 限制 `.xlsx` 可简化解析链路，减少格式兼容性成本。

### Alternatives considered
- 支持 `.xls` / `.csv`：兼容面更大但实现与测试成本更高，暂不纳入 V1.3。

## 6) 字幕交付与失败策略

### Decision
- 默认同时输出：外置字幕文件（如 `.srt`）+ 视频内嵌硬字幕（FR-060）。
- 字幕生成失败时自动重试一次；重试仍失败：仍输出视频，并明确提示字幕失败但不影响视频结果（FR-061）。

### Rationale
- 外置字幕便于二次编辑与分发；硬字幕满足多数用户“即用”诉求。

### Alternatives considered
- 仅硬字幕或仅外置字幕：不满足多场景需求。

## 7) 取消策略与临时文件清理

### Decision
- 单条任务：取消需确认；取消后尽力停止流水线并清理临时产物；用户可立即再次发起新的生成（FR-051）。
- 批量任务：取消整个批量需确认；取消后停止后续条目并清理临时文件；已完成条目产物保留；正在执行条目尽力中止并视为失败/未完成（FR-076）。

### Rationale
- 明确的清理策略避免磁盘占用不可控，并减少“取消后无法再生成”的坏体验。

### Alternatives considered
- 取消后保留所有中间文件：便于调试但对用户是负担，默认不采用。

## References
- IPC contract: `specs/001-ai-dubber-prd/contracts/ipc-api.md`
- License contract: `specs/001-ai-dubber-prd/contracts/license.md`
