# Data Model: AI数字人口播桌面客户端

**Branch**: `001-ai-dubber-desktop` | **Date**: 2026-02-19

---

## Storage Overview

| 存储层 | 内容 | 位置 |
|--------|------|------|
| SQLite DB | 作品库、项目配置快照、数字人记录、音色记录 | `{userDataDir}/dubber.db` |
| JSON 文件 | 应用设置、授权状态 | `{userDataDir}/settings.json`, `{userDataDir}/license.dat`（加密） |
| 本地文件系统 | MP4 视频、模型文件、视频封面图、BGM 音频 | 用户可自定义路径 |

---

## SQLite 实体（表结构）

### 1. `works` — 作品库

已生成的视频记录。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | TEXT (UUID) | PK | 唯一标识 |
| `name` | TEXT | NOT NULL | 视频名称，用户可改 |
| `file_path` | TEXT | NOT NULL | 本地 MP4 绝对路径 |
| `thumbnail_path` | TEXT | NOT NULL | 封面图绝对路径（首帧截图）|
| `duration_seconds` | REAL | NOT NULL | 视频时长（秒） |
| `resolution` | TEXT | NOT NULL | 固定 "1080P" |
| `aspect_ratio` | TEXT | NOT NULL | "16:9" 或 "9:16" |
| `file_size_bytes` | INTEGER | | 文件大小 |
| `created_at` | TEXT (ISO8601) | NOT NULL | 生成完成时间 |
| `project_config_id` | TEXT (UUID) | FK → project_configs | 关联的制作配置快照 |
| `is_trial_watermark` | INTEGER (bool) | NOT NULL, DEFAULT 0 | 是否带试用水印 |

**索引**: `created_at` DESC, `name`, `aspect_ratio`

**状态转换**: 记录在视频生成成功后写入，删除时同步删除本地 MP4 和封面图文件。

---

### 2. `project_configs` — 制作配置快照

每次生成视频时保存完整配置，用于「重新编辑」功能恢复现场。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | TEXT (UUID) | PK | |
| `script` | TEXT | NOT NULL | 原始文案内容 |
| `voice_id` | TEXT | NOT NULL | 所选音色 ID |
| `voice_speed` | REAL | NOT NULL, DEFAULT 1.0 | 语速（0.5-2.0） |
| `voice_volume` | REAL | NOT NULL, DEFAULT 1.0 | 音量（0-2.0） |
| `voice_emotion` | REAL | NOT NULL, DEFAULT 0.5 | 情感强度（0-1.0） |
| `digital_human_id` | TEXT | NOT NULL | 所选数字人 ID |
| `background_type` | TEXT | NOT NULL | "solid_color" / "scene" / "custom_image" |
| `background_value` | TEXT | NOT NULL | 颜色值或图片路径 |
| `aspect_ratio` | TEXT | NOT NULL | "16:9" / "9:16" |
| `subtitle_enabled` | INTEGER (bool) | NOT NULL, DEFAULT 1 | 字幕开关 |
| `subtitle_config` | TEXT (JSON) | | 字幕配置（字体、字号、颜色、位置） |
| `bgm_enabled` | INTEGER (bool) | NOT NULL, DEFAULT 0 | BGM 开关 |
| `bgm_id` | TEXT | | BGM ID（内置）或 null |
| `bgm_custom_path` | TEXT | | 自定义 BGM 文件路径 |
| `voice_volume_ratio` | REAL | DEFAULT 1.0 | 人声混音比例 |
| `bgm_volume_ratio` | REAL | DEFAULT 0.5 | BGM 混音比例 |
| `created_at` | TEXT (ISO8601) | NOT NULL | |

**subtitle_config JSON 结构**:
```json
{
  "font_family": "Microsoft YaHei",
  "font_size": 30,
  "color": "#FFFFFF",
  "position": "bottom_center"
}
```

---

### 3. `digital_humans` — 数字人

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | TEXT (UUID) | PK | |
| `name` | TEXT | NOT NULL | 显示名称 |
| `category` | TEXT | NOT NULL | "male_host" / "female_host" / "professional" / "friendly" / "expert" / "other" |
| `source` | TEXT | NOT NULL | "official" / "custom" |
| `thumbnail_path` | TEXT | NOT NULL | 预览图路径 |
| `preview_video_path` | TEXT | NOT NULL | 动作小样视频路径 |
| `adapted_video_path` | TEXT | | 口型适配后的视频路径（自定义数字人） |
| `adaptation_status` | TEXT | NOT NULL, DEFAULT "ready" | "ready" / "processing" / "failed" / "pending" |
| `adaptation_error` | TEXT | | 适配失败原因 |
| `is_favorited` | INTEGER (bool) | NOT NULL, DEFAULT 0 | |
| `favorited_at` | TEXT (ISO8601) | | 收藏时间 |
| `created_at` | TEXT (ISO8601) | NOT NULL | |
| `sort_order` | INTEGER | NOT NULL, DEFAULT 0 | 官方数字人排序 |

**状态转换**:
```
custom 上传 → adaptation_status: "pending"
    → 适配中: "processing"
    → 成功: "ready" (adapted_video_path 填充)
    → 失败: "failed" (adaptation_error 填充)
    → 用户重新适配: 回到 "pending"
```

**业务规则**:
- `source = "official"` 的记录不可删除
- 删除 `source = "custom"` 时，同步删除 `adapted_video_path` 指向的文件

---

### 4. `voice_models` — 音色

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | TEXT (UUID) | PK | |
| `name` | TEXT | NOT NULL | 音色名称（如「男声-沉稳」） |
| `category` | TEXT | NOT NULL | "male" / "female" / "emotional" / "dialect" |
| `description` | TEXT | | 适用场景描述 |
| `model_size_mb` | REAL | NOT NULL | 模型文件大小（MB） |
| `download_status` | TEXT | NOT NULL, DEFAULT "not_downloaded" | "not_downloaded" / "downloading" / "downloaded" / "error" |
| `download_progress` | REAL | DEFAULT 0 | 下载进度（0-1.0） |
| `model_path` | TEXT | | 已下载模型本地路径 |
| `download_url` | TEXT | NOT NULL | 模型下载地址 |
| `is_emotional` | INTEGER (bool) | NOT NULL, DEFAULT 0 | 是否支持情感强度调节 |
| `is_favorited` | INTEGER (bool) | NOT NULL, DEFAULT 0 | |
| `favorited_at` | TEXT (ISO8601) | | |
| `sort_order` | INTEGER | NOT NULL, DEFAULT 0 | 展示排序 |

**状态转换**:
```
not_downloaded → 触发下载 → downloading (progress: 0→1.0) → downloaded
downloaded → 删除模型 → not_downloaded
downloading → 网络错误 → error → 重试 → downloading
```

---

### 5. `bgm_tracks` — 背景音乐

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | TEXT (UUID) | PK | |
| `name` | TEXT | NOT NULL | BGM 名称 |
| `category` | TEXT | NOT NULL | "upbeat" / "soothing" / "grand" |
| `source` | TEXT | NOT NULL | "builtin" / "custom" |
| `file_path` | TEXT | NOT NULL | 本地音频文件路径 |
| `duration_seconds` | REAL | | 时长 |

**业务规则**: `source = "builtin"` 随安装包分发，不可删除。

---

## JSON 文件实体

### 6. `settings.json` — 应用设置

```typescript
interface AppSettings {
  // 基础设置
  autoStartOnBoot: boolean;           // 默认 false
  defaultVideoSavePath: string;       // 默认 ~/Documents/智影口播/作品
  theme: "light" | "dark";           // 默认 "light"
  language: "zh-CN";                  // 固定，预留扩展

  // 模型下载设置
  modelStoragePath: string;           // 默认 ~/Documents/智影口播/models
  downloadSpeedLimitKBps: number;     // 0 = 无限制
  autoDownloadModels: boolean;        // 默认 true

  // 性能设置
  inferenceMode: "auto" | "cpu" | "gpu";  // 默认 "auto"
  cpuUsageLimitPercent: number;           // 0 = 无限制，范围 10-90

  // 缓存设置
  autoClearCacheEnabled: boolean;     // 默认 false
  autoClearCycleDays: number;         // 7 / 30

  // 更新设置
  autoCheckUpdate: boolean;           // 默认 true

  // 元数据
  updatedAt: string;                  // ISO8601
}
```

---

### 7. `license.dat`（加密文件）— 授权状态

文件内容 AES-256 加密，密钥基于硬件指纹派生，防止跨设备复制。

```typescript
interface LicenseState {
  type: "trial" | "activated";
  usedTrialCount: number;            // 已消耗试用次数（最大 5）
  activationCode?: string;           // 激活后保存（部分隐藏用于显示）
  activatedAt?: string;              // 激活时间 ISO8601
  deviceFingerprint: string;         // 当前设备硬件指纹 hash
}
```

**业务规则**:
- 软件安装首次启动时创建，type = "trial", usedTrialCount = 0
- 每次成功生成视频（单条或批量每条）: usedTrialCount += 1
- usedTrialCount >= 5 且 type = "trial": 阻止生成，弹出激活引导
- 激活成功后: type = "activated"，usedTrialCount 不再增减

---

## 实体关系图

```
works ─────────────── project_configs
  │                       │
  │                    voice_models (via voice_id)
  │                    digital_humans (via digital_human_id)
  │                    bgm_tracks (via bgm_id)
  │
license.dat (独立，不关联 works)
settings.json (独立，全局单例)
```

---

## 数据访问层规则

1. **SQLite 通过 Python 后端访问**：前端不直接读写数据库，所有数据通过 IPC HTTP 接口获取。
2. **settings.json 由 Python 后端读写**：前端通过 `/api/settings` 接口读取和更新设置。
3. **license.dat 由 Python 后端独占读写**：激活逻辑和状态查询均走 `/api/license` 接口。
4. **文件路径存储绝对路径**：所有 `*_path` 字段存储绝对路径；用户迁移存储路径时，批量更新相关路径字段。
5. **删除联动**：删除作品时同步删除 MP4 + 封面图；删除自定义数字人时同步删除适配视频文件；删除音色模型时只删除 model_path 文件，保留数据库记录（状态改为 not_downloaded）。

---

## Schema 迁移策略

**版本管理机制**：使用 SQLite 内置的 `PRAGMA user_version` 存储当前 schema 版本号。

**迁移文件结构**（在 `python-engine/src/storage/migrations/` 目录下）：

```text
migrations/
├── V001__initial_schema.sql       # 建表：works, project_configs, digital_humans, voice_models, bgm_tracks
├── V002__add_works_resolution.sql # 示例：新增字段
└── V003__voice_model_checksum.sql # 示例：新增 checksum 字段
```

**命名规范**：`V{三位序号}__{snake_case_描述}.sql`，序号严格递增。

**执行时机**：Python 引擎每次启动时在 `database.py` 中执行：
```python
current_version = conn.execute("PRAGMA user_version").fetchone()[0]
# 按序号升序扫描 migrations/ 目录，执行 version > current_version 的所有脚本
# 每个脚本执行成功后立即 PRAGMA user_version = N
```

**原子性保证**：每个迁移脚本在单个事务中执行，失败则回滚并终止启动（显示「数据库迁移失败」错误对话框）。

---

## 模型文件完整性校验

**目标**：检测下载不完整或磁盘损坏的模型文件，避免推理时静默失败。

**校验文件**：每个模型目录下存储 `checksums.json`（由服务端随模型一同发布）：

```json
{
  "wav2lip.pth": "sha256:a3f1c2d4...",
  "wav2lip_gan.pth": "sha256:b7e9f0a2...",
  "cosyvoice2_base.pt": "sha256:c1d2e3f4..."
}
```

**校验时机**：

| 时机 | 行为 |
|------|------|
| 下载完成后 | 立即校验；失败则标记 `download_status = "error"`，删除损坏文件 |
| 应用启动时 | 对已下载模型的关键权重文件进行快速校验（仅验 SHA-256 前 4KB 哈希，< 200ms） |
| 推理任务开始前 | 完整校验当前任务所需模型；失败返回 `MODEL_CORRUPTED` 错误码 |

**错误码补充**（新增至 ipc-api.md 错误码表）：

| code | 含义 |
|------|------|
| `MODEL_CORRUPTED` | 模型文件校验失败，需重新下载 |
| `MODEL_DOWNLOAD_INCOMPLETE` | 下载未完成，文件不完整 |

**孤立模型文件处理**：启动时扫描模型目录，若存在不在 `voice_models.model_path` 中的文件，且文件大小 > 100MB，则列入「未识别文件」提示用户清理（不自动删除）。
