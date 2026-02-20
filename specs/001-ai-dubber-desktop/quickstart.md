# 开发环境快速搭建指南

**Branch**: `001-ai-dubber-desktop` | **Date**: 2026-02-19

---

## 前置条件

| 工具 | 版本要求 | 说明 |
|------|----------|------|
| Node.js | 20 LTS | 前端 Electron + Vue 运行时 |
| Python | 3.11.x | 后端推理引擎 |
| Git | 最新版 | 版本控制 |
| FFmpeg | 6.x+ | 视频合成（需在 PATH 或指定路径） |
| CUDA Toolkit | 11.8（可选） | GPU 加速，无则跳过 |
| VS Code | 推荐 | 配套 Volar / Pylance 插件 |

---

## 1. 克隆仓库

```bash
git clone <repo-url>
cd local-aI-dubber-desktop
```

---

## 2. 前端环境（React 渲染进程）

前端基于谷歌 AI 生成的初始项目，位于 `local-aI-dubber-desktop/electron-app/`。开发时将此目录作为渲染进程工作目录。

```bash
# 安装依赖（补充 tailwindcss 和 zustand）
npm install
npm install tailwindcss @tailwindcss/vite zustand

# 开发模式（Vite dev server，浏览器预览）
npm run dev

# 构建 renderer bundle（供 Electron 加载）
npm run build
```

**注意**：`index.html` 当前通过 CDN 加载 Tailwind（`<script src="https://cdn.tailwindcss.com">`）。在整合 Electron 前，必须将其替换为 npm 包方式，否则 Electron 离线环境无法加载 CDN 资源。

**Electron 主进程**（新建 `electron-app/` 目录）：

```bash
cd electron-app
npm install
npm run dev      # 启动 Electron（加载 Vite dev server）
npm run build:win  # electron-builder 打包 Windows NSIS 安装包
```

**关键脚本说明**:

| 脚本 | 说明 |
|------|------|
| `npm run dev`（renderer） | 启动 Vite dev server，浏览器预览 React UI |
| `npm run dev`（electron-app） | 启动 Vite dev server + Electron（自动连接 Python 引擎） |
| `npm run build`（renderer） | 构建 renderer bundle |
| `npm run build:win` | electron-builder 打包 Windows NSIS 安装包 |
| `npm run test:unit` | Vitest 单元测试 |
| `npm run test:e2e` | Playwright E2E 测试（需先启动 Python 引擎） |
| `npm run lint` | ESLint + TypeScript 类型检查 |

**主要前端依赖说明**:

| 包 | 版本 | 用途 |
|----|------|------|
| `electron` | 40+ | 桌面应用壳 |
| `react` | 19.x | UI 框架 |
| `react-dom` | 19.x | DOM 渲染 |
| `react-router-dom` | 7.x | 客户端路由（HashRouter） |
| `zustand` | 5.x | 轻量状态管理 |
| `tailwindcss` | 4.x | 原子化样式框架（需 npm 安装，替换 CDN） |
| `lucide-react` | 最新 | 图标库 |
| `vite` | 6.x | 构建工具 |
| `typescript` | 5.x | 类型安全 |

---

## 3. Python 推理引擎（python-engine/）

```bash
cd python-engine

# 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate      # Windows

# 安装依赖
pip install -r requirements.txt

# 仅 CPU 推理（不需要 CUDA）
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# GPU 推理（需要 CUDA 11.8）
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# 启动引擎（随机端口，输出端口号供 Electron 读取）
python src/api/server.py
# 输出示例: {"status": "ready", "port": 18432}

# 仅运行测试
pytest tests/
```

**依赖说明** (requirements.txt 主要包):

| 包 | 用途 |
|----|------|
| `fastapi` + `uvicorn` | HTTP API 服务 |
| `sse-starlette` | SSE 进度推送 |
| `torch` + `torchvision` | 深度学习推理框架 |
| `wav2lip` (本地安装) | 口型同步 |
| `vits` / `cosyvoice` (本地安装) | TTS 语音合成 |
| `ffmpeg-python` | FFmpeg 调用封装 |
| `cryptography` | AES-256 授权文件加密 |
| `wmi` | Windows 硬件信息获取 |
| `aiofiles` | 异步文件操作 |
| `pytest` + `pytest-asyncio` | 测试框架 |

---

## 4. 模型文件准备（开发测试用）

首次开发需下载基础模型：

```bash
# 在 python-engine 目录下运行
python scripts/download_dev_models.py --models wav2lip,tts_male_basic

# 模型存储位置（开发环境）
# 默认: %USERPROFILE%\Documents\local-aI-dubber-desktop\models\
```

---

## 5. 联调开发流程

开发时需同时启动前端和后端：

**终端 1 — Python 引擎**:
```bash
cd python-engine
.venv\Scripts\activate
python src/api/server.py
# 记录输出的端口号
```

**终端 2 — Electron 前端**:
```bash
cd electron-app
npm run dev
# Electron 会自动读取 Python 输出的端口并建立连接
```

开发模式下 Python 引擎和 Electron 均支持热重载（后端使用 `--reload` 标志，前端使用 Vite HMR）。

---

## 6. 运行测试

```bash
# 前端单元测试（Vitest + React Testing Library）
cd 智影口播-·-ai数字人视频助手 && npm run test:unit

# 后端单元测试
cd python-engine && pytest tests/unit/ -v

# 后端集成测试（需启动引擎）
cd python-engine && pytest tests/integration/ -v

# E2E 测试（需同时启动前端+后端）
cd electron-app && npm run test:e2e
```

---

## 7. 常见问题

**Q: Python 引擎启动失败，提示找不到 FFmpeg**
A: 下载 FFmpeg Windows 版本，解压后将 `bin/` 目录加入系统 PATH，或在 `settings.json` 中设置 `ffmpeg_path` 字段。

**Q: Wav2Lip 推理报 CUDA 相关错误**
A: 检查 CUDA Toolkit 版本是否与 PyTorch 匹配；或在设置中切换为 CPU 推理模式。

**Q: 前端提示「无法连接到推理引擎」**
A: 确认 Python 引擎已启动且输出了 `{"status": "ready", "port": ...}`；检查防火墙是否阻止了本地回环端口。

**Q: 授权 license.dat 在开发环境如何处理**
A: 开发模式下（`NODE_ENV=development`）授权检查跳过，无限制生成，水印不添加。生产构建时恢复完整授权逻辑。
