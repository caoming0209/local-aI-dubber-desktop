# Quickstart: 智影口播 · AI数字人视频助手（Windows版）V1.3

## Prerequisites

- Node.js 20 LTS
- Python 3.11
- FFmpeg 6.x+ (available in PATH)
- Git
- (Optional) CUDA Toolkit 11.8 for GPU acceleration

## Repository structure

- `electron-app/`: Electron main process (窗口管理 + Python 子进程启动)
- `renderer/`: React 19 renderer (从已有原型迁移，见下方说明)
- `python-engine/`: Python local engine (FastAPI 推理引擎)
- `shared/`: shared TypeScript types (IPC 请求/响应类型)
- `specs/001-ai-dubber-prd/`: 设计文档（spec, plan, research, data-model, contracts）

## Frontend prototype

已有前端原型项目位于 `D:\Git.Project\智影口播-·-ai数字人视频助手`（Google AI Studio 生成）。

**迁移步骤**（首次设置时执行一次）：

```bash
# 1) 将原型代码复制到 renderer/ 目录
cp -r "D:/Git.Project/智影口播-·-ai数字人视频助手/src" renderer/src
cp "D:/Git.Project/智影口播-·-ai数字人视频助手/index.html" renderer/index.html
cp "D:/Git.Project/智影口播-·-ai数字人视频助手/vite.config.ts" renderer/vite.config.ts
cp "D:/Git.Project/智影口播-·-ai数字人视频助手/tsconfig.json" renderer/tsconfig.json

# 2) 初始化 renderer package.json（保留核心依赖，移除不需要的包）
cd renderer
npm init -y
npm install react@19 react-dom@19 lucide-react zustand react-router-dom
npm install -D typescript @types/react @types/react-dom vite @vitejs/plugin-react @tailwindcss/vite vitest @testing-library/react

# 注意：不要安装 @google/genai、express、better-sqlite3（这些不属于渲染进程）
```

## Setup

### 1) Python engine

```bash
cd python-engine
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
python src/api/server.py
```

Expected output includes:

```json
{"status": "ready", "port": 18432}
```

### 2) Renderer (standalone preview)

```bash
cd renderer
npm install
npm run dev
```

Opens at `http://localhost:5173` (Vite default) for UI development without Electron.

### 3) Electron app (full integration)

```bash
cd electron-app
npm install
npm run dev
```

Starts Electron window → spawns Python engine → connects via HTTP.

## Smoke test checklist

- [ ] Open the app (Electron or browser preview)
- [ ] Verify all 5+ navigation tabs render without error
- [ ] Verify engine handshake succeeds and UI becomes interactive (Electron mode)
- [ ] Run a single-generation workflow with sample image + script
- [ ] Confirm output video and subtitle files exist in output folder
- [ ] Verify resource monitor shows real CPU/Memory/VRAM data
- [ ] Verify batch generation executes serially

## Notes

- Core generation MUST work offline; avoid network actions unless explicitly testing activation/model download/update.
- Batch generation MUST be serial and capped at <= 30 items.
- Development mode (`NODE_ENV=development`) skips license checks.
- Frontend prototype uses mock data by default; real API integration requires Python engine running.
