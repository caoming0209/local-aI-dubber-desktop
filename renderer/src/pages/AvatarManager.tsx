import React from 'react';
import { Plus, Search, Star } from 'lucide-react';
import { MOCK_AVATARS } from '../constants';

const AvatarManager: React.FC = () => {
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
                        className="pl-10 pr-4 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent w-64 transition-all"
                    />
                </div>
                <button className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium flex items-center hover:bg-indigo-700 shadow-sm hover:shadow active:scale-95 transition-all">
                    <Plus size={18} className="mr-2" /> 上传自定义形象
                </button>
            </div>
        </div>

        <div className="border-b border-slate-200 mb-6">
            <nav className="flex space-x-8">
                <button className="border-b-2 border-indigo-600 py-4 px-1 text-sm font-medium text-indigo-600 hover:text-indigo-800 transition-colors">全部数字人</button>
                <button className="border-b-2 border-transparent py-4 px-1 text-sm font-medium text-slate-500 hover:text-slate-700 hover:border-slate-300 transition-all">我的收藏</button>
                <button className="border-b-2 border-transparent py-4 px-1 text-sm font-medium text-slate-500 hover:text-slate-700 hover:border-slate-300 transition-all">自定义</button>
            </nav>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-6">
            {MOCK_AVATARS.map((avatar) => (
                <div key={avatar.id} className="group relative bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden hover:shadow-lg hover:-translate-y-1 transition-all duration-300">
                    <div className="aspect-[3/4] relative overflow-hidden bg-slate-100">
                        <img 
                            src={avatar.thumbnail} 
                            alt={avatar.name} 
                            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" 
                        />
                        <div className="absolute top-2 right-2">
                             <button className="p-1.5 bg-white/80 backdrop-blur rounded-full text-slate-400 hover:text-yellow-400 hover:scale-110 active:scale-95 transition-all shadow-sm">
                                 <Star size={14} />
                             </button>
                        </div>
                        {avatar.category === 'custom' && (
                             <div className="absolute top-2 left-2 bg-indigo-600 text-white text-[10px] px-1.5 py-0.5 rounded font-medium shadow-sm">自定义</div>
                        )}
                        <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                             <button className="px-4 py-1.5 bg-white rounded-full text-xs font-bold text-slate-900 transform translate-y-2 group-hover:translate-y-0 transition-all duration-300 hover:bg-indigo-50 active:scale-95 shadow-lg">立即使用</button>
                        </div>
                    </div>
                    <div className="p-3">
                        <h3 className="font-medium text-slate-800 text-sm truncate">{avatar.name}</h3>
                        <div className="flex gap-1 mt-1.5">
                            {avatar.tags.map(tag => (
                                <span key={tag} className="text-[10px] bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded">{tag}</span>
                            ))}
                        </div>
                    </div>
                </div>
            ))}
            
            {/* Add New Placeholder */}
            <div className="border-2 border-dashed border-slate-200 rounded-xl flex flex-col items-center justify-center aspect-[3/4] cursor-pointer hover:border-indigo-400 hover:bg-indigo-50 transition-all duration-300 group active:scale-[0.98]">
                <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center shadow-sm mb-3 group-hover:scale-110 group-hover:shadow-md transition-all">
                    <Plus size={24} className="text-indigo-500" />
                </div>
                <span className="text-sm font-medium text-slate-600 group-hover:text-indigo-600 transition-colors">添加自定义数字人</span>
            </div>
        </div>
    </div>
  );
};

export default AvatarManager;