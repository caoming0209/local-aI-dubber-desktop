import React from 'react';
import { PlayCircle, MoreVertical, FolderOpen, Trash2, Edit } from 'lucide-react';
import { MOCK_PROJECTS } from '../constants';

const WorksLibrary: React.FC = () => {
  return (
    <div className="p-8 max-w-7xl mx-auto">
         <div className="flex justify-between items-center mb-8">
            <h1 className="text-2xl font-bold text-slate-800">作品库</h1>
            <button className="text-sm font-medium text-indigo-600 hover:text-indigo-700 flex items-center bg-indigo-50 hover:bg-indigo-100 px-4 py-2 rounded-lg transition-all active:scale-95">
                <FolderOpen size={18} className="mr-2" /> 打开本地文件夹
            </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {MOCK_PROJECTS.map((project) => (
                <div key={project.id} className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden group hover:shadow-lg hover:border-indigo-200 hover:-translate-y-1 transition-all duration-300">
                    <div className="aspect-video relative bg-slate-100 overflow-hidden">
                         <img src={project.thumbnail} alt={project.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700" />
                         <div className="absolute inset-0 bg-black/30 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer duration-300">
                             <PlayCircle size={48} className="text-white drop-shadow-lg hover:scale-110 transition-transform active:scale-95" />
                         </div>
                         <div className="absolute bottom-2 right-2 bg-black/60 backdrop-blur-sm text-white text-[10px] px-1.5 py-0.5 rounded">
                             {project.duration}
                         </div>
                         {project.status === 'draft' && (
                             <div className="absolute top-2 left-2 bg-yellow-400 text-yellow-900 text-[10px] px-2 py-0.5 rounded font-bold uppercase shadow-sm">
                                 草稿
                             </div>
                         )}
                    </div>
                    <div className="p-4">
                        <div className="flex justify-between items-start mb-2">
                            <h3 className="font-bold text-slate-800 truncate pr-2 group-hover:text-indigo-700 transition-colors" title={project.title}>{project.title}</h3>
                            <button className="text-slate-400 hover:text-slate-600 p-1 hover:bg-slate-100 rounded transition-colors">
                                <MoreVertical size={16} />
                            </button>
                        </div>
                        <div className="text-xs text-slate-500 mb-4">
                            生成时间：{project.createdAt}
                        </div>
                        <div className="flex border-t border-slate-100 pt-3">
                            <button className="flex-1 flex items-center justify-center text-xs font-medium text-slate-600 hover:text-indigo-600 hover:bg-indigo-50 py-1.5 rounded transition-all active:scale-95 border-r border-slate-100">
                                <Edit size={14} className="mr-1.5" /> 重新编辑
                            </button>
                            <button className="flex-1 flex items-center justify-center text-xs font-medium text-slate-600 hover:text-red-600 hover:bg-red-50 py-1.5 rounded transition-all active:scale-95">
                                <Trash2 size={14} className="mr-1.5" /> 删除
                            </button>
                        </div>
                    </div>
                </div>
            ))}
        </div>
    </div>
  );
};

export default WorksLibrary;