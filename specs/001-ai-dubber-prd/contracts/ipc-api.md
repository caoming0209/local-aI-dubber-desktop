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
- File upload: `multipart/form-data`

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

**Validation**:
- `script_text`: non-empty, ≤ 3000 characters (FR-020a)
- `avatar_image_path`: must be jpg/png, minimum 256×256
- `voice_params.style`: must be one of: `neutral_natural` (default), `gentle`, `cheerful`, `serious`, `sad`, `angry` (FR-033c)
- Rejects with `JOB_ALREADY_RUNNING` if any job is currently `running` or `paused` (FR-085)

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

**Validation**:
- `items`: ≤ 30 items (FR-071); if >30 items submitted, rejects with `BATCH_LIMIT_EXCEEDED` (frontend SHOULD truncate to 30 before sending; backend enforces as safety net)
- Each item `script_text`: non-empty, ≤ 3000 characters (FR-020a)
- Rejects with `JOB_ALREADY_RUNNING` if any job is currently `running` or `paused` (FR-085)

#### GET `/pipeline/progress/{job_id}` (SSE)

SSE event stream. Uses named SSE event types for client parsing.

**Event types**:
- `event: progress` — Stage progress update (includes resource data)
- `event: resource` — Independent resource heartbeat (sent at ≤2s intervals when no progress event fires, ensuring FR-080 compliance)
- `event: complete` — Job finished (succeeded/failed/canceled)
- `event: error` — Unrecoverable error

**Resource heartbeat guarantee**: The server MUST emit either a `progress` or `resource` event at least once every 2 seconds during job execution, regardless of pipeline stage advancement (Constitution IV compliance).

Progress event schema:

```json
{
  "job_id": "job_...",
  "stage": "tts",
  "progress": 42,
  "message": "Generating audio",
  "resource": {"cpu": 45, "mem": 62, "vram": "N/A"}
}
```

Resource heartbeat event schema (sent when no progress event in 2s):

```json
{
  "job_id": "job_...",
  "resource": {"cpu": 45, "mem": 62, "vram": "N/A"}
}
```

For batch jobs, additional fields:

```json
{
  "job_id": "batch_...",
  "current_item_index": 2,
  "total_items": 10,
  "item_status": "running",
  "stage": "lipsync",
  "progress": 65,
  "message": "Processing item 3/10: lip sync",
  "resource": {"cpu": 78, "mem": 71, "vram": 82}
}
```

### Jobs

#### GET `/jobs/{job_id}/state`

Return job snapshot for reconnection/resume UI.

**Response**: `200`

For single jobs:

```json
{
  "job_id": "job_...",
  "type": "single",
  "status": "running",
  "stage": "tts",
  "progress": 42,
  "started_at": "2026-02-28T10:00:00Z",
  "output_video_path": null
}
```

For batch jobs:

```json
{
  "job_id": "batch_...",
  "type": "batch",
  "status": "running",
  "cursor_index": 5,
  "total_items": 30,
  "items": [
    {"item_id": "...", "index": 0, "status": "succeeded"},
    {"item_id": "...", "index": 1, "status": "failed", "failure_reason": {"error_code": "...", "error_message": "..."}},
    {"item_id": "...", "index": 2, "status": "running"}
  ],
  "created_at": "2026-02-28T10:00:00Z"
}
```

#### GET `/jobs?status={status_list}`

Return jobs matching given statuses (comma-separated). Used by UI on startup to detect unfinished batch jobs for resume prompt, and by Home page for recent completed jobs.

**Query Parameters**

- `status` (required): Comma-separated status values, e.g. `running,paused` or `succeeded`
- `limit` (optional): Maximum number of results to return (default: 50)
- `sort` (optional): Sort order, `desc` (default, newest first) or `asc`

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

### Settings

#### GET `/settings`

Return current application settings.

**Response**: `200`

```json
{
  "inferenceMode": "auto",
  "defaultVideoSavePath": "C:\\Users\\...\\Documents\\智影口播\\作品",
  "modelStoragePath": "C:\\Users\\...\\Documents\\智影口播\\models",
  "theme": "light",
  "language": "zh-CN"
}
```

#### PUT `/settings`

Update application settings (partial update).

**Request**

```json
{"inferenceMode": "gpu"}
```

**Response**: `200` — Returns updated settings object.

### Pipeline control

- POST `/pipeline/pause/{job_id}` — Pause a running job
- POST `/pipeline/resume/{job_id}` — Resume a paused job
- POST `/pipeline/cancel/{job_id}` — Cancel a job (requires frontend confirm before calling)

### Voice Templates (FR-030 ~ FR-034)

#### GET `/voice-templates`

List all voice templates.

**Query Parameters**

- `status` (optional): Filter by status, e.g. `ready`

**Response**: `200`

```json
[
  {
    "id": "vt_...",
    "name": "My Voice",
    "created_at": "2026-02-28T10:00:00Z",
    "source_audio_duration_seconds": 45.2,
    "format": "wav",
    "status": "ready"
  }
]
```

#### POST `/voice-templates/upload`

Upload audio file and start voice feature extraction.

**Request**: `multipart/form-data`

- `audio` (file, required): MP3 or WAV, ≥30s duration, ≤100MB
- `name` (string, required): Template display name

**Response**: `202 Accepted`

```json
{
  "id": "vt_...",
  "name": "My Voice",
  "status": "processing"
}
```

**Validation errors**:

- `VOICE_INVALID_FORMAT` — Not MP3 or WAV
- `VOICE_TOO_SHORT` — Duration < 30 seconds
- `VOICE_TOO_LARGE` — File size > 100MB
- `VOICE_NAME_EMPTY` — Name is empty after trimming
- `VOICE_NAME_DUPLICATE` — Name already exists (FR-032a)

#### GET `/voice-templates/{id}/progress` (SSE)

SSE stream for voice extraction progress.

```json
{
  "template_id": "vt_...",
  "progress": 65,
  "message": "Extracting voice features..."
}
```

Terminal event:

```json
{
  "template_id": "vt_...",
  "progress": 100,
  "status": "ready",
  "message": "Voice template ready"
}
```

Or on failure:

```json
{
  "template_id": "vt_...",
  "progress": 0,
  "status": "failed",
  "error_code": "VOICE_EXTRACTION_FAILED",
  "message": "Failed to extract voice features"
}
```

#### DELETE `/voice-templates/{id}`

Delete a voice template (hard delete, not recoverable).

**Response**: `204 No Content`

**Errors**:

- `NOT_FOUND` — Template does not exist

### Batch Item Retry (FR-075)

#### POST `/pipeline/batch/{batch_id}/retry/{item_id}`

Retry a single failed item within a batch job.

**Response**: `202 Accepted`

```json
{"message": "Retrying item", "item_id": "..."}
```

**Errors**:

- `NOT_FOUND` — Batch or item not found
- `INVALID_STATE` — Item is not in `failed` status

## Errors

All errors return JSON with an `error_code` and human-friendly `message`.

Example:

```json
{"error_code": "INVALID_SCRIPT", "message": "Script is empty"}
```

### Error codes

Pipeline & input:
- `INVALID_SCRIPT` — Script is empty or invalid
- `SCRIPT_TOO_LONG` — Script exceeds 3000 characters (FR-020a)
- `INVALID_IMAGE_FORMAT` — Image format not supported (only jpg/png)
- `IMAGE_TOO_SMALL` — Image resolution too low
- `JOB_ALREADY_RUNNING` — A generation job is already running or paused (FR-085)

Voice templates:
- `VOICE_INVALID_FORMAT` — Audio format not MP3 or WAV
- `VOICE_TOO_SHORT` — Audio duration < 30 seconds
- `VOICE_TOO_LARGE` — Audio file > 100MB
- `VOICE_NAME_EMPTY` — Template name empty
- `VOICE_NAME_DUPLICATE` — Template name already exists (FR-032a)
- `VOICE_EXTRACTION_FAILED` — Feature extraction failed

Batch:
- `BATCH_LIMIT_EXCEEDED` — Items exceed 30 limit
- `INVALID_STATE` — Operation not valid for current state

Resources:
- `RESOURCE_CRITICAL` — Resource pressure at dangerous threshold, includes degradation suggestions

Models:
- `MODEL_NOT_FOUND` / `MODEL_LOADING` / `MODEL_CORRUPTED` / `MODEL_DOWNLOAD_INCOMPLETE`

System:
- `GPU_UNAVAILABLE` / `INSUFFICIENT_DISK`
- `NOT_FOUND` / `INTERNAL_ERROR`
