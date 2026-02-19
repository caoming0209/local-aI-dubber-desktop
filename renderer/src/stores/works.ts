import { create } from 'zustand';
import { api } from '../services/engine';
import type {
  Work,
  WorkDetail,
  WorksListResponse,
  WorksQueryParams,
} from '@shared/ipc-types';

interface WorksState {
  works: Work[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  loading: boolean;
  error: string | null;
  query: WorksQueryParams;
  loadWorks: (params?: Partial<WorksQueryParams>) => Promise<void>;
  getWork: (id: string) => Promise<WorkDetail | null>;
  renameWork: (id: string, name: string) => Promise<boolean>;
  deleteWork: (id: string) => Promise<boolean>;
  batchDelete: (ids: string[]) => Promise<boolean>;
  clearAll: () => Promise<boolean>;
}

export const useWorksStore = create<WorksState>((set, get) => ({
  works: [],
  total: 0,
  page: 1,
  pageSize: 12,
  totalPages: 0,
  loading: false,
  error: null,
  query: {},

  loadWorks: async (params) => {
    const query = { ...get().query, ...params };
    set({ loading: true, error: null, query });

    const searchParams = new URLSearchParams();
    if (query.search) searchParams.set('search', query.search);
    if (query.aspect_ratio) searchParams.set('aspect_ratio', query.aspect_ratio);
    if (query.date_range) searchParams.set('date_range', query.date_range);
    if (query.sort) searchParams.set('sort', query.sort);
    searchParams.set('page', String(query.page ?? 1));
    searchParams.set('page_size', String(query.page_size ?? 12));

    const res = await api.get<WorksListResponse>(`/api/works?${searchParams}`);
    if (res.success && res.data) {
      set({
        works: res.data.items,
        total: res.data.total,
        page: res.data.page,
        pageSize: res.data.page_size,
        totalPages: res.data.total_pages,
        loading: false,
      });
    } else {
      set({ loading: false, error: res.error?.message ?? '加载作品失败' });
    }
  },

  getWork: async (id) => {
    const res = await api.get<WorkDetail>(`/api/works/${id}`);
    return res.success && res.data ? res.data : null;
  },

  renameWork: async (id, name) => {
    const res = await api.patch(`/api/works/${id}`, { name });
    if (res.success) {
      await get().loadWorks();
      return true;
    }
    return false;
  },

  deleteWork: async (id) => {
    const res = await api.delete(`/api/works/${id}`);
    if (res.success) {
      await get().loadWorks();
      return true;
    }
    return false;
  },

  batchDelete: async (ids) => {
    const res = await api.delete('/api/works', { ids });
    if (res.success) {
      await get().loadWorks();
      return true;
    }
    return false;
  },

  clearAll: async () => {
    const res = await api.delete('/api/works/all', { confirm: true });
    if (res.success) {
      await get().loadWorks();
      return true;
    }
    return false;
  },
}));
