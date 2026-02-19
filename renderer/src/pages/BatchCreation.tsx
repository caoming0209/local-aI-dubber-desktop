import React from 'react';
import { UploadCloud, FileText, Trash2, Plus, ArrowRight } from 'lucide-react';

const BatchCreation: React.FC = () => {
  return (
    <div className="p-8 max-w-7xl mx-auto h-full flex flex-col">
       <div className="mb-8">
            <h1 className="text-2xl font-bold text-slate-800">批量制作</h1>
            <p className="text-slate-500 mt-1">支持批量导入文案，一键统一生成多个视频。</p>
       </div>

       <div className="flex gap-6 flex-1 min-h-0">
           {/* Left: Input Area */}
           <div className="w-2/3 flex flex-col bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
               <div className="p-4 border-b border-slate-100 bg-slate-50 flex justify-between items-center">
                   <div className="flex space-x-2">
                       <button className="px-3 py-1.5 bg-white border border-slate-300 rounded-md text-sm text-slate-700 shadow-sm hover:border-indigo-400 hover:text-indigo-600 active:scale-95 transition-all flex items-center">
                          <Plus size={14} className="inline mr-1"/>手动添加
                       </button>
                       <button className="px-3 py-1.5 bg-white border border-slate-300 rounded-md text-sm text-slate-700 shadow-sm hover:border-indigo-400 hover:text-indigo-600 active:scale-95 transition-all flex items-center">
                          <UploadCloud size={14} className="inline mr-1"/>导入TXT
                       </button>
                   </div>
                   <span className="text-xs text-slate-400">已导入 3 条文案</span>
               </div>
               
               <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-slate-50/30">
                   {[1, 2, 3].map((i) => (
                       <div key={i} className="bg-white p-4 rounded-lg border border-slate-200 group hover:border-indigo-300 hover:shadow-sm transition-all duration-200">
                           <div className="flex justify-between items-start mb-2">
                               <span className="text-xs font-bold text-slate-400 bg-slate-100 px-2 py-0.5 rounded group-hover:bg-indigo-50 group-hover:text-indigo-500 transition-colors">#{i}</span>
                               <button className="text-slate-400 hover:text-red-500 hover:bg-red-50 p-1 rounded transition-colors" title="删除">
                                   <Trash2 size={14} />
                               </button>
                           </div>
                           <p className="text-sm text-slate-700 line-clamp-2">
                               {i === 1 ? '大家好，今天给大家推荐一款超级好用的洗地机，它不仅能吸尘还能拖地...' : 
                                i === 2 ? '本期视频我们来聊聊关于AI人工智能的未来发展趋势，主要包含三个方面...' : 
                                '秋季养生小知识：多吃梨可以润肺止咳，尤其是对于经常熬夜的人群...'}
                           </p>
                           <div className="flex justify-between items-center mt-3">
                               <span className="text-[10px] text-slate-400">120字 · 预计时长 25s</span>
                               <span className="text-[10px] text-green-600 bg-green-50 px-1.5 py-0.5 rounded border border-green-100">文案有效</span>
                           </div>
                       </div>
                   ))}
               </div>
           </div>

           {/* Right: Config & Action */}
           <div className="w-1/3 flex flex-col space-y-6">
                <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex-1">
                    <h3 className="font-bold text-slate-800 mb-4">统一配置</h3>
                    <div className="space-y-4">
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-slate-600">选择数字人</label>
                            <div className="flex items-center p-3 border border-slate-200 rounded-lg bg-slate-50 hover:border-indigo-200 transition-colors group cursor-pointer">
                                <div className="w-10 h-10 rounded-full bg-slate-300 mr-3 overflow-hidden group-hover:scale-110 transition-transform">
                                     <img src="https://picsum.photos/id/64/100/100" className="w-full h-full object-cover"/>
                                </div>
                                <div className="flex-1">
                                    <div className="text-sm font-medium">安娜 (新闻)</div>
                                    <div className="text-xs text-slate-500">默认形象</div>
                                </div>
                                <button className="text-indigo-600 text-xs font-medium hover:underline">更换</button>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium text-slate-600">选择音色</label>
                            <div className="flex items-center p-3 border border-slate-200 rounded-lg bg-slate-50 hover:border-indigo-200 transition-colors group cursor-pointer">
                                <div className="flex-1">
                                    <div className="text-sm font-medium">云希 (男声)</div>
                                    <div className="text-xs text-slate-500">沉稳 · 语速1.0x</div>
                                </div>
                                <button className="text-indigo-600 text-xs font-medium hover:underline">更换</button>
                            </div>
                        </div>

                        <div className="pt-4 border-t border-slate-100">
                             <div className="flex justify-between items-center text-sm mb-2">
                                 <span className="text-slate-600">视频比例</span>
                                 <span className="font-medium text-slate-800">9:16 (竖屏)</span>
                             </div>
                             <div className="flex justify-between items-center text-sm">
                                 <span className="text-slate-600">保存路径</span>
                                 <span className="font-medium text-slate-800 underline cursor-pointer truncate max-w-[150px] hover:text-indigo-600">D:/Videos/Batch_Output</span>
                             </div>
                        </div>
                    </div>
                </div>

                <button className="w-full py-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl shadow-lg shadow-indigo-200 font-bold text-lg flex items-center justify-center transition-all transform active:scale-[0.98] hover:shadow-xl">
                    立即批量生成 (3条) <ArrowRight size={20} className="ml-2 group-hover:translate-x-1 transition-transform"/>
                </button>
           </div>
       </div>
    </div>
  );
};

export default BatchCreation;