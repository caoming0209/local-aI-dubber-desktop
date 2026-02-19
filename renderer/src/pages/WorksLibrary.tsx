import React, { useEffect, useState } from 'react';
import { PlayCircle, FolderOpen, Trash2, Edit, Search, Filter, ChevronLeft, ChevronRight } from 'lucide-react';
import { useWorksStore } from '../stores/works';
import type { AspectRatio } from '@shared/ipc-types';

const WorksLibrary: React.FC = () => {
  const { works, total, page, totalPages, loading, loadWorks, deleteWork, renameWork } = useWorksStore();
  const [search, setSearch] = useState('');
  const [aspectFilter, setAspectFilter] = useState<string>('');
  const [sortBy, setSortBy] = useState('created_at_desc');

  useEffect(() => {
    loadWorks();
  }, []);

  const handleSearch = () => {
    loadWorks({ search, aspect_ratio: aspectFilter as AspectRatio, sort: sortBy as any, page: 1 });
  };

  const handlePageChange = (newPage: number) => {
    loadWorks({ page: newPage });
  };

  const handleDelete = async (id: string, name: string) => {
    if (confirm(`确定删除「${name}」？视频文件将同时被删除。`)) {
      await deleteWork(id);
    }
  };

  const handleRename = async (id: string, currentName: string) => {
    const newName = prompt('输入新名称', currentName);
    if (newName && newName !== currentName) {
      await renameWork(id, newName);
    }
  };

  const handleOpenFolder = () => {
    if (window.electronAPI) {
      window.electronAPI.system.selectDirectory();
    }
  };

  const formatDate = (iso: string) => {
    try {
      return new Date(iso).toLocaleString('zh-CN');
    } catch {
      return iso;
    }
  };

  const formatDuration = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-slate-800">作品库</h1>
        <button onClick={handleOpenFolder} className="text-sm font-medium text-indigo-600 hover:text-indigo-700 flex items-center bg-indigo-50 hover:bg-indigo-100 px-4 py-2 rounded-lg transition-all active:scale-95">
          <FolderOpen size={18} className="mr-2" /> 打开本地文件夹
        </button>
      </div>

      {/* Search & Filter Bar */}
      <div className="flex items-center gap-3 mb-6">
        <div className="flex-1 relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="搜索作品名称..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            className="w-full pl-9 pr-4 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
          />
        </div>
        <select
          title="画面比例筛选"
          value={aspectFilter}
          onChange={(e) => { setAspectFilter(e.target.value); loadWorks({ aspect_ratio: e.target.value as AspectRatio, page: 1 }); }}
          className="px-3 py-2 border border-slate-200 rounded-lg text-sm bg-white"
        >
          <option value="">全部比例</option>
          <option value="16:9">横屏 16:9</option>
          <option value="9:16">竖屏 9:16</option>
        </select>
        <select
          title="排序方式"
          value={sortBy}
          onChange={(e) => { setSortBy(e.target.value); loadWorks({ sort: e.target.value as any, page: 1 }); }}
          className="px-3 py-2 border border-slate-200 rounded-lg text-sm bg-white"
        >
          <option value="created_at_desc">最新优先</option>
          <option value="created_at_asc">最早优先</option>
          <option value="duration">时长排序</option>
        </select>
      </div>

      {/* Works Grid */}
      {loading ? (
        <div className="flex items-center justify-center py-20 text-slate-400">加载中...</div>
      ) : works.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-slate-400">
          <Film size={48} className="mb-4 opacity-50" />
          <p>暂无作品，快去创建第一条视频吧</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {works.map((work) => (
            <div key={work.id} className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden group hover:shadow-lg hover:border-indigo-200 hover:-translate-y-1 transition-all duration-300">
              <div className="aspect-video relative bg-slate-100 overflow-hidden">
                {work.thumbnail_path ? (
                  <img src={`file://${work.thumbnail_path}`} alt={work.name} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700" />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-slate-300">
                    <PlayCircle size={48} />
                  </div>
                )}
                <div className="absolute inset-0 bg-black/30 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer duration-300">
                  <PlayCircle size={48} className="text-white drop-shadow-lg hover:scale-110 transition-transform" />
                </div>
                <div className="absolute bottom-2 right-2 bg-black/60 backdrop-blur-sm text-white text-[10px] px-1.5 py-0.5 rounded">
                  {formatDuration(work.duration_seconds)}
                </div>
                {work.is_trial_watermark && (
                  <div className="absolute top-2 left-2 bg-yellow-400 text-yellow-900 text-[10px] px-2 py-0.5 rounded font-bold shadow-sm">
                    试用
                  </div>
                )}
              </div>
              <div className="p-4">
                <div className="flex justify-between items-start mb-2">
                  <h3 className="font-bold text-slate-800 truncate pr-2 group-hover:text-indigo-700 transition-colors" title={work.name}>{work.name}</h3>
                  <span className="text-[10px] text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded flex-shrink-0">{work.aspect_ratio}</span>
                </div>
                <div className="text-xs text-slate-500 mb-4">
                  {formatDate(work.created_at)}
                </div>
                <div className="flex border-t border-slate-100 pt-3">
                  <button onClick={() => handleRename(work.id, work.name)} className="flex-1 flex items-center justify-center text-xs font-medium text-slate-600 hover:text-indigo-600 hover:bg-indigo-50 py-1.5 rounded transition-all active:scale-95 border-r border-slate-100">
                    <Edit size={14} className="mr-1.5" /> 重命名
                  </button>
                  <button onClick={() => handleDelete(work.id, work.name)} className="flex-1 flex items-center justify-center text-xs font-medium text-slate-600 hover:text-red-600 hover:bg-red-50 py-1.5 rounded transition-all active:scale-95">
                    <Trash2 size={14} className="mr-1.5" /> 删除
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 mt-8">
          <button
            onClick={() => handlePageChange(page - 1)}
            disabled={page <= 1}
            title="上一页"
            className="p-2 rounded-lg border border-slate-200 hover:bg-slate-50 disabled:opacity-30 disabled:cursor-not-allowed"
          >
            <ChevronLeft size={16} />
          </button>
          <span className="text-sm text-slate-600 px-3">
            {page} / {totalPages}
          </span>
          <button
            onClick={() => handlePageChange(page + 1)}
            disabled={page >= totalPages}
            title="下一页"
            className="p-2 rounded-lg border border-slate-200 hover:bg-slate-50 disabled:opacity-30 disabled:cursor-not-allowed"
          >
            <ChevronRight size={16} />
          </button>
          <span className="text-xs text-slate-400 ml-2">共 {total} 条</span>
        </div>
      )}
    </div>
  );
};

// Need Film icon for empty state
import { Film } from 'lucide-react';

export default WorksLibrary;
