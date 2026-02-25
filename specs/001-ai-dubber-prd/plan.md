# Implementation Plan: 智影口播 · AI数字人视频助手（Windows版）V1.3

**Branch**: `001-ai-dubber-prd` | **Date**: 2026-02-24 | **Spec**: `specs/001-ai-dubber-prd/spec.md`
**Input**: Feature specification (`specs/001-ai-dubber-prd/spec.md`) + 技术参考（`智影口播_技术方案_V1.0.md`）

**Note**: This document is generated/maintained by the `/speckit.plan` workflow.

## Summary

交付一个 Windows 10/11 离线可用的桌面端“AI 数字人口播视频助手”V1.3：用户可单条生成口播视频（1080P 默认、可切换 720P），支持字幕（外置字幕文件 + 视频内嵌硬字幕）、可取消、可观测进度与资源状态；并支持声音克隆生成可复用“声音模板”，以及批量生成（≤30 条、严格串行、异常退出后按条目续跑的断点续传）。

整体架构采用 Electron（主进程壳）+ React 渲染进程（UI）+ 本地 Python 引擎（FastAPI + SSE）双进程模型：核心推理与视频合成全部在本机离线完成；仅激活验证、模型下载、更新检查等能力在用户主动触发时联网。

## Technical Context

**Language/Version**: TypeScript (Node.js 20) + Python 3.11

**Primary Dependencies**:
- Electron 40+ + React 19.2 + Vite 6 + Tailwind CSS 4 + Zustand 5 + React Router v7
- Python: FastAPI + uvicorn
- ML runtime: PyTorch (engine inference)
- Media: FFmpeg 6.x+

**Storage**: SQLite（Python stdlib sqlite3）+ settings.json（本地 JSON）+ license.dat（AES-256-GCM）+ 本地文件系统（视频/模型/素材）

**Testing**: Vitest + React Testing Library（前端），pytest（后端），Playwright（E2E）

**Target Platform**: Windows 10/11 x64 桌面端（.exe 安装包）

**Project Type**: desktop-app（Electron UI）+ local-engine（Python 推理/合成）

**Performance Goals**:
- 启动至可操作 ≤ 10s
- SSE 进度推送延迟 ≤ 200ms
- 作品库 500 条搜索 ≤ 1s
- 单条生成关键操作响应 ≤ 1s

**Constraints**:
- 核心流程离线；联网能力（激活/模型下载/更新检查）必须与离线生成解耦
- IPC 仅监听 `127.0.0.1:{random_port}`
- 一次性调用 REST；长任务进度 SSE
- 批量严格串行（同一时间仅运行 1 条）
- 资源监控更新频率 ≥ 2s/次（CPU/内存/显存；CPU 模式显存 N/A）
- 隐私默认不上传、不遥测
- 目标硬件参考：8GB 显存 + 32GB 内存（来自 `智影口播_技术方案_V1.0.md` 的本地优化假设）

**Scale/Scope**:
- 单机单用户
- 批量单批 ≤ 30 条
- 单段文案 120 字上限（自动拆分）
- 声音克隆输入 ≥30s 且 ≤100MB

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

**Gate evaluation (post-design)**: PASS（见 `specs/001-ai-dubber-prd/research.md`）

## Project Structure

### Documentation (this feature)

```text
specs/001-ai-dubber-prd/
├── spec.md              # Feature spec
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

## 方案补充（参考 `智影口播_技术方案_V1.0.md`）

以下补充项来自 V1.0 技术方案的本地优化经验，但会按本项目宪章与 PRD 约束做取舍（离线优先、批量串行、最小复杂度）。

### 1) 通信选型差异（WebSocket vs REST+SSE）

- V1.0 提到 WebSocket 或 REST。
- 本项目保持 **REST + SSE**：一次性调用与进度流分离，断线恢复与调试更直接；且与现有目录约束（FastAPI + SSE）一致。

### 2) 资源与显存管理（Memory Guard 思路）

- 每个重计算阶段（TTS、口型、合成）结束后执行显存与对象清理（例如 PyTorch 的 cache 清理），降低碎片化风险。
- 资源采样（CPU/内存/显存）以 ≥2s/次节奏进入 SSE 事件，供前端展示与预警（与 FR-080/081 对齐）。
- 当显存/内存压力持续高位时，优先采取”可控降级”策略：例如建议切换 720P、缩小批量规模、改为 CPU 模式。
- 阈值参考（可调配置）：显存 ≥ 总量 90% → 预警 SSE（type=resource_warning）；显存 ≥ 95% 或连续 3 次采样高位 → 建议降级（RESOURCE_CRITICAL 错误码 + 附带建议）；可用磁盘 < 1GB → 阻断并提示清理。

### 3) 阶段性 CPU Offload 与管线拆分

- V1.0 建议部分环节转移到 CPU 以节省显存（例如人脸检测）。
- 本项目保持：能在 CPU 上完成的轻量步骤优先 CPU（如人脸检测/裁剪、编码封装），GPU 主要用于模型推理阶段。

### 4) 字幕策略补充

- V1.0 使用 Whisper small 做字幕对齐。
- V1.3 以“离线、最小复杂度”为优先：优先基于 TTS 的分段与音频时长生成字幕时间轴；ASR 对齐作为后续可选增强（若引入需评估模型体积与性能）。

### 5) 画质增强（可选，不作为 V1.3 默认路径）

- V1.0 提到 Real-ESRGAN/GFPGAN 等增强。
- V1.3 默认不引入到主链路：避免增加模型体积与算力消耗；若未来引入，必须提供开关并默认关闭，且对低配设备可用。

## Complexity Tracking

无需要豁免宪章门禁的复杂度引入项；本节不适用。

## 范围排除说明

- **授权模块（license）**：已有接口草案（`contracts/license.md`），V1.3 不实现；开发期间跳过授权检查（`NODE_ENV=development`）以保证离线闭环可验证。待后续迭代落地。
- **作品库模块**：为已有模块，V1.3 不做功能性变更，但需确保离线可用（回归验证）。
