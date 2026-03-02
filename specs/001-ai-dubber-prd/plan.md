# Implementation Plan: 智影口播 · AI数字人视频助手（Windows版）V1.3

**Branch**: `001-ai-dubber-prd` | **Date**: 2026-02-28 | **Spec**: `specs/001-ai-dubber-prd/spec.md`
**Input**: Feature specification from `/specs/001-ai-dubber-prd/spec.md`

## Summary

实现 V1.3 核心闭环：离线单条/批量口播视频生成、声音克隆模板管理、字幕输出、资源监控与稳定性兜底。

技术方案采用 Electron + React 19 前端 + Python FastAPI 本地推理引擎双进程架构，通过 HTTP REST + SSE 进行本地 IPC 通信。核心推理流水线为：文案自动拆分 → CosyVoice3-0.5B TTS → Wav2Lip 口型同步 → FFmpeg 视频合成 + 字幕。安装包内置核心模型确保开箱即离线可用。

**前端基础项目已存在**：位于 `D:\Git.Project\智影口播-·-ai数字人视频助手`，由 Google AI Studio 生成的高保真原型。包含 5 个核心页面组件（SingleVideo、BatchVideo、VoiceManagement、TaskRecords、Settings）+ 布局组件（TopBar、Sidebar、RightSidebar），使用 React 19 + Tailwind CSS v4 + Lucide React。当前为纯 UI 原型（所有操作为 mock），需迁移至本仓库 `renderer/` 并进行架构升级。

## Technical Context

**Language/Version**: TypeScript 5.x (Electron/React 前端) + Python 3.11 (推理引擎)
**Primary Dependencies**: Electron 40+, React 19.2, Tailwind CSS 4.x, Zustand 5.x, React Router 7.x (HashRouter), Vite 6, Lucide React, FastAPI, uvicorn, CosyVoice3-0.5B, Wav2Lip, ffmpeg-python, Pillow
**Storage**: SQLite (stdlib sqlite3, 无 ORM) + JSON 文件 + AES-256-GCM 加密文件
**Testing**: Vitest + React Testing Library (前端), pytest (后端), Playwright (E2E)
**Target Platform**: Windows 10/11 x64, .exe 安装包分发
**Project Type**: desktop-app (Electron + Python 双进程)
**Performance Goals**: 单条 1080P 生成中位数 ≤ 3min; SSE 进度延迟 ≤ 200ms; 资源状态更新 ≥ 0.5Hz; 应用启动 ≤ 10s
**Constraints**: 全程离线可用; 批量 ≤ 30 条串行; 文案 ≤ 3000 字/任务, 120 字/段; 阻止并发生成; 资源超限自动暂停
**Scale/Scope**: 单用户桌面应用; 作品库 500 条; 批量 ≤ 30 条; ~9 页面模块

## Existing Frontend Analysis

### 源项目位置

`D:\Git.Project\智影口播-·-ai数字人视频助手` — Google AI Studio 生成的 React 19 原型项目。

### 已有组件清单

| 组件 | 文件 | 状态 | 可复用度 |
|------|------|------|----------|
| TopBar | TopBar.tsx | UI 完成 | 高 — 保留布局，补充窗口控制 IPC |
| Sidebar | Sidebar.tsx | UI 完成 | 中 — 需从 tab 切换改为 NavLink + HashRouter |
| RightSidebar | RightSidebar.tsx | UI 完成 | 高 — 资源监控 UI 已实现，需接 SSE 数据源 |
| SingleVideo | SingleVideo.tsx | UI 完成 | 高 — 核心制作页面骨架完整，需接真实 API + 扩展字数上限 |
| BatchVideo | BatchVideo.tsx | UI 完成 | 高 — 批量制作+任务表格完整，需接 API + 断点续传逻辑 |
| VoiceManagement | VoiceManagement.tsx | UI 完成 | 高 — 上传+提取+列表完整，需接 API + 名称唯一校验 |
| TaskRecords | TaskRecords.tsx | UI 完成 | 高 — 历史记录表格完整，需接真实数据 |
| Settings | Settings.tsx | UI 完成 | 高 — 设置页完整，需接 settings API + 补充推理模式选择 |

### 缺失页面/组件

| 缺失项 | 规格要求 | 优先级 |
|--------|----------|--------|
| Home（首页） | 快速入口 + 最近记录 + 教程引导 | P1 |
| WorksLibrary（作品库） | 卡片式展示 + 搜索/筛选/排序 + 播放/删除 | P1 |
| AvatarManager（数字人管理） | 官方 + 自定义上传 | P2 |
| Help（帮助与反馈） | 教程 + FAQ + 客服入口 | P3 |
| ActivationModal | 激活弹窗 | P3（V1.3 不实现，预留接口） |
| ProgressBar | 可复用进度条组件 | P1 |
| VideoPlayer | 视频播放器 | P1 |

### 架构迁移项

| 现状 | 目标 | 影响范围 |
|------|------|----------|
| Tab 条件渲染（无路由） | React Router v7 HashRouter | App.tsx, Sidebar.tsx |
| State 提升到 App.tsx | Zustand stores | 所有组件 |
| setTimeout/setInterval mock | HTTP REST + SSE 真实 API | 所有交互组件 |
| 无 Electron 集成 | preload contextBridge (window.electronAPI) | 文件操作、窗口控制 |
| 文案上限 300 字 | 3000 字 (FR-020a) | SingleVideo.tsx |
| 无持久化 | SQLite via Python 后端 | 全局 |
| @google/genai 依赖 | 移除（离线产品不需要云端 AI） | package.json |
| motion 动画库 | 评估保留或替换为 CSS transitions | package.json |

### 样式系统

已有项目使用的色彩系统与设计规范可直接复用：
- 主色 `#2F80ED` (蓝)，成功 `#36D399` (绿)，危险 `#F87272` (红)
- 卡片阴影 `shadow-[0_2px_8px_rgba(0,0,0,0.1)]`
- 字体 "Microsoft YaHei", "Source Han Sans CN"
- Tailwind CSS v4 (npm 包，非 CDN) ✅ 与规格一致

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Gate

| # | 宪章原则 | 门禁项 | 状态 |
|---|----------|--------|------|
| I | 离线优先与隐私保护 | 核心生成闭环离线可用; 安装包内置模型 (FR-001/001a); 不收集不上传 (FR-002); 移除 @google/genai 云端依赖 | ✅ PASS |
| II | 本地 IPC 边界与安全 | 仅绑定 127.0.0.1; SSE 进度流; stdout 握手; 输入边界校验 | ✅ PASS |
| III | 可恢复作业与可观测进度 | job_id + state 快照; 每条状态展示; 取消需确认+清理; 按条目续跑 | ✅ PASS |
| IV | 资源感知与稳定性优先 | RightSidebar 已有资源监控 UI; 需接 SSE 真实数据; 预警阈值; 自动暂停; 串行 | ✅ PASS |
| V | 最小复杂度与可维护性 | 复用已有前端原型; 最小化迁移变更; 使用现有技术栈 | ✅ PASS |

### Post-Design Gate

| # | 门禁项 | 设计产物验证 | 状态 |
|---|--------|-------------|------|
| I | 离线闭环 | data-model 无云端依赖; ipc-api 无外网调用; 模型内置; @google/genai 已列入移除项 | ✅ PASS |
| II | IPC 安全 | ipc-api.md 仅 127.0.0.1; 所有输入有验证规则与错误码 | ✅ PASS |
| III | 可恢复性 | jobs/batch_jobs/batch_items 表持久化; state 快照接口; resume 语义明确 | ✅ PASS |
| IV | 资源稳定性 | SSE resource 字段; RESOURCE_CRITICAL 错误码; auto-pause 策略; 并发阻止 (JOB_ALREADY_RUNNING) | ✅ PASS |
| V | 最小复杂度 | 复用已有 UI 组件; 无新框架引入; 新增 stores/services 层与规格架构一致 | ✅ PASS |

**Result**: 所有门禁通过，无需 Complexity Tracking。

## Project Structure

### Documentation (this feature)

```text
specs/001-ai-dubber-prd/
├── plan.md              # This file
├── research.md          # Phase 0: 技术决策研究
├── data-model.md        # Phase 1: 数据模型定义
├── quickstart.md        # Phase 1: 开发环境搭建指南
├── contracts/
│   ├── ipc-api.md       # Phase 1: 前后端 HTTP IPC 接口合约
│   └── license.md       # Phase 1: 授权接口合约（草案，V1.3 不实现）
└── tasks.md             # Phase 2: 任务清单（由 /speckit.tasks 生成）
```

### Source Code (repository root)

```text
electron-app/                        # Electron 主进程（待创建）
├── src/
│   ├── main/
│   │   ├── index.ts                 # 窗口管理、Python 子进程启动
│   │   ├── python-manager.ts        # Python 进程生命周期（启动/握手/崩溃恢复）
│   │   └── ipc-bridge.ts            # 主进程 IPC 路由（preload → HTTP 代理）
│   └── preload/
│       └── index.ts                 # contextBridge: window.electronAPI
├── package.json
└── electron-builder.yml

renderer/                            # React 19 渲染进程（从已有原型迁移）
├── src/
│   ├── App.tsx                      # [迁移] HashRouter + 路由配置（替换 tab 条件渲染）
│   ├── main.tsx                     # [迁移] 渲染进程入口
│   ├── index.css                    # [迁移] 全局样式（Tailwind + 自定义字体）
│   ├── types.ts                     # [新建] RoutePath 枚举、共享实体接口
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Layout.tsx           # [新建] flex h-screen 主布局（TopBar + Sidebar + Content + RightSidebar）
│   │   │   ├── TopBar.tsx           # [迁移] 顶部栏（补充 Electron 窗口控制 IPC）
│   │   │   ├── Sidebar.tsx          # [迁移] 侧边栏（NavLink 替换 tab onClick）
│   │   │   └── RightSidebar.tsx     # [迁移] 资源监控面板（接 SSE 真实数据）
│   │   ├── ProgressBar.tsx          # [新建] 可复用生成进度条
│   │   ├── VideoPlayer.tsx          # [新建] 视频播放器
│   │   ├── ResourceWarning.tsx      # [新建] 资源预警非阻断提示
│   │   └── ConfirmDialog.tsx        # [新建] 通用确认弹窗
│   ├── pages/
│   │   ├── Home.tsx                 # [新建] 首页（快速入口 + 最近记录 + 教程引导）
│   │   ├── SingleCreation.tsx       # [迁移自 SingleVideo.tsx] 单条制作（文案上限→3000、接 API）
│   │   ├── BatchCreation.tsx        # [迁移自 BatchVideo.tsx] 批量制作（接 API + 断点续传）
│   │   ├── AvatarManager.tsx        # [新建] 数字人管理
│   │   ├── VoiceManager.tsx         # [迁移自 VoiceManagement.tsx] 声音模板管理（接 API + 名称唯一）
│   │   ├── WorksLibrary.tsx         # [新建] 作品库（卡片展示 + 搜索/筛选/排序）
│   │   ├── Settings.tsx             # [迁移] 设置（接 API + 补充推理模式选择）
│   │   └── Help.tsx                 # [新建] 帮助与反馈
│   ├── stores/                      # [新建] Zustand 状态管理（替换 App.tsx state 提升）
│   │   ├── project.ts               # 当前制作任务配置
│   │   ├── jobs.ts                  # 单条/批量作业状态 + SSE 订阅
│   │   ├── voice-templates.ts       # 声音模板列表与状态
│   │   ├── works.ts                 # 作品库
│   │   ├── resource-monitor.ts      # 资源监控状态（接 SSE）
│   │   ├── license.ts               # 授权状态
│   │   └── settings.ts              # 应用设置
│   └── services/                    # [新建] HTTP API 调用封装
│       ├── engine.ts                # 引擎通信基础层（通过 window.electronAPI 代理）
│       ├── pipeline.ts              # 生成流水线 API + SSE 订阅
│       ├── voice-templates.ts       # 声音模板 CRUD + SSE
│       ├── works.ts                 # 作品库 API
│       └── license.ts               # 授权 API
├── index.html
├── vite.config.ts
├── tailwind.config.ts               # [迁移] Tailwind 配置（如有）
└── package.json

python-engine/                       # Python 推理引擎（待创建）
├── src/
│   ├── api/
│   │   ├── server.py                # FastAPI 入口（随机端口 + stdout 握手）
│   │   └── routes/
│   │       ├── pipeline.py          # /pipeline/* 生成流水线路由
│   │       ├── jobs.py              # /jobs/* 作业查询路由
│   │       ├── voice_templates.py   # /voice-templates/* 声音模板路由
│   │       ├── works.py             # /works/* 作品库路由
│   │       ├── models.py            # /models/* 模型管理路由
│   │       ├── license.py           # /license/* 授权路由
│   │       └── system.py            # /system/* + /settings 系统路由
│   ├── core/
│   │   ├── tts_engine.py            # CosyVoice3-0.5B / VITS 封装
│   │   ├── lipsync_engine.py        # Wav2Lip 封装
│   │   ├── video_synthesizer.py     # FFmpeg 流水线（合成+字幕+BGM）
│   │   ├── voice_cloner.py          # 声音特征提取（CosyVoice speaker embedding）
│   │   ├── script_splitter.py       # 文案自动拆分（120 字/段，自然断句）
│   │   ├── image_processor.py       # 图片校验 + resize 512×512
│   │   ├── subtitle_generator.py    # SRT 生成 + 硬字幕烧录
│   │   ├── job_manager.py           # 作业调度（串行、并发阻止、暂停/恢复/取消）
│   │   ├── resource_monitor.py      # CPU/内存/显存监控 + 预警阈值检测
│   │   ├── model_manager.py         # 模型校验（启动快速校验 + 推理前完整校验）
│   │   └── gpu_detector.py          # CUDA 检测 + 推理模式决策
│   ├── storage/
│   │   ├── database.py              # SQLite 连接 + PRAGMA user_version 迁移
│   │   ├── works_repo.py            # 作品库数据访问
│   │   ├── jobs_repo.py             # jobs/batch_jobs/batch_items 数据访问
│   │   ├── voice_templates_repo.py  # 声音模板数据访问
│   │   ├── settings_store.py        # JSON 设置读写
│   │   └── migrations/              # V{NNN}__description.sql
│   ├── license/
│   │   ├── fingerprint.py           # 硬件指纹
│   │   ├── validator.py             # 激活码验证
│   │   └── store.py                 # AES-256-GCM 加密存储
│   └── utils/
│       ├── progress.py              # SSE 进度事件生成器
│       └── file_utils.py            # 路径、缩略图、临时文件清理
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
└── requirements.txt

shared/                              # 前后端共享类型（待创建）
└── ipc-types.ts                     # IPC 请求/响应 TypeScript 类型
```

**Structure Decision**: 采用 CLAUDE.md 定义的三模块结构（electron-app / renderer / python-engine）。前端 `renderer/` 从已有原型项目迁移，保留已有组件的 UI/样式，替换架构层（路由→HashRouter、状态→Zustand、数据→HTTP API+SSE）。每个迁移文件标记为 `[迁移]`，新增文件标记为 `[新建]`。

### 前端迁移策略

1. **代码迁入**：将 `D:\Git.Project\智影口播-·-ai数字人视频助手/src/` 内容复制到 `renderer/src/`
2. **依赖清理**：移除 `@google/genai`、`express`、`better-sqlite3`（后端独立管理）；保留 `react`、`@tailwindcss/vite`、`lucide-react`、`vite`；新增 `zustand`、`react-router-dom`
3. **路由迁移**：App.tsx 中 tab 条件渲染 → HashRouter + Route 配置 + Sidebar NavLink
4. **状态迁移**：App.tsx 中 useState → Zustand stores（jobs、resource-monitor、settings 等）
5. **API 接入**：setTimeout mock → services/ 层调用 window.electronAPI.engine.request()
6. **组件重组**：SingleVideo→SingleCreation、BatchVideo→BatchCreation、VoiceManagement→VoiceManager（命名对齐 CLAUDE.md）
7. **参数修正**：文案上限 300→3000、声音模板名称唯一校验、批量上限 30 条（已有）

## Complexity Tracking

> 所有宪章门禁通过，无需记录违规。

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (无) | — | — |
