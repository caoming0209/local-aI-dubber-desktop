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
