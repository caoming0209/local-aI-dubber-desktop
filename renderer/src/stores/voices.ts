import { create } from 'zustand';
import { api } from '../services/engine';
import type { VoiceModel } from '@shared/ipc-types';

interface VoicesState {
  items: VoiceModel[];
  loading: boolean;
  error: string | null;
  loadVoices: (params?: { search?: string; category?: string; download_status?: string }) => Promise<void>;
  toggleFavorite: (id: string) => Promise<void>;
  startDownload: (id: string) => Promise<void>;
  pauseDownload: (id: string) => Promise<void>;
  resumeDownload: (id: string) => Promise<void>;
  deleteModel: (id: string) => Promise<boolean>;
  previewVoice: (id: string, text?: string) => Promise<void>;
}

export const useVoicesStore = create<VoicesState>((set, get) => ({
  items: [],
  loading: false,
  error: null,

  loadVoices: async (params) => {
    set({ loading: true, error: null });
    const searchParams = new URLSearchParams();
    if (params?.search) searchParams.set('search', params.search);
    if (params?.category) searchParams.set('category', params.category);
    if (params?.download_status) searchParams.set('download_status', params.download_status);

    const qs = searchParams.toString();
    const res = await api.get<VoiceModel[]>(`/api/voices${qs ? `?${qs}` : ''}`);
    if (res.success && res.data) {
      set({ items: res.data, loading: false });
    } else {
      set({ loading: false, error: res.error?.message ?? '加载音色列表失败' });
    }
  },

  toggleFavorite: async (id) => {
    await api.post(`/api/voices/${id}/favorite`);
    await get().loadVoices();
  },

  startDownload: async (id) => {
    await api.post(`/api/voices/${id}/download`);
    await get().loadVoices();
  },

  pauseDownload: async (id) => {
    await api.post(`/api/voices/${id}/download/pause`);
    await get().loadVoices();
  },

  resumeDownload: async (id) => {
    await api.post(`/api/voices/${id}/download/resume`);
    await get().loadVoices();
  },

  deleteModel: async (id) => {
    const res = await api.delete(`/api/voices/${id}/model`);
    if (res.success) {
      await get().loadVoices();
      return true;
    }
    return false;
  },

  previewVoice: async (id, text) => {
    const port = window.electronAPI?.getEnginePort() ?? 18432;
    try {
      const body: any = {};
      if (text) {
        body.text = text;
      }
      const res = await fetch(`http://127.0.0.1:${port}/api/voices/${id}/preview`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (res.ok) {
        const contentType = res.headers.get('content-type') || '';
        if (contentType.includes('audio/')) {
          const blob = await res.blob();
          const url = URL.createObjectURL(blob);
          const audio = new Audio(url);
          audio.play();
          audio.onended = () => URL.revokeObjectURL(url);
        } else {
          const data = await res.json();
          if (!data.success && data.error) {
            alert(data.error.message || '试听失败');
          }
        }
      } else {
        const data = await res.json().catch(() => ({}));
        alert(data.error?.message || '试听失败，请稍后重试');
      }
    } catch (err) {
      console.error('[voices] Preview error:', err);
      alert('试听失败，请检查网络连接');
    }
  },
}));
