-- V001: Initial schema for 智影口播
-- Tables: works, project_configs, digital_humans, voice_models, bgm_tracks

CREATE TABLE IF NOT EXISTS project_configs (
    id                TEXT PRIMARY KEY,
    script            TEXT NOT NULL,
    voice_id          TEXT NOT NULL,
    voice_speed       REAL NOT NULL DEFAULT 1.0,
    voice_volume      REAL NOT NULL DEFAULT 1.0,
    voice_emotion     REAL NOT NULL DEFAULT 0.5,
    digital_human_id  TEXT NOT NULL,
    background_type   TEXT NOT NULL,
    background_value  TEXT NOT NULL,
    aspect_ratio      TEXT NOT NULL,
    subtitle_enabled  INTEGER NOT NULL DEFAULT 1,
    subtitle_config   TEXT,
    bgm_enabled       INTEGER NOT NULL DEFAULT 0,
    bgm_id            TEXT,
    bgm_custom_path   TEXT,
    voice_volume_ratio REAL DEFAULT 1.0,
    bgm_volume_ratio  REAL DEFAULT 0.5,
    created_at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS works (
    id                 TEXT PRIMARY KEY,
    name               TEXT NOT NULL,
    file_path          TEXT NOT NULL,
    thumbnail_path     TEXT NOT NULL,
    duration_seconds   REAL NOT NULL,
    resolution         TEXT NOT NULL DEFAULT '1080P',
    aspect_ratio       TEXT NOT NULL,
    file_size_bytes    INTEGER,
    created_at         TEXT NOT NULL,
    project_config_id  TEXT REFERENCES project_configs(id),
    is_trial_watermark INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_works_created_at ON works(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_works_name ON works(name);
CREATE INDEX IF NOT EXISTS idx_works_aspect_ratio ON works(aspect_ratio);

CREATE TABLE IF NOT EXISTS digital_humans (
    id                 TEXT PRIMARY KEY,
    name               TEXT NOT NULL,
    category           TEXT NOT NULL,
    source             TEXT NOT NULL,
    thumbnail_path     TEXT NOT NULL,
    preview_video_path TEXT NOT NULL,
    adapted_video_path TEXT,
    adaptation_status  TEXT NOT NULL DEFAULT 'ready',
    adaptation_error   TEXT,
    is_favorited       INTEGER NOT NULL DEFAULT 0,
    favorited_at       TEXT,
    created_at         TEXT NOT NULL,
    sort_order         INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS voice_models (
    id                TEXT PRIMARY KEY,
    name              TEXT NOT NULL,
    category          TEXT NOT NULL,
    description       TEXT,
    model_size_mb     REAL NOT NULL,
    download_status   TEXT NOT NULL DEFAULT 'not_downloaded',
    download_progress REAL DEFAULT 0,
    model_path        TEXT,
    download_url      TEXT NOT NULL,
    is_emotional      INTEGER NOT NULL DEFAULT 0,
    is_favorited      INTEGER NOT NULL DEFAULT 0,
    favorited_at      TEXT,
    sort_order        INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS bgm_tracks (
    id               TEXT PRIMARY KEY,
    name             TEXT NOT NULL,
    category         TEXT NOT NULL,
    source           TEXT NOT NULL,
    file_path        TEXT NOT NULL,
    duration_seconds REAL
);
