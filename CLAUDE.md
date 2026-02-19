# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

**智影口播 · AI数字人视频助手** — Windows 桌面客户端，输入文字即可在本地离线生成高清数字人口播视频。

产品名称：AI数字人口播桌面客户端
目标平台：Windows 10/11（64位），以 .exe 安装包分发

## 技术栈

| 层 | 技术 | 版本 |
|----|------|------|
| 前端框架 | Electron + React 19 + TypeScript | Electron 40+, React 19.2 |
| 样式 | Tailwind CSS（npm 包，非 CDN） | 4.x |
| 状态管理 | Zustand | 5.x |
| 路由 | React Router v7（HashRouter） | 7.x |
| 图标 | Lucide React | 最新 |
| 构建 | Vite 6 | 6.x |
| 核心引擎 | Python 3.11 + FastAPI + uvicorn | |
| 口型同步 | Wav2Lip（v1.0）→ MuseTalk（v2.0 路线图） | |
| 语音合成 | CosyVoice 2（主）、MB-iSTFT-VITS2（低配备选） | |
| 视频合成 | FFmpeg（ffmpeg-python 封装） | 6.x+ |
| 存储 | SQLite（stdlib sqlite3，无 ORM）+ JSON 文件 | |
| 打包 | electron-builder（前端）+ PyInstaller（Python）+ Nuitka（仅 license 模块） | |
| 测试 | Vitest + React Testing Library（前端）、pytest（后端）、Playwright（E2E） | |

## 架构

应用采用双进程架构：
1. **Electron + React 19 前端** — UI 层，左侧固定菜单 + 右侧内容区布局；前端基于谷歌 AI 生成的初始项目（`D:\Git.Project\智影口播-·-ai数字人视频助手\`）继续开发
2. **Python 后端** — 本地推理引擎，负责 TTS（CosyVoice 2）、口型同步（Wav2Lip）和 FFmpeg 视频合成

### IPC 通信模式

- **协议**: HTTP/1.1，绑定 `127.0.0.1:{random_port}`（不触发 Windows 防火墙）
- **一次性调用**（CRUD、设置读写、状态查询）：标准 HTTP REST
- **长任务进度流**（TTS、口型同步、视频合成）：SSE（Server-Sent Events）单向推送
- **启动握手**: Python 进程启动后向 stdout 输出 `{"status": "ready", "port": 18432}`，Electron 读取后切换至 HTTP 通信
- **崩溃恢复**: 启动 10s 内无就绪信号或运行中异常退出，自动重启（指数退避），最多 3 次

### 核心流水线（全程本地离线，不依赖云端）

```
文案输入 → 文案优化（自动断句、口语化改写）
    → TTS 模型（CosyVoice 2，生成 WAV 24kHz → FFmpeg 重采样 16kHz）
    → Wav2Lip（语音与数字人视频口型同步）
    → FFmpeg（合成背景、字幕、BGM）
    → 输出 MP4 → 同步至作品库
```

### 9 大功能模块

1. **首页** — 快速入口（新建视频/批量制作/查看作品）、最近 3 条记录、教程引导
2. **单条制作** — 5 步向导：文案输入 → 语音选择 → 数字人选择 → 视频设置 → 生成视频
3. **批量制作** — 导入 TXT 或多行输入（最多 100 条文案），统一配置后串行批量生成
4. **数字人管理** — 官方数字人 + 自定义 MP4 上传（自动 Wav2Lip 适配）
5. **音色管理** — 音色浏览、试听、收藏、模型下载（支持暂停/继续）与删除
6. **作品库** — 卡片式展示（每页 12 条），支持搜索/筛选/排序、播放、重新编辑、批量删除
7. **设置** — 路径配置、推理模式（CPU/GPU/自动）、缓存清理、更新、硬件信息、主题切换、授权管理
8. **帮助与反馈** — 分类教程、FAQ（支持搜索）、客服入口
9. **授权与激活** — 试用 5 次（带水印）→ 激活码一次联网验证 → 正式版（无水印/无限制/完全离线）

### 关键技术约束

- 全程本地离线运行，不涉及云端上传/存储（仅激活和模型下载需联网）
- 模型首次使用时下载，存储路径可由用户自定义
- GPU 加速通过 CUDA 11.8 实现，可选（无 GPU 时回退到 CPU 推理）
- 最低配置：i5 CPU、8GB 内存、5GB 磁盘空间；推荐配置：i7+、16GB 内存、NVIDIA 显卡（显存 ≥ 4GB）
- 默认视频输出分辨率 1080P，不可修改（保证口型同步质量）
- 批量任务严格串行执行（内存/显存限制，不支持并行推理）

## 项目目录结构

```text
electron-app/                        # Electron 主进程壳
├── src/
│   ├── main/
│   │   ├── index.ts                 # 入口：窗口管理、Python 子进程启动
│   │   ├── python-manager.ts        # Python 进程生命周期管理
│   │   └── ipc-bridge.ts            # 主进程 IPC 路由
│   └── preload/
│       └── index.ts                 # 安全沙箱：暴露 window.electronAPI
├── package.json
└── electron-builder.yml

renderer/                            # React 19 渲染进程（基于 AI 生成初始项目）
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
│   │   ├── Home.tsx, SingleCreation.tsx, BatchCreation.tsx
│   │   ├── AvatarManager.tsx, VoiceManager.tsx
│   │   ├── WorksLibrary.tsx, Settings.tsx, Help.tsx
│   ├── stores/                      # Zustand 状态管理（待实现）
│   │   ├── project.ts, works.ts, license.ts, settings.ts
│   └── services/                    # HTTP API 调用封装（待实现）
│       ├── engine.ts, pipeline.ts, license.ts
├── index.html
├── vite.config.ts
└── package.json

python-engine/                       # Python 推理引擎
├── src/
│   ├── api/
│   │   ├── server.py                # FastAPI 入口（随机端口，stdout 输出端口号）
│   │   └── routes/                  # pipeline, tts, lipsync, synthesis, works, models, license, system
│   ├── core/
│   │   ├── tts_engine.py            # CosyVoice 2 / VITS 封装
│   │   ├── lipsync_engine.py        # Wav2Lip 封装
│   │   ├── video_synthesizer.py     # FFmpeg 流水线
│   │   ├── model_manager.py         # 模型下载、校验、删除
│   │   └── gpu_detector.py          # CUDA 检测
│   ├── storage/
│   │   ├── database.py              # SQLite 连接与 PRAGMA user_version 迁移
│   │   ├── works_repo.py            # 作品库数据访问
│   │   ├── settings_store.py        # JSON 设置读写
│   │   └── migrations/              # V{NNN}__description.sql 迁移脚本
│   ├── license/
│   │   ├── fingerprint.py           # 硬件指纹（CPU+主板+硬盘 SHA-256）
│   │   ├── validator.py             # 激活码验证（本地 + 远程）
│   │   └── store.py                 # AES-256-GCM 加密存储
│   └── utils/
│       ├── progress.py              # SSE 进度事件生成器
│       └── file_utils.py            # 路径、缩略图工具
├── tests/
└── requirements.txt

shared/                              # 前后端共享类型定义
└── ipc-types.ts                     # IPC 请求/响应 TypeScript 类型

specs/001-ai-dubber-desktop/         # 设计文档
├── spec.md                          # 产品规格（用户故事、功能需求、验收条件）
├── plan.md                          # 实现计划（架构决策、项目结构）
├── research.md                      # 技术选型研究（IPC、TTS、存储、授权等）
├── data-model.md                    # 数据模型定义
├── quickstart.md                    # 开发环境搭建指南
└── contracts/
    ├── ipc-api.md                   # 前端↔后端 HTTP IPC 接口定义
    └── license.md                   # 授权激活接口定义
```

## 数据模型

### 存储层

| 存储层 | 内容 | 位置 |
|--------|------|------|
| SQLite DB | 作品库、项目配置快照、数字人、音色、BGM | `{userDataDir}/dubber.db` |
| JSON 文件 | 应用设置 | `{userDataDir}/settings.json` |
| 加密文件 | 授权状态 | `{userDataDir}/license.dat`（AES-256-GCM，密钥由设备指纹派生） |
| 本地文件系统 | MP4 视频、模型文件、封面图、BGM 音频 | 用户可自定义路径 |

### SQLite 核心表

- **`works`** — 已生成视频记录（id, name, file_path, thumbnail_path, duration_seconds, resolution, aspect_ratio, file_size_bytes, created_at, project_config_id FK, is_trial_watermark）
- **`project_configs`** — 制作配置快照，用于「重新编辑」（script, voice_id, voice_speed/volume/emotion, digital_human_id, background_type/value, aspect_ratio, subtitle_enabled/config JSON, bgm 相关字段）
- **`digital_humans`** — 数字人（name, category, source[official/custom], thumbnail_path, preview_video_path, adapted_video_path, adaptation_status[ready/processing/failed/pending], is_favorited）
- **`voice_models`** — 音色（name, category[male/female/emotional/dialect], model_size_mb, download_status[not_downloaded/downloading/downloaded/error], model_path, download_url, is_emotional, is_favorited）
- **`bgm_tracks`** — BGM（name, category[upbeat/soothing/grand], source[builtin/custom], file_path）

### JSON 配置

```typescript
interface AppSettings {
  autoStartOnBoot: boolean;           // 默认 false
  defaultVideoSavePath: string;       // 默认 ~/Documents/智影口播/作品
  theme: "light" | "dark";           // 默认 "light"
  language: "zh-CN";
  modelStoragePath: string;           // 默认 ~/Documents/智影口播/models
  downloadSpeedLimitKBps: number;     // 0 = 无限制
  autoDownloadModels: boolean;        // 默认 true
  inferenceMode: "auto" | "cpu" | "gpu";  // 默认 "auto"
  cpuUsageLimitPercent: number;           // 0 = 无限制
  autoClearCacheEnabled: boolean;     // 默认 false
  autoClearCycleDays: number;         // 7 / 30
  autoCheckUpdate: boolean;           // 默认 true
  updatedAt: string;                  // ISO8601
}
```

### 授权状态（license.dat 解密后）

```typescript
interface LicenseState {
  type: "trial" | "activated";
  usedTrialCount: number;            // 最大 5
  activationCode?: string;           // 部分隐藏显示
  activatedAt?: string;
  deviceFingerprint: string;         // SHA-256(CPU_ID|主板UUID|硬盘序列号)
}
```

### 数据访问规则

- SQLite 通过 Python 后端访问，前端不直接读写数据库
- settings.json 和 license.dat 由 Python 后端独占读写
- 所有 `*_path` 字段存储绝对路径
- 删除联动：删除作品→删除 MP4+封面图；删除自定义数字人→删除适配视频；删除音色模型→仅删文件，保留记录（状态改 not_downloaded）
- Schema 迁移：`PRAGMA user_version` + `migrations/V{NNN}__desc.sql` 脚本按序执行

### 模型文件完整性校验

- 每个模型目录下 `checksums.json` 存储 SHA-256 哈希
- 下载完成后立即校验；启动时快速校验（前 4KB 哈希，< 200ms）；推理前完整校验
- 校验失败错误码：`MODEL_CORRUPTED`、`MODEL_DOWNLOAD_INCOMPLETE`

## IPC API 概览

基础路径：`http://127.0.0.1:{port}/api`，JSON 格式，无认证。

### Preload API（渲染进程可用）

渲染进程通过 `window.electronAPI` 访问：
- `engine.request(method, path, body?)` — HTTP 请求代理
- `pipeline.subscribeProgress(jobId, onEvent, onDone, onError)` — SSE 进度订阅
- `system.openPath/showItemInFolder/selectDirectory/selectFile` — 系统操作
- `getEnginePort()` — 获取引擎端口

### 视频生成

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/pipeline/single` | POST | 单条生成，返回 job_id（202） |
| `/api/pipeline/batch` | POST | 批量生成，串行执行（202） |
| `/api/pipeline/progress/{job_id}` | GET | SSE 进度流 |
| `/api/jobs/{job_id}/state` | GET | 作业状态快照（SSE 断连恢复用） |
| `/api/pipeline/pause/{job_id}` | POST | 暂停 |
| `/api/pipeline/resume/{job_id}` | POST | 继续 |
| `/api/pipeline/cancel/{job_id}` | POST | 取消 |

### 作品库

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/works` | GET | 列表（支持 search/aspect_ratio/date_range/sort/page） |
| `/api/works/{id}` | GET | 详情（含 project_config） |
| `/api/works/{id}` | PATCH | 重命名 |
| `/api/works/{id}` | DELETE | 删除（含本地文件） |
| `/api/works` | DELETE | 批量删除（body: ids 数组） |
| `/api/works/all` | DELETE | 清空（需 confirm:true） |

### 数字人

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/digital-humans` | GET | 列表（search/source/category） |
| `/api/digital-humans/upload` | POST | 上传 MP4（multipart，≤100MB）→ 自动适配 |
| `/api/digital-humans/{id}` | PATCH | 编辑名称/分类 |
| `/api/digital-humans/{id}/favorite` | POST | 切换收藏 |
| `/api/digital-humans/{id}/re-adapt` | POST | 重新适配 |
| `/api/digital-humans/{id}` | DELETE | 删除（仅自定义） |

### 音色

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/voices` | GET | 列表（search/category/download_status） |
| `/api/voices/{id}/favorite` | POST | 切换收藏 |
| `/api/voices/{id}/download` | POST | 触发下载 |
| `/api/voices/{id}/download/pause` | POST | 暂停下载 |
| `/api/voices/{id}/download/resume` | POST | 继续下载 |
| `/api/voices/{id}/model` | DELETE | 删除模型文件 |
| `/api/voices/{id}/preview` | POST | 合成预览音频 |

### 授权

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/license/status` | GET | 当前授权状态 |
| `/api/license/activate` | POST | 激活码验证（联网） |
| `/api/license/unbind` | POST | 解绑当前设备（联网） |
| `/api/license/consume-trial` | POST | 扣减试用次数（内部调用） |

### 系统与设置

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/settings` | GET/PUT | 读取/更新设置 |
| `/api/system/hardware` | GET | 硬件信息 |
| `/api/system/gpu-check` | POST | GPU 兼容性检测 |
| `/api/system/cache-info` | GET | 缓存大小 |
| `/api/system/cache` | DELETE | 清理缓存 |
| `/api/system/version` | GET | 版本信息 |
| `/api/system/check-update` | POST | 检查更新 |

### 通用错误码

`MODEL_NOT_FOUND` / `MODEL_LOADING` / `MODEL_CORRUPTED` / `MODEL_DOWNLOAD_INCOMPLETE` / `INVALID_SCRIPT` / `GPU_UNAVAILABLE` / `INSUFFICIENT_DISK` / `LICENSE_TRIAL_EXHAUSTED` / `LICENSE_INVALID_CODE` / `LICENSE_DEVICE_LIMIT` / `LICENSE_NETWORK_ERROR` / `NOT_FOUND` / `INTERNAL_ERROR`

## 关键设计决策

| 决策 | 选型 | 核心理由 |
|------|------|----------|
| IPC 通信 | FastAPI HTTP + SSE | 一次性调用与进度流分离；绑定 127.0.0.1 无防火墙问题；可 curl 调试 |
| 中文 TTS | CosyVoice 2 + VITS 备选 | 中文质量最优；Instruct 情感控制；纯 PyTorch 无框架冲突 |
| 存储 | SQLite + JSON config blob | 索引查询满足搜索筛选；无 ORM；config blob 简化重编辑 |
| 授权 | 一次联网激活 + AES-256-GCM + 硬件指纹 | 服务端强制设备限制（每码 2 台）；机器绑定防文件复制；激活后永久离线 |
| 前端 | React 19 + Tailwind + Zustand | 复用 AI 生成初始项目；React 训练数据最丰富；Tailwind 无组件库学习成本 |
| 口型同步 | Wav2Lip（v1.0）→ MuseTalk（v2.0） | Wav2Lip 成熟稳定，AI 代码生成质量高；MuseTalk 效果更自然但过新 |
| 打包保护 | electron-builder + PyInstaller + Nuitka（license 模块） | license 模块原生编译防逆向；目标防御普通用户分享激活码 |

## 开发环境

### 前置条件

Node.js 20 LTS、Python 3.11、Git、FFmpeg 6.x+（需在 PATH）、CUDA Toolkit 11.8（可选）

### 启动方式

```bash
# 终端 1 — Python 引擎
cd python-engine && .venv/Scripts/activate && python src/api/server.py

# 终端 2 — Electron 前端
cd electron-app && npm run dev
```

### 关键脚本

| 脚本 | 说明 |
|------|------|
| renderer: `npm run dev` | Vite dev server 浏览器预览 |
| electron-app: `npm run dev` | Electron + Vite（自动连接 Python 引擎） |
| electron-app: `npm run build:win` | electron-builder 打包 Windows NSIS |
| renderer: `npm run test:unit` | Vitest 单元测试 |
| electron-app: `npm run test:e2e` | Playwright E2E 测试 |
| python-engine: `pytest tests/` | 后端测试 |

### 开发模式特殊行为

- `NODE_ENV=development` 时授权检查跳过，无限制生成，不添加水印
- Python 引擎支持 `--reload` 热重载
- Tailwind CDN 已迁移为 npm 包（Electron 离线环境必须）

## 性能目标

- 单条视频操作响应 ≤ 1s
- SSE 进度更新推送延迟 ≤ 200ms
- 作品库 500 条搜索 ≤ 1s
- 应用启动至可操作 ≤ 10s
- 激活验证 ≤ 5s
- GPU 兼容性检测 ≤ 10s
