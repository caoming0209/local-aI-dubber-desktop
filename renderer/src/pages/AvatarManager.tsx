import React, { useEffect, useState, useRef } from 'react';
import { Plus, Search, Star, Trash2, Users, RefreshCw } from 'lucide-react';
import { useDigitalHumansStore } from '../stores/digitalHumans';

const AvatarManager: React.FC = () => {
  const { items, loading, loadDigitalHumans, toggleFavorite, deleteDigitalHuman, uploadDigitalHuman } = useDigitalHumansStore();
  const [search, setSearch] = useState('');
  const [sourceFilter, setSourceFilter] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadDigitalHumans();
  }, []);

  const handleSearch = () => {
    loadDigitalHumans({ search, source: sourceFilter });
  };

  const handleFilterChange = (source: string) => {
    setSourceFilter(source);
    loadDigitalHumans({ search, source });
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const name = file.name.replace(/\.[^.]+$/, '');
    await uploadDigitalHuman(file, name, 'other');
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleDelete = async (id: string, name: string) => {
    if (confirm(`确定删除「${name}」？相关文件将同时被删除。`)) {
      await deleteDigitalHuman(id);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-2xl font-bold text-slate-800">数字人管理</h1>
        <div className="flex space-x-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" size={18} />
            <input
              type="text"
              placeholder="搜索数字人..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              className="pl-10 pr-4 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent w-64 transition-all"
            />
          </div>
          <label className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium flex items-center hover:bg-indigo-700 shadow-sm hover:shadow active:scale-95 transition-all cursor-pointer">
            <Plus size={18} className="mr-2" /> 上传自定义形象
            <input ref={fileInputRef} type="file" accept="video/mp4" onChange={handleUpload} className="hidden" />
          </label>
        </div>
      </div>

      <div className="border-b border-slate-200 mb-6">
        <nav className="flex space-x-8">
          <button
            type="button"
            onClick={() => handleFilterChange('')}
            className={`border-b-2 py-4 px-1 text-sm font-medium transition-colors ${sourceFilter === '' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'}`}
          >
            全部数字人
          </button>
          <button
            type="button"
            onClick={() => handleFilterChange('official')}
            className={`border-b-2 py-4 px-1 text-sm font-medium transition-colors ${sourceFilter === 'official' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'}`}
          >
            官方
          </button>
          <button
            type="button"
            onClick={() => handleFilterChange('custom')}
            className={`border-b-2 py-4 px-1 text-sm font-medium transition-colors ${sourceFilter === 'custom' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'}`}
          >
            自定义
          </button>
        </nav>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20 text-slate-400">加载中...</div>
      ) : items.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-slate-400">
          <Users size={48} className="mb-4 opacity-50" />
          <p>暂无数字人</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-6">
          {items.map((avatar) => (
            <div key={avatar.id} className="group relative bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden hover:shadow-lg hover:-translate-y-1 transition-all duration-300">
              <div className="aspect-[3/4] relative overflow-hidden bg-slate-100">
                {avatar.thumbnail_path ? (
                  <img src={`file://${avatar.thumbnail_path}`} alt={avatar.name} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-slate-300"><Users size={32} /></div>
                )}
                <div className="absolute top-2 right-2">
                  <button
                    type="button" title="收藏"
                    onClick={() => toggleFavorite(avatar.id)}
                    className={`p-1.5 bg-white/80 backdrop-blur rounded-full hover:scale-110 active:scale-95 transition-all shadow-sm ${avatar.is_favorited ? 'text-yellow-400' : 'text-slate-400 hover:text-yellow-400'}`}
                  >
                    <Star size={14} fill={avatar.is_favorited ? 'currentColor' : 'none'} />
                  </button>
                </div>
                {avatar.source === 'custom' && (
                  <div className="absolute top-2 left-2 bg-indigo-600 text-white text-[10px] px-1.5 py-0.5 rounded font-medium shadow-sm">自定义</div>
                )}
                {avatar.adaptation_status === 'processing' && (
                  <div className="absolute inset-0 bg-black/50 flex items-center justify-center"><RefreshCw size={24} className="text-white animate-spin" /></div>
                )}
                {avatar.adaptation_status === 'failed' && (
                  <div className="absolute bottom-0 inset-x-0 bg-red-500 text-white text-[10px] text-center py-1">适配失败</div>
                )}
                <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                  {avatar.source === 'custom' && (
                    <button type="button" onClick={() => handleDelete(avatar.id, avatar.name)} className="px-3 py-1.5 bg-red-500 rounded-full text-xs font-bold text-white mr-2 hover:bg-red-600 active:scale-95 transition-all shadow-lg">删除</button>
                  )}
                  <button type="button" className="px-4 py-1.5 bg-white rounded-full text-xs font-bold text-slate-900 hover:bg-indigo-50 active:scale-95 shadow-lg">立即使用</button>
                </div>
              </div>
              <div className="p-3">
                <h3 className="font-medium text-slate-800 text-sm truncate">{avatar.name}</h3>
                <div className="flex gap-1 mt-1.5">
                  <span className="text-[10px] bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded">{avatar.category}</span>
                  <span className="text-[10px] bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded">{avatar.source === 'official' ? '官方' : '自定义'}</span>
                </div>
              </div>
            </div>
          ))}

          <label className="border-2 border-dashed border-slate-200 rounded-xl flex flex-col items-center justify-center aspect-[3/4] cursor-pointer hover:border-indigo-400 hover:bg-indigo-50 transition-all duration-300 group active:scale-[0.98]">
            <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center shadow-sm mb-3 group-hover:scale-110 group-hover:shadow-md transition-all">
              <Plus size={24} className="text-indigo-500" />
            </div>
            <span className="text-sm font-medium text-slate-600 group-hover:text-indigo-600 transition-colors">添加自定义数字人</span>
            <input type="file" accept="video/mp4" onChange={handleUpload} className="hidden" />
          </label>
        </div>
      )}
    </div>
  );
};

export default AvatarManager;
