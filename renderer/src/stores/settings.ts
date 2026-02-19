import { create } from 'zustand';
import { api } from '../services/engine';
import type { AppSettings } from '../../shared/ipc-types';

const DEFAULT_SETTINGS: AppSettings = {
  autoStartOnBoot: false,
  defaultVideoSavePath: '',
  theme: 'light',
  language: 'zh-CN',
  modelStoragePath: '',
  downloadSpeedLimitKBps: 0,
  autoDownloadModels: true,
  inferenceMode: 'auto',
  cpuUsageLimitPercent: 0,
  autoClearCacheEnabled: false,
  autoClearCycleDays: 7,
  autoCheckUpdate: true,
  updatedAt: new Date().toISOString(),
};

interface SettingsState {
  settings: AppSettings;
  loading: boolean;
  error: string | null;
  loadSettings: () => Promise<void>;
  updateSettings: (partial: Partial<AppSettings>) => Promise<void>;
}

export const useSettingsStore = create<SettingsState>((set, get) => ({
  settings: DEFAULT_SETTINGS,
  loading: false,
  error: null,

  loadSettings: async () => {
    set({ loading: true, error: null });
    const res = await api.get<AppSettings>('/api/settings');
    if (res.success && res.data) {
      set({ settings: res.data, loading: false });
      applyTheme(res.data.theme);
    } else {
      set({ loading: false, error: res.error?.message ?? '加载设置失败' });
    }
  },

  updateSettings: async (partial) => {
    set({ loading: true, error: null });
    const res = await api.put<AppSettings>('/api/settings', partial);
    if (res.success && res.data) {
      set({ settings: res.data, loading: false });
      if (partial.theme) {
        applyTheme(partial.theme);
      }
    } else {
      set({ loading: false, error: res.error?.message ?? '更新设置失败' });
    }
  },
}));

function applyTheme(theme: 'light' | 'dark') {
  if (theme === 'dark') {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }
}
