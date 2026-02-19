# Tasks: AI数字人口播桌面客户端（Windows）

**Input**: Design documents from `/specs/001-ai-dubber-desktop/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Constitution 要求每个用户故事至少一个验收测试。测试任务包含在各 Phase 末尾。

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

本项目为双进程桌面应用，采用三目录结构：
- **electron-app/**: Electron 主进程壳
- **renderer/**: React 19 渲染进程（基于 AI 生成初始项目）
- **python-engine/**: Python 推理引擎
- **shared/**: 前后端共享类型定义

### 开发规范提醒

- **契约先行**：任何涉及新增或修改 Electron↔Python API 端点的任务，实现代码前必须先更新 contracts/ 对应文档
- **测试覆盖**：每个 User Story 末尾包含验收测试任务，不可跳过

---

## Phase 1: Setup（项目初始化）

**Purpose**: 搭建三目录项目结构，安装依赖，配置构建工具链

- [ ] T001 创建 electron-app/ 目录结构：src/main/、src/preload/、package.json、electron-builder.yml（按 plan.md 结构）
- [ ] T002 初始化 electron-app/ Node.js 项目，安装 electron、electron-builder、vite 依赖，配置 package.json scripts（dev/build:win）
- [ ] T003 [P] 将 renderer/ 中 Tailwind CSS 从 CDN（`<script src="https://cdn.tailwindcss.com">`）迁移为 npm 包：安装 tailwindcss@4.x + @tailwindcss/vite，更新 renderer/vite.config.ts，移除 renderer/index.html 中 CDN script 标签
- [ ] T004 [P] 在 renderer/ 安装 zustand@5.x 状态管理依赖
- [ ] T005 [P] 创建 shared/ipc-types.ts，定义通用 ApiResponse、ApiError、ErrorCode 类型（按 contracts/ipc-api.md 通用响应结构）
- [ ] T006 [P] 创建 python-engine/ 目录结构：src/api/、src/api/routes/、src/core/、src/storage/、src/storage/migrations/、src/license/、src/utils/、tests/unit/、tests/integration/
- [ ] T007 [P] 创建 python-engine/requirements.txt，声明核心依赖：fastapi、uvicorn、sse-starlette、ffmpeg-python、cryptography、wmi、aiofiles、pytest、pytest-asyncio
- [ ] T008 [P] 初始化 python-engine 虚拟环境，安装 requirements.txt 依赖

---

## Phase 2: Foundational（阻塞性基础设施）

**Purpose**: Electron 主进程壳、Preload 安全沙箱、Python FastAPI 框架、SQLite 数据库、设置存储——所有用户故事的共同依赖

**⚠️ CRITICAL**: 在此阶段完成前，不可开始任何用户故事的实现

### Electron 主进程 & Preload

- [ ] T110 审查 contracts/ 文档完整性：逐一核对 contracts/ipc-api.md 和 contracts/license.md 中定义的所有端点，确认与 spec.md 功能需求一一对应，补充缺失的错误码（MODEL_CORRUPTED、MODEL_DOWNLOAD_INCOMPLETE），标注后续 Phase 中需新增的端点
- [ ] T009 实现 Electron 主进程入口 electron-app/src/main/index.ts：创建 BrowserWindow（加载 renderer Vite dev server 或 dist/index.html）、设置 nodeIntegration:false + contextIsolation:true
- [ ] T010 实现 Python 进程管理器 electron-app/src/main/python-manager.ts：启动 python-engine 子进程、读取 stdout 解析 `{"status":"ready","port":N}`、崩溃恢复（指数退避 1s/2s/4s，最多 3 次）、关闭时 SIGTERM + 3s 强制 kill
- [ ] T011 实现 Preload 脚本 electron-app/src/preload/index.ts：通过 contextBridge 暴露 window.electronAPI（engine.request、pipeline.subscribeProgress、system.openPath/showItemInFolder/selectDirectory/selectFile、getEnginePort），按 contracts/ipc-api.md Preload API 定义
- [ ] T012 实现 IPC 桥接 electron-app/src/main/ipc-bridge.ts：监听渲染进程 ipcMain 事件，将 engine.request 转发为 HTTP 请求到 127.0.0.1:{port}，将 pipeline.subscribeProgress 转发为 SSE 订阅

### Python FastAPI 框架

- [ ] T013 实现 FastAPI 服务入口 python-engine/src/api/server.py：随机端口绑定 127.0.0.1、stdout 输出 `{"status":"ready","port":N}`、注册路由蓝图、CORS 中间件、全局异常处理（返回 contracts/ipc-api.md 错误响应格式）
- [ ] T014 [P] 实现 SSE 进度事件生成器 python-engine/src/utils/progress.py：ProgressEmitter 类，支持发送 step/progress/message 事件，按 contracts/ipc-api.md SSE 格式定义
- [ ] T015 [P] 实现文件工具 python-engine/src/utils/file_utils.py：路径规范化、缩略图提取（FFmpeg 首帧截图）、文件大小格式化

### SQLite 数据库

- [ ] T016 实现 SQLite 数据库连接与迁移框架 python-engine/src/storage/database.py：连接池管理、PRAGMA user_version 读取、按序扫描 migrations/ 目录执行迁移脚本（单事务原子性）、迁移失败终止启动
- [ ] T017 创建初始迁移脚本 python-engine/src/storage/migrations/V001__initial_schema.sql：建表 works、project_configs、digital_humans、voice_models、bgm_tracks（按 data-model.md 完整字段定义），创建索引（works.created_at DESC、works.name、works.aspect_ratio）

### 设置存储

- [ ] T018 实现 JSON 设置读写 python-engine/src/storage/settings_store.py：读取/写入 {userDataDir}/settings.json，合并更新（部分字段覆盖），首次运行生成默认值（按 data-model.md AppSettings 接口定义）
- [ ] T019 实现设置 API 路由 python-engine/src/api/routes/system.py：GET /api/settings 返回完整设置、PUT /api/settings 合并更新

### 前端服务层基础

- [ ] T020 实现 API 客户端封装 renderer/src/services/engine.ts：通过 window.electronAPI.engine.request 发起请求，统一处理 ApiResponse/ApiError，提供 get/post/put/patch/delete 方法
- [ ] T021 [P] 实现 SSE 进度订阅封装 renderer/src/services/pipeline.ts：通过 window.electronAPI.pipeline.subscribeProgress 订阅进度流，返回 unsubscribe 函数
- [ ] T022 [P] 实现应用设置 Zustand store renderer/src/stores/settings.ts：加载设置、更新设置、主题状态（light/dark）

**Checkpoint**: 基础设施就绪——Electron 可启动并连接 Python 引擎，FastAPI 可响应请求，SQLite 已建表，设置可读写。用户故事实现可以开始。

---

## Phase 3: User Story 1 — 单条视频制作（核心流程）(Priority: P1) 🎯 MVP

**Goal**: 用户输入文案 → 选择语音 → 选择数字人 → 配置视频参数 → 生成可播放的 MP4 视频。5 步向导式制作流程。

**Independent Test**: 仅开发步骤式向导（文案→语音→数字人→视频设置→生成）和实时预览区，即可向用户演示完整价值。

### 后端：视频生成流水线

- [ ] T023 [P] [US1] 实现 TTS 引擎封装 python-engine/src/core/tts_engine.py：CosyVoice 2 推理接口（输入文案+音色+语速/音量/情感参数 → 输出 WAV 24kHz），FFmpeg 重采样至 16kHz，支持 GPU/CPU 双模式
- [ ] T024 [P] [US1] 实现口型同步引擎封装 python-engine/src/core/lipsync_engine.py：Wav2Lip 推理接口（输入视频+音频 → 输出口型同步视频），支持 GPU/CPU 双模式
- [ ] T025 [P] [US1] 实现 FFmpeg 视频合成器 python-engine/src/core/video_synthesizer.py：合成背景（纯色/场景/自定义图片）、叠加字幕（字体/字号/颜色/位置）、混入 BGM（音量比例控制）、输出 1080P MP4
- [ ] T026 [P] [US1] 实现 GPU 检测器 python-engine/src/core/gpu_detector.py：检测 CUDA 可用性、显卡型号、显存大小、推荐推理模式（auto/cpu/gpu）
- [ ] T112 [US1] 实现流水线模型预检与自动下载 python-engine/src/core/model_manager.py 补充：pipeline 启动前检测 CosyVoice 2 和 Wav2Lip 模型是否已下载，未下载时自动触发下载并通过 SSE 推送下载进度（FR-091），下载完成后继续执行流水线；模型缺失且用户取消下载时返回 MODEL_NOT_FOUND 错误
- [ ] T027 [US1] 实现单条生成流水线路由 python-engine/src/api/routes/pipeline.py：POST /api/pipeline/single（接收完整配置，创建 job，返回 job_id 202）、GET /api/pipeline/progress/{job_id}（SSE 进度流，按 contracts/ipc-api.md 格式：script_optimization→tts→lipsync→synthesis→completed/failed）、POST /api/pipeline/pause/{job_id}、POST /api/pipeline/resume/{job_id}、POST /api/pipeline/cancel/{job_id}
- [ ] T028 [US1] 实现作业状态查询路由 python-engine/src/api/routes/pipeline.py：GET /api/jobs/{job_id}/state 返回作业当前状态快照（status/current_step/progress），用于 SSE 断连恢复
- [ ] T029 [US1] 实现作品写入 python-engine/src/storage/works_repo.py：视频生成成功后写入 works 表和 project_configs 表（关联 FK），提取首帧封面图

### 前端：5 步向导页面

- [ ] T030 [US1] 实现制作配置 Zustand store renderer/src/stores/project.ts：管理当前 5 步向导状态（文案、音色及参数、数字人、背景/比例/字幕/BGM、生成状态/进度），支持步骤切换和配置保留
- [ ] T031 [US1] 实现 SingleCreation 页面主框架 renderer/src/pages/SingleCreation.tsx：5 步向导布局（步骤指示器 + 左侧配置区 + 右侧实时预览区），步骤切换逻辑（FR-010），步骤间保留已配置内容
- [ ] T032 [US1] 实现步骤 1 — 文案输入组件 renderer/src/pages/SingleCreation.tsx 或 renderer/src/components/creation/ScriptInput.tsx：文案输入框、实时字数统计、10 字最低限制校验（FR-011）、文案模板选择（5 类模板 FR-013）、自动断句和口语化优化按钮（FR-012，可还原）
- [ ] T033 [US1] 实现步骤 2 — 语音选择组件 renderer/src/components/creation/VoiceSelector.tsx：按分类展示音色（男声/女声/情感音/方言音 FR-014）、试听按钮、收藏按钮、语速/音量/情感强度参数调节滑块（FR-015）
- [ ] T034 [US1] 实现步骤 3 — 数字人选择组件 renderer/src/components/creation/AvatarSelector.tsx：按分类展示数字人（FR-016）、hover 预览动作小样、点击选择后右侧预览区同步展示
- [ ] T035 [US1] 实现步骤 4 — 视频设置组件 renderer/src/components/creation/VideoSettings.tsx：背景选择（纯色/场景/自定义图片）、视频比例（9:16/16:9）、字幕开关与样式配置、BGM 开关与选择（FR-017）
- [ ] T036 [US1] 实现步骤 5 — 生成视频组件 renderer/src/components/creation/GenerateVideo.tsx：调用 POST /api/pipeline/single，订阅 SSE 进度流，显示实时进度条+步骤文字（FR-018），暂停/继续/取消按钮，生成成功后展示播放/打开文件位置/重新生成/制作下一条按钮（FR-019），失败时展示错误原因+重试+帮助入口（FR-020）
- [ ] T037 [US1] 实现进度条组件 renderer/src/components/ProgressBar.tsx：0-100% 进度条 + 当前步骤文字描述 + 预估剩余时间
- [ ] T038 [US1] 实现视频播放器组件 renderer/src/components/VideoPlayer.tsx：播放/暂停、进度条拖动、音量调节，支持本地 MP4 文件路径播放
- [ ] T039 [US1] 实现加载动画：所有耗时超过 3 秒的操作（文案优化、语音合成、口型同步）显示加载状态（FR-021）
- [ ] T040 [US1] 实现右侧预览区实时更新：配置变更后 1 秒内同步更新效果展示（FR-022）
- [ ] T100 [US1] 验收测试：编写 Playwright E2E 测试 renderer/tests/e2e/single-creation.spec.ts — 验证从文案输入到视频生成成功的完整 5 步向导流程（对应 spec.md US1 Acceptance Scenario 3）
- [ ] T101 [US1] 验收测试：编写 pytest 集成测试 python-engine/tests/integration/test_pipeline_single.py — 验证 POST /api/pipeline/single 返回 job_id、SSE 进度流推送完整步骤、生成成功后 works 表写入记录

**Checkpoint**: 用户可完成从文案输入到 MP4 视频生成的全流程。MVP 可演示。

---

## Phase 4: User Story 2 — 批量视频制作（提升效率）(Priority: P2)

**Goal**: 用户导入多条文案（TXT 文件或手动输入），统一配置后串行批量生成视频。

**Independent Test**: 开发批量导入和批量生成流程，配合与单条制作相同的配置面板即可独立验证。

### 后端：批量生成

- [ ] T041 [US2] 实现批量生成路由 python-engine/src/api/routes/pipeline.py：POST /api/pipeline/batch（接收 scripts 数组+shared_config+output_settings，返回 job_id 202），串行执行每条文案（严格串行，内存/显存限制），SSE 推送批量进度（batch_item_start/batch_item_progress/batch_item_done/batch_item_failed/batch_completed），失败跳过继续
- [ ] T042 [US2] 批量生成取消逻辑：暂停/取消时已生成的视频保留，未生成的跳过

### 前端：批量制作页面

- [ ] T043 [US2] 实现 BatchCreation 页面 renderer/src/pages/BatchCreation.tsx：手动多行输入 + TXT 文件导入两种模式（FR-030），100 条上限校验（FR-031），自动校验有效性并标注无效文案（FR-032），文案列表的查看/编辑/删除/批量删除/清空操作（FR-033）
- [ ] T044 [US2] 实现批量统一配置面板：复用 US1 的语音/数字人/视频设置组件，预览展示第一条文案效果（FR-034），自定义保存路径和命名前缀（FR-035）
- [ ] T045 [US2] 实现批量生成进度展示：整体进度 + 当前生成条数（「正在生成第 N 条 / 共 M 条」FR-036），暂停/继续/取消按钮，完成后汇总失败条数和原因（FR-037）
- [ ] T102 [US2] 验收测试：编写 pytest 集成测试 python-engine/tests/integration/test_pipeline_batch.py — 验证批量生成串行执行、失败跳过继续、完成后汇总失败条数

**Checkpoint**: 用户可批量导入文案并一键串行生成多条视频。

---

## Phase 5: User Story 3 — 数字人管理（个性化形象）(Priority: P3)

**Goal**: 用户可浏览官方数字人、上传自定义 MP4 视频作为专属数字人、管理收藏。

**Independent Test**: 独立开发数字人管理模块的上传、适配、命名、删除流程，无需依赖视频生成流程。

### 后端：数字人 API

- [ ] T046 [P] [US3] 实现数字人 CRUD 路由 python-engine/src/api/routes/digital_humans.py：GET /api/digital-humans（列表，支持 search/source/category 筛选）、PATCH /api/digital-humans/{id}（编辑名称/分类，仅 custom）、POST /api/digital-humans/{id}/favorite（切换收藏）、DELETE /api/digital-humans/{id}（仅 custom，联动删除适配视频文件）
- [ ] T047 [US3] 实现数字人上传与适配路由 python-engine/src/api/routes/digital_humans.py：POST /api/digital-humans/upload（multipart，≤500MB，支持 MP4/MOV/AVI/MKV，3-300s，≥360P，人脸预验证），返回 job_id + digital_human_id（202），GET /api/digital-humans/adapt-progress/{job_id}（SSE 适配进度），POST /api/digital-humans/{id}/re-adapt（重新适配）
- [ ] T048 [US3] 实现上传视频预验证与 FFmpeg 预处理流程：① 校验文件大小≤500MB 和容器格式（MP4/MOV/AVI/MKV）；② FFmpeg 预处理（转码 H.264 + 缩放≤1080P + 统一 25fps + 去除音轨）；③ 人脸检测（s3fd，单人正脸±30°）；④ 校验时长 3-300s、分辨率≥360P；不合格返回 400 错误码并提示具体原因；超过 120s 时长附加慢速处理提示

### 前端：数字人管理页面

- [ ] T049 [US3] 实现 AvatarManager 页面 renderer/src/pages/AvatarManager.tsx：三分类展示（官方/我的收藏/自定义 FR-040）、预览循环播放、收藏/取消收藏、使用按钮跳转制作（FR-041）、搜索框实时筛选 0.5s 内（FR-046）
- [ ] T050 [US3] 实现自定义数字人上传流程：上传 MP4、适配进度展示（10-30s FR-044）、命名和分类选择、适配失败提示+重新上传入口（FR-045）
- [ ] T051 [US3] 实现自定义数字人管理操作：编辑名称/分类、删除确认弹窗（FR-042）、重新适配、「立即使用」跳转单条制作步骤 3（FR-043）
- [ ] T103 [US3] 验收测试：编写 pytest 集成测试 python-engine/tests/integration/test_digital_humans.py — 验证上传 MP4 预验证、适配进度 SSE、适配成功后记录写入

**Checkpoint**: 用户可浏览官方数字人，上传自定义数字人并完成口型适配。

---

## Phase 6: User Story 4 — 音色管理（声音选择）(Priority: P3)

**Goal**: 用户可浏览、试听、收藏音色，管理模型下载（暂停/继续），删除模型释放磁盘空间。

**Independent Test**: 独立开发音色试听、收藏、模型下载/删除功能，无需依赖视频生成流程。

### 后端：音色 API

- [ ] T052 [P] [US4] 实现音色 CRUD 路由 python-engine/src/api/routes/voices.py：GET /api/voices（列表，支持 search/category/download_status 筛选）、POST /api/voices/{id}/favorite（切换收藏）
- [ ] T053 [US4] 实现模型下载管理路由 python-engine/src/api/routes/voices.py：POST /api/voices/{id}/download（触发下载）、GET /api/voices/{id}/download-progress（SSE 进度：progress/downloaded_mb/total_mb/speed_kbps/eta_seconds）、POST /api/voices/{id}/download/pause、POST /api/voices/{id}/download/resume、DELETE /api/voices/{id}/model（删除模型文件，保留记录，状态改 not_downloaded）
- [ ] T054 [US4] 实现模型下载核心逻辑 python-engine/src/core/model_manager.py：HTTP 断点续传下载、进度回调、暂停/恢复、SHA-256 完整性校验（按 data-model.md 校验策略），下载完成/失败更新 voice_models.download_status
- [ ] T055 [US4] 实现语音预览路由 python-engine/src/api/routes/voices.py：POST /api/voices/{id}/preview（输入文本+参数 → 调用 tts_engine → 返回 audio/wav 流）

### 前端：音色管理页面

- [ ] T056 [US4] 实现 VoiceManager 页面 renderer/src/pages/VoiceManager.tsx：按分类展示音色（男声/女声/情感音/方言音 FR-050）、显示名称/描述/模型大小、下载状态标识（FR-051）、搜索框实时筛选（FR-056）、收藏功能（FR-055）
- [ ] T057 [US4] 实现音色试听功能：点击试听 1 秒内开始播放（FR-052），暂停/重新播放，未下载音色自动触发下载
- [ ] T058 [US4] 实现模型下载进度 UI：实时进度条+剩余时间（FR-053），暂停/继续下载按钮
- [ ] T059 [US4] 实现模型删除功能：确认弹窗+空间释放说明（FR-054），删除后状态变为「未下载」
- [ ] T104 [US4] 验收测试：编写 pytest 集成测试 python-engine/tests/integration/test_voices.py — 验证模型下载触发、暂停/继续、SHA-256 校验、删除后状态变更

**Checkpoint**: 用户可浏览试听音色，下载/删除模型，收藏常用音色。

---

## Phase 7: User Story 5 — 作品库管理（内容资产管理）(Priority: P4)

**Goal**: 用户可浏览、搜索、筛选已生成视频，播放、重新编辑、重命名、删除作品。

**Independent Test**: 独立开发视频卡片展示、搜索筛选、重新编辑、删除功能即可验证。

### 后端：作品库 API

- [ ] T060 [US5] 实现作品库 CRUD 路由 python-engine/src/api/routes/works.py：GET /api/works（列表，支持 search/aspect_ratio/date_range/date_from/date_to/sort/page/page_size 参数，按 contracts/ipc-api.md 分页格式）、GET /api/works/{id}（详情，含 project_config 完整快照）、PATCH /api/works/{id}（重命名）、DELETE /api/works/{id}（删除记录+MP4+封面图）、DELETE /api/works（批量删除，body: ids 数组）、DELETE /api/works/all（清空，需 confirm:true）
- [ ] T061 [US5] 实现作品数据访问 python-engine/src/storage/works_repo.py 补充：列表查询（SQL 索引搜索/筛选/排序/分页）、详情查询（JOIN project_configs）、批量删除、清空、孤立记录检测（启动时检查 file_path 存在性）

### 前端：作品库页面

- [ ] T062 [US5] 实现作品库 Zustand store renderer/src/stores/works.ts：作品列表、分页状态、搜索/筛选条件、加载/删除操作
- [ ] T063 [US5] 实现 WorksLibrary 页面 renderer/src/pages/WorksLibrary.tsx：卡片式展示（封面/名称/时长/生成时间/分辨率/存储路径 FR-060）、每页 12 条分页+页码跳转（FR-062）、按生成时间/时长排序（FR-061）、搜索框+筛选器（名称/日期/分辨率/比例 FR-063）
- [ ] T064 [US5] 实现作品操作：播放（复用 VideoPlayer 组件 FR-064）、打开文件位置、重新编辑（准确恢复原始配置跳转 SingleCreation FR-065）、重命名、删除确认弹窗（FR-066）、批量勾选删除、清理全部确认弹窗（FR-067）
- [ ] T065 [US5] 实现作品库空状态：显示引导文案+跳转单条制作入口
- [ ] T105 [US5] 验收测试：编写 Playwright E2E 测试 renderer/tests/e2e/works-library.spec.ts — 验证作品卡片展示、搜索筛选、重新编辑恢复原始配置、批量删除

**Checkpoint**: 用户可浏览管理所有已生成视频，支持搜索筛选、播放、重新编辑、删除。

---

## Phase 8: User Story 8 — 软件激活与授权（付费使用）(Priority: P4)

**Goal**: 实现试用 5 次（带水印）→ 激活码一次联网验证 → 正式版（无水印/无限制/完全离线）的完整授权流程。

**Independent Test**: 独立开发「试用状态判断 → 次数扣减 → 激活码输入 → 激活验证 → 状态持久化」流程，可在不依赖视频生成的情况下完整验证。

### 后端：授权模块

- [ ] T066 [P] [US8] 实现设备指纹生成 python-engine/src/license/fingerprint.py：通过 WMI 获取 CPU ProcessorId + 主板 SerialNumber + 系统磁盘 SerialNumber，任一获取失败用 "UNKNOWN" 占位，SHA-256 哈希生成指纹
- [ ] T067 [P] [US8] 实现授权状态加密存储 python-engine/src/license/store.py：AES-256-GCM 加密/解密 license.dat，密钥由 PBKDF2(设备指纹, 固定salt, 100000 次) 派生，文件格式 {nonce(12B)}{ciphertext}{tag(16B)} Base64 编码，首次启动创建 trial 状态
- [ ] T068 [US8] 实现激活码验证器 python-engine/src/license/validator.py：POST 到 ACTIVATION_SERVER/api/v1/activate（编译期硬编码 HTTPS 地址），校验激活码+绑定设备指纹，成功后更新本地 license.dat 为 activated 状态；POST /api/v1/unbind 解绑设备
- [ ] T069 [US8] 实现授权 API 路由 python-engine/src/api/routes/license.py：GET /api/license/status（返回授权状态，按 contracts/license.md 格式）、POST /api/license/activate（触发远程验证）、POST /api/license/unbind（解绑设备）、POST /api/license/consume-trial（扣减试用次数，内部调用）

### 前端：激活 UI

- [ ] T070 [US8] 实现授权 Zustand store renderer/src/stores/license.ts：授权状态、剩余试用次数、激活/解绑操作
- [ ] T071 [US8] 实现授权 API 调用封装 renderer/src/services/license.ts：getLicenseStatus、activate、unbind
- [ ] T072 [US8] 实现激活弹窗组件 renderer/src/components/ActivationModal.tsx：试用耗尽时弹出，展示购买渠道（微信客服二维码+淘宝店链接 FR-102）、「已有激活码，去激活」入口、激活码输入+激活按钮、成功/失败/网络错误提示（FR-103~FR-107）
- [ ] T073 [US8] 在单条制作步骤 5 和批量制作生成按钮处集成授权检查：显示当前状态和剩余次数（FR-101），试用耗尽阻止生成并弹出激活引导（FR-102）
- [ ] T074 [US8] 实现首次启动试用版提示弹窗：说明免费次数和激活方式，可关闭后不再自动弹出（FR-109）
- [ ] T075 [US8] 实现试用版水印叠加：视频生成时根据 license.type 决定是否添加右下角水印（FR-096/FR-100/FR-108）

### 后端：水印叠加

- [ ] T076 [US8] 在 python-engine/src/core/video_synthesizer.py 中集成水印逻辑：试用版生成的视频右下角叠加软件水印，正式版无水印
- [ ] T106 [US8] 验收测试：编写 pytest 集成测试 python-engine/tests/integration/test_license.py — 验证试用次数扣减、激活码验证流程、加密存储读写、设备指纹生成

**Checkpoint**: 完整授权流程可用——试用 5 次、水印、激活码输入、联网验证、离线使用。

---

## Phase 9: User Story 6 — 软件设置（运行优化）(Priority: P5)

**Goal**: 用户可配置推理模式、存储路径、缓存、主题、自启动等参数。

**Independent Test**: 独立开发设置项的读取、修改和持久化功能，验证参数变更是否正确生效。

### 后端：系统 API

- [ ] T077 [P] [US6] 实现硬件信息路由 python-engine/src/api/routes/system.py 补充：GET /api/system/hardware（CPU/内存/显卡/显存/磁盘剩余空间/OS）
- [ ] T078 [P] [US6] 实现 GPU 兼容性检测路由 python-engine/src/api/routes/system.py 补充：POST /api/system/gpu-check（CUDA 检测，≤10s，返回 gpu_available/cuda_version/recommendation）
- [ ] T079 [P] [US6] 实现缓存管理路由 python-engine/src/api/routes/system.py 补充：GET /api/system/cache-info（缓存大小）、DELETE /api/system/cache（清理临时缓存，不影响作品和模型）
- [ ] T080 [P] [US6] 实现版本与更新路由 python-engine/src/api/routes/system.py 补充：GET /api/system/version（当前版本+最新版本+是否可更新）、POST /api/system/check-update（实时检查）

### 前端：设置页面

- [ ] T081 [US6] 实现 Settings 页面 renderer/src/pages/Settings.tsx：基础设置（开机自启/默认保存路径/主题切换 FR-070/FR-071）、模型下载设置（存储路径/下载限速/自动下载 FR-072）、性能设置（推理模式/CPU 限制 FR-073）、硬件信息展示+GPU 检测按钮（FR-074）、缓存查看+清理按钮（FR-075）、版本检查+更新按钮（FR-076）、重置所有设置按钮（FR-077）
- [ ] T082 [US6] 实现主题切换功能：light/dark 主题实时切换（FR-071），Tailwind dark mode 类名切换，持久化到 settings
- [ ] T083 [US6] 在 Settings 页面集成授权管理子项：展示授权类型/剩余次数/激活码/绑定设备数/解绑按钮（FR-108）
- [ ] T107 [US6] 验收测试：编写 Playwright E2E 测试 renderer/tests/e2e/settings.spec.ts — 验证设置读取/修改/持久化、主题切换实时生效、GPU 检测返回结果

**Checkpoint**: 用户可配置所有软件参数，GPU 检测正常，主题切换生效。

---

## Phase 10: User Story 7 — 首页与快速导航（快速上手）(Priority: P5)

**Goal**: 新用户通过首页快速入口和教程引导，3 分钟内了解主要功能并开始第一条视频制作。

**Independent Test**: 独立开发首页布局和教程弹窗，通过测试新用户能否快速找到核心功能。

- [ ] T084 [US7] 实现 Home 首页 renderer/src/pages/Home.tsx：三个主操作按钮（新建视频/批量制作/查看作品 FR-001）、最近 3 条记录展示（FR-002，hover 显示播放/编辑/删除选项）、软件版本号展示（FR-004）
- [ ] T085 [US7] 实现教程弹窗组件：3 步快速制作图文教程，可拖动/可关闭/可重复查看（FR-003）
- [ ] T086 [US7] 首页最近记录数据接入：调用 GET /api/works?sort=created_at_desc&page_size=3 获取最新 3 条作品
- [ ] T108 [US7] 验收测试：编写 Playwright E2E 测试 renderer/tests/e2e/home.spec.ts — 验证首页三个快速入口可点击跳转、最近 3 条记录展示

**Checkpoint**: 首页展示完整，新用户可快速找到功能入口。

---

## Phase 11: User Story 9 — 帮助与反馈（问题解决）(Priority: P6)

**Goal**: 用户可按分类浏览教程和 FAQ，搜索关键词找到解答，通过客服入口获取帮助。

**Independent Test**: 独立开发教程内容、FAQ 和搜索功能，脱离其他模块单独验证。

- [ ] T087 [P] [US9] 实现 Help 页面 renderer/src/pages/Help.tsx：分类使用教程（快速入门/单条制作/批量制作/数字人上传/音色使用 FR-080）、分类 FAQ 展开/折叠（FR-081）、关键词搜索实时筛选（FR-082）、客服入口（FR-083）
- [ ] T088 [P] [US9] 准备静态帮助内容数据：教程图文和 FAQ 条目 JSON/TS 常量（内置静态内容，随版本更新）
- [ ] T109 [US9] 验收测试：编写 Playwright E2E 测试 renderer/tests/e2e/help.spec.ts — 验证 FAQ 搜索实时筛选、教程分类展示、客服入口可点击

**Checkpoint**: 帮助模块可用，FAQ 搜索正常。

---

## Phase 12: Polish & Cross-Cutting Concerns

**Purpose**: 全局优化、安全加固、打包配置

- [ ] T089 实现全局确认弹窗组件 renderer/src/components/ConfirmDialog.tsx：所有危险操作（删除/清理/取消/重置）使用统一确认弹窗（FR-094）
- [ ] T090 实现全局按钮状态反馈：点击视觉反馈、不可点击置灰+hover 提示原因（FR-095）
- [ ] T091 [P] 实现全局加载动画组件：耗时操作统一 loading spinner/skeleton（FR-021）
- [ ] T092 实现模型文件完整性校验 python-engine/src/core/model_manager.py 补充：checksums.json SHA-256 校验（下载后即校验、启动时快速校验前 4KB < 200ms、推理前完整校验），失败返回 MODEL_CORRUPTED/MODEL_DOWNLOAD_INCOMPLETE 错误码
- [ ] T093 [P] 实现 BGM 数据初始化：内置 10 首 BGM 数据插入 bgm_tracks 表（builtin，随安装包分发），支持自定义上传
- [ ] T094 [P] 实现官方数字人数据初始化：内置 10-20 个官方数字人数据插入 digital_humans 表（official，随安装包分发）
- [ ] T095 配置 electron-builder.yml 打包参数：Windows NSIS 安装包配置、文件关联、安装路径、包含 python-engine 打包产物
- [ ] T111 [US6] 实现自动更新下载与安装流程 electron-app/src/main/updater.ts：集成 electron-updater，检测到新版本后下载更新包、显示下载进度、下载完成提示用户重启安装；更新过程中禁止关闭软件（拦截 window close 事件）；下载失败时提示并支持重试（FR-076）
- [ ] T096 配置 PyInstaller 打包 python-engine 为独立 .exe：包含所有依赖和模型加载逻辑
- [ ] T097 配置 Nuitka 单独编译 python-engine/src/license/ 模块为原生 .pyd 扩展：防逆向保护激活验证逻辑
- [ ] T098 实现开发模式特殊行为：NODE_ENV=development 时跳过授权检查、无水印、无生成限制
- [ ] T099 验证 quickstart.md 开发环境搭建流程：按指南从零搭建并确认所有脚本可正常运行

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: 无依赖 — 可立即开始
- **Phase 2 (Foundational)**: 依赖 Phase 1 完成 — **阻塞所有用户故事**
- **Phase 3-11 (User Stories)**: 全部依赖 Phase 2 完成
  - 用户故事可按优先级串行执行（P1 → P2 → P3 → P4 → P5 → P6）
  - 若多人协作，可并行执行不同用户故事
- **Phase 12 (Polish)**: 依赖所有目标用户故事完成

### User Story Dependencies

- **US1 (P1 单条制作)**: Phase 2 完成后可开始，无其他用户故事依赖。**MVP 核心**。
- **US2 (P2 批量制作)**: 依赖 Phase 2。复用 US1 的配置组件和流水线逻辑，建议在 US1 之后开发。
- **US3 (P3 数字人管理)**: 依赖 Phase 2。可独立于 US1 开发。
- **US4 (P3 音色管理)**: 依赖 Phase 2。可独立于 US1 开发。
- **US5 (P4 作品库)**: 依赖 Phase 2。建议在 US1 之后（有实际作品数据）。
- **US8 (P4 授权)**: 依赖 Phase 2。可独立开发，但需在 US1 中集成授权检查。
- **US6 (P5 设置)**: 依赖 Phase 2。独立开发。
- **US7 (P5 首页)**: 依赖 Phase 2。需 US5 的作品列表 API。
- **US9 (P6 帮助)**: 依赖 Phase 2。完全独立，纯前端静态内容。

### Within Each User Story

- 后端 API 先于前端页面实现
- 数据模型/存储层先于路由层
- 核心引擎先于 API 路由
- 前端 store 先于页面组件

### Parallel Opportunities

- Phase 1: T003/T004/T005/T006/T007/T008 全部可并行
- Phase 2: T014/T015 可并行；T020/T021/T022 可并行
- Phase 3 (US1): T023/T024/T025/T026 四个核心引擎可并行；T032-T035 四个步骤组件可在 T031 后并行
- Phase 5 (US3) 和 Phase 6 (US4) 可并行（不同模块）
- Phase 8 (US8): T066/T067 可并行
- Phase 9 (US6): T077/T078/T079/T080 四个系统路由可并行
- Phase 11 (US9): T087/T088 可并行

---

## Parallel Example: User Story 1 (Phase 3)

```bash
# 四个核心引擎可同时开发（不同文件，无依赖）:
Task T023: "实现 TTS 引擎封装 in python-engine/src/core/tts_engine.py"
Task T024: "实现口型同步引擎封装 in python-engine/src/core/lipsync_engine.py"
Task T025: "实现 FFmpeg 视频合成器 in python-engine/src/core/video_synthesizer.py"
Task T026: "实现 GPU 检测器 in python-engine/src/core/gpu_detector.py"

# 流水线路由（依赖上述四个引擎完成）:
Task T027: "实现单条生成流水线路由 in python-engine/src/api/routes/pipeline.py"

# 前端四个步骤组件可并行（在 T031 主框架完成后）:
Task T032: "步骤 1 — 文案输入 in renderer/src/components/creation/ScriptInput.tsx"
Task T033: "步骤 2 — 语音选择 in renderer/src/components/creation/VoiceSelector.tsx"
Task T034: "步骤 3 — 数字人选择 in renderer/src/components/creation/AvatarSelector.tsx"
Task T035: "步骤 4 — 视频设置 in renderer/src/components/creation/VideoSettings.tsx"
```

## Parallel Example: User Story 3 & 4 (Phase 5 & 6)

```bash
# 数字人管理和音色管理完全独立，可由不同开发者同时进行:
Developer A: Phase 5 (US3) 数字人管理 T046-T051
Developer B: Phase 6 (US4) 音色管理 T052-T059
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup（项目结构 + 依赖安装）
2. Complete Phase 2: Foundational（Electron 壳 + Python 框架 + SQLite + 设置）
3. Complete Phase 3: User Story 1（5 步向导 + 视频生成流水线）
4. **STOP and VALIDATE**: 验证从文案输入到 MP4 输出的完整流程
5. 可演示 MVP

### Incremental Delivery

1. Setup + Foundational → 基础设施就绪
2. Add US1 (单条制作) → 验证 → **MVP 可演示** ✅
3. Add US2 (批量制作) → 验证批量流程
4. Add US3 + US4 (数字人 + 音色管理) → 资源管理完整
5. Add US5 + US8 (作品库 + 授权) → 商业化就绪
6. Add US6 + US7 (设置 + 首页) → 用户体验完善
7. Add US9 (帮助) → 全模块交付
8. Polish → 打包 → 发布

### Parallel Team Strategy

多人协作时：

1. 全员完成 Phase 1 + Phase 2
2. Phase 2 完成后：
   - **Developer A**: US1 (单条制作) → US2 (批量制作)
   - **Developer B**: US3 (数字人) + US4 (音色) → US5 (作品库)
   - **Developer C**: US8 (授权) → US6 (设置) + US7 (首页) + US9 (帮助)
3. 各用户故事独立完成后集成测试

---

## Notes

- [P] 标记的任务可与同阶段其他 [P] 任务并行执行（不同文件，无依赖）
- [USn] 标记将任务关联到对应用户故事，便于追溯
- 每个用户故事独立可测试、独立可交付
- 后端 API 先实现再做前端页面，确保接口可用
- 提交频率：每个任务或逻辑分组完成后提交
- 在任意 Checkpoint 处可暂停并独立验证该用户故事
- 开发模式下跳过授权检查（T098），方便日常开发调试
