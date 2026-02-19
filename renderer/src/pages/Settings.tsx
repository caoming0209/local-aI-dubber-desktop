import React from 'react';
import { Save, RefreshCw, Cpu, Database } from 'lucide-react';

const Settings: React.FC = () => {
  return (
    <div className="p-8 max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold text-slate-800 mb-8">设置</h1>
        
        <div className="space-y-6">
            {/* General */}
            <section className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 hover:shadow-md transition-shadow">
                <h2 className="text-lg font-bold text-slate-800 mb-4 border-b border-slate-100 pb-2">基础设置</h2>
                <div className="space-y-4">
                    <div className="flex items-center justify-between">
                        <span className="text-sm text-slate-700">开机自启动</span>
                        <label className="relative inline-flex items-center cursor-pointer">
                            <input type="checkbox" className="sr-only peer" />
                            <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600 hover:bg-slate-300 peer-checked:hover:bg-indigo-700"></div>
                        </label>
                    </div>
                     <div className="flex items-center justify-between">
                        <span className="text-sm text-slate-700">自动检查更新</span>
                        <label className="relative inline-flex items-center cursor-pointer">
                            <input type="checkbox" checked readOnly className="sr-only peer" />
                            <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600 hover:bg-slate-300 peer-checked:hover:bg-indigo-700"></div>
                        </label>
                    </div>
                </div>
            </section>

            {/* Storage */}
            <section className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 hover:shadow-md transition-shadow">
                <h2 className="text-lg font-bold text-slate-800 mb-4 border-b border-slate-100 pb-2 flex items-center">
                    <Database size={20} className="mr-2 text-indigo-500" />存储设置
                </h2>
                <div className="space-y-4">
                     <div>
                         <label className="block text-sm font-medium text-slate-700 mb-1">作品保存路径</label>
                         <div className="flex">
                             <input type="text" value="D:\Users\Admin\Documents\AI_Videos" readOnly className="flex-1 p-2 bg-slate-50 border border-slate-200 rounded-l-lg text-sm text-slate-500" />
                             <button className="px-4 py-2 bg-white border border-l-0 border-slate-200 rounded-r-lg text-sm font-medium text-indigo-600 hover:bg-slate-50 hover:text-indigo-800 transition-colors active:bg-slate-100">修改</button>
                         </div>
                     </div>
                     <div>
                         <label className="block text-sm font-medium text-slate-700 mb-1">模型存储路径</label>
                         <div className="flex">
                             <input type="text" value="D:\Users\Admin\AppData\Local\AI_Models" readOnly className="flex-1 p-2 bg-slate-50 border border-slate-200 rounded-l-lg text-sm text-slate-500" />
                             <button className="px-4 py-2 bg-white border border-l-0 border-slate-200 rounded-r-lg text-sm font-medium text-indigo-600 hover:bg-slate-50 hover:text-indigo-800 transition-colors active:bg-slate-100">修改</button>
                         </div>
                         <p className="text-xs text-slate-400 mt-1">建议预留至少 10GB 空间</p>
                     </div>
                </div>
            </section>

            {/* Performance */}
            <section className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 hover:shadow-md transition-shadow">
                <h2 className="text-lg font-bold text-slate-800 mb-4 border-b border-slate-100 pb-2 flex items-center">
                    <Cpu size={20} className="mr-2 text-indigo-500" />性能设置
                </h2>
                <div className="space-y-4">
                    <div className="flex items-center justify-between">
                        <div>
                            <span className="block text-sm text-slate-700 font-medium">推理模式</span>
                            <span className="text-xs text-slate-500">GPU 加速可显著提高视频生成速度</span>
                        </div>
                        <select className="p-2 border border-slate-200 rounded-lg text-sm bg-white focus:ring-2 focus:ring-indigo-500 cursor-pointer hover:border-indigo-300 transition-colors">
                            <option>自动选择 (推荐)</option>
                            <option>GPU (CUDA)</option>
                            <option>CPU 仅使用</option>
                        </select>
                    </div>
                     <div className="bg-green-50 p-3 rounded-lg flex items-center text-sm text-green-700 border border-green-100">
                         <span className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></span>
                         检测到兼容的 GPU: NVIDIA GeForce RTX 4060
                     </div>
                </div>
            </section>
            
            <div className="flex justify-end space-x-4 pt-4">
                <button className="px-6 py-2.5 rounded-lg border border-slate-300 text-slate-600 font-medium hover:bg-slate-50 hover:border-slate-400 text-sm flex items-center transition-all active:scale-95">
                    <RefreshCw size={16} className="mr-2" /> 重置默认
                </button>
                <button className="px-6 py-2.5 rounded-lg bg-indigo-600 text-white font-medium hover:bg-indigo-700 text-sm flex items-center shadow-sm hover:shadow-md transition-all active:scale-95">
                    <Save size={16} className="mr-2" /> 保存设置
                </button>
            </div>
        </div>
    </div>
  );
};

export default Settings;