# Tasks: 智影口播 · AI数字人视频助手（Windows版）V1.3

**Input**: `specs/001-ai-dubber-prd/` (plan.md, spec.md, research.md, data-model.md, contracts/)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

> Note: spec.md 未明确要求 TDD/测试先行，因此本 tasks 列表不强制生成"先写测试"的任务；如需补充测试任务，可在实现前按故事增补。

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 统一开发/运行入口与基础约束落地，保证 Electron↔Python 本地双进程可跑通。

- [ ] T001 统一开发启动脚本与文档入口（对齐 quickstart）在 `electron-app/package.json`
- [ ] T002 梳理并固定 Python engine 启动参数与工作目录约定在 `electron-app/src/main/python-manager.ts`
- [ ] T003 [P] 确认共享类型与 contract 对齐（如 job_id/stage/error_code）在 `shared/ipc-types.ts`
- [ ] T004 [P] 定义渲染进程到主进程的 API 入口（request + SSE subscribe）在 `electron-app/src/preload/index.ts`
- [ ] T005 [P] 定义渲染进程 HTTP client 基础封装（baseURL=127.0.0.1:{port}）在 `renderer/src/services/engine.ts`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 核心"离线闭环、IPC 边界、可恢复作业、资源监控"能力的基础设施；完成后各用户故事可并行推进。

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 固化引擎 stdout 握手协议解析与 10s 就绪超时/最多 3 次重启策略在 `electron-app/src/main/python-manager.ts`
- [ ] T007 限制 IPC 仅绑定 127.0.0.1 随机端口并输出就绪 JSON（status/port）在 `python-engine/src/api/server.py`
- [ ] T008 [P] 统一错误返回结构（error_code + message）与 FastAPI 异常处理在 `python-engine/src/api/server.py`
- [ ] T009 建立"稳定 job_id + 状态快照"持久化与查询骨架在 `python-engine/src/storage/database.py`
- [ ] T010 [P] 定义 jobs/batch_jobs/batch_items/voice_templates 最小表结构与迁移机制在 `python-engine/src/storage/migrations/`
- [ ] T011 实现 `GET /api/jobs/{job_id}/state`（用于断线恢复/重连 UI）在 `python-engine/src/api/routes/jobs.py`
- [ ] T012 实现 SSE 事件生成与统一事件 schema（job_id/stage/progress/message/resource）在 `python-engine/src/utils/progress.py`
- [ ] T013 实现资源采样（CPU/内存/显存；CPU 模式 vram=N/A）并确保 ≥2s/次推送在 `python-engine/src/api/routes/system.py`
- [ ] T014 [P] 在引擎侧生成链路入口（pipeline/single、pipeline/batch）添加网络请求断言：生成过程中禁止发出任何外部网络请求；联网能力（activate/unbind/model-download/check-update）在路由层标注 `requires_network=True` 并在响应中附带标识字段在 `python-engine/src/api/server.py`
- [ ] T015 实现引擎关键阶段（TTS/lipsync/mux）前后资源阈值检测（显存≥90%预警SSE/≥95%建议降级/可用磁盘<1GB阻断），返回结构化预警事件或中断错误码（RESOURCE_CRITICAL + 附带建议），对齐 plan.md Memory Guard 策略在 `python-engine/src/utils/resource_guard.py`

**Checkpoint**: 基础设施完成后，US1/US2/US3 可开始实现。

---

## Phase 3: User Story 1 - 单条生成口播视频（离线、1080P/720P、含字幕）(Priority: P1) 🎯 MVP

**Goal**: 断网可用的单条生成闭环：输入图片+文案+声音模板 → 生成视频(1080p/720p) + 外置字幕 + 硬字幕；可取消；可观测进度与资源。

**Independent Test**: 按 `specs/001-ai-dubber-prd/quickstart.md` 跑起引擎与桌面端，在断网环境完成一次单条生成并产出 `mp4 + srt`，可打开输出目录。

### Implementation for User Story 1

- [ ] T016 [US1] 定义单条生成配置的 Zustand store（voice_params/resolution/avatar 等），确保每次新建任务默认加载推荐参数集、修改仅影响当前 store 实例在 `renderer/src/stores/generation-config.ts`
- [ ] T017 [US1] 渲染进程实现单条制作 5 步向导的状态与表单数据结构在 `renderer/src/pages/SingleCreation.tsx`
- [ ] T018 [P] [US1] 实现分辨率选择 UI（默认 1080P，可切 720P + 差异说明）在 `renderer/src/pages/SingleCreation.tsx`
- [ ] T019 [P] [US1] 实现图片上传/预览/删除 + 前端预校验（仅 jpg/png、文件大小）在 `renderer/src/pages/SingleCreation.tsx`
- [ ] T020 [US1] 引擎侧实现图片校验（格式仅 jpg/png、最小分辨率阈值、自动 resize 512x512）并返回结构化错误码（INVALID_IMAGE_FORMAT / IMAGE_TOO_SMALL）在 `python-engine/src/api/routes/pipeline.py`
- [ ] T021 [US1] 实现文案输入字数提示与 120 字/段自动拆分（请求前处理，按标点/语义断句保持连贯）在 `renderer/src/services/pipeline.ts`
- [ ] T022 [P] [US1] 实现声音模板选择 + 参数调节（speed/volume/style，默认 neutral_natural 推荐）在 `renderer/src/pages/SingleCreation.tsx`
- [ ] T023 [P] [US1] 实现"生成前配置摘要"组件（展示已选分辨率/声音模板/情感风格/语速音量关键值），避免用户误以为仍是默认在 `renderer/src/components/ConfigSummary.tsx`
- [ ] T024 [US1] 实现 `POST /api/pipeline/single` 调用封装与请求校验（空文案/缺图片/缺模板等）在 `renderer/src/services/pipeline.ts`
- [ ] T025 [US1] 实现单条 pipeline 路由（202 返回 job_id；落库 queued→running）在 `python-engine/src/api/routes/pipeline.py`
- [ ] T026 [US1] 实现单条取消 `POST /api/pipeline/cancel/{job_id}`（清理临时文件、状态=canceled）在 `python-engine/src/api/routes/pipeline.py`
- [ ] T027 [US1] 渲染进程实现单条取消确认弹窗（二次确认 + 取消后提示"已取消" + 可立即重新发起）在 `renderer/src/pages/SingleCreation.tsx`
- [ ] T028 [US1] 实现单条生成核心流水线骨架（tts→lipsync→mux→subtitles）并持续更新进度在 `python-engine/src/core/video_synthesizer.py`
- [ ] T029 [US1] 实现字幕生成（外置 srt + ffmpeg 硬字幕；时间轴基于 TTS 分段时长生成），失败自动重试一次，仍失败不阻断视频产出在 `python-engine/src/core/video_synthesizer.py`
- [ ] T030 [US1] 渲染进程订阅 SSE `GET /api/pipeline/progress/{job_id}` 并展示进度/阶段/资源在 `renderer/src/components/ProgressBar.tsx`
- [ ] T031 [P] [US1] 生成完成后提供打开输出目录与复制路径入口在 `renderer/src/pages/SingleCreation.tsx`
- [ ] T032 [P] [US1] 生成成功后在结果页展示字幕文件路径并提供"查看字幕/复制字幕文本"入口（复制成功有明确反馈）；字幕失败时展示"字幕未生成"状态在 `renderer/src/pages/SingleCreation.tsx`

**Checkpoint**: US1 完成后，在断网环境能稳定产出视频与字幕，并可取消、查看输出目录、查看/复制字幕。

---

## Phase 4: User Story 2 - 本地声音克隆与声音模板管理（可复用、可删除）(Priority: P2)

**Goal**: 本地上传音频→提取→命名保存为声音模板；列表可选择/删除（确认后不可恢复）。

**Independent Test**: 上传合规 MP3/WAV（≥30s、≤100MB）生成一个模板；再删除该模板并验证不可恢复。

### Implementation for User Story 2

- [ ] T033 [US2] 渲染进程实现声音模板管理页面骨架（上传、列表、删除）在 `renderer/src/pages/VoiceManager.tsx`
- [ ] T034 [US2] 渲染进程实现音频校验（mp3/wav、≥30s、≤100MB）与错误提示在 `renderer/src/pages/VoiceManager.tsx`
- [ ] T035 [US2] 实现声音模板 REST API（create/list/delete）在 `python-engine/src/api/routes/voices.py`
- [ ] T036 [US2] 实现声音模板提取任务（processing→ready/failed）与特征文件落盘在 `python-engine/src/core/tts_engine.py`
- [ ] T037 [US2] 实现 voice_templates 表的数据访问（unique name、状态、基础信息）在 `python-engine/src/storage/voices_repo.py`
- [ ] T038 [US2] 实现删除模板二次确认与硬删除（含特征文件删除）在 `renderer/src/pages/VoiceManager.tsx`
- [ ] T039 [P] [US2] 在单条/批量生成页面复用模板选择器组件在 `renderer/src/components/VoiceTemplatePicker.tsx`

**Checkpoint**: US2 完成后，可独立完成"上传音频→提取→保存→选择→删除"闭环。

---

## Phase 5: User Story 3 - 批量生成（≤30条、串行执行、断点续传、可监控）(Priority: P3)

**Goal**: 导入 TXT/Excel(.xlsx) 多条文案（≤30）→ 严格串行批量生成 → 单条失败不阻塞 → 异常退出后可按条目续跑（输出目录固定）。

**Independent Test**: 导入 3 条文案启动批量；中途强制退出应用；重启后选择继续，验证已完成条目不重复，正在执行条目从头重跑。

### Implementation for User Story 3

- [ ] T040 [US3] 渲染进程实现批量制作页面：导入、预览编辑、统一配置、开始/取消、状态列表在 `renderer/src/pages/BatchCreation.tsx`
- [ ] T041 [US3] 实现 TXT 编码识别（UTF-8/UTF-8 BOM/GBK）导入解析在 `renderer/src/services/importers/txt.ts`
- [ ] T042 [US3] 实现 Excel(.xlsx) 导入解析（取第一列为文案；仅支持 xlsx）在 `renderer/src/services/importers/xlsx.ts`
- [ ] T043 [US3] 导入后限制 ≤30 条并给出明确提示（保留前 30）在 `renderer/src/pages/BatchCreation.tsx`
- [ ] T044 [US3] 实现 `POST /api/pipeline/batch` 调用封装与批次配置摘要展示在 `renderer/src/services/pipeline.ts`
- [ ] T045 [US3] 引擎侧创建 batch job（落库 batch_jobs + batch_items；固定 output_dir）在 `python-engine/src/api/routes/pipeline.py`
- [ ] T046 [US3] 批量严格串行执行器：按 cursor_index 依次执行，条目失败记录原因并继续在 `python-engine/src/core/batch_runner.py`
- [ ] T047 [US3] 实现异常退出后的恢复：启动时扫描未完成 batch_jobs 并提供 state 查询在 `python-engine/src/storage/batch_repo.py`
- [ ] T048 [US3] 实现 `GET /api/jobs?status={status_list}` 接口供 UI 启动时检测未完成批量在 `python-engine/src/api/routes/jobs.py`
- [ ] T049 [US3] 实现"继续未完成批量/放弃清空"控制接口（resume/cancel）在 `python-engine/src/api/routes/pipeline.py`
- [ ] T050 [US3] 实现失败条目单独重试接口（仅 failed items）在 `python-engine/src/api/routes/pipeline.py`
- [ ] T051 [US3] 渲染进程实现批量取消确认弹窗（二次确认 + 已完成产物保留 + 执行中条目尽力中止标记失败 + 清理临时文件提示）在 `renderer/src/pages/BatchCreation.tsx`
- [ ] T052 [US3] 渲染进程实现批量 SSE 订阅与条目级状态展示（含汇总成功/失败数量、失败原因展示）在 `renderer/src/pages/BatchCreation.tsx`
- [ ] T053 [US3] 渲染进程在应用启动时查询 `GET /api/jobs?status=running,paused` 判断是否存在未完成批量；若存在则弹出恢复面板（展示批次摘要/已完成数/待续数），提供"继续"与"放弃清空"操作在 `renderer/src/pages/BatchCreation.tsx`

**Checkpoint**: US3 完成后，可稳定串行批量、可取消、可恢复续跑、可对失败条目重试。

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 跨故事一致性、稳定性与可用性补齐（不改变核心需求）。

- [ ] T054 [P] 将资源预警提示做成不遮挡的 UI 组件并复用到单条/批量在 `renderer/src/components/ResourceWarning.tsx`
- [ ] T055 [P] 落地"可控降级建议"（如建议切 720P/改 CPU/缩小批量）并与错误码映射在 `renderer/src/services/errors.ts`
- [ ] T056 [P] 对齐 contracts 文档与实际实现（补齐缺失字段/错误码）在 `specs/001-ai-dubber-prd/contracts/ipc-api.md`
- [ ] T057 [P] 更新 quickstart smoke checklist 覆盖 US1/US2/US3 关键路径在 `specs/001-ai-dubber-prd/quickstart.md`
- [ ] T058 [P] 验证现有作品库模块（浏览/搜索/播放/删除）在断网环境可正常使用，记录回归验证结果在 `specs/001-ai-dubber-prd/quickstart.md`
- [ ] T059 [P] 创建本地性能验收清单并验证：(a) 冷启动至 UI 可操作 ≤10s；(b) SSE 进度事件间隔 ≤200ms；(c) 批量 30 条跑完无 OOM 崩溃；记录在 `specs/001-ai-dubber-prd/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Depends on Phase 2 (握手、SSE、job state、资源守卫)
- **US2 (P2)**: Depends on Phase 2 (DB、错误返回)；US1 的模板选择器可复用
- **US3 (P3)**: Depends on Phase 2 (job state、SSE、持久化)；复用 US1 pipeline 骨架

### Within Each User Story

- Store/状态定义 before UI 组件
- Models/数据访问 before services
- Services before endpoints/routes
- Core implementation before integration
- Story complete before moving to next priority

## Parallel Opportunities

- Phase 1/2 内标记 [P] 的任务可并行
- Phase 2 完成后，US1/US2/US3 可由不同开发者并行推进（文件冲突较少）
- US1 内: T018/T019/T022/T023 可并行（不同文件/不同关注点）
- US3 内: T041/T042 可并行（两个独立的导入解析器）

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: 断网环境端到端闭环测试
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Demo (MVP!)
3. Add User Story 2 → Test independently → Demo
4. Add User Story 3 → Test independently → Demo
5. Polish phase → Final validation
