# Data Model: 智影口播 · AI数字人视频助手（Windows版）V1.3

> Phase 1 output of `/speckit.plan` for `specs/001-ai-dubber-prd/spec.md`

## Overview

本数据模型描述 V1.3 范围内引擎侧（Python）需持久化的核心实体。

### 存储层概览

| 存储层 | 内容 | 位置 |
|--------|------|------|
| SQLite DB | 作品库、配置快照、数字人、音色模型、BGM、声音模板、作业 | `{userDataDir}/dubber.db` |
| JSON 文件 | 应用设置 | `{userDataDir}/settings.json` |
| 加密文件 | 授权状态 | `{userDataDir}/license.dat`（AES-256-GCM） |
| 本地文件系统 | MP4 视频、模型文件、封面图、BGM 音频、声音特征文件 | 用户可自定义路径 |

### 设计原则

- 关键状态必须可恢复（支持重启后 UI 继续显示与续跑）
- 所有 `*_path` 字段存储绝对路径
- 批量严格串行，断点续传按条目续跑
- Schema 迁移：`PRAGMA user_version` + `migrations/V{NNN}__desc.sql` 按序执行

## 既有表（CLAUDE.md 已定义，V1.3 不做结构变更）

以下表在 CLAUDE.md 中已定义，V1.3 不修改其结构，仅确保离线环境下可正常读写。

### works（作品库）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| name | TEXT | 作品名称 |
| file_path | TEXT | MP4 绝对路径 |
| thumbnail_path | TEXT | 封面图绝对路径 |
| duration_seconds | REAL | 视频时长 |
| resolution | TEXT | 分辨率 (e.g. "1080p") |
| aspect_ratio | TEXT | 画面比例 |
| file_size_bytes | INTEGER | 文件大小 |
| created_at | TEXT | ISO8601 创建时间 |
| project_config_id | INTEGER FK | 关联配置快照 |
| is_trial_watermark | INTEGER | 是否有试用水印 (0/1) |

### project_configs（制作配置快照）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| script | TEXT | 文案内容 |
| voice_id | TEXT | 音色/模板 ID |
| voice_speed | REAL | 语速 |
| voice_volume | REAL | 音量 |
| voice_emotion | TEXT | 情感/风格（V1.3 统一使用 voice_style 枚举值） |
| digital_human_id | INTEGER | 数字人 ID |
| background_type | TEXT | 背景类型 |
| background_value | TEXT | 背景值 |
| aspect_ratio | TEXT | 画面比例 |
| subtitle_enabled | INTEGER | 是否启用字幕 |
| subtitle_config | TEXT | 字幕配置 JSON |
| bgm_id | INTEGER | BGM ID |
| bgm_volume | REAL | BGM 音量 |

### digital_humans（数字人）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| name | TEXT | 名称 |
| category | TEXT | 分类 |
| source | TEXT | `official` / `custom` |
| thumbnail_path | TEXT | 缩略图绝对路径 |
| preview_video_path | TEXT | 预览视频路径 |
| adapted_video_path | TEXT | 适配后视频路径 |
| adaptation_status | TEXT | `ready`/`processing`/`failed`/`pending` |
| is_favorited | INTEGER | 收藏标记 (0/1) |

### voice_models（预置音色模型）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| name | TEXT | 名称 |
| category | TEXT | `male`/`female`/`emotional`/`dialect` |
| model_size_mb | REAL | 模型大小 |
| download_status | TEXT | `not_downloaded`/`downloading`/`downloaded`/`error` |
| model_path | TEXT | 模型文件路径 |
| download_url | TEXT | 下载地址 |
| is_emotional | INTEGER | 是否支持情感 (0/1) |
| is_favorited | INTEGER | 收藏标记 (0/1) |

### bgm_tracks（BGM）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| name | TEXT | 名称 |
| category | TEXT | `upbeat`/`soothing`/`grand` |
| source | TEXT | `builtin`/`custom` |
| file_path | TEXT | 文件绝对路径 |

## V1.3 新增实体

### 1) voice_templates（声音模板）— 用户自定义声音克隆

**Purpose**: 用户上传本地音频（MP3/WAV），提取声音特征保存为可复用模板，供单条/批量生成时选择。

> 注意：与 `voice_models`（预置音色）不同，`voice_templates` 由用户创建。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT PK | UUID |
| name | TEXT NOT NULL UNIQUE | 模板名称（trim 后唯一，FR-032a） |
| created_at | TEXT NOT NULL | ISO8601 |
| source_audio_path | TEXT NOT NULL | 原始音频绝对路径 |
| source_audio_duration_seconds | REAL NOT NULL | 原始音频时长 |
| source_audio_size_bytes | INTEGER NOT NULL | 原始音频大小 |
| format | TEXT NOT NULL | `mp3` / `wav` |
| status | TEXT NOT NULL | `processing` / `ready` / `failed` |
| features_path | TEXT | 声音特征文件绝对路径 |
| error_code | TEXT | 失败错误码 |
| error_message | TEXT | 用户可读失败原因 |

**Validation rules**
- format MUST be `mp3` or `wav` (FR-030)
- duration MUST >= 30 seconds (FR-031)
- size MUST <= 100MB (FR-031)
- name MUST be non-empty after trimming
- name MUST be unique after trimming (FR-032a); duplicate returns `VOICE_NAME_DUPLICATE`

**State transitions**
- `processing → ready` — 特征提取成功
- `processing → failed` — 特征提取失败
- `ready|failed → (hard delete)` — 删除不可恢复 (FR-034)

---

### 2) jobs（单条生成任务）

**Purpose**: 持久化单条生成流程的任务记录，支持进度展示、断线恢复与失败原因追踪。

| 字段 | 类型 | 说明 |
|------|------|------|
| job_id | TEXT PK | 稳定唯一标识 |
| type | TEXT NOT NULL | `single` |
| script_text | TEXT NOT NULL | 原始文案 |
| script_segments | TEXT | JSON 数组（自动拆分后） |
| resolution | TEXT NOT NULL | `1080p` / `720p` |
| avatar_image_path | TEXT NOT NULL | 数字人图片绝对路径 |
| voice_template_id | TEXT | FK → voice_templates.id |
| voice_speed | REAL DEFAULT 1.0 | 语速 |
| voice_volume | REAL DEFAULT 1.0 | 音量 |
| voice_style | TEXT DEFAULT 'neutral_natural' | 情感/风格，枚举值见下方 |
| subtitle_external_srt | INTEGER DEFAULT 1 | 是否输出外置字幕 |
| subtitle_burned_in | INTEGER DEFAULT 1 | 是否内嵌字幕 |
| subtitle_status | TEXT DEFAULT 'pending' | `pending`/`ready`/`failed` |
| subtitle_srt_path | TEXT | 外置 SRT 文件路径 |
| output_dir | TEXT NOT NULL | 输出目录绝对路径 |
| output_video_path | TEXT | 输出视频路径 |
| status | TEXT NOT NULL DEFAULT 'queued' | `queued`/`running`/`paused`/`succeeded`/`failed`/`canceled` |
| current_stage | TEXT | `script`/`tts`/`lipsync`/`mux`/`subtitles` |
| progress | INTEGER DEFAULT 0 | 0-100 |
| started_at | TEXT | ISO8601 |
| ended_at | TEXT | ISO8601 |
| error_code | TEXT | 失败错误码 |
| error_message | TEXT | 用户可读失败原因 |

**Validation rules**
- script_text MUST be non-empty after trimming (FR-020)
- script_text MUST be <= 3000 characters (FR-020a); exceeding returns `SCRIPT_TOO_LONG`
- script auto-split at 120 chars/segment (FR-021)
- resolution MUST be `1080p` or `720p`
- avatar_image_path MUST be jpg/png; minimum 256×256; auto-resized to 512×512 via center-crop (FR-010)
- voice_style MUST be one of the defined enum values (FR-033c)
- Concurrent generation blocked: new job rejected with `JOB_ALREADY_RUNNING` if any job is `running`/`paused` (FR-085)

**voice_style 枚举值** (FR-033c)

| 值 | 中文标签 | 说明 |
|----|----------|------|
| `neutral_natural` | 中性/自然（推荐） | 默认，最佳通用效果 |
| `gentle` | 温柔 | 轻柔语调 |
| `cheerful` | 开朗/愉悦 | 正向积极 |
| `serious` | 严肃/正式 | 新闻播报风格 |
| `sad` | 低沉/忧伤 | 情绪化叙事 |
| `angry` | 激昂/愤怒 | 强调力度 |

**State transitions**
- `queued → running` — 开始执行
- `running → paused` — 资源超限自动暂停 (FR-082)
- `paused → running` — 用户手动恢复
- `running → succeeded` — 生成完成
- `running → failed` — 生成失败
- `running|queued → canceled` — 用户取消

---

### 3) batch_jobs（批量生成任务）

**Purpose**: 严格串行执行的批量任务容器，支持条目级断点续传。

| 字段 | 类型 | 说明 |
|------|------|------|
| batch_id | TEXT PK | 稳定唯一标识 |
| type | TEXT NOT NULL | `batch` |
| avatar_image_path | TEXT NOT NULL | 统一数字人图片 |
| voice_template_id | TEXT | FK → voice_templates.id |
| voice_speed | REAL DEFAULT 1.0 | 统一语速 |
| voice_volume | REAL DEFAULT 1.0 | 统一音量 |
| voice_style | TEXT DEFAULT 'neutral_natural' | 统一情感/风格 |
| resolution | TEXT NOT NULL | `1080p` / `720p` |
| subtitle_external_srt | INTEGER DEFAULT 1 | |
| subtitle_burned_in | INTEGER DEFAULT 1 | |
| output_dir | TEXT NOT NULL | 输出目录（断点续传固定不变） |
| status | TEXT NOT NULL DEFAULT 'queued' | `queued`/`running`/`paused`/`succeeded`/`failed`/`canceled` |
| cursor_index | INTEGER DEFAULT 0 | 下一个待执行条目索引 |
| created_at | TEXT NOT NULL | ISO8601 |
| updated_at | TEXT NOT NULL | ISO8601 |

**Validation rules**
- items count MUST <= 30 (超出截断至前 30 条, FR-071)
- execution MUST be strictly serial (FR-072)

**Resume semantics (FR-074)**
- 异常退出时，当前运行条目重置为 `waiting`（视为未完成）
- 恢复时从 cursor_index 对应的条目开始，仅执行状态为 `waiting` 的条目
- 状态为 `failed` 的条目跳过（需通过 FR-075 显式重试）
- 状态为 `succeeded` 的条目跳过（不重复生成）
- output_dir MUST 固定为批次创建时的目录

---

### 4) batch_items（批量条目）

**Purpose**: 批量任务中的单个执行条目。

| 字段 | 类型 | 说明 |
|------|------|------|
| item_id | TEXT PK | 唯一标识 |
| batch_id | TEXT NOT NULL | FK → batch_jobs.batch_id |
| idx | INTEGER NOT NULL | 条目索引（0-based） |
| script_text | TEXT NOT NULL | 文案 |
| status | TEXT NOT NULL DEFAULT 'waiting' | `waiting`/`running`/`succeeded`/`failed`/`canceled` |
| output_video_path | TEXT | 输出视频路径 |
| subtitle_srt_path | TEXT | 外置字幕路径 |
| subtitle_status | TEXT DEFAULT 'pending' | `pending`/`ready`/`failed` |
| error_code | TEXT | 失败错误码 |
| error_message | TEXT | 用户可读失败原因 |
| started_at | TEXT | ISO8601 |
| ended_at | TEXT | ISO8601 |

**Validation rules**
- script_text MUST be non-empty after trimming
- script_text MUST be <= 3000 characters (FR-020a); exceeding returns `SCRIPT_TOO_LONG`

---

### 5) License State（授权状态）

**Purpose**: 试用/激活状态，决定水印与试用次数。

**Storage**: `{userDataDir}/license.dat` (AES-256-GCM, key derived from device fingerprint SHA-256)

**Decrypted schema**

| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | `trial` / `activated` |
| used_trial_count | number | 0..5 |
| activation_code_masked | string? | 部分隐藏 |
| activated_at | string? | ISO8601 日期 |
| device_fingerprint | string | SHA-256(CPU_ID\|主板UUID\|硬盘序列号) |

> 注：授权模块不在 V1.3 核心闭环范围内；开发模式（NODE_ENV=development）下授权检查跳过。

## 删除联动规则

| 删除操作 | 联动清理 |
|----------|----------|
| 删除作品 (works) | 删除 MP4 + 封面图 |
| 删除自定义数字人 | 删除适配视频文件 |
| 删除预置音色模型 | 仅删文件，保留记录（状态改 `not_downloaded`） |
| 删除声音模板 | 删除特征文件 + 原始音频副本 + 数据库记录（hard delete） |
| 取消单条任务 | 清理临时中间文件；已完成产物不删 |
| 取消批量任务 | 停止后续条目；清理正在执行条目的临时文件；已完成条目产物保留 |

## 模型文件完整性校验

- 每个模型目录下 `checksums.json` 存储 SHA-256 哈希
- 下载完成后立即校验
- 启动时快速校验（前 4KB 哈希，< 200ms）
- 推理前完整校验
- 校验失败错误码：`MODEL_CORRUPTED`、`MODEL_DOWNLOAD_INCOMPLETE`

## Error codes (align with contracts)

Pipeline: `INVALID_SCRIPT` / `SCRIPT_TOO_LONG` / `INVALID_IMAGE_FORMAT` / `IMAGE_TOO_SMALL` / `JOB_ALREADY_RUNNING`
Voice: `VOICE_INVALID_FORMAT` / `VOICE_TOO_SHORT` / `VOICE_TOO_LARGE` / `VOICE_NAME_EMPTY` / `VOICE_NAME_DUPLICATE` / `VOICE_EXTRACTION_FAILED`
Batch: `BATCH_LIMIT_EXCEEDED` / `INVALID_STATE`
Resources: `RESOURCE_CRITICAL`
Models: `MODEL_NOT_FOUND` / `MODEL_LOADING` / `MODEL_CORRUPTED` / `MODEL_DOWNLOAD_INCOMPLETE`
System: `GPU_UNAVAILABLE` / `INSUFFICIENT_DISK` / `NOT_FOUND` / `INTERNAL_ERROR`
License: `LICENSE_TRIAL_EXHAUSTED` / `LICENSE_INVALID_CODE` / `LICENSE_DEVICE_LIMIT` / `LICENSE_NETWORK_ERROR`
