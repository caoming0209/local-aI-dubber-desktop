// ─── 通用响应 ─────────────────────────────────────────────────
export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: ApiError;
}

export interface ApiError {
  code: ErrorCode;
  message: string;
}

export type ErrorCode =
  | 'MODEL_NOT_FOUND'
  | 'MODEL_LOADING'
  | 'MODEL_CORRUPTED'
  | 'MODEL_DOWNLOAD_INCOMPLETE'
  | 'INVALID_SCRIPT'
  | 'GPU_UNAVAILABLE'
  | 'INSUFFICIENT_DISK'
  | 'LICENSE_TRIAL_EXHAUSTED'
  | 'LICENSE_INVALID_CODE'
  | 'LICENSE_DEVICE_LIMIT'
  | 'LICENSE_NETWORK_ERROR'
  | 'LICENSE_ALREADY_ACTIVATED'
  | 'NOT_FOUND'
  | 'INTERNAL_ERROR';

// ─── 视频生成流水线 ───────────────────────────────────────────
export interface SinglePipelineRequest {
  script: string;
  voice_id: string;
  voice_params: VoiceParams;
  digital_human_id: string;
  background: Background;
  aspect_ratio: AspectRatio;
  subtitle: SubtitleConfig;
  bgm: BgmConfig;
  output_name: string;
}

export interface VoiceParams {
  speed: number;
  volume: number;
  emotion: number;
}

export interface Background {
  type: 'solid_color' | 'scene' | 'custom_image';
  value: string;
}

export type AspectRatio = '16:9' | '9:16';

export interface SubtitleConfig {
  enabled: boolean;
  font_family?: string;
  font_size?: number;
  color?: string;
  position?: 'bottom_center' | 'top_center';
}

export interface BgmConfig {
  enabled: boolean;
  bgm_id?: string | null;
  custom_path?: string | null;
  voice_volume?: number;
  bgm_volume?: number;
}

export interface PipelineJobResponse {
  job_id: string;
  estimated_steps: number;
}

export interface BatchPipelineRequest {
  scripts: { index: number; content: string }[];
  shared_config: Omit<SinglePipelineRequest, 'script' | 'output_name'>;
  output_settings: {
    save_path: string;
    name_prefix: string;
  };
}

export interface BatchJobResponse {
  job_id: string;
  total_count: number;
}

// ─── SSE 进度事件 ─────────────────────────────────────────────
export interface SingleProgressEvent {
  step: 'script_optimization' | 'tts' | 'lipsync' | 'synthesis' | 'completed' | 'failed' | 'timeout';
  step_index: number;
  total_steps: number;
  progress: number;
  message: string;
  result?: { work_id: string; file_path: string; duration_seconds: number };
  error?: ApiError;
}

export interface BatchProgressEvent {
  type: 'batch_item_start' | 'batch_item_progress' | 'batch_item_done' | 'batch_item_failed' | 'batch_completed';
  item_index?: number;
  total?: number;
  step?: string;
  progress?: number;
  message?: string;
  work_id?: string;
  error?: ApiError;
  succeeded?: number;
  failed?: number;
  failed_indices?: number[];
}

export type JobStatus = 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled' | 'not_found';

export interface JobState {
  job_id: string;
  status: JobStatus;
  current_step: string;
  step_index: number;
  total_steps: number;
  progress: number;
  created_at: string;
}

// ─── 作品库 ───────────────────────────────────────────────────
export interface Work {
  id: string;
  name: string;
  file_path: string;
  thumbnail_path: string;
  duration_seconds: number;
  resolution: string;
  aspect_ratio: AspectRatio;
  file_size_bytes: number;
  created_at: string;
  is_trial_watermark: boolean;
}

export interface WorkDetail extends Work {
  project_config: ProjectConfig;
}

export interface WorksListResponse {
  items: Work[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface WorksQueryParams {
  search?: string;
  aspect_ratio?: AspectRatio;
  date_range?: 'today' | 'yesterday' | 'last_7_days' | 'custom';
  date_from?: string;
  date_to?: string;
  sort?: 'created_at_desc' | 'created_at_asc' | 'duration';
  page?: number;
  page_size?: number;
}

// ─── 项目配置快照 ─────────────────────────────────────────────
export interface ProjectConfig {
  id: string;
  script: string;
  voice_id: string;
  voice_speed: number;
  voice_volume: number;
  voice_emotion: number;
  digital_human_id: string;
  background_type: string;
  background_value: string;
  aspect_ratio: AspectRatio;
  subtitle_enabled: boolean;
  subtitle_config: SubtitleConfig | null;
  bgm_enabled: boolean;
  bgm_id: string | null;
  bgm_custom_path: string | null;
  voice_volume_ratio: number;
  bgm_volume_ratio: number;
  created_at: string;
}

// ─── 数字人 ───────────────────────────────────────────────────
export type DigitalHumanCategory = 'male_host' | 'female_host' | 'professional' | 'friendly' | 'expert' | 'other';
export type DigitalHumanSource = 'official' | 'custom';
export type AdaptationStatus = 'ready' | 'processing' | 'failed' | 'pending';

export interface DigitalHuman {
  id: string;
  name: string;
  category: DigitalHumanCategory;
  source: DigitalHumanSource;
  thumbnail_path: string;
  preview_video_path: string;
  adapted_video_path: string | null;
  adaptation_status: AdaptationStatus;
  adaptation_error: string | null;
  is_favorited: boolean;
  favorited_at: string | null;
  created_at: string;
  sort_order: number;
}

// ─── 音色 ─────────────────────────────────────────────────────
export type VoiceCategory = 'male' | 'female' | 'emotional' | 'dialect';
export type DownloadStatus = 'not_downloaded' | 'downloading' | 'downloaded' | 'error';

export interface VoiceModel {
  id: string;
  name: string;
  category: VoiceCategory;
  description: string | null;
  model_size_mb: number;
  download_status: DownloadStatus;
  download_progress: number;
  model_path: string | null;
  download_url: string;
  is_emotional: boolean;
  is_favorited: boolean;
  favorited_at: string | null;
  sort_order: number;
}

// ─── BGM ──────────────────────────────────────────────────────
export type BgmCategory = 'upbeat' | 'soothing' | 'grand';
export type BgmSource = 'builtin' | 'custom';

export interface BgmTrack {
  id: string;
  name: string;
  category: BgmCategory;
  source: BgmSource;
  file_path: string;
  duration_seconds: number | null;
}

// ─── 设置 ──────────────────────────────────────────────────────
export interface AppSettings {
  autoStartOnBoot: boolean;
  defaultVideoSavePath: string;
  theme: 'light' | 'dark';
  language: 'zh-CN';
  modelStoragePath: string;
  downloadSpeedLimitKBps: number;
  autoDownloadModels: boolean;
  inferenceMode: 'auto' | 'cpu' | 'gpu';
  cpuUsageLimitPercent: number;
  autoClearCacheEnabled: boolean;
  autoClearCycleDays: number;
  autoCheckUpdate: boolean;
  updatedAt: string;
}

// ─── 授权 ──────────────────────────────────────────────────────
export type LicenseType = 'trial' | 'activated';

export interface LicenseStatus {
  type: LicenseType;
  used_trial_count: number;
  max_trial_count: number;
  remaining_trial_count: number;
  activated_at: string | null;
  activation_code_masked: string | null;
  device_count: number;
  max_device_count: number;
}

export interface ActivateRequest {
  activation_code: string;
}

export interface ActivateResponse {
  type: 'activated';
  activated_at: string;
  activation_code_masked: string;
  device_count: number;
  max_device_count: number;
}

// ─── 系统 ──────────────────────────────────────────────────────
export interface HardwareInfo {
  cpu: string;
  memory_gb: number;
  gpu: string;
  gpu_vram_gb: number;
  disk_free_gb: number;
  os: string;
}

export interface GpuCheckResult {
  gpu_available: boolean;
  cuda_version: string | null;
  recommendation: 'compatible' | 'incompatible' | 'not_detected';
}

export interface CacheInfo {
  size_mb: number;
}

export interface VersionInfo {
  current: string;
  latest: string | null;
  update_available: boolean;
}

// ─── Preload API 类型 ──────────────────────────────────────────
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

export interface FileFilter {
  name: string;
  extensions: string[];
}

export interface ElectronAPI {
  engine: {
    request<T = unknown>(method: HttpMethod, path: string, body?: object): Promise<ApiResponse<T>>;
  };
  pipeline: {
    subscribeProgress(
      jobId: string,
      onEvent: (data: SingleProgressEvent | BatchProgressEvent) => void,
      onDone: () => void,
      onError: (err: Error) => void,
    ): () => void;
  };
  system: {
    openPath(path: string): Promise<void>;
    showItemInFolder(path: string): Promise<void>;
    selectDirectory(): Promise<string | null>;
    selectFile(filters: FileFilter[]): Promise<string | null>;
  };
  getEnginePort(): number;
  toLocalFileUrl(filePath: string): string;
}

declare global {
  interface Window {
    electronAPI: ElectronAPI;
  }
}
