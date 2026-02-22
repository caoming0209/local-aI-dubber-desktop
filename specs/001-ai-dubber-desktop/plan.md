# Implementation Plan: AI数字人口播桌面客户端（Windows）

**Branch**: `001-ai-dubber-desktop` | **Date**: 2026-02-19 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-ai-dubber-desktop/spec.md`

## Summary

构建「智影口播 · AI数字人视频助手」Windows 桌面客户端，实现从文案输入到数字人口播视频的全本地离线生成。采用双进程架构：Electron + React 19 前端（样式：Tailwind CSS，状态：Zustand）负责 UI 交互，Python 推理引擎负责 TTS 语音合成（CosyVoice3-0.5B）、口型同步（v1.0 Wav2Lip，v2.0 升级 MuseTalk）、FFmpeg 视频合成。两进程通过本地 HTTP + SSE（Server-Sent Events）通信——CRUD/设置类调用走 REST，长耗时任务（合成流水线）走 SSE 实时推送进度。license 模块以 Nuitka 编译为原生扩展，提供更强防逆向保护。产品包含 9 大功能模块（含授权激活），以 Electron + Python 打包为 .exe 安装包分发。前端基于谷歌 AI 生成的 React 19 初始项目（`智影口播-·-ai数字人视频助手/`）继续开发。

## Technical Context

**Language/Version**: JavaScript/TypeScript (Electron 40+, React 19, Node 20 LTS) + Python 3.11
**Primary Dependencies**: Electron, React 19, React Router v7, Zustand, Vite 6, Tailwind CSS, Lucide React; Python: FastAPI, Wav2Lip（v1.0）, CosyVoice3-0.5B（主 TTS）, VITS（低配备选 TTS）, FFmpeg-python, SQLite3, cryptography; 打包保护: electron-builder, PyInstaller, Nuitka（仅 license 模块）
**Storage**: SQLite（作品库 + 项目配置快照）; JSON 文件（应用设置、授权状态）; 本地文件系统（视频、模型、缩略图、BGM）
**Testing**: Vitest + React Testing Library（前端单元）; Playwright（E2E/Electron）; pytest（Python 后端）
**Target Platform**: Windows 10/11 64-bit 桌面应用，以 electron-builder 打包为 NSIS 安装包
**Project Type**: 双进程桌面应用（Electron 主进程 + Python 子进程，通过本地 HTTP 通信）
**Performance Goals**: 单条视频操作响应 ≤ 1s；进度更新推送延迟 ≤ 200ms；作品库 500 条搜索 ≤ 1s；应用启动至可操作 ≤ 10s
**Constraints**: 全程离线运行（模型下载后）；GPU 加速可选（CUDA），无 GPU 回退 CPU；最低 8GB 内存；生成视频无水印（正式版）
**Scale/Scope**: 单用户桌面应用；9 个 UI 模块；约 50 条功能需求；作品库支持 500+ 视频；批量任务最多 100 条

## Constitution Check

*关口：Phase 0 研究前必须通过；Phase 1 设计完成后重新核查。*

| 检查项 | 状态 | 说明 |
|--------|------|------|
| 一、离线优先：核心功能无需联网 | PASS | 所有 AI 推理本地运行；仅激活和模型下载需网络；用户数据不上传 |
| 二、双进程契约隔离：跨进程仅通过 HTTP+SSE 契约通信 | PASS | 契约已定义于 contracts/ipc-api.md 和 contracts/license.md；两进程无其他耦合 |
| 三、单一权威来源：每个数据域单一存储位置 | PASS | 作品库→SQLite；设置→settings.json；授权→license.dat；无跨层数据重复 |
| 四、AI 代码生成友好性：技术选型权重 AI 生成质量 | PASS | React 19 + Tailwind（训练数据最丰富）；Wav2Lip v1.0（成熟稳定）；MuseTalk 列为 v2.0 路线图 |
| 五、匹配威胁模型的安全措施 | PASS | Nuitka 编译 license 模块；AES-256-GCM 设备绑定加密；无企业级 DRM 或每次启动联网验证 |
| 性能标准：关键操作满足响应时间目标 | PASS | UI 交互 ≤1s；SSE 延迟 ≤200ms；作品库搜索 ≤1s；启动 ≤10s |

## Project Structure

### Documentation (this feature)

```text
specs/001-ai-dubber-desktop/
├── plan.md              # This file
├── research.md          # Phase 0: IPC、TTS、存储、授权选型
├── data-model.md        # Phase 1: 所有实体定义与关系
├── quickstart.md        # Phase 1: 开发环境搭建指南
├── contracts/
│   ├── ipc-api.md       # 前端↔后端 HTTP IPC 接口定义（含视频生成流水线）
│   └── license.md       # 授权激活接口
└── tasks.md             # Phase 2 (/speckit.tasks 生成)
```

### Source Code (repository root)

```text
electron-app/                        # Electron 主进程壳（新建）
├── src/
│   ├── main/                        # Electron 主进程
│   │   ├── index.ts                 # 入口：窗口管理、Python 子进程启动
│   │   ├── python-manager.ts        # Python 进程生命周期管理
│   │   └── ipc-bridge.ts            # 主进程 IPC 路由
│   └── preload/
│       └── index.ts                 # 安全沙箱：暴露有限 API 给渲染进程
├── package.json
└── electron-builder.yml

renderer/                            # React 19 渲染进程（基于 AI 生成初始项目）
│                                    # 原始路径: 智影口播-·-ai数字人视频助手/
├── src/
│   ├── App.tsx                      # HashRouter + 路由配置（已有）
│   ├── main.tsx                     # 渲染进程入口（已有）
│   ├── types.ts                     # RoutePath 枚举、实体接口（已有）
│   ├── components/
│   │   ├── Layout.tsx               # flex h-screen 布局（已有）
│   │   ├── Sidebar.tsx              # 深色侧边栏 + NavLink（已有）
│   │   ├── ProgressBar.tsx          # 生成进度条（待实现）
│   │   ├── VideoPlayer.tsx          # 视频播放器（待实现）
│   │   └── ActivationModal.tsx      # 激活弹窗（待实现）
│   ├── pages/                       # 各功能模块页面（骨架已有）
│   │   ├── Home.tsx                 # 首页（已有骨架）
│   │   ├── SingleCreation.tsx       # 5步制作向导（已有骨架）
│   │   ├── BatchCreation.tsx        # 批量制作（已有骨架）
│   │   ├── AvatarManager.tsx        # 数字人管理（已有骨架）
│   │   ├── VoiceManager.tsx         # 音色管理（已有骨架）
│   │   ├── WorksLibrary.tsx         # 作品库（已有骨架）
│   │   ├── Settings.tsx             # 设置（已有骨架）
│   │   └── Help.tsx                 # 帮助（待实现）
│   ├── stores/                      # Zustand 状态管理（待实现）
│   │   ├── project.ts               # 当前制作配置
│   │   ├── works.ts                 # 作品库
│   │   ├── license.ts               # 授权状态
│   │   └── settings.ts              # 应用设置
│   └── services/                    # HTTP API 调用封装（待实现）
│       ├── engine.ts                # Python 引擎 API 客户端
│       ├── pipeline.ts              # 流水线调用（含 SSE 进度）
│       └── license.ts               # 授权激活调用
├── tests/
│   ├── unit/
│   └── e2e/
├── index.html                       # 已有（Tailwind CDN → 迁移为 npm）
├── vite.config.ts                   # 已有
└── package.json                     # 已有（需补充 tailwindcss、zustand）

python-engine/                       # Python 推理引擎
├── src/
│   ├── api/
│   │   ├── server.py                # FastAPI 入口（随机端口启动）
│   │   ├── routes/
│   │   │   ├── pipeline.py          # 视频生成流水线（SSE）
│   │   │   ├── tts.py               # 语音合成
│   │   │   ├── lipsync.py           # 口型同步
│   │   │   ├── synthesis.py         # FFmpeg 视频合成
│   │   │   ├── works.py             # 作品库 CRUD
│   │   │   ├── models.py            # 模型下载管理
│   │   │   ├── license.py           # 授权激活
│   │   │   └── system.py            # 硬件信息、GPU 检测
│   ├── core/
│   │   ├── tts_engine.py            # TTS 推理（VITS/CosyVoice 封装）
│   │   ├── lipsync_engine.py        # Wav2Lip 封装
│   │   ├── video_synthesizer.py     # FFmpeg 流水线
│   │   ├── model_manager.py         # 模型下载、校验、删除
│   │   └── gpu_detector.py          # CUDA 检测与选择
│   ├── storage/
│   │   ├── database.py              # SQLite 连接与迁移
│   │   ├── works_repo.py            # 作品库数据访问
│   │   └── settings_store.py        # JSON 设置读写
│   ├── license/
│   │   ├── fingerprint.py           # 硬件指纹生成（Windows WMI）
│   │   ├── validator.py             # 激活码验证（本地 + 远程）
│   │   └── store.py                 # 授权状态加密存储
│   └── utils/
│       ├── progress.py              # SSE 进度事件生成器
│       └── file_utils.py            # 路径、缩略图提取工具
├── tests/
│   ├── unit/
│   └── integration/
└── requirements.txt

shared/                              # 前后端共享类型定义
└── ipc-types.ts                     # IPC 请求/响应 TypeScript 类型
```

**Structure Decision**: 采用「Electron 壳 + React 渲染进程 + Python 引擎」三目录结构。React 渲染进程基于谷歌 AI 生成的初始项目继续开发，通过 Vite 构建后由 Electron 加载；两者通过本地 HTTP 通信而非共享代码，shared/ 仅存放类型定义作为契约锚点。**Tailwind CDN 必须迁移为 npm 包**以支持 Electron 离线加载和生产打包 tree-shaking。

## Complexity Tracking

> Constitution 未配置，以下记录架构复杂性决策原因：

| 决策 | 原因 | 更简单方案被拒原因 |
|------|----|------------------|
| 双进程架构（Electron + Python） | Python 生态有 Wav2Lip、CosyVoice3-0.5B 等成熟 AI 推理库，JS 生态缺乏等价替代 | 纯 Electron + WASM：AI 模型无法高效运行；纯 Python GUI（tkinter/PyQt）：开发体验差，跨平台 UI 弱 |
| HTTP + SSE 通信 | 同时支持 REST 简单调用和流式进度推送，无需引入 WebSocket 框架 | stdin/stdout JSON-RPC：不支持并发请求，进度流处理复杂；纯 polling：延迟高，CPU 开销大 |
| SQLite 作品库 | 支持 SQL 搜索、筛选、排序，500+ 条数据下性能好 | JSON 文件：查询需全量加载，无法高效筛选 |
| 激活码 + 一次联网激活 | 防止多设备共享，硬件绑定不可被简单绕过 | 纯本地验证（无服务器）：激活码可被逆向后批量生成 |
| React 19 + Tailwind CSS（前端） | 复用谷歌 AI 生成的初始项目（含所有页面骨架）；React 是训练数据最丰富的前端框架 | Vue 3 + Element Plus：重写已有页面浪费；从零搭建代价高 |
| Zustand（状态管理） | 极简 API 配合 React Hooks，AI 生成 store 代码无模板冗余；体积小 | Pinia（Vue Only）；Redux Toolkit：对单用户桌面应用过度复杂 |
| Wav2Lip（v1.0 口型同步） | 发布于 2020 年，成熟稳定，AI 代码生成质量高，集成文档完善 | MuseTalk（字节跳动，2024）：效果更好但过新，AI 生成代码质量低，踩坑风险高；规划为 v2.0 升级项 |
| Nuitka 编译 license 模块 | 将 Python 编译为原生 C 扩展，逆向难度远高于 PyInstaller 的 bytecode 打包 | PyArmor（免费版）：混淆质量有限，已有成熟破解工具；全量 Nuitka：编译耗时长，收益边际递减 |
