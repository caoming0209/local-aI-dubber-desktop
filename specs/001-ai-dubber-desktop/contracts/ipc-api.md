# IPC API Contract: 前端 ↔ Python 引擎

**Branch**: `001-ai-dubber-desktop` | **Date**: 2026-02-19

---

## 通信架构

- **协议**: HTTP/1.1，监听 `127.0.0.1:{random_port}`（端口由 Python 启动时随机选取，通过 stdout 输出给 Electron 主进程）
- **格式**: JSON（Content-Type: application/json）
- **进度推送**: Server-Sent Events（SSE），Content-Type: text/event-stream
- **认证**: 无（本地环回地址，仅本机可访问）
- **基础路径**: `http://127.0.0.1:{port}/api`

---

## 启动握手

Python 进程启动后，向 stdout 输出一行 JSON：

```json
{"status": "ready", "port": 18432}
```

Electron 主进程读取此行后，将 `port` 存储并转发给渲染进程。

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
- `file`: MP4 文件（≤ 100MB）

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
