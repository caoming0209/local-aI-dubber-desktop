import { create } from 'zustand';
import { api } from '../services/engine';
import type { LicenseStatus, ActivateResponse } from '../../shared/ipc-types';

interface LicenseState {
  status: LicenseStatus | null;
  loading: boolean;
  error: string | null;
  loadStatus: () => Promise<void>;
  activate: (code: string) => Promise<boolean>;
  unbind: () => Promise<boolean>;
}

export const useLicenseStore = create<LicenseState>((set) => ({
  status: null,
  loading: false,
  error: null,

  loadStatus: async () => {
    set({ loading: true, error: null });
    const res = await api.get<LicenseStatus>('/api/license/status');
    if (res.success && res.data) {
      set({ status: res.data, loading: false });
    } else {
      set({ loading: false, error: res.error?.message ?? '获取授权状态失败' });
    }
  },

  activate: async (code: string) => {
    set({ loading: true, error: null });
    const res = await api.post<ActivateResponse>('/api/license/activate', { activation_code: code });
    if (res.success && res.data) {
      set({
        status: {
          type: 'activated',
          used_trial_count: 5,
          max_trial_count: 5,
          remaining_trial_count: 0,
          activated_at: res.data.activated_at,
          activation_code_masked: res.data.activation_code_masked,
          device_count: res.data.device_count,
          max_device_count: res.data.max_device_count,
        },
        loading: false,
      });
      return true;
    }
    set({ loading: false, error: res.error?.message ?? '激活失败' });
    return false;
  },

  unbind: async () => {
    set({ loading: true, error: null });
    const res = await api.post('/api/license/unbind');
    if (res.success) {
      // Reload status after unbind
      const statusRes = await api.get<LicenseStatus>('/api/license/status');
      if (statusRes.success && statusRes.data) {
        set({ status: statusRes.data, loading: false });
      }
      return true;
    }
    set({ loading: false, error: res.error?.message ?? '解绑失败' });
    return false;
  },
}));
