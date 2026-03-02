# Research: 智影口播 · AI数字人视频助手（Windows版）V1.3

> Phase 0 output of `/speckit.plan` for `specs/001-ai-dubber-prd/spec.md`

本文件沉淀 V1.3 的关键技术决策，目标是消除实现阶段的关键不确定性，并确保与 `.specify/memory/constitution.md` 的门禁一致。

## 0) 已有前端原型项目分析与迁移策略

### Decision
- 将 `D:\Git.Project\智影口播-·-ai数字人视频助手` 中的前端代码迁入本仓库 `renderer/` 目录。
- 保留已有 UI 组件的视觉设计与交互骨架，替换架构层：tab 条件渲染 → HashRouter、state 提升 → Zustand、setTimeout mock → HTTP REST + SSE 真实 API。
- 移除不需要的依赖（`@google/genai`、`express`、`better-sqlite3`）；新增架构依赖（`zustand`、`react-router-dom`）。

### 已有组件可复用性评估

| 组件 | 文件大小 | 可复用度 | 迁移工作量 |
|------|---------|----------|-----------|
| TopBar.tsx | ~2KB | 高 | 低 — 补充 Electron 窗口控制 IPC |
| Sidebar.tsx | ~3KB | 中 | 中 — tab onClick → NavLink + HashRouter |
| RightSidebar.tsx | ~6KB | 高 | 中 — mock VRAM → SSE resource 数据 |
| SingleVideo.tsx | ~13KB | 高 | 中 — 字数上限 300→3000、接 pipeline API |
| BatchVideo.tsx | ~16KB | 高 | 中 — 接 batch API + 断点续传逻辑 |
| VoiceManagement.tsx | ~11KB | 高 | 中 — 接 voice-templates API + 名称唯一校验 |
| TaskRecords.tsx | ~7KB | 高 | 低 — 接 jobs API 替换 mock 数据 |
| Settings.tsx | ~7KB | 高 | 低 — 接 settings/system API + 推理模式选择 |

### 缺失页面（需新建）

- **Home.tsx** — 首页快速入口 + 最近 3 条记录 + 教程引导
- **WorksLibrary.tsx** — 作品库卡片展示 + 搜索/筛选/排序 + 播放/删除
- **AvatarManager.tsx** — 数字人管理（官方 + 自定义上传）
- **Help.tsx** — 帮助与反馈（教程 + FAQ）

### 架构差异与迁移方案

| 差异 | 迁移方案 |
|------|---------|
| 无路由（tab 条件渲染） | 引入 React Router v7 HashRouter；Sidebar 改用 NavLink |
| State 全在 App.tsx | 拆分为 7 个 Zustand stores（jobs, project, voice-templates, works, resource-monitor, license, settings） |
| 所有操作 mock | 新建 services/ 层通过 window.electronAPI.engine.request() 调用后端 |
| 无 Electron 集成 | 通过 preload/index.ts 暴露 window.electronAPI |
| @google/genai 依赖 | 移除（离线产品，宪章 I 要求） |
| 文案上限 300 字 | 改为 3000 字 (FR-020a) |
| 无声音模板名称校验 | 添加唯一性校验 + VOICE_NAME_DUPLICATE 错误处理 |

### 样式系统
- 色彩系统、卡片阴影、字体配置可直接复用
- Tailwind CSS v4 npm 包与目标架构一致
- Lucide React 图标库与目标架构一致

### Rationale
- 复用已有高保真 UI 原型可大幅减少前端工作量（约 ~60KB 组件代码）。
- 仅替换架构层（路由、状态、API）而非重写 UI，符合宪章 V（最小复杂度）。
- 移除云端依赖符合宪章 I（离线优先）。

### Alternatives considered
- 从零重写前端：耗时且无必要，已有原型质量高。
- 保留 tab 条件渲染不引入 Router：不利于深链接、Electron 历史栈管理，与 CLAUDE.md 架构不一致。

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

## 7) 声音克隆与声音模板（Voice Cloning）

### Decision
- 用户上传本地音频（MP3/WAV，≥30s，≤100MB），由 CosyVoice3-0.5B 提取声音特征（speaker embedding），保存为可复用的"声音模板"。
- 声音模板与预置音色模型（`voice_models`）为独立概念：前者是用户自建克隆，后者是官方预训练模型。
- 提取为异步操作：上传后返回 `processing` 状态，通过 SSE 推送进度，完成后状态变为 `ready`。
- 声音模板存储在 SQLite `voice_templates` 表 + 本地文件系统（特征文件）。
- 删除为 hard delete，不可恢复（FR-034）。

### Rationale
- CosyVoice3-0.5B 原生支持 zero-shot/few-shot 声音克隆，提取 speaker embedding 后可在 TTS 推理时传入，实现声音复用。
- 异步提取避免阻塞 UI；SSE 进度与生成任务一致，降低前端复杂度。
- 独立于 `voice_models` 可避免概念混淆：预置模型需下载，用户模板需上传音频提取。

### Alternatives considered
- 同步提取（上传后阻塞等待）：耗时可能达数十秒，UX 差。
- 复用 `voice_models` 表：字段含义不同（download_url vs source_audio_path），强行复用反增复杂度。

## 8) 取消策略与临时文件清理

### Decision
- 单条任务：取消需确认；取消后尽力停止流水线并清理临时产物；用户可立即再次发起新的生成（FR-051）。
- 批量任务：取消整个批量需确认；取消后停止后续条目并清理临时文件；已完成条目产物保留；正在执行条目尽力中止并视为失败/未完成（FR-076）。

### Rationale
- 明确的清理策略避免磁盘占用不可控，并减少”取消后无法再生成”的坏体验。

### Alternatives considered
- 取消后保留所有中间文件：便于调试但对用户是负担，默认不采用。

## 9) 文案自动拆分策略

### Decision
- 文案输入后按 120 字/段自动拆分（FR-021），拆分算法优先在自然断句处切分（句号、问号、感叹号、逗号等），避免破坏语义。
- 拆分结果保存为 `script_segments` JSON 数组，各段独立送入 TTS 后由 FFmpeg 顺序拼接。
- 对用户透明：用户看到的是连续输出视频，不感知拆分。

### Rationale
- 120 字是 CosyVoice3-0.5B 单次推理的安全上限，超出可能导致质量下降或 OOM。
- 自然断句拆分比硬截断更能保持语音连贯性。

### Alternatives considered
- 要求用户手动分段：增加操作负担，违反 FR-021。
- 不拆分：长文案推理不稳定，质量无法保证。

## 10) 并发生成策略

### Decision
- 系统 MUST 阻止并发生成：当任一生成任务（单条或批量）正在执行时，后端拒绝新任务（返回 `JOB_ALREADY_RUNNING`），前端禁用"开始生成"按钮并提示用户（FR-085）。

### Rationale
- 桌面应用 GPU/CPU 资源有限，串行执行已是核心约束；阻止并发是最简单且最安全的方案。
- 排队机制增加状态复杂度且用户难以理解"排队中"的概念。

### Alternatives considered
- 任务队列：增加状态管理复杂度，对单用户桌面场景无必要。
- 替换当前：用户易误操作导致丢失进度。

## 11) 核心模型内置策略

### Decision
- 安装包 MUST 内置 CosyVoice3-0.5B TTS 模型与 Wav2Lip 口型同步模型（FR-001a），确保安装即可离线生成。
- 额外音色模型（预置 voice_models）仍通过联网下载获取，但不影响核心生成功能。

### Rationale
- 离线生成是产品核心承诺；首次使用时若模型缺失，用户将在断网环境下陷入死锁。
- 内置核心模型虽增加安装包体积，但保证开箱即用。

### Alternatives considered
- 首次启动联网下载：违反 FR-001 离线门禁。
- 仅内置低配模型（VITS）：生成质量不达标，首次体验差。

## 12) 资源耗尽降级策略

### Decision
- 资源超限时系统自动暂停当前生成任务（status → `paused`），弹出非阻断提示告知原因，并建议用户关闭其他程序或缩小批量规模后手动恢复（FR-082）。
- 暂停期间已完成产物保留。
- 预警阈值：显存 ≥ 90%、内存 ≥ 90%、磁盘剩余 < 1GB。

### Rationale
- 自动暂停 + 用户决策恢复是最安全的策略：避免数据损坏、不替用户做破坏性决定。
- 自动降级（如切换分辨率）可能改变用户预期输出，不可控。

### Alternatives considered
- 自动降级（GPU→CPU / 1080P→720P）：输出与用户选择不一致，易造成困惑。
- 直接中止：丢失当前进度，用户体验差。

## 13) 文案总字数上限

### Decision
- 单条任务文案总字数上限为 **3000 字**（FR-020a）。
- 超限时前端阻止生成并提示用户缩减文案或拆分为多条任务。
- 按 120 字/段拆分约 25 段，对应约 10-15 分钟视频。

### Rationale
- 无上限可能导致极长生成时间且资源消耗不可控。
- 3000 字是口播类内容的合理上限。

### Alternatives considered
- 无限制：生成时间不可预期，资源消耗不可控。
- 更低上限（1000 字）：限制过严，不满足较长脚本需求。

## 14) 声音模板名称唯一性

### Decision
- 声音模板名称 MUST 唯一（FR-032a）。
- 保存时后端校验重复并返回 `VOICE_NAME_DUPLICATE`；前端提示用户修改名称。
- 唯一性基于 trim 后的名称值。

### Rationale
- 强制唯一避免用户在列表选择时因同名模板混淆。
- 简化数据层设计（UNIQUE 约束）。

### Alternatives considered
- 允许重复名称：需额外区分信息（创建时间等），增加用户认知负担。
- 自动追加序号：隐式行为，用户不可预期。

## References
- IPC contract: `specs/001-ai-dubber-prd/contracts/ipc-api.md`
- License contract: `specs/001-ai-dubber-prd/contracts/license.md`
- Data model: `specs/001-ai-dubber-prd/data-model.md`
