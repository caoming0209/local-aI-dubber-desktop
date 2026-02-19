import React, { useEffect, useState, useRef } from 'react';
import { UploadCloud, Trash2, Plus, ArrowRight, AlertCircle, CheckCircle2 } from 'lucide-react';
import { useDigitalHumansStore } from '../stores/digitalHumans';
import { useVoicesStore } from '../stores/voices';
import { api } from '../services/engine';
import { subscribeProgress } from '../services/pipeline';
import type { BatchProgressEvent, BatchJobResponse } from '@shared/ipc-types';

const BatchCreation: React.FC = () => {
  const { items: avatars, loadDigitalHumans } = useDigitalHumansStore();
  const { items: voices, loadVoices } = useVoicesStore();

  const [scripts, setScripts] = useState<{ index: number; content: string }[]>([]);
  const [selectedVoiceId, setSelectedVoiceId] = useState('');
  const [selectedAvatarId, setSelectedAvatarId] = useState('');
  const [aspectRatio, setAspectRatio] = useState<'9:16' | '16:9'>('9:16');

  const [isGenerating, setIsGenerating] = useState(false);
  const [batchProgress, setBatchProgress] = useState({ current: 0, total: 0, message: '' });
  const [batchDone, setBatchDone] = useState(false);
  const [batchError, setBatchError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadDigitalHumans();
    loadVoices();
  }, []);

  const addScript = () => {
    setScripts(prev => [...prev, { index: prev.length, content: '' }]);
  };

  const updateScript = (idx: number, content: string) => {
    setScripts(prev => prev.map((s, i) => i === idx ? { ...s, content } : s));
  };

  const removeScript = (idx: number) => {
    setScripts(prev => prev.filter((_, i) => i !== idx).map((s, i) => ({ ...s, index: i })));
  };

  const importTxt = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const text = await file.text();
    const lines = text.split('\n').map(l => l.trim()).filter(l => l.length > 0);
    setScripts(lines.slice(0, 100).map((content, index) => ({ index, content })));
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const validScripts = scripts.filter(s => s.content.length >= 2);

  const startBatch = async () => {
    if (validScripts.length === 0) return;
    setIsGenerating(true);
    setBatchProgress({ current: 0, total: validScripts.length, message: '准备中...' });
    setBatchDone(false);
    setBatchError('');

    try {
      const res = await api.post<BatchJobResponse>('/api/pipeline/batch', {
        scripts: validScripts.map((s, i) => ({ index: i, content: s.content })),
        shared_config: {
          voice_id: selectedVoiceId,
          voice_params: { speed: 1.0, volume: 1.0, emotion: 0.5 },
          digital_human_id: selectedAvatarId,
          background: { type: 'solid_color', value: '#F5F5F5' },
          aspect_ratio: aspectRatio,
          subtitle: { enabled: true },
          bgm: { enabled: false },
        },
        output_settings: { save_path: '', name_prefix: '批量视频' },
      });

      if (!res.success || !res.data) {
        setBatchError(res.error?.message ?? '创建批量任务失败');
        setIsGenerating(false);
        return;
      }

      subscribeProgress(
        res.data.job_id,
        (event) => {
          const e = event as BatchProgressEvent;
          if (e.type === 'batch_item_start' || e.type === 'batch_item_progress') {
            setBatchProgress({ current: (e.item_index ?? 0) + 1, total: e.total ?? validScripts.length, message: e.message ?? '' });
          }
          if (e.type === 'batch_completed') {
            setBatchDone(true);
            setIsGenerating(false);
            setBatchProgress(prev => ({ ...prev, message: `完成 ${e.succeeded ?? 0} 条，失败 ${e.failed ?? 0} 条` }));
          }
        },
        () => {},
        (err) => { setBatchError(err.message); setIsGenerating(false); },
      );
    } catch (e: any) {
      setBatchError(e.message ?? '网络错误');
      setIsGenerating(false);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto h-full flex flex-col">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-800">批量制作</h1>
        <p className="text-slate-500 mt-1">支持批量导入文案，一键统一生成多个视频。</p>
      </div>

      {isGenerating || batchDone ? (
        <div className="flex-1 flex flex-col items-center justify-center space-y-6">
          {batchError ? (
            <>
              <AlertCircle size={48} className="text-red-500" />
              <p className="text-red-600 font-medium">{batchError}</p>
              <button type="button" onClick={() => { setIsGenerating(false); setBatchError(''); }} className="px-6 py-2 bg-indigo-600 text-white rounded-lg">重试</button>
            </>
          ) : batchDone ? (
            <>
              <CheckCircle2 size={48} className="text-green-500" />
              <h3 className="text-xl font-bold text-slate-800">批量生成完成</h3>
              <p className="text-slate-500">{batchProgress.message}</p>
              <button type="button" onClick={() => { setBatchDone(false); setScripts([]); }} className="px-6 py-2 bg-indigo-600 text-white rounded-lg">继续制作</button>
            </>
          ) : (
            <>
              <div className="w-20 h-20 relative">
                <div className="absolute inset-0 rounded-full border-4 border-slate-100"></div>
                <div className="absolute inset-0 rounded-full border-4 border-indigo-600 border-t-transparent animate-spin"></div>
                <div className="absolute inset-0 flex items-center justify-center text-sm font-bold text-indigo-600">
                  {batchProgress.current}/{batchProgress.total}
                </div>
              </div>
              <p className="text-slate-600 font-medium">{batchProgress.message}</p>
            </>
          )}
        </div>
      ) : (
        <div className="flex gap-6 flex-1 min-h-0">
          {/* Left: Input Area */}
          <div className="w-2/3 flex flex-col bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="p-4 border-b border-slate-100 bg-slate-50 flex justify-between items-center">
              <div className="flex space-x-2">
                <button type="button" onClick={addScript} className="px-3 py-1.5 bg-white border border-slate-300 rounded-md text-sm text-slate-700 shadow-sm hover:border-indigo-400 hover:text-indigo-600 active:scale-95 transition-all flex items-center">
                  <Plus size={14} className="inline mr-1" />手动添加
                </button>
                <label className="px-3 py-1.5 bg-white border border-slate-300 rounded-md text-sm text-slate-700 shadow-sm hover:border-indigo-400 hover:text-indigo-600 active:scale-95 transition-all flex items-center cursor-pointer">
                  <UploadCloud size={14} className="inline mr-1" />导入TXT
                  <input ref={fileInputRef} type="file" accept=".txt" onChange={importTxt} className="hidden" />
                </label>
              </div>
              <span className="text-xs text-slate-400">已添加 {scripts.length} 条文案</span>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-slate-50/30">
              {scripts.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-slate-400 text-sm">
                  <UploadCloud size={32} className="mb-2 opacity-50" />
                  <p>点击"手动添加"或"导入TXT"开始</p>
                </div>
              ) : (
                scripts.map((script, i) => (
                  <div key={i} className="bg-white p-4 rounded-lg border border-slate-200 group hover:border-indigo-300 hover:shadow-sm transition-all duration-200">
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-xs font-bold text-slate-400 bg-slate-100 px-2 py-0.5 rounded group-hover:bg-indigo-50 group-hover:text-indigo-500 transition-colors">#{i + 1}</span>
                      <button type="button" title="删除文案" onClick={() => removeScript(i)} className="text-slate-400 hover:text-red-500 hover:bg-red-50 p-1 rounded transition-colors">
                        <Trash2 size={14} />
                      </button>
                    </div>
                    <textarea
                      value={script.content}
                      onChange={(e) => updateScript(i, e.target.value)}
                      placeholder="输入文案内容..."
                      className="w-full text-sm text-slate-700 border border-slate-200 rounded p-2 resize-none h-16 focus:ring-1 focus:ring-indigo-500 focus:border-transparent"
                    />
                    <div className="flex justify-between items-center mt-2">
                      <span className="text-[10px] text-slate-400">{script.content.length}字</span>
                      {script.content.length >= 2 ? (
                        <span className="text-[10px] text-green-600 bg-green-50 px-1.5 py-0.5 rounded border border-green-100">文案有效</span>
                      ) : (
                        <span className="text-[10px] text-red-500 bg-red-50 px-1.5 py-0.5 rounded border border-red-100">至少2字</span>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Right: Config & Action */}
          <div className="w-1/3 flex flex-col space-y-6">
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex-1">
              <h3 className="font-bold text-slate-800 mb-4">统一配置</h3>
              <div className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-600">选择数字人</label>
                  <select title="选择数字人" value={selectedAvatarId} onChange={(e) => setSelectedAvatarId(e.target.value)} className="w-full p-3 border border-slate-200 rounded-lg bg-slate-50 text-sm">
                    <option value="">请选择数字人</option>
                    {avatars.map(a => <option key={a.id} value={a.id}>{a.name} ({a.category})</option>)}
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-600">选择音色</label>
                  <select title="选择音色" value={selectedVoiceId} onChange={(e) => setSelectedVoiceId(e.target.value)} className="w-full p-3 border border-slate-200 rounded-lg bg-slate-50 text-sm">
                    <option value="">请选择音色</option>
                    {voices.map(v => <option key={v.id} value={v.id}>{v.name} ({v.category})</option>)}
                  </select>
                </div>
                <div className="pt-4 border-t border-slate-100">
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-slate-600">视频比例</span>
                    <select title="视频比例" value={aspectRatio} onChange={(e) => setAspectRatio(e.target.value as '9:16' | '16:9')} className="p-1 border border-slate-200 rounded text-sm bg-white">
                      <option value="9:16">9:16 (竖屏)</option>
                      <option value="16:9">16:9 (横屏)</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>

            <button
              type="button"
              disabled={validScripts.length === 0 || !selectedVoiceId || !selectedAvatarId}
              onClick={startBatch}
              className="w-full py-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl shadow-lg shadow-indigo-200 font-bold text-lg flex items-center justify-center transition-all transform active:scale-[0.98] hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed"
            >
              立即批量生成 ({validScripts.length}条) <ArrowRight size={20} className="ml-2" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default BatchCreation;
