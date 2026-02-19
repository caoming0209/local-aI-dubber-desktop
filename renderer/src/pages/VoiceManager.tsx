import React, { useEffect, useState } from 'react';
import { Play, Download, Trash2, Search, Star, Pause, Heart } from 'lucide-react';
import { useVoicesStore } from '../stores/voices';

const VoiceManager: React.FC = () => {
  const { items, loading, loadVoices, toggleFavorite, startDownload, pauseDownload, resumeDownload, deleteModel, previewVoice } = useVoicesStore();
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');

  useEffect(() => {
    loadVoices();
  }, []);

  const handleSearch = () => {
    loadVoices({ search, category: categoryFilter });
  };

  const handleCategoryChange = (category: string) => {
    setCategoryFilter(category);
    loadVoices({ search, category });
  };

  const handleDelete = async (id: string, name: string) => {
    if (confirm(`确定删除「${name}」的模型文件？记录将保留，可重新下载。`)) {
      await deleteModel(id);
    }
  };

  const categoryLabel = (cat: string) => {
    const map: Record<string, string> = { male: '男声', female: '女声', emotional: '情感', dialect: '方言' };
    return map[cat] ?? cat;
  };

  const statusLabel = (status: string) => {
    const map: Record<string, { text: string; cls: string }> = {
      downloaded: { text: '已下载', cls: 'bg-green-100 text-green-700 border-green-200' },
      downloading: { text: '下载中', cls: 'bg-blue-100 text-blue-700 border-blue-200' },
      not_downloaded: { text: '未下载', cls: 'bg-slate-100 text-slate-500 border-slate-200' },
      error: { text: '下载失败', cls: 'bg-red-100 text-red-600 border-red-200' },
    };
    const s = map[status] ?? map.not_downloaded;
    return <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${s.cls}`}>{s.text}</span>;
  };

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-2xl font-bold text-slate-800">音色管理</h1>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" size={18} />
          <input
            type="text"
            placeholder="搜索音色..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            className="pl-10 pr-4 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent w-64 transition-all"
          />
        </div>
      </div>

      <div className="border-b border-slate-200 mb-6">
        <nav className="flex space-x-8">
          {[{ key: '', label: '全部' }, { key: 'male', label: '男声' }, { key: 'female', label: '女声' }, { key: 'emotional', label: '情感' }, { key: 'dialect', label: '方言' }].map(tab => (
            <button
              key={tab.key}
              type="button"
              onClick={() => handleCategoryChange(tab.key)}
              className={`border-b-2 py-4 px-1 text-sm font-medium transition-colors ${categoryFilter === tab.key ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'}`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20 text-slate-400">加载中...</div>
      ) : items.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-slate-400">
          <Play size={48} className="mb-4 opacity-50" />
          <p>暂无音色</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead className="bg-slate-50 text-slate-500 text-xs uppercase font-semibold">
              <tr>
                <th className="px-6 py-4">音色名称</th>
                <th className="px-6 py-4">分类</th>
                <th className="px-6 py-4">模型大小</th>
                <th className="px-6 py-4">状态</th>
                <th className="px-6 py-4 text-right">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {items.map((voice) => (
                <tr key={voice.id} className="hover:bg-slate-50 group transition-colors">
                  <td className="px-6 py-4">
                    <div className="flex items-center">
                      <button
                        type="button"
                        title="试听"
                        onClick={() => previewVoice(voice.id)}
                        disabled={voice.download_status !== 'downloaded'}
                        className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center mr-3 hover:bg-indigo-600 hover:text-white hover:scale-110 active:scale-95 transition-all shadow-sm disabled:opacity-40 disabled:cursor-not-allowed"
                      >
                        <Play size={14} fill="currentColor" />
                      </button>
                      <span className="font-medium text-slate-700">{voice.name}</span>
                      {voice.is_emotional && (
                        <span className="ml-2 text-[10px] bg-purple-100 text-purple-600 px-1.5 py-0.5 rounded">情感</span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-600">{categoryLabel(voice.category)}</td>
                  <td className="px-6 py-4 text-sm text-slate-600">{voice.model_size_mb > 0 ? `${voice.model_size_mb} MB` : '-'}</td>
                  <td className="px-6 py-4">
                    {statusLabel(voice.download_status)}
                    {voice.download_status === 'downloading' && voice.download_progress > 0 && (
                      <span className="ml-2 text-xs text-blue-600">{voice.download_progress}%</span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end space-x-2">
                      <button
                        type="button"
                        title={voice.is_favorited ? '取消收藏' : '收藏'}
                        onClick={() => toggleFavorite(voice.id)}
                        className={`p-2 rounded-full transition-all active:scale-95 ${voice.is_favorited ? 'text-yellow-400 hover:text-yellow-500' : 'text-slate-300 hover:text-yellow-400'}`}
                      >
                        <Star size={16} fill={voice.is_favorited ? 'currentColor' : 'none'} />
                      </button>

                      {voice.download_status === 'downloaded' ? (
                        <button
                          type="button"
                          title="删除模型"
                          onClick={() => handleDelete(voice.id, voice.name)}
                          className="text-slate-400 hover:text-red-500 hover:bg-red-50 p-2 rounded-full transition-all active:scale-95"
                        >
                          <Trash2 size={16} />
                        </button>
                      ) : voice.download_status === 'downloading' ? (
                        <button
                          type="button"
                          title="暂停下载"
                          onClick={() => pauseDownload(voice.id)}
                          className="text-blue-600 hover:text-blue-800 p-2 rounded-full hover:bg-blue-50 transition-all active:scale-95"
                        >
                          <Pause size={16} />
                        </button>
                      ) : (
                        <button
                          type="button"
                          title="下载模型"
                          onClick={() => startDownload(voice.id)}
                          className="text-indigo-600 hover:text-indigo-800 font-medium text-sm flex items-center px-3 py-1.5 hover:bg-indigo-50 rounded-lg transition-all active:scale-95"
                        >
                          <Download size={16} className="mr-1" /> 下载
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default VoiceManager;
