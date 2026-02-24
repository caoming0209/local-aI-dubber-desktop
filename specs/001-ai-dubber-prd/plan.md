# Implementation Plan: 智影口播 · AI数字人视频助手（Windows版）V1.3

**Branch**: `001-ai-dubber-prd` | **Date**: 2026-02-24 | **Spec**: `specs/001-ai-dubber-prd/spec.md`
**Input**: Feature specification from `/specs/001-ai-dubber-prd/spec.md`

**Note**: This document is generated/maintained by the `/speckit.plan` workflow.

## Summary

交付一个 Windows 10/11 离线可用的桌面端“AI 数字人口播视频助手”V1.3：用户可单条生成口播视频（1080P 默认、可切换 720P），支持字幕（外置字幕文件 + 视频内嵌硬字幕）、可取消、可观测进度与资源状态；并支持声音克隆生成可复用“声音模板”，以及批量生成（≤30 条、严格串行、异常退出后按条目续跑的断点续传）。

整体架构采用 Electron（主进程壳）+ React 渲染进程（UI）+ 本地 Python 引擎（FastAPI + SSE）双进程模型：核心推理与视频合成全部在本机离线完成；仅激活验证、模型下载、更新检查等能力在用户主动触发时联网。

## Technical Context

**Language/Version**: TypeScript (Node.js 20) + Python 3.11
**Primary Dependencies**: Electron 40+ + React 19.2 + Vite 6 + Tailwind CSS 4 + Zustand 5 + React Router v7; FastAPI + uvicorn; FFmpeg 6.x+
**Storage**: SQLite（Python stdlib sqlite3）+ settings.json（本地 JSON）+ license.dat（AES-256-GCM）+ 本地文件系统（视频/模型/素材）
**Testing**: Vitest + React Testing Library（前端），pytest（后端），Playwright（E2E）
**Target Platform**: Windows 10/11 x64 桌面端（.exe 安装包）
**Project Type**: desktop-app（Electron UI）+ local-engine（Python 推理/合成）
**Performance Goals**: 启动至可操作 ≤ 10s；SSE 进度推送延迟 ≤ 200ms；作品库 500 条搜索 ≤ 1s；单条生成关键操作响应 ≤ 1s
**Constraints**: 核心流程离线；IPC 仅监听 127.0.0.1 随机端口；批量严格串行；资源监控更新频率 ≥ 2s/次；隐私默认不上传不遥测
**Scale/Scope**: 单机单用户；批量单批 ≤ 30 条；单段文案 120 字上限（自动拆分）；声音克隆输入 ≥30s 且 ≤100MB

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

以下门禁来自 `.specify/memory/constitution.md`，本计划在设计阶段必须满足：

- 离线闭环：单条/批量生成、字幕、作品访问在断网环境可用；联网能力与离线生成解耦，且 UI 明确标识
- 隐私边界：默认不上传、不收集用户内容；不得引入默认遥测
- IPC 边界与安全：仅绑定 `127.0.0.1:{random_port}`；一次性调用 REST；长任务进度 SSE；引擎就绪握手通过 stdout 输出端口
- 作业可恢复：任务具备稳定 `job_id`；支持状态快照查询；批量断点续传按条目续跑（正在执行条目视为未完成，恢复从头重跑该条目）
- 资源感知与稳定性：生成期展示 CPU/内存/显存（CPU 模式显存 N/A），更新频率 ≥ 2s/次；资源预警不遮挡核心操作；无法安全继续时可控降级/中断并给出可执行建议；批量严格串行
- 最小复杂度：遵循既有 Electron/React + Python/FastAPI 目录与技术栈；避免跨层耦合与过度抽象；用户可见行为变更需可验证

**Gate evaluation (pre-research)**: PASS（无新增架构违反项）

**Gate evaluation (post-design)**: PASS（见 `specs/001-ai-dubber-prd/research.md` 的 IPC/作业/资源与离线约束决策）

## Project Structure

### Documentation (this feature)

```text
specs/001-ai-dubber-prd/
├── spec.md              # Feature spec (already exists)
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── ipc-api.md
│   └── license.md
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
electron-app/
  src/
    main/
      index.ts
      python-manager.ts
      ipc-bridge.ts
    preload/
      index.ts

renderer/
  src/
    App.tsx
    main.tsx
    components/
    pages/
    stores/
    services/

python-engine/
  src/
    api/
      server.py
      routes/
    core/
    storage/
    license/
    utils/
  tests/

shared/
  ipc-types.ts
```

**Structure Decision**: 采用 Electron + React 作为 UI 层，Python(FastAPI) 作为本地推理/合成引擎；前后端通过本地 HTTP + SSE 通信，绑定 127.0.0.1 随机端口并以 stdout 握手完成端口发现。

## Complexity Tracking

无需要豁免宪章门禁的复杂度引入项；本节不适用。
