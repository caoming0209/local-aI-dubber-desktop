# IPC API Contract: 前端 ↔ Python 引擎

**Branch**: `001-ai-dubber-desktop` | **Date**: 2026-02-19

---

## 通信架构

- **协议**: HTTP/1.1，监听 `127.0.0.1:{random_port}`（端口由 Python 启动时随机选取，通过 stdout 输出给 Electron 主进程）
- **格式**: JSON（Content-Type: application/json）
- **进度推送**: Server-Sent Events（SSE），Content-Type: text/event-stream
- **认证**: 无（本地环回地址，仅本机可访问）
- **基础路径**: `http://127.0.0.1:{port}/api`

**最后更新**: 2026-02-19（补充：预加载 API 层定义、SSE 生命周期、作业状态查询、批量并发模型、数字人上传视频规格）

---

## 预加载 API 层（Preload API）

Electron 通过 `contextBridge` 向渲染进程暴露 `window.electronAPI` 对象。渲染进程**只能**通过此对象与主进程/后端通信，不得直接访问 Node.js 模块。

```typescript
// preload/index.ts 中暴露的 API 接口

window.electronAPI = {
  // ─── HTTP 请求代理 ───────────────────────────────────────────
  // 渲染进程通过此方法发起对 Python 引擎的 REST 请求
  engine: {
    request(method: 'GET'|'POST'|'PUT'|'PATCH'|'DELETE', path: string, body?: object): Promise<ApiResponse>,
  },

  // ─── SSE 进度订阅 ────────────────────────────────────────────
  // 订阅指定 job_id 的 SSE 进度流
  // onEvent: 每条 SSE data 回调；onDone: 流结束回调；onError: 错误回调
  // 返回 unsubscribe 函数
  pipeline: {
    subscribeProgress(jobId: string, onEvent: (data: object) => void, onDone: () => void, onError: (err: Error) => void): () => void,
  },

  // ─── 系统操作 ────────────────────────────────────────────────
  system: {
    openPath(path: string): Promise<void>,           // 用系统默认程序打开文件
    showItemInFolder(path: string): Promise<void>,   // 在资源管理器中显示
    selectDirectory(): Promise<string | null>,        // 打开目录选择对话框
    selectFile(filters: FileFilter[]): Promise<string | null>,  // 打开文件选择对话框
  },

  // ─── 引擎端口（只读） ────────────────────────────────────────
  getEnginePort(): number,
}
```

**安全约束**：
- 渲染进程中禁止 `require()`、`import` Node.js 内置模块
- `engine.request` 只转发到 `127.0.0.1:{port}`，不允许请求外部 URL
- `system` 方法中涉及文件路径的操作，主进程须校验路径在允许范围内（不允许遍历到系统目录）

---

## 启动握手

Python 进程启动后，向 stdout 输出一行 JSON：

```json
{"status": "ready", "port": 18432}
```

Electron 主进程读取此行后，将 `port` 存储并转发给渲染进程。

**Python 进程崩溃恢复策略**：

| 场景 | 行为 |
|------|------|
| 启动后 10 秒内未收到就绪信号 | 自动重启，最多 3 次；第 3 次失败后弹出错误对话框 |
| 运行中进程异常退出（exit code ≠ 0） | 自动重启（指数退避：1s、2s、4s），最多 3 次 |
| 3 次重启均失败 | 显示「推理引擎启动失败」对话框，提供「重新启动引擎」按钮；应用主窗口保持打开（不退出） |
| 用户主动关闭应用 | Electron 主进程向 Python 发送 SIGTERM，等待 3 秒后强制 kill |

进行中的生成任务在引擎崩溃后视为失败，不自动恢复；前端展示「生成失败，引擎意外退出」错误提示。

---

## 通用响应结构

### 成功响应
```json
{
  "success": true,
  "data": { ... }
}
```

### 错误响应
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "用户友好的错误描述"
  }
}
```

### 错误码

| code | 含义 |
|------|------|
| `MODEL_NOT_FOUND` | 所需模型未下载 |
| `MODEL_LOADING` | 模型正在加载中 |
| `INVALID_SCRIPT` | 文案不符合要求 |
| `GPU_UNAVAILABLE` | 请求 GPU 模式但不可用 |
| `INSUFFICIENT_DISK` | 磁盘空间不足 |
| `LICENSE_TRIAL_EXHAUSTED` | 试用次数耗尽 |
| `LICENSE_INVALID_CODE` | 激活码无效 |
| `LICENSE_DEVICE_LIMIT` | 设备绑定已达上限 |
| `LICENSE_NETWORK_ERROR` | 激活时网络不可用 |
| `NOT_FOUND` | 资源不存在 |
| `INTERNAL_ERROR` | 内部错误 |

---

## 视频生成流水线 API

### POST /api/pipeline/single
**说明**: 发起单条视频生成任务，返回 job_id，通过 SSE 跟踪进度。

**Request**:
```json
{
  "script": "大家好，今天给大家介绍...",
  "voice_id": "voice_male_steady_001",
  "voice_params": {
    "speed": 1.0,
    "volume": 1.0,
    "emotion": 0.5
  },
  "digital_human_id": "dh_female_host_001",
  "background": {
    "type": "solid_color",
    "value": "#F5F5F5"
  },
  "aspect_ratio": "9:16",
  "subtitle": {
    "enabled": true,
    "font_family": "Microsoft YaHei",
    "font_size": 30,
    "color": "#FFFFFF",
    "position": "bottom_center"
  },
  "bgm": {
    "enabled": false,
    "bgm_id": null,
    "custom_path": null,
    "voice_volume": 1.0,
    "bgm_volume": 0.5
  },
  "output_name": "my_video"
}
```

**Response** (202 Accepted):
```json
{
  "success": true,
  "data": {
    "job_id": "job_abc123",
    "estimated_steps": 4
  }
}
```

---

### GET /api/pipeline/progress/{job_id}
**说明**: SSE 端点，实时推送生成进度。

**SSE 连接生命周期**：
- 服务端在任务完成（`step: "completed"`）或失败（`step: "failed"`）后发送最后一条事件，然后**主动关闭连接**。
- 若 SSE 连接意外断开（网络抖动、前端页面切换），前端在 2 秒后自动调用 `GET /api/jobs/{job_id}/state` 查询当前状态，按需重新订阅或展示最终结果。
- 同一 `job_id` 可多次订阅（幂等），服务端在任务运行中可接受多个并发 SSE 客户端。
- 超时：若任务超过 30 分钟未完成，服务端发送 `{"step": "timeout"}` 事件并取消任务。

**Response** (text/event-stream):
```
data: {"step": "script_optimization", "step_index": 1, "total_steps": 4, "progress": 0.2, "message": "文案优化中..."}

data: {"step": "tts", "step_index": 2, "total_steps": 4, "progress": 0.4, "message": "语音合成中..."}

data: {"step": "lipsync", "step_index": 3, "total_steps": 4, "progress": 0.7, "message": "口型同步中..."}

data: {"step": "synthesis", "step_index": 4, "total_steps": 4, "progress": 0.9, "message": "视频合成中..."}

data: {"step": "completed", "step_index": 4, "total_steps": 4, "progress": 1.0, "message": "生成完成", "result": {"work_id": "work_xyz", "file_path": "C:/...", "duration_seconds": 45.2}}

data: {"step": "failed", "error": {"code": "MODEL_NOT_FOUND", "message": "语音模型未下载，请前往音色管理下载"}}
```

---

### GET /api/jobs/{job_id}/state
**说明**: 查询作业当前状态快照（用于 SSE 断连后的状态恢复）。作业状态仅保存在 Python 进程内存中，引擎重启后丢失。

**Response** (200):
```json
{
  "success": true,
  "data": {
    "job_id": "job_abc123",
    "status": "running",
    "current_step": "lipsync",
    "step_index": 3,
    "total_steps": 4,
    "progress": 0.65,
    "created_at": "2026-02-19T10:30:00Z"
  }
}
```

`status` 可选值：`pending` / `running` / `paused` / `completed` / `failed` / `cancelled` / `not_found`

`not_found` 表示引擎重启后状态已丢失，前端应展示「生成状态未知，请检查作品库」提示。

---

### POST /api/pipeline/pause/{job_id}
**说明**: 暂停正在执行的任务。

**Response** (200):
```json
{"success": true, "data": {"status": "paused"}}
```

### POST /api/pipeline/resume/{job_id}
**Response** (200):
```json
{"success": true, "data": {"status": "running"}}
```

### POST /api/pipeline/cancel/{job_id}
**说明**: 取消任务，清理临时文件，已生成视频不保留。

**Response** (200):
```json
{"success": true, "data": {"status": "cancelled"}}
```

---

### POST /api/pipeline/batch
**说明**: 发起批量生成任务。

**并发模型**：批量任务采用**严格串行执行**（每次只处理一条）。原因：Wav2Lip 推理在 CPU 模式下占用约 80% 内存，并行执行会触发 OOM；GPU 显存容量同样不支持并行推理。前端展示当前进度为"第 N 条 / 共 M 条"，用户可随时暂停或取消。

**Request**:
```json
{
  "scripts": [
    {"index": 0, "content": "第一条文案..."},
    {"index": 1, "content": "第二条文案..."}
  ],
  "shared_config": {
    "voice_id": "voice_female_warm_001",
    "voice_params": { "speed": 1.0, "volume": 1.0, "emotion": 0.5 },
    "digital_human_id": "dh_male_host_001",
    "background": { "type": "scene", "value": "office_001" },
    "aspect_ratio": "9:16",
    "subtitle": { "enabled": true, "font_family": "Microsoft YaHei", "font_size": 30, "color": "#FFFFFF", "position": "bottom_center" },
    "bgm": { "enabled": false }
  },
  "output_settings": {
    "save_path": "C:/Users/.../批量视频",
    "name_prefix": "视频"
  }
}
```

**Response** (202):
```json
{
  "success": true,
  "data": {
    "job_id": "batch_job_001",
    "total_count": 50
  }
}
```

**SSE 进度格式** (GET /api/pipeline/progress/{job_id}):
```
data: {"type": "batch_item_start", "item_index": 2, "total": 50, "message": "正在生成第 3 条 / 共 50 条"}

data: {"type": "batch_item_progress", "item_index": 2, "step": "tts", "progress": 0.4}

data: {"type": "batch_item_done", "item_index": 2, "work_id": "work_abc"}

data: {"type": "batch_item_failed", "item_index": 5, "error": {"code": "INVALID_SCRIPT", "message": "文案少于 10 字"}}

data: {"type": "batch_completed", "total": 50, "succeeded": 48, "failed": 2, "failed_indices": [5, 23]}
```

---

## 作品库 API

### GET /api/works
**Query 参数**:
- `search` (string): 搜索名称或日期（如 "2026-02-19"）
- `aspect_ratio` ("16:9" | "9:16"): 筛选
- `date_range` ("today" | "yesterday" | "last_7_days" | "custom"): 筛选
- `date_from` / `date_to` (ISO8601 date string): 自定义日期范围
- `sort` ("created_at_desc" | "created_at_asc" | "duration"): 默认 created_at_desc
- `page` (int, 默认 1): 分页
- `page_size` (int, 默认 12): 每页条数

**Response**:
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "work_xyz",
        "name": "我的第一条视频",
        "file_path": "C:/...",
        "thumbnail_path": "C:/.../.thumbs/work_xyz.jpg",
        "duration_seconds": 45.2,
        "resolution": "1080P",
        "aspect_ratio": "9:16",
        "file_size_bytes": 52428800,
        "created_at": "2026-02-19T10:30:00Z",
        "is_trial_watermark": false
      }
    ],
    "total": 128,
    "page": 1,
    "page_size": 12,
    "total_pages": 11
  }
}
```

### GET /api/works/{id}
返回单条作品详情，含 `project_config`（完整配置快照，用于重新编辑）。

### PATCH /api/works/{id}
**Request**: `{"name": "新名称"}`（仅支持 name 修改）

### DELETE /api/works/{id}
删除记录并删除本地 MP4 + 封面图文件。

### DELETE /api/works (批量)
**Request**: `{"ids": ["work_1", "work_2"]}`

### DELETE /api/works/all
清空所有作品（含本地文件）。需额外确认参数：`{"confirm": true}`

---

## 数字人 API

### GET /api/digital-humans
**Query**: `search` (string), `source` ("official" | "custom"), `category`

### POST /api/digital-humans/upload
**Content-Type**: multipart/form-data
- `file`: 视频文件（≤ 500MB）

**上传视频技术要求**（Wav2Lip 口型适配前提）：

| 参数 | 用户可见限制 | 内部预处理 | 说明 |
|------|------------|-----------|------|
| 容器格式 | MP4、MOV、AVI、MKV | FFmpeg 统一转为 MP4 | Wav2Lip 通过 FFmpeg 解码，支持所有 FFmpeg 可解码格式 |
| 视频编码 | 不限（H.264/H.265/VP9/AV1 等） | FFmpeg 统一转为 H.264 (AVC) | 用户无需关心编码格式 |
| 分辨率 | 360P – 4K | 超过 1080P 自动缩放至 1080P | 低于 360P 人脸检测成功率下降；Wav2Lip 内部处理 96×96 人脸裁剪 |
| 帧率 | 不限 | FFmpeg 统一转为 25fps | Wav2Lip 对帧率无硬性要求 |
| 时长 | 3 – 300 秒 | 超过 120 秒提示处理较慢 | 过短（<3s）口型不自然；过长受 GPU 显存限制 |
| 人脸要求 | 单人正脸或不超过 ±30° 侧脸 | s3fd 人脸检测预验证 | Wav2Lip 对大侧脸角度效果差 |
| 音轨 | 不限（有无均可） | 自动去除音轨 | 数字人素材不需要原始音频 |
| 文件大小 | ≤ 500 MB | 转码后通常远小于原始 | 超出拒绝上传并提示压缩 |

**预处理流程**：上传 → 格式/大小校验 → FFmpeg 预处理（转码 H.264 + 缩放 ≤1080P + 25fps + 去音轨）→ 人脸检测预验证 → 通过后进入适配队列。预验证失败返回 400 错误，不进入适配队列。

**Response** (202):
```json
{
  "success": true,
  "data": {"job_id": "adapt_job_001", "digital_human_id": "dh_custom_001"}
}
```
适配进度通过 SSE: GET /api/digital-humans/adapt-progress/{job_id}

### PATCH /api/digital-humans/{id}
**Request**: `{"name": "我的专属形象", "category": "female_host"}`（自定义数字人可编辑）

### POST /api/digital-humans/{id}/favorite
切换收藏状态。**Response**: `{"is_favorited": true}`

### POST /api/digital-humans/{id}/re-adapt
重新执行口型适配。

### DELETE /api/digital-humans/{id}
仅限自定义数字人。同步删除适配视频文件。

---

## 音色 API

### GET /api/voices
**Query**: `search`, `category` ("male"|"female"|"emotional"|"dialect"), `download_status`

### POST /api/voices/{id}/favorite
切换收藏状态。

### POST /api/voices/{id}/download
触发模型下载，通过 SSE 跟踪: GET /api/voices/{id}/download-progress

**SSE 格式**:
```
data: {"progress": 0.35, "downloaded_mb": 120.5, "total_mb": 344.2, "speed_kbps": 1024, "eta_seconds": 218}

data: {"progress": 1.0, "status": "completed"}

data: {"status": "error", "message": "下载失败，请检查网络连接"}
```

### POST /api/voices/{id}/download/pause
### POST /api/voices/{id}/download/resume

### DELETE /api/voices/{id}/model
删除已下载模型文件，保留数据库记录（状态改为 not_downloaded）。

### POST /api/voices/{id}/preview
实时合成预览音频。

**Request**: `{"text": "大家好，欢迎使用智影口播助手", "speed": 1.0, "volume": 1.0, "emotion": 0.5}`
**Response**: audio/wav 二进制流（或 Base64 编码 JSON）

---

## 系统与设置 API

### GET /api/settings
返回完整 AppSettings 对象。

### PUT /api/settings
**Request**: 完整或部分 AppSettings 对象（合并更新）。

### GET /api/system/hardware
```json
{
  "success": true,
  "data": {
    "cpu": "Intel Core i7-10700K",
    "memory_gb": 16,
    "gpu": "NVIDIA GeForce RTX 3060",
    "gpu_vram_gb": 12,
    "disk_free_gb": 245.3,
    "os": "Windows 11 Pro 64-bit"
  }
}
```

### POST /api/system/gpu-check
检测 GPU 是否支持推理（≤ 10 秒）。
```json
{
  "success": true,
  "data": {
    "gpu_available": true,
    "cuda_version": "11.8",
    "recommendation": "compatible"
  }
}
```

### GET /api/system/cache-info
```json
{"success": true, "data": {"size_mb": 212.4}}
```

### DELETE /api/system/cache
清理临时缓存，不影响作品和模型。

### GET /api/system/version
```json
{"success": true, "data": {"current": "1.0.0", "latest": null, "update_available": false}}
```

### POST /api/system/check-update
实时检查更新，返回同上结构。
