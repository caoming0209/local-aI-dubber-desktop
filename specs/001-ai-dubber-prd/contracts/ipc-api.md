# IPC API Contract (Local Engine)

Base URL: `http://127.0.0.1:{port}/api`

## Transport

- REST for request/response calls
- SSE for progress streaming
- Engine binds **only** to `127.0.0.1:{random_port}`
- Engine readiness handshake via stdout JSON: `{"status":"ready","port":18432}`

## Content types

- REST: `application/json`
- SSE: `text/event-stream`

## Endpoints

### Pipeline

#### POST `/pipeline/single`

Start a single generation job.

**Request**

```json
{
  "script_text": "...",
  "resolution": "1080p",
  "avatar_image_path": "C:\\...\\avatar.png",
  "voice_template_id": "vt_...",
  "voice_params": {"speed": 1.0, "volume": 1.0, "style": "neutral_natural"},
  "subtitle": {"external_srt": true, "burned_in": true},
  "output_dir": "C:\\...\\Outputs"
}
```

**Response**: `202 Accepted`

```json
{"job_id": "job_..."}
```

#### POST `/pipeline/batch`

Start a batch job (serial execution).

**Request**

```json
{
  "items": [{"script_text": "..."}],
  "common_config": {
    "resolution": "1080p",
    "avatar_image_path": "C:\\...\\avatar.png",
    "voice_template_id": "vt_...",
    "voice_params": {"speed": 1.0, "volume": 1.0, "style": "neutral_natural"},
    "subtitle": {"external_srt": true, "burned_in": true},
    "output_dir": "C:\\...\\Outputs"
  }
}
```

**Response**: `202 Accepted`

```json
{"job_id": "batch_..."}
```

#### GET `/pipeline/progress/{job_id}` (SSE)

SSE event stream.

Event schema (example):

```json
{
  "job_id": "job_...",
  "stage": "tts",
  "progress": 42,
  "message": "Generating audio",
  "resource": {"cpu": 45, "mem": 62, "vram": "N/A"}
}
```

#### GET `/jobs/{job_id}/state`

Return job snapshot for reconnection/resume UI.

#### GET `/jobs?status={status_list}`

Return jobs matching given statuses (comma-separated). Used by UI on startup to detect unfinished batch jobs for resume prompt.

**Query Parameters**

- `status` (required): Comma-separated status values, e.g. `running,paused`

**Response**: `200`

```json
[
  {
    "job_id": "batch_...",
    "type": "batch",
    "status": "running",
    "cursor_index": 5,
    "total_items": 30,
    "created_at": "2026-02-24T10:00:00Z"
  }
]
```

### Pipeline control

- POST `/pipeline/pause/{job_id}`
- POST `/pipeline/resume/{job_id}`
- POST `/pipeline/cancel/{job_id}`

## Errors

All errors return JSON with an `error_code` and human-friendly `message`.

Example:

```json
{"error_code": "INVALID_SCRIPT", "message": "Script is empty"}
```

### Error codes

- `INVALID_SCRIPT` — 文案为空或不合规
- `INVALID_IMAGE_FORMAT` — 图片格式不支持（仅 jpg/png）
- `IMAGE_TOO_SMALL` — 图片分辨率不足
- `RESOURCE_CRITICAL` — 资源压力达到危险阈值，附带降级建议
- `MODEL_NOT_FOUND` / `MODEL_LOADING` / `MODEL_CORRUPTED` / `MODEL_DOWNLOAD_INCOMPLETE`
- `GPU_UNAVAILABLE` / `INSUFFICIENT_DISK`
- `NOT_FOUND` / `INTERNAL_ERROR`
