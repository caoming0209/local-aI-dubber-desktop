import React from 'react';
import { Play, Pause, Download, Trash2, Search } from 'lucide-react';
import { MOCK_VOICES } from '../constants';

const VoiceManager: React.FC = () => {
  return (
    <div className="p-8 max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
            <h1 className="text-2xl font-bold text-slate-800">音色管理</h1>
            <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" size={18} />
                <input 
                    type="text" 
                    placeholder="搜索音色..." 
                    className="pl-10 pr-4 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent w-64 transition-all"
                />
            </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
            <table className="w-full text-left border-collapse">
                <thead className="bg-slate-50 text-slate-500 text-xs uppercase font-semibold">
                    <tr>
                        <th className="px-6 py-4">音色名称</th>
                        <th className="px-6 py-4">性别</th>
                        <th className="px-6 py-4">风格</th>
                        <th className="px-6 py-4">模型状态</th>
                        <th className="px-6 py-4 text-right">操作</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                    {MOCK_VOICES.map((voice) => (
                        <tr key={voice.id} className="hover:bg-slate-50 group transition-colors">
                            <td className="px-6 py-4">
                                <div className="flex items-center">
                                    <button className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center mr-3 hover:bg-indigo-600 hover:text-white hover:scale-110 active:scale-95 transition-all shadow-sm">
                                        <Play size={14} fill="currentColor" />
                                    </button>
                                    <span className="font-medium text-slate-700">{voice.name}</span>
                                </div>
                            </td>
                            <td className="px-6 py-4 text-sm text-slate-600">{voice.gender === 'male' ? '男声' : '女声'}</td>
                            <td className="px-6 py-4 text-sm text-slate-600">{voice.style}</td>
                            <td className="px-6 py-4">
                                {voice.isDownloaded ? (
                                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700 border border-green-200">
                                        已下载 (120MB)
                                    </span>
                                ) : (
                                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-500 border border-slate-200">
                                        未下载
                                    </span>
                                )}
                            </td>
                            <td className="px-6 py-4 text-right">
                                {voice.isDownloaded ? (
                                    <button className="text-slate-400 hover:text-red-500 hover:bg-red-50 p-2 rounded-full transition-all active:scale-95" title="删除模型">
                                        <Trash2 size={18} />
                                    </button>
                                ) : (
                                    <button className="text-indigo-600 hover:text-indigo-800 font-medium text-sm flex items-center justify-end ml-auto px-3 py-1.5 hover:bg-indigo-50 rounded-lg transition-all active:scale-95">
                                        <Download size={16} className="mr-1" /> 下载模型
                                    </button>
                                )}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    </div>
  );
};

export default VoiceManager;