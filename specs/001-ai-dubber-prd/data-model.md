# Data Model: 智影口播 · AI数字人视频助手（Windows版）V1.3

> Phase 1 output of `/speckit.plan` for `specs/001-ai-dubber-prd/spec.md`

## Overview

该数据模型描述本地引擎侧（Python）需要持久化或在运行期维护的核心实体：
- 声音模板（Voice Template）
- 单条任务（Single Job）
- 批量任务（Batch Job）与条目（Batch Item）
- 授权状态（License State）（加密存储）

原则：
- 关键状态必须可恢复（支持重启后 UI 继续显示与续跑）
- 所有 `*_path` 字段存储绝对路径
- 批量严格串行，断点续传按条目续跑

## Entities

### 1) Voice Template（声音模板）

**Purpose**: 将本地音频（MP3/WAV）提取为可复用的声音特征资产，供单条/批量生成复用。

**Key fields**
- `id`: string (uuid)
- `name`: string (required, unique per user)
- `created_at`: datetime (ISO8601)
- `source_audio_path`: absolute path
- `source_audio_duration_seconds`: number
- `source_audio_size_bytes`: number
- `format`: enum (`mp3` | `wav`)
- `status`: enum (`processing` | `ready` | `failed`)
- `features_path`: absolute path (feature blob file)
- `error_code?`: string
- `error_message?`: string (user-friendly)

**Validation rules**
- audio format MUST be `mp3` or `wav` (FR-030)
- audio duration MUST be >= 30 seconds (FR-031)
- audio size MUST be <= 100MB (FR-031)
- name MUST be non-empty after trimming

**State transitions**
- `processing -> ready`
- `processing -> failed`
- delete: `ready|failed -> deleted` (hard delete)

---

### 2) Single Job（单条生成任务）

**Purpose**: 表示一次单条生成流程的持久化任务记录，支持进度展示与失败原因追踪。

**Key fields**
- `job_id`: string (stable)
- `type`: enum (`single`)
- `script_text`: string
- `script_segments`: array<string> (derived)
- `resolution`: enum (`1080p` | `720p`) (FR-040)
- `avatar_image_path`: absolute path
- `voice_template_id`: ref -> Voice Template
- `voice_params`: object
  - `speed`: number (default 1.0)
  - `volume`: number (default 1.0)
  - `style`: string (default `neutral_natural`) (FR-033a)
- `subtitle`: object
  - `external_srt`: bool (default true)
  - `burned_in`: bool (default true)
  - `status`: enum (`pending` | `ready` | `failed`)
  - `external_srt_path?`: absolute path
- `output_dir`: absolute path
- `output_video_path?`: absolute path
- `status`: enum (`queued` | `running` | `succeeded` | `failed` | `canceled`)
- `current_stage`: enum (`script` | `tts` | `lipsync` | `mux` | `subtitles`)
- `progress`: number (0-100)
- `started_at?`: datetime
- `ended_at?`: datetime
- `failure_reason?`: object
  - `error_code`: string
  - `error_message`: string

**Validation rules**
- `script_text` MUST be non-empty after trimming (FR-020)
- script segment limit MUST be 120 chars per segment (auto-split) (FR-021)
- `resolution` MUST be `1080p` or `720p`
- `avatar_image_path` MUST point to jpg|png; resized to 512x512 for pipeline input (FR-010)

---

### 3) Batch Job（批量生成任务）

**Purpose**: 严格串行执行的批量任务容器，支持条目级断点续传。

**Key fields**
- `batch_id`: string (stable)
- `type`: enum (`batch`)
- `items`: array<Batch Item>
- `common_config`: object
  - `avatar_image_path`: absolute path
  - `voice_template_id`: ref
  - `voice_params`: object (same shape as Single Job)
  - `resolution`: enum (`1080p` | `720p`)
  - `output_dir`: absolute path (fixed for resume)
- `status`: enum (`queued` | `running` | `paused` | `succeeded` | `failed` | `canceled`)
- `cursor_index`: number (next item index)
- `created_at`: datetime
- `updated_at`: datetime

**Validation rules**
- number of items MUST be <= 30 (keep first 30 if imported more) (FR-071)
- batch execution MUST be strictly serial (FR-072)

**Resume semantics**
- on abnormal exit, currently running item MUST be treated as not completed (FR-074)
- resume starts from first non-succeeded item (by index) (FR-074)
- output_dir MUST remain fixed to the batch created output_dir (FR-074)

---

### 4) Batch Item（批量条目）

**Purpose**: 批量中的单个执行条目，记录单条的输出与失败原因。

**Key fields**
- `item_id`: string
- `index`: number
- `script_text`: string
- `status`: enum (`waiting` | `running` | `succeeded` | `failed` | `canceled`)
- `output_video_path?`: absolute path
- `external_subtitle_path?`: absolute path
- `failure_reason?`: object
  - `error_code`: string
  - `error_message`: string
- `started_at?`: datetime
- `ended_at?`: datetime

**Validation rules**
- `script_text` MUST be non-empty after trimming

---

### 5) License State（授权状态）

**Purpose**: 记录试用/激活状态，用于决定是否需要水印与试用次数扣减。

**Storage**
- File: `{userDataDir}/license.dat` (AES-256-GCM)
- Key: derived from `device_fingerprint` (sha256)

**Decrypted schema**
- `type`: enum (`trial` | `activated`)
- `used_trial_count`: number (0..5)
- `activation_code_masked?`: string
- `activated_at?`: date (YYYY-MM-DD)
- `device_fingerprint`: string

## Storage mapping (suggested)

- SQLite tables:
  - `voice_templates`
  - `jobs`
  - `batch_jobs`
  - `batch_items`
- Filesystem:
  - outputs stored in user-selected directory
  - voice template feature files stored under app data directory
  - license.dat stored under app data directory

## Error codes (align with contracts/spec)

- `INVALID_SCRIPT`
- `MODEL_NOT_FOUND` / `MODEL_LOADING` / `MODEL_CORRUPTED` / `MODEL_DOWNLOAD_INCOMPLETE`
- `GPU_UNAVAILABLE` / `INSUFFICIENT_DISK`
- `LICENSE_TRIAL_EXHAUSTED` / `LICENSE_INVALID_CODE` / `LICENSE_DEVICE_LIMIT` / `LICENSE_NETWORK_ERROR`
- `NOT_FOUND`
- `INTERNAL_ERROR`
