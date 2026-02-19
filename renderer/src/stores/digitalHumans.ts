import { create } from 'zustand';
import { api } from '../services/engine';
import type { DigitalHuman } from '@shared/ipc-types';

interface DigitalHumansState {
  items: DigitalHuman[];
  loading: boolean;
  error: string | null;
  loadDigitalHumans: (params?: { search?: string; source?: string; category?: string }) => Promise<void>;
  toggleFavorite: (id: string) => Promise<void>;
  deleteDigitalHuman: (id: string) => Promise<boolean>;
  uploadDigitalHuman: (file: File, name: string, category: string) => Promise<string | null>;
}

export const useDigitalHumansStore = create<DigitalHumansState>((set, get) => ({
  items: [],
  loading: false,
  error: null,

  loadDigitalHumans: async (params) => {
    set({ loading: true, error: null });
    const searchParams = new URLSearchParams();
    if (params?.search) searchParams.set('search', params.search);
    if (params?.source) searchParams.set('source', params.source);
    if (params?.category) searchParams.set('category', params.category);

    const qs = searchParams.toString();
    const res = await api.get<DigitalHuman[]>(`/api/digital-humans${qs ? `?${qs}` : ''}`);
    if (res.success && res.data) {
      set({ items: res.data, loading: false });
    } else {
      set({ loading: false, error: res.error?.message ?? '加载数字人列表失败' });
    }
  },

  toggleFavorite: async (id) => {
    await api.post(`/api/digital-humans/${id}/favorite`);
    await get().loadDigitalHumans();
  },

  deleteDigitalHuman: async (id) => {
    const res = await api.delete(`/api/digital-humans/${id}`);
    if (res.success) {
      await get().loadDigitalHumans();
      return true;
    }
    return false;
  },

  uploadDigitalHuman: async (file, name, category) => {
    // Upload via multipart form — need direct fetch since api helper uses JSON
    const port = window.electronAPI?.getEnginePort() ?? 18432;
    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', name);
    formData.append('category', category);

    try {
      let res: Response;
      if (typeof window !== 'undefined' && window.electronAPI) {
        // In Electron, use IPC — but upload needs special handling
        // For now, direct fetch to engine
        res = await fetch(`http://127.0.0.1:${port}/api/digital-humans/upload`, {
          method: 'POST',
          body: formData,
        });
      } else {
        res = await fetch(`http://127.0.0.1:${port}/api/digital-humans/upload`, {
          method: 'POST',
          body: formData,
        });
      }
      const data = await res.json();
      if (data.success) {
        await get().loadDigitalHumans();
        return data.data?.digital_human_id ?? null;
      }
      set({ error: data.error?.message ?? '上传失败' });
      return null;
    } catch (e: any) {
      set({ error: e.message ?? '上传失败' });
      return null;
    }
  },
}));
