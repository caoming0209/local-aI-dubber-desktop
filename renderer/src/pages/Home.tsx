import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Video, Layers, Film, PlayCircle, Clock, ChevronRight, BookOpen } from 'lucide-react';
import { RoutePath } from '../types';
import { useWorksStore } from '../stores/works';
import { toLocalFileUrl } from '../services/engine';

const Home: React.FC = () => {
  const navigate = useNavigate();
  const { works, loadWorks } = useWorksStore();

  useEffect(() => {
    loadWorks({ page: 1, page_size: 3, sort: 'created_at_desc' });
  }, []);

  const formatDuration = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const formatDate = (iso: string) => {
    try {
      return new Date(iso).toLocaleString('zh-CN');
    } catch {
      return iso;
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Welcome Section */}
      <div className="bg-gradient-to-r from-indigo-600 to-violet-600 rounded-2xl p-8 text-white shadow-lg shadow-indigo-200 transform hover:scale-[1.005] transition-transform duration-500">
        <h1 className="text-3xl font-bold mb-2">欢迎回来，创作者</h1>
        <p className="opacity-90">今天也要高效创作哦～ 您的AI数字人助手已准备就绪。</p>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <button
          onClick={() => navigate(RoutePath.SINGLE_CREATE)}
          className="group relative bg-white p-6 rounded-xl shadow-sm border border-slate-200 hover:shadow-lg hover:border-indigo-300 transition-all duration-300 text-left flex flex-col items-start active:scale-[0.98]"
        >
          <div className="w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center text-indigo-600 mb-4 group-hover:scale-110 group-hover:bg-indigo-600 group-hover:text-white transition-all duration-300">
            <Video size={24} />
          </div>
          <h3 className="text-lg font-bold text-slate-800 group-hover:text-indigo-600 transition-colors">新建单条视频</h3>
          <p className="text-sm text-slate-500 mt-1">适用于短视频、口播、讲解等单条内容制作。</p>
        </button>

        <button
          onClick={() => navigate(RoutePath.BATCH_CREATE)}
          className="group relative bg-white p-6 rounded-xl shadow-sm border border-slate-200 hover:shadow-lg hover:border-emerald-300 transition-all duration-300 text-left flex flex-col items-start active:scale-[0.98]"
        >
          <div className="w-12 h-12 bg-emerald-100 rounded-full flex items-center justify-center text-emerald-600 mb-4 group-hover:scale-110 group-hover:bg-emerald-600 group-hover:text-white transition-all duration-300">
            <Layers size={24} />
          </div>
          <h3 className="text-lg font-bold text-slate-800 group-hover:text-emerald-600 transition-colors">批量制作</h3>
          <p className="text-sm text-slate-500 mt-1">批量导入文案，一键生成多条视频，效率倍增。</p>
        </button>

        <button
          onClick={() => navigate(RoutePath.WORKS)}
          className="group relative bg-white p-6 rounded-xl shadow-sm border border-slate-200 hover:shadow-lg hover:border-amber-300 transition-all duration-300 text-left flex flex-col items-start active:scale-[0.98]"
        >
          <div className="w-12 h-12 bg-amber-100 rounded-full flex items-center justify-center text-amber-600 mb-4 group-hover:scale-110 group-hover:bg-amber-600 group-hover:text-white transition-all duration-300">
            <Film size={24} />
          </div>
          <h3 className="text-lg font-bold text-slate-800 group-hover:text-amber-600 transition-colors">查看作品库</h3>
          <p className="text-sm text-slate-500 mt-1">管理已生成的视频，支持播放、导出与编辑。</p>
        </button>
      </div>

      {/* Recent Projects */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <Clock size={18} className="text-slate-400" />
            <h3 className="font-bold text-slate-800">最近使用记录</h3>
          </div>
          <button
            onClick={() => navigate(RoutePath.WORKS)}
            className="text-sm text-indigo-600 hover:text-indigo-800 flex items-center font-medium hover:underline transition-all"
          >
            全部作品 <ChevronRight size={14} />
          </button>
        </div>
        <div className="divide-y divide-slate-100">
          {works.length === 0 ? (
            <div className="p-8 text-center text-slate-400 text-sm">暂无作品记录，快去创建第一条视频吧</div>
          ) : (
            works.slice(0, 3).map((work) => (
              <div key={work.id} className="p-4 flex items-center hover:bg-slate-50 transition-colors group cursor-pointer active:bg-slate-100">
                <div className="relative w-24 h-14 rounded-md overflow-hidden bg-slate-200 flex-shrink-0 group-hover:ring-2 ring-indigo-100 transition-all">
                  {work.thumbnail_path ? (
                    <img src={toLocalFileUrl(work.thumbnail_path)} alt={work.name} className="w-full h-full object-cover transform group-hover:scale-110 transition-transform duration-500" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-slate-300">
                      <PlayCircle size={20} />
                    </div>
                  )}
                  <div className="absolute inset-0 bg-black/20 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                    <PlayCircle className="text-white drop-shadow-md" size={24} />
                  </div>
                </div>
                <div className="ml-4 flex-1">
                  <h4 className="text-sm font-semibold text-slate-900 group-hover:text-indigo-600 transition-colors">{work.name}</h4>
                  <div className="flex items-center space-x-4 mt-1">
                    <span className="text-xs text-slate-500">时长: {formatDuration(work.duration_seconds)}</span>
                    <span className="text-xs text-slate-400">{formatDate(work.created_at)}</span>
                  </div>
                </div>
                <span className="text-xs px-2 py-1 rounded-full bg-green-100 text-green-700">已完成</span>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Help Section Hint */}
      <div className="flex items-center justify-between bg-blue-50 border border-blue-100 rounded-lg p-4 transition-colors hover:bg-blue-100/50">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-100 rounded-full text-blue-600">
            <BookOpen size={20} />
          </div>
          <div>
            <h4 className="text-sm font-bold text-blue-900">新手教程</h4>
            <p className="text-xs text-blue-700">不知道如何开始？查看3分钟快速入门指南。</p>
          </div>
        </div>
        <button
          onClick={() => navigate(RoutePath.HELP)}
          className="px-4 py-2 bg-white text-blue-600 text-sm font-medium rounded-md shadow-sm border border-blue-100 hover:bg-blue-600 hover:text-white hover:border-blue-600 transition-all active:scale-95"
        >
          查看教程
        </button>
      </div>
    </div>
  );
};

export default Home;
