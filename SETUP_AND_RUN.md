# 项目安装与运行说明 (Windows, PowerShell)

本文档说明如何在 Windows (PowerShell) 环境下，为本仓库准备开发环境并启动前后端与 Electron 桌面壳。

**假设**
- 已克隆仓库到 `D:\Git.Project\local-aI-dubber-desktop`
- 已安装 `Python 3.11`、`Node.js 20.x (推荐)`、`Git`、`ffmpeg`（已加入 PATH）

## 1. 全局前置项（仅需一次）

- 安装 Git、Node.js（推荐 20 LTS）、Python 3.11
- 安装 FFmpeg 并加入系统 PATH（确保 ffmpeg 命令可用）
- （可选）安装 Visual Studio Build Tools（用于编译本地 Node 原生模块）

### 1.1 克隆仓库及子模块

本项目包含两个 Git 子模块，需要递归克隆：

```powershell
# 方式一：首次克隆时递归拉取所有子模块
git clone --recursive https://github.com/your-repo/local-aI-dubber-desktop.git

# 方式二：如果已克隆但未拉取子模块，执行以下命令
cd D:\Git.Project\local-aI-dubber-desktop
git submodule update --init --recursive
```

**子模块说明：**

| 子模块 | 来源仓库 | 用途 |
|--------|----------|------|
| `python-engine/third_party/CosyVoice` | https://github.com/FunAudioLLM/CosyVoice.git | 语音合成引擎（TTS） |
| `python-engine/third_party/Wav2Lip` | https://github.com/Rudrabha/Wav2Lip.git | 唇形同步引擎 |

**注意：** CosyVoice 内部还依赖 `Matcha-TTS` 子模块（位于 `CosyVoice/third_party/Matcha-TTS`），`--recursive` 参数会一并拉取。

## 2. Python（后端引擎）

1. 进入 Python 引擎目录并创建虚拟环境：

```powershell
cd D:\Git.Project\local-aI-dubber-desktop\python-engine
python -m venv .venv
.venv\Scripts\Activate.ps1
```

2. 安装常规依赖：

```powershell
# 在已激活的虚拟环境中
pip install -r requirements.txt
```

3. 安装 PyTorch / torchaudio（建议使用随项目提供的检测脚本）：

```powershell
# 脚本会检测 GPU 并尝试安装合适的 wheel（可能下载较大）
python scripts\setup_env.py
```

可选参数：`--force-cpu` / `--force-cuda` / `--force-rocm` / `--skip-requirements`。

4. 启动 Python 引擎（开发模式，输出 ready 信号）：

```powershell
# 保持虚拟环境激活
python src\api\server.py
```

成功时控制台会先输出类似：

```
{"status":"ready","port":18432}
```

然后 Uvicorn 会在该端口上启动服务。

5. 下载 CosyVoice3 模型（首次使用时需要）：

```powershell
# 下载 CosyVoice3 基础模型
python download_cosyvoice3.py

# 可选：下载 Wav2Lip 模型（用于唇形同步）
python download_wav2lip.py
```

模型会下载到 `~/Documents/local-aI-dubber-desktop/models/` 目录。

## 3. 前端（Renderer）

1. 打开新终端（不需要 Python venv），进入 `renderer`：

```powershell
cd D:\Git.Project\local-aI-dubber-desktop\renderer
node -v
npm -v
```

2. 安装依赖：

```powershell
# 若遇到 peer dependency 问题，使用 --legacy-peer-deps
npm install --legacy-peer-deps
```

3. 启动开发服务器（Vite）：

```powershell
npm run dev
```

默认会在浏览器打开 Vite 的预览地址（或 Electron 内嵌渲染进程会加载它）。

## 4. Electron 主进程（桌面壳）

1. 在新终端进入 `electron-app`：

```powershell
cd D:\Git.Project\local-aI-dubber-desktop\electron-app
node -v
npm -v
```

2. 安装依赖并启动：

```powershell
npm install --legacy-peer-deps
npm run dev
```

`npm run dev` 会先执行 `tsc -b` 编译 TypeScript，然后启动 `electron .`。
Electron 进程会监听 Python 引擎在 stdout 输出的 ready 信号，并连接到所报端口。

## 5. 常见问题与排查

- npm install 失败：
  - 检查 Node 版本（推荐 20），清理缓存：`npm cache clean --force`，删除 `node_modules` 与 `package-lock.json` 后重装。
  - 如为原生模块编译错误，安装 Visual Studio Build Tools。

- Python 安装或 PyTorch 问题：
  - 若网络或带宽受限，可先使用 `python scripts\setup_env.py --skip-requirements`，手动安装小依赖并再单独安装 PyTorch wheel（参见 PyTorch 官方安装页面）。

- 端口冲突：
  - 开发模式默认端口 `18432`（见 `src/api/server.py` 的 dev 模式），如果该端口被占用，关闭占用程序或修改环境变量 `DEV_MODE`。

## 6. 常用命令速查

```powershell
# Python 后端（在 python-engine, venv 激活）
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts\setup_env.py
python src\api\server.py

# Renderer
cd renderer
npm install --legacy-peer-deps
npm run dev

# Electron
cd electron-app
npm install --legacy-peer-deps
npm run dev
```

## 7. 开发与测试说明

- 单元测试（后端）:

```powershell
cd python-engine
.venv\Scripts\Activate.ps1
pytest tests/
```

- 前端 E2E（Playwright）：在 `electron-app` 中运行 `npm run test:e2e`。

## 8. 其它备注

- 项目保持本地离线推理为目标；首次使用模型时可能会触发模型下载。
- 若需要我帮你定位具体的 `npm install` 或 `pip` 安装错误，请把终端完整错误粘贴到会话中，我会继续协助修复。

***
该文档已放置于仓库根：SETUP_AND_RUN.md
