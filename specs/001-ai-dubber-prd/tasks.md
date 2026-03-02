# Tasks: 智影口播 · AI数字人视频助手（Windows版）V1.3

**Input**: Design documents from `/specs/001-ai-dubber-prd/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ipc-api.md, contracts/license.md, quickstart.md

**Tests**: Constitution Principle V requires testability ("对用户可见行为的变更 MUST 可验证"). Test tasks are included per phase: pytest unit tests for backend core modules, Vitest unit tests for frontend stores, pytest integration tests for API contracts, Playwright E2E for critical flows.

**Organization**: Tasks grouped by user story (US1=P1 MVP, US2=P2, US3=P3) per spec.md priorities.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks in same phase)
- **[Story]**: US1, US2, US3 — maps to spec.md user stories
- Exact file paths included in descriptions

---

## Phase 1: Setup (Project Initialization)

**Purpose**: Create project directory structure and initialize all three sub-projects with correct dependencies.

- [ ] T001 Create full project directory structure per plan.md (electron-app/src/main/, electron-app/src/preload/, renderer/src/components/, renderer/src/pages/, renderer/src/stores/, renderer/src/services/, python-engine/src/api/routes/, python-engine/src/core/, python-engine/src/storage/migrations/, python-engine/src/license/, python-engine/src/utils/, python-engine/tests/unit/, python-engine/tests/integration/, shared/)
- [ ] T002 [P] Initialize electron-app: package.json with electron 40+, typescript, electron-builder; tsconfig.json; electron-builder.yml targeting Windows NSIS x64 in electron-app/
- [ ] T003 [P] Initialize renderer: package.json with react 19.2, react-dom, react-router 7, zustand 5, lucide-react, tailwind css 4 (npm, not CDN); vite.config.ts with React plugin + resolve alias for shared/; tsconfig.json with paths mapping "@shared/*" → "../shared/*"; tailwind.config; index.html entry in renderer/
- [ ] T004 [P] Initialize python-engine: requirements.txt with fastapi, uvicorn, torch, Pillow, ffmpeg-python, openpyxl, chardet; create src/__init__.py and tests/conftest.py in python-engine/
- [ ] T005 [P] Define shared IPC TypeScript types: job status enums (queued/running/paused/succeeded/failed/canceled), SSE event types (progress/resource/complete/error per ipc-api.md), SSE event payloads (stage/progress/message/resource), voice_style enum (neutral_natural/gentle/cheerful/serious/sad/angry), all error codes from contracts/ipc-api.md, API request/response interfaces in shared/ipc-types.ts

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure — database, server, Electron shell, React scaffold, IPC plumbing, resource monitoring. MUST complete before ANY user story starts.

**CRITICAL**: No user story work can begin until this phase is complete.

### Backend Infrastructure

- [ ] T006 Implement SQLite database module: connection management, PRAGMA user_version migration runner (read version → apply V{NNN}__desc.sql scripts in order), initial schema creation for existing tables (works, project_configs, digital_humans, voice_models, bgm_tracks per CLAUDE.md) in python-engine/src/storage/database.py + python-engine/src/storage/migrations/V001__initial_schema.sql
- [ ] T007 [P] Implement JSON settings store: read/write/defaults per AppSettings interface (autoStartOnBoot, defaultVideoSavePath, theme, inferenceMode, etc.), atomic writes, create if missing in python-engine/src/storage/settings_store.py
- [ ] T008 Implement FastAPI server entry: random port selection, bind only 127.0.0.1, stdout JSON handshake {"status":"ready","port":N}, lifespan startup (init DB, start resource monitor) / shutdown (cleanup), CORS for local dev in python-engine/src/api/server.py
- [ ] T009 [P] Implement unified error handling: FastAPI exception handlers mapping domain errors to JSON {error_code, message}, cover all error codes from contracts (INVALID_SCRIPT, SCRIPT_TOO_LONG, JOB_ALREADY_RUNNING, VOICE_*, BATCH_*, RESOURCE_CRITICAL, MODEL_*, GPU_UNAVAILABLE, INSUFFICIENT_DISK, NOT_FOUND, INTERNAL_ERROR) in python-engine/src/api/server.py
- [ ] T010 [P] Implement GPU detector: check CUDA availability via torch.cuda, get device name/memory info, determine inference mode (auto→GPU if available else CPU, or user-forced CPU/GPU from settings) in python-engine/src/core/gpu_detector.py
- [ ] T011 [P] Implement resource monitor: periodic sampling (CPU% via psutil, memory% via psutil, VRAM% via torch.cuda or N/A if CPU mode), 2s interval, threshold detection (VRAM≥90%, mem≥90%, disk<1GB), emit structured warning events in python-engine/src/core/resource_monitor.py
- [ ] T012 [P] Implement model integrity checker: read checksums.json per model directory, fast 4KB-prefix check (<200ms) at startup, full SHA-256 check before inference, return MODEL_CORRUPTED or MODEL_DOWNLOAD_INCOMPLETE on failure in python-engine/src/core/model_manager.py
- [ ] T013 [P] Implement SSE progress event generator: format events as text/event-stream with stage/progress/message/resource fields, support both single-job and batch-job event shapes per contracts/ipc-api.md in python-engine/src/utils/progress.py
- [ ] T014 [P] Implement file utilities: path normalization for Windows, temp directory management under output_dir, temp file cleanup helper, thumbnail generation from video first frame in python-engine/src/utils/file_utils.py

### Frontend Infrastructure

- [ ] T015 Implement Electron main process: BrowserWindow creation with appropriate security settings; python-manager.ts (spawn Python process, read stdout line-by-line for handshake JSON, 10s timeout, exponential backoff restart max 3 attempts); ipc-bridge.ts (IPC handlers for HTTP proxy and system operations) in electron-app/src/main/index.ts + electron-app/src/main/python-manager.ts + electron-app/src/main/ipc-bridge.ts
- [ ] T016 [P] Implement preload API: contextBridge exposing window.electronAPI with engine.request(method, path, body?), pipeline.subscribeProgress(jobId, onEvent, onDone, onError), system.openPath/showItemInFolder/selectDirectory/selectFile/readTextFile(path), getEnginePort() in electron-app/src/preload/index.ts
- [ ] T017 [P] Implement HTTP client base: request wrapper with dynamic engine port injection from preload, JSON serialization/deserialization, error code extraction from response, typed return values in renderer/src/services/engine.ts
- [ ] T018 [P] Implement SSE subscription utility: EventSource-compatible wrapper using preload API, auto-reconnect on disconnect, typed event parsing per ipc-types.ts, callback interface (onEvent, onDone, onError), unsubscribe cleanup in renderer/src/services/pipeline.ts
- [ ] T019 Create React app shell: main.tsx entry, App.tsx with HashRouter and route definitions for all 8 pages, Layout.tsx (flex h-screen with sidebar + main content), Sidebar.tsx (dark sidebar with lucide-react icons, NavLink active states), placeholder pages for Home/SingleCreation/BatchCreation/AvatarManager/VoiceManager/WorksLibrary/Settings/Help in renderer/src/
- [ ] T020 [P] Create Zustand store skeletons: settings.ts (AppSettings read/write), license.ts (LicenseState stub, dev mode bypass), resource-monitor.ts (cpu/mem/vram values, warningActive flag, threshold constants) in renderer/src/stores/

**Checkpoint**: Foundation ready — `npm run dev` in electron-app launches window, Python engine starts with stdout handshake, React shell renders with sidebar navigation to all routes, HTTP client can reach engine, SSE subscription functional.

---

## Phase 3: User Story 1 — 单条生成口播视频 (Priority: P1) MVP

**Goal**: Offline single video generation end-to-end: avatar image + script text + voice template → video (1080p/720p) + SRT subtitle + hardcoded subtitle. Progress + resource monitoring. Cancel support. Output directory navigation.

**Independent Test**: In offline environment, open SingleCreation → upload avatar jpg → input 200-char script → select voice template → choose 1080P → click generate → verify SSE progress updates → verify MP4 + SRT in output dir → click "打开输出目录".

### Backend — Pipeline Core

- [ ] T021 [P] [US1] Implement image processor: validate file is jpg/png (return INVALID_IMAGE_FORMAT if not), check minimum resolution (return IMAGE_TOO_SMALL if below threshold), auto-resize to 512×512 via Pillow, save processed image to temp dir in python-engine/src/core/image_processor.py
- [ ] T022 [P] [US1] Implement script splitter: validate non-empty (INVALID_SCRIPT), validate ≤3000 chars (SCRIPT_TOO_LONG per FR-020a), auto-split at 120 chars/segment using natural breakpoints (。？！，；、\n), return ordered segments array, preserve semantic coherence per research #9 in python-engine/src/core/script_splitter.py
- [ ] T023 [P] [US1] Implement TTS engine wrapper: load CosyVoice3-0.5B model, accept script segment + speaker embedding (from voice template features_path) + voice params (speed/volume/style), generate WAV 24kHz audio, FFmpeg resample to 16kHz for Wav2Lip input in python-engine/src/core/tts_engine.py
- [ ] T024 [P] [US1] Implement lipsync engine wrapper: load Wav2Lip model, accept audio WAV (16kHz) + avatar image (512×512), output lip-synced video segment in python-engine/src/core/lipsync_engine.py
- [ ] T025 [P] [US1] Implement subtitle generator: generate SRT file from script segments + audio timestamps (segment index → start/end time), burn hardcoded subtitles into video via FFmpeg drawtext/ass, retry once on failure (FR-061), update subtitle_status field in python-engine/src/core/subtitle_generator.py
- [ ] T026 [US1] Implement video synthesizer: orchestrate FFmpeg pipeline to concatenate per-segment lip-synced videos, merge audio tracks, apply subtitle overlay, output final MP4 at configured resolution (1080p/720p), clean up intermediate files in python-engine/src/core/video_synthesizer.py

### Backend — Job Management & API Routes

- [ ] T027 [US1] Create V002 migration: jobs table DDL with all fields per data-model.md (job_id PK, type, script_text, script_segments, resolution, avatar_image_path, voice_template_id, voice_speed/volume/style, subtitle fields, output fields, status with DEFAULT 'queued', current_stage, progress, timestamps, error fields); implement CRUD in jobs_repo.py in python-engine/src/storage/migrations/V002__jobs_table.sql + python-engine/src/storage/jobs_repo.py
- [ ] T028 [US1] Implement job manager for single jobs: create job with UUID-based job_id, concurrent generation guard (query for running/paused jobs → reject with JOB_ALREADY_RUNNING per FR-085 + research #10), execute pipeline stages sequentially (script_split → tts → lipsync → mux → subtitles) with progress updates via SSE (including resource heartbeat at ≤2s intervals), auto-pause on resource exhaustion (status→paused per FR-082 + research #12, thresholds: VRAM≥90%, mem≥90%, disk<1GB), resume handler (paused→running), cancel handler (cleanup temp files via file_utils, preserve completed output files, status→canceled per FR-051), state transition enforcement per data-model.md in python-engine/src/core/job_manager.py
- [ ] T029 [US1] Implement pipeline routes: POST /pipeline/single (validate request per contracts, create job, return 202 + job_id), GET /pipeline/progress/{job_id} (SSE stream: stage/progress/message/resource at ≥2s interval), POST /pipeline/pause/{job_id}, POST /pipeline/resume/{job_id}, POST /pipeline/cancel/{job_id} in python-engine/src/api/routes/pipeline.py
- [ ] T030 [US1] Implement jobs query routes: GET /jobs/{job_id}/state (return full snapshot for UI reconnection per contracts), GET /jobs?status={csv} (list jobs matching statuses for startup recovery detection) in python-engine/src/api/routes/jobs.py

### Frontend — Single Creation UI

- [ ] T031 [P] [US1] Create project config store (Zustand): script text, avatar image path, voice_template_id, voice_params {speed: 1.0, volume: 1.0, style: 'neutral_natural'} with recommended defaults (FR-033b), resolution ('1080p' default), subtitle settings, output_dir; reset action for new task in renderer/src/stores/project.ts
- [ ] T032 [P] [US1] Create jobs store (Zustand): active job_id, status, stage, progress, resource data, SSE connection lifecycle (subscribe on job start, update on event, unsubscribe on complete/cancel), isJobRunning computed flag for concurrency guard (FR-085) in renderer/src/stores/jobs.ts
- [ ] T033 [US1] Implement SingleCreation page — Step 1 Script Input: textarea with real-time character counter showing current/3000 (FR-020/020a), over-limit warning styling, auto-split preview count (segments = ceil(length/120)), paste support in renderer/src/pages/SingleCreation.tsx
- [ ] T034 [US1] Implement SingleCreation page — Step 2 Voice Selection: voice template list fetched from GET /voice-templates?status=ready, selectable cards (name, duration, created_at per FR-032), voice params panel with speed slider (0.5-2.0), volume slider (0.5-2.0), style dropdown enum with "中性/自然（推荐）" default selected + marked as recommended (FR-033a/033c) in renderer/src/pages/SingleCreation.tsx
- [ ] T035 [US1] Implement SingleCreation page — Step 3 Avatar Upload: file picker restricted to jpg/png via dialog filter, image preview thumbnail, delete + re-upload buttons, frontend pre-validation (file type check), backend validation error display (INVALID_IMAGE_FORMAT/IMAGE_TOO_SMALL) in renderer/src/pages/SingleCreation.tsx
- [ ] T036 [US1] Implement SingleCreation page — Step 4 Video Settings: resolution radio toggle (1080P "推荐·高清" default / 720P "更快·更稳定" per FR-041), subtitle options (external SRT + burned-in defaults), output directory selector via system.selectDirectory() in renderer/src/pages/SingleCreation.tsx
- [ ] T037 [US1] Implement SingleCreation page — Step 5 Generate: config summary showing all params (resolution, voice template name, style/speed/volume with non-default values highlighted per FR-033d), "开始生成" button disabled when isJobRunning (FR-085) with tooltip, call POST /pipeline/single on click, transition to progress view in renderer/src/pages/SingleCreation.tsx
- [ ] T038 [US1] Implement ProgressBar component: progress bar (0-100%), current stage label (文案处理/语音合成/口型同步/视频合成/字幕生成), elapsed timer; SSE subscription via jobs store on job start; cancel button with confirmation dialog ("确认取消？取消后临时文件将被清理" per FR-051); on cancel success show "已取消" toast in renderer/src/components/ProgressBar.tsx
- [ ] T039 [P] [US1] Implement ResourceMonitor component: CPU/mem/VRAM gauge displays (VRAM shows "N/A（未使用 GPU）" for CPU mode per FR-080), data from SSE resource field via jobs store; non-blocking warning toast at VRAM≥90% or mem≥90% or disk<1GB (FR-081, not overlapping main content, include actionable suggestions: "建议关闭其他程序"/"下次可尝试720P"/"可在设置中切换推理模式"); auto-pause notification when status becomes 'paused' with reason + "恢复" button calling POST /pipeline/resume (FR-082) in renderer/src/components/ResourceMonitor.tsx
- [ ] T040 [US1] Implement generation complete view: success/fail status banner, subtitle status indicator (✓ ready / ⚠ failed with "字幕未生成，不影响视频" message per FR-061), "打开输出目录" button via system.showItemInFolder + "复制路径" button with clipboard feedback (FR-090), "查看字幕" link via system.openPath + "复制字幕文本" via system.readTextFile(srt_path) + clipboard copy with success toast (FR-062) in renderer/src/pages/SingleCreation.tsx

**Checkpoint**: User Story 1 MVP complete — offline single generation end-to-end works: script → voice → avatar → settings → generate with progress + resource monitoring → output MP4 + SRT → open directory. Cancel, auto-pause on resource exhaustion, concurrent generation blocking all functional.

### Tests — US1

- [ ] T070 [P] [US1] Unit tests for script_splitter: empty input → INVALID_SCRIPT, >3000 chars → SCRIPT_TOO_LONG, natural breakpoint splitting at 120 chars, preservation of semantic coherence, edge case: exactly 120 chars in python-engine/tests/unit/test_script_splitter.py
- [ ] T071 [P] [US1] Unit tests for image_processor: non-jpg/png → INVALID_IMAGE_FORMAT, below-min-resolution → IMAGE_TOO_SMALL, successful 512×512 resize with aspect preservation (center-crop), oversized image downscale in python-engine/tests/unit/test_image_processor.py
- [ ] T072 [P] [US1] Unit tests for job_manager single-job lifecycle: queued→running→succeeded, queued→running→failed, running→paused (resource), paused→running (resume), running→canceled (cleanup), concurrent guard (JOB_ALREADY_RUNNING rejection) in python-engine/tests/unit/test_job_manager.py
- [ ] T073 [P] [US1] Integration tests for pipeline API: POST /pipeline/single returns 202 + job_id, GET /pipeline/progress/{job_id} returns SSE stream with correct event shape (stage/progress/message/resource), POST /pipeline/cancel/{job_id} returns 200, concurrent POST returns 409 + JOB_ALREADY_RUNNING in python-engine/tests/integration/test_pipeline_api.py
- [ ] T074 [P] [US1] Integration test for jobs API: GET /jobs/{job_id}/state returns correct snapshot, GET /jobs?status=succeeded returns list with limit support in python-engine/tests/integration/test_jobs_api.py

---

## Phase 4: User Story 2 — 声音克隆与声音模板管理 (Priority: P2)

**Goal**: Upload local audio (MP3/WAV) → extract voice features via CosyVoice3 → save as reusable template with unique name. List, select for generation, delete with confirmation.

**Independent Test**: Upload compliant WAV (≥30s, ≤100MB) → see extraction progress → name template (unique name enforced) → verify in template list → select in SingleCreation → delete with confirm → verify hard-deleted.

### Backend — Voice Template Infrastructure

- [ ] T041 [P] [US2] Create V003 migration: voice_templates table DDL (id TEXT PK, name TEXT NOT NULL UNIQUE, created_at, source_audio_path, source_audio_duration_seconds, source_audio_size_bytes, format, status, features_path, error_code, error_message per data-model.md); implement CRUD with hard delete in voice_templates_repo.py in python-engine/src/storage/migrations/V003__voice_templates.sql + python-engine/src/storage/voice_templates_repo.py
- [ ] T042 [P] [US2] Implement voice cloner: accept audio file path, validate format MP3/WAV (VOICE_INVALID_FORMAT), validate duration≥30s via ffprobe (VOICE_TOO_SHORT), validate size≤100MB (VOICE_TOO_LARGE), validate name non-empty (VOICE_NAME_EMPTY) + unique (VOICE_NAME_DUPLICATE per FR-032a + research #14), extract CosyVoice3 speaker embedding, save features file, report progress percentage, update status processing→ready/failed in python-engine/src/core/voice_cloner.py
- [ ] T043 [US2] Implement voice template routes: GET /voice-templates (list with optional status filter, return id/name/created_at/duration/format/status), POST /voice-templates/upload (multipart audio+name, validate, create record as processing, start async extraction, return 202), GET /voice-templates/{id}/progress (SSE with progress/message, terminal event with status ready/failed), DELETE /voice-templates/{id} (hard delete record + features file + audio copy, return 204 or NOT_FOUND) in python-engine/src/api/routes/voice_templates.py

### Frontend — Voice Template Management UI

- [ ] T044 [P] [US2] Create voice-templates store (Zustand): template list, selected template id, loading state, upload/extraction progress tracking in renderer/src/stores/voice-templates.ts
- [ ] T045 [P] [US2] Create voice-templates service: listTemplates(), uploadTemplate(file, name) as multipart, subscribeExtractionProgress(id) as SSE, deleteTemplate(id) in renderer/src/services/voice-templates.ts
- [ ] T046 [US2] Implement VoiceManager page: audio upload zone (accept MP3/WAV, show validation errors for wrong format/too short <30s/too large >100MB per FR-031), extraction progress bar with SSE, name input field with uniqueness check on blur (FR-032a), template list table (name, created_at, source duration per FR-032), delete button per row with confirmation dialog "删除后不可恢复" (FR-034) in renderer/src/pages/VoiceManager.tsx
- [ ] T047 [US2] Update SingleCreation Step 2 voice selection: fetch templates from voice-templates store, show selection cards with ready status filter, display selected template info, integrate with project config store voice_template_id in renderer/src/pages/SingleCreation.tsx
- [ ] T048 [US2] Enhance config summary in Step 5: ensure selected voice template name + effective style/speed/volume are shown clearly, highlight any non-default values to avoid user confusion (FR-033d) in renderer/src/pages/SingleCreation.tsx

**Checkpoint**: User Story 2 complete — upload audio → extraction with progress → save with unique name → list/select/delete templates → selected template flows into single generation.

### Tests — US2

- [ ] T075 [P] [US2] Unit tests for voice_cloner: non-MP3/WAV → VOICE_INVALID_FORMAT, <30s → VOICE_TOO_SHORT, >100MB → VOICE_TOO_LARGE, empty name → VOICE_NAME_EMPTY, duplicate name → VOICE_NAME_DUPLICATE, successful extraction → status ready in python-engine/tests/unit/test_voice_cloner.py
- [ ] T076 [P] [US2] Integration tests for voice-templates API: POST /voice-templates/upload returns 202 + processing status, GET /voice-templates lists ready templates, GET /voice-templates/{id}/progress returns SSE stream, DELETE /voice-templates/{id} returns 204 + hard delete verified, duplicate name POST returns 409 + VOICE_NAME_DUPLICATE in python-engine/tests/integration/test_voice_templates_api.py

---

## Phase 5: User Story 3 — 批量生成 (Priority: P3)

**Goal**: Import scripts from TXT (UTF-8/BOM/GBK) or XLSX (first column), cap at ≤30, configure shared avatar + voice + resolution, serial batch generation. Per-item status monitoring. Failed item retry. Crash recovery with resume on restart.

**Independent Test**: Import 3-item TXT → start batch → verify serial execution (one at a time) with per-item status → force-kill app → restart → see resume prompt → click "继续" → verify completed items preserved + current item restarted.

### Backend — Batch Execution

- [ ] T049 [P] [US3] Implement TXT importer: read file bytes, auto-detect encoding (UTF-8/UTF-8 BOM/GBK via chardet per research #5), decode to string, split by newlines, strip whitespace, filter empty lines, cap at 30 items with notification (FR-071, BATCH_LIMIT_EXCEEDED if original count >30) in python-engine/src/core/importers.py
- [ ] T050 [P] [US3] Implement XLSX importer: read .xlsx via openpyxl, extract first column values as strings, filter empty cells, cap at 30 items in python-engine/src/core/importers.py
- [ ] T051 [US3] Create V004 migration: batch_jobs + batch_items tables DDL per data-model.md (batch_id, type, config fields, status with DEFAULT 'queued', cursor_index DEFAULT 0, timestamps; item_id, batch_id FK, idx, script_text, status DEFAULT 'waiting', output fields, error fields); extend jobs_repo.py with batch CRUD (insert batch+items, update cursor/item status, get batch state with items, query by status) in python-engine/src/storage/migrations/V004__batch_tables.sql + python-engine/src/storage/jobs_repo.py
- [ ] T052 [US3] Extend job manager for batch execution: create batch with UUID batch_id + items, concurrent guard reuse (JOB_ALREADY_RUNNING per FR-085), serial execution via cursor_index (advance after each item), per-item pipeline execution (reuse single job pipeline stages), fail-continue strategy (mark item failed + record error + advance cursor per FR-073), batch status transitions (queued→running→succeeded/failed/canceled, running→paused on resource), SSE progress with batch fields (current_item_index, total_items, item_status per contracts) in python-engine/src/core/job_manager.py
- [ ] T053 [US3] Implement startup recovery: on server lifespan startup query for jobs/batch_jobs with status running/paused, reset in-progress items to 'waiting' (item was running at crash → treat as not-completed per FR-074), log recovery candidates; expose via existing GET /jobs?status= endpoint in python-engine/src/core/job_manager.py
- [ ] T054 [US3] Implement batch pipeline route: POST /pipeline/batch (validate items array ≤30 per FR-071, each script_text non-empty + ≤3000, JOB_ALREADY_RUNNING guard, create batch, return 202 + batch_id); batch SSE progress via existing GET /pipeline/progress/{batch_id} with batch-specific fields in python-engine/src/api/routes/pipeline.py
- [ ] T055 [US3] Implement batch item retry route: POST /pipeline/batch/{batch_id}/retry/{item_id} (validate batch exists, validate item is in 'failed' status else INVALID_STATE, reset item to 'waiting', execute single item pipeline, return 202) per FR-075 in python-engine/src/api/routes/pipeline.py
- [ ] T056 [US3] Implement batch cancel: extend POST /pipeline/cancel/{batch_id} for batch type (stop remaining items, cancel current in-progress item best-effort, cleanup temp files for current item, preserve completed item outputs, set remaining as canceled, update batch status per FR-076) in python-engine/src/api/routes/pipeline.py

### Frontend — Batch Creation UI

- [ ] T057 [P] [US3] Extend jobs store for batch tracking: batch_id, items array with per-item {id, index, status, progress, error}, summary computed values (total/succeeded/failed/waiting/running), SSE subscription for batch events in renderer/src/stores/jobs.ts
- [ ] T058 [US3] Implement BatchCreation page — Import panel: file upload button (TXT or XLSX filter), import progress indicator, preview table (row number, script text truncated, edit button, delete button per row), clear all button, item count display "N/30 条" with warning when original import exceeded 30 (FR-071), manual text input area as alternative in renderer/src/pages/BatchCreation.tsx
- [ ] T059 [US3] Implement BatchCreation page — Config panel: shared avatar upload (reuse component from SingleCreation Step 3), voice template selector (reuse from VoiceManager integration), voice params (speed/volume/style with defaults), resolution toggle, output directory selector, config summary with all effective values in renderer/src/pages/BatchCreation.tsx
- [ ] T060 [US3] Implement BatchCreation page — Monitoring panel: per-item status table (columns: #, script preview, status badge waiting/running/succeeded/failed, progress bar for running item, error message expandable for failed), overall summary bar (X succeeded, Y failed, Z waiting per FR-073), cancel batch button with confirmation dialog (FR-076), retry button per failed item (FR-075) in renderer/src/pages/BatchCreation.tsx
- [ ] T061 [US3] Implement RecoveryDialog component: on App.tsx mount call GET /jobs?status=running,paused, if results contain batch jobs show modal with batch info (created_at, N items total, X completed, Y remaining), "继续未完成任务" button (POST /pipeline/resume/{batch_id}), "放弃并清空" button (POST /pipeline/cancel/{batch_id} + cleanup), dismiss closes dialog (FR-074) in renderer/src/components/RecoveryDialog.tsx
- [ ] T062 [US3] Wire BatchCreation to APIs: POST /pipeline/batch on start, SSE subscription for batch progress, cancel via POST /pipeline/cancel, retry via POST /pipeline/batch/{id}/retry/{item_id}, integrate RecoveryDialog into App.tsx startup lifecycle in renderer/src/pages/BatchCreation.tsx

**Checkpoint**: User Story 3 complete — import TXT/XLSX → preview/edit items → configure shared settings → serial batch with per-item status → fail-continue → retry failed → cancel preserves completed → crash recovery with resume.

### Tests — US3

- [ ] T077 [P] [US3] Unit tests for importers: TXT UTF-8/BOM/GBK encoding detection, XLSX first-column extraction, empty-line filtering, cap at 30 items with truncation notification in python-engine/tests/unit/test_importers.py
- [ ] T078 [P] [US3] Unit tests for batch job_manager: serial execution (items run one at a time), fail-continue (failed item does not block next), cursor_index advancement, cancel preserves completed items, resume from first non-succeeded item (skipping failed per FR-075) in python-engine/tests/unit/test_batch_job_manager.py
- [ ] T079 [P] [US3] Integration tests for batch API: POST /pipeline/batch returns 202, batch SSE includes current_item_index/total_items, POST /pipeline/batch/{id}/retry/{item_id} validates failed status, concurrent batch rejected with JOB_ALREADY_RUNNING in python-engine/tests/integration/test_batch_api.py

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Cross-story refinements, consistency hardening, and final validation.

- [ ] T063 [P] Create comprehensive error-to-user-message mapping (Chinese): all error codes from contracts (INVALID_SCRIPT→"文案不能为空", SCRIPT_TOO_LONG→"文案超过3000字上限", JOB_ALREADY_RUNNING→"有任务正在执行，请等待完成或取消后重试", VOICE_*→音频相关提示, RESOURCE_CRITICAL→资源预警+可执行建议, etc.) in renderer/src/utils/error-messages.ts
- [ ] T064 [P] Implement Home page: quick-start buttons (新建视频→SingleCreation, 批量制作→BatchCreation, 查看作品→WorksLibrary), recent 3 generation records from GET /jobs?status=succeeded (latest), tutorial/guide placeholder in renderer/src/pages/Home.tsx
- [ ] T065 [P] Add inference mode setting to Settings page: "推理模式" section with auto/CPU/GPU radio (default auto per FR-083), GPU compatibility check trigger via POST /api/system/gpu-check, hardware info display via GET /api/system/hardware in renderer/src/pages/Settings.tsx
- [ ] T066 Implement concurrency guard integration: on SingleCreation and BatchCreation page mount, check isJobRunning from jobs store (populated via GET /jobs?status=running,paused), disable "开始生成"/"开始批量" buttons with tooltip "有任务正在执行中" (FR-085), auto-refresh on job completion in renderer/src/stores/jobs.ts + renderer/src/pages/SingleCreation.tsx + renderer/src/pages/BatchCreation.tsx
- [ ] T067 Validate all API endpoints match contracts/ipc-api.md: verify request schemas, response shapes, error codes, SSE event formats across all route files in python-engine/src/api/routes/
- [ ] T068 Add offline assertion: verify no external network calls in pipeline execution path (wrap httpx/requests to assert only 127.0.0.1 calls during generation), log violations in python-engine/src/api/server.py
- [ ] T069 Run quickstart.md smoke test: engine handshake, single generation end-to-end (MP4+SRT output), voice template upload+extract+delete cycle, batch 3-item serial generation, cancel during generation, resource monitor display, output directory navigation, works library offline access verification

### Tests — E2E & Build

- [ ] T080 [P] E2E test: single generation full flow — launch app → upload avatar → input script → select voice → generate → verify progress SSE updates → verify MP4 + SRT in output dir → verify "打开输出目录" works in electron-app/tests/e2e/single-generation.spec.ts (Playwright)
- [ ] T081 [P] E2E test: batch resume flow — launch app → import 3-item TXT → start batch → force-terminate during item 2 → relaunch → verify recovery dialog → click resume → verify item 1 preserved, item 2 restarts in electron-app/tests/e2e/batch-resume.spec.ts (Playwright)
- [ ] T082 Configure model bundling: add CosyVoice3-0.5B and Wav2Lip model directories to electron-builder.yml extraResources, ensure models are copied to app resources during build, verify models available at runtime via model_manager.py path resolution (FR-001a) in electron-app/electron-builder.yml + python-engine/src/core/model_manager.py

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup)
  └─→ Phase 2 (Foundational) ── BLOCKS ALL ──┐
                                               ├─→ Phase 3 (US1: Single Gen) ─→ MVP ✓
                                               ├─→ Phase 4 (US2: Voice Templates)
                                               └─→ Phase 5 (US3: Batch Gen)
                                                         │
                                               Phase 6 (Polish) ←─── after all stories
```

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — **BLOCKS all user stories**
- **Phase 3 (US1)**: Depends on Phase 2 — MVP deliverable
- **Phase 4 (US2)**: Depends on Phase 2; integrates with US1 SingleCreation page (T047-T048)
- **Phase 5 (US3)**: Depends on Phase 2; extends US1 job_manager + reuses UI components
- **Phase 6 (Polish)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Standalone after Phase 2 — full single generation pipeline
- **US2 (P2)**: Backend independent; frontend touches SingleCreation (requires Phase 3 T034 voice selection UI)
- **US3 (P3)**: Backend extends job_manager from US1 (requires T028); frontend reuses config components

**Recommended execution order**: Phase 1 → Phase 2 → Phase 3 (US1) → Phase 4 (US2) → Phase 5 (US3) → Phase 6

### Within Each User Story

1. Storage/migrations before repositories
2. Core modules (engine wrappers, processors) before orchestrators (job_manager)
3. API routes after core + storage
4. Frontend stores before pages
5. Frontend services before page wiring

### Parallel Opportunities

**Phase 1**: T002, T003, T004, T005 all parallel (independent projects)
**Phase 2 Backend**: T007, T009, T010, T011, T012, T013, T014 parallel after T006+T008
**Phase 2 Frontend**: T016, T017, T018, T020 parallel after T015
**US1 Core**: T021, T022, T023, T024, T025 parallel (independent pipeline components)
**US1 Frontend**: T031, T032, T039 parallel (independent stores/components)
**US1 Tests**: T070, T071, T072, T073, T074 all parallel (independent test files)
**US2**: T041, T042 parallel (schema + cloner); T044, T045 parallel (store + service)
**US2 Tests**: T075, T076 parallel
**US3**: T049, T050 parallel (importers); T057 parallel with backend tasks
**US3 Tests**: T077, T078, T079 all parallel
**Polish**: T063, T064, T065 all parallel; T080, T081 parallel (E2E tests)

---

## Parallel Example: US1 Backend Pipeline

```text
# Wave 1 — All independent pipeline components (5 parallel agents):
Agent 1: T021 — image_processor.py (validate + resize)
Agent 2: T022 — script_splitter.py (validate + split)
Agent 3: T023 — tts_engine.py (CosyVoice3 wrapper)
Agent 4: T024 — lipsync_engine.py (Wav2Lip wrapper)
Agent 5: T025 — subtitle_generator.py (SRT + hardcoded)

# Wave 2 — Orchestration (sequential, depends on Wave 1):
T026 — video_synthesizer.py (FFmpeg pipeline using all above)
T027 — jobs_repo.py (table schema + CRUD)
T028 — job_manager.py (orchestrates pipeline + concurrency + pause/resume)

# Wave 3 — API exposure (depends on Wave 2):
T029 — pipeline routes (HTTP endpoints)
T030 — jobs routes (query endpoints)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (5 tasks, ~1 session)
2. Complete Phase 2: Foundational (15 tasks, ~2-3 sessions)
3. Complete Phase 3: User Story 1 (20 tasks, ~3-4 sessions)
4. **STOP and VALIDATE**: Offline single generation end-to-end
5. Demo/deliver MVP (~40 tasks total)

### Incremental Delivery

| Milestone | Cumulative Tasks | Deliverable |
|-----------|-----------------|-------------|
| Foundation | 20 | Dev environment, shell app, IPC working |
| + US1 (MVP) | 45 | Single video generation, full pipeline + tests |
| + US2 | 55 | Voice cloning + template management + tests |
| + US3 | 72 | Batch generation + resume + retry + tests |
| + Polish | 82 | Production quality, E2E, model bundling |

---

## Summary

| Phase | Tasks | ID Range | Scope |
|-------|-------|----------|-------|
| Phase 1: Setup | 5 | T001–T005 | Project initialization |
| Phase 2: Foundational | 15 | T006–T020 | DB, server, Electron, React shell, IPC |
| Phase 3: US1 Single Gen | 20 + 5 tests | T021–T040, T070–T074 | Pipeline core + single generation UI (MVP) |
| Phase 4: US2 Voice Templates | 8 + 2 tests | T041–T048, T075–T076 | Voice cloning + template CRUD |
| Phase 5: US3 Batch Gen | 14 + 3 tests | T049–T062, T077–T079 | Batch import + serial execution + resume |
| Phase 6: Polish | 7 + 2 E2E + 1 build | T063–T069, T080–T082 | Error UX, home, settings, E2E, model bundling |
| **Total** | **82** | | |

## Notes

- [P] tasks = different files, no dependencies within same phase
- [US1/US2/US3] maps task to specific user story for traceability
- Each user story delivers an independently testable increment
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Core models (CosyVoice3-0.5B, Wav2Lip) bundled into installer via T082 (FR-001a)
- License module (contracts/license.md) out of V1.3 scope; dev mode bypasses auth
- Test tasks (T070-T081) satisfy Constitution V testability requirement; pytest for backend, Vitest for frontend, Playwright for E2E
