import React, { useState, useEffect, useCallback } from 'react';
import {
  ArrowLeft,
  ChevronRight,
  Wand2,
  Play,
  Volume2,
  Type,
  CheckCircle2,
  AlertCircle,
  DownloadCloud,
  Users,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { RoutePath, Step } from '../types';
import { useProjectStore } from '../stores/project';
import { useDigitalHumansStore } from '../stores/digitalHumans';
import { useVoicesStore } from '../stores/voices';
import { api, toLocalFileUrl } from '../services/engine';
import { subscribeProgress } from '../services/pipeline';
import type { SingleProgressEvent, PipelineJobResponse } from '@shared/ipc-types';

const TEXT_TEMPLATES = [
  { title: '好物推荐', content: '家人们！今天给大家推荐一款超级好用的...' },
  { title: '知识讲解', content: '你知道吗？在量子力学中...' },
  { title: '团购探店', content: '只要99元，满满一大桌！今天我们来到了...' },
];

const SingleCreation: React.FC = () => {
  const navigate = useNavigate();

  // Stores
  const project = useProjectStore();
  const { items: avatars, loadDigitalHumans } = useDigitalHumansStore();
  const { items: voices, loadVoices, previewVoice } = useVoicesStore();

  // Local UI state
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationProgress, setGenerationProgress] = useState(0);
  const [generationStep, setGenerationStep] = useState('');
  const [generationMessage, setGenerationMessage] = useState('');
  const [generationDone, setGenerationDone] = useState(false);
  const [generationError, setGenerationError] = useState('');
  const [jobId, setJobId] = useState<string | null>(null);

  // Load data on mount
  useEffect(() => {
    loadDigitalHumans();
    loadVoices();
  }, []);

  const currentAvatar = avatars.find(a => a.id === project.digitalHumanId);

  const handleStepChange = (direction: 'next' | 'prev') => {
    if (direction === 'next') {
      if (project.currentStep === Step.TEXT && project.script.length < 10) return;
      if (project.currentStep === Step.VOICE && !project.voiceId) return;
      if (project.currentStep === Step.AVATAR && !project.digitalHumanId) return;
      if (project.currentStep < Step.GENERATE) {
        project.setCurrentStep(project.currentStep + 1);
      }
    } else {
      if (project.currentStep > Step.TEXT) {
        project.setCurrentStep(project.currentStep - 1);
      }
    }
  };

  const startGeneration = useCallback(async () => {
    project.setCurrentStep(Step.GENERATE);
    setIsGenerating(true);
    setGenerationProgress(0);
    setGenerationStep('');
    setGenerationMessage('准备中...');
    setGenerationDone(false);
    setGenerationError('');

    try {
      const req = project.toRequest();
      const res = await api.post<PipelineJobResponse>('/api/pipeline/single', req);

      if (!res.success || !res.data) {
        setGenerationError(res.error?.message ?? '创建任务失败');
        setIsGenerating(false);
        return;
      }

      const id = res.data.job_id;
      setJobId(id);

      subscribeProgress(
        id,
        (event) => {
          const e = event as SingleProgressEvent;
          setGenerationStep(e.step);
          setGenerationProgress(Math.round(e.progress * 100));
          setGenerationMessage(e.message);

          if (e.step === 'failed') {
            setGenerationError(e.error?.message ?? '生成失败');
            setIsGenerating(false);
          }
          if (e.step === 'completed') {
            setGenerationDone(true);
            setIsGenerating(false);
          }
        },
        () => {
          // SSE done
        },
        (err) => {
          setGenerationError(err.message);
          setIsGenerating(false);
        },
      );
    } catch (e: any) {
      setGenerationError(e.message ?? '网络错误');
      setIsGenerating(false);
    }
  }, [project]);

  const cancelGeneration = async () => {
    if (jobId) {
      await api.post(`/api/pipeline/cancel/${jobId}`);
    }
    setIsGenerating(false);
    setGenerationError('已取消');
  };

  // Step renderers
  const renderStepContent = () => {
    switch (project.currentStep) {
      case Step.TEXT:
        return (
          <div className="space-y-4">
            <div className="flex justify-between items-center mb-2">
              <label className="text-sm font-medium text-slate-700">输入口播文案</label>
              <span className={`text-xs ${project.script.length < 10 ? 'text-red-500' : 'text-slate-500'}`}>
                {project.script.length} 字 (建议 50-500 字)
              </span>
            </div>
            <textarea
              value={project.script}
              onChange={(e) => project.setScript(e.target.value)}
              placeholder="在此输入或粘贴文案，我们将为您生成数字人口播视频..."
              className="w-full h-64 p-4 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none text-slate-700 transition-shadow duration-200"
            />
            <div className="flex space-x-3">
              <button
                type="button"
                className="flex items-center px-3 py-1.5 bg-indigo-50 text-indigo-700 rounded-md text-sm font-medium hover:bg-indigo-100 active:scale-95 transition-all"
              >
                <Wand2 size={16} className="mr-2" /> AI 口语化优化
              </button>
              <button
                type="button"
                onClick={() => project.setScript('')}
                className="px-3 py-1.5 text-slate-500 hover:text-red-500 text-sm hover:bg-red-50 rounded-md transition-all active:scale-95"
              >
                清空
              </button>
            </div>
            <div className="mt-6">
              <h4 className="text-sm font-medium text-slate-700 mb-3">推荐模板</h4>
              <div className="flex flex-wrap gap-2">
                {TEXT_TEMPLATES.map((tpl, idx) => (
                  <button
                    type="button"
                    key={idx}
                    onClick={() => project.setScript(tpl.content)}
                    className="px-3 py-1.5 border border-slate-200 rounded-full text-xs text-slate-600 hover:border-indigo-300 hover:bg-indigo-50 hover:text-indigo-700 transition-all active:scale-95"
                  >
                    {tpl.title}
                  </button>
                ))}
              </div>
            </div>
          </div>
        );

      case Step.VOICE:
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              {voices.map((voice) => (
                <div
                  key={voice.id}
                  onClick={() => project.setVoiceId(voice.id)}
                  className={`p-4 rounded-xl border cursor-pointer transition-all duration-200 flex items-center justify-between active:scale-[0.98] ${
                    project.voiceId === voice.id
                      ? 'border-indigo-500 bg-indigo-50 ring-1 ring-indigo-500 shadow-sm'
                      : 'border-slate-200 hover:border-indigo-300 hover:shadow-md'
                  }`}
                >
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-bold text-slate-800">{voice.name}</span>
                      <span className="text-xs px-1.5 py-0.5 bg-slate-100 text-slate-500 rounded">{voice.category}</span>
                    </div>
                    <div className="text-xs text-slate-500 mt-1">
                      {voice.download_status === 'downloaded' ? '已下载' : '未下载'}
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {voice.download_status !== 'downloaded' && (
                      <DownloadCloud size={16} className="text-slate-400" />
                    )}
                    <button
                      type="button"
                      title={voice.download_status === 'downloaded' ? '试听音色' : '请先下载音色'}
                      onClick={(e) => { e.stopPropagation(); previewVoice(voice.id); }}
                      disabled={voice.download_status !== 'downloaded'}
                      className="w-8 h-8 rounded-full bg-white border border-slate-200 flex items-center justify-center text-slate-600 hover:text-indigo-600 hover:border-indigo-300 hover:scale-110 transition-all disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100"
                    >
                      <Play size={14} fill="currentColor" />
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {project.voiceId && (
              <div className="bg-slate-50 p-4 rounded-lg border border-slate-200 space-y-4">
                <h4 className="text-sm font-medium text-slate-700 flex items-center">
                  <Volume2 size={16} className="mr-2" /> 语音参数调节
                </h4>
                <div className="space-y-3">
                  <div className="flex items-center space-x-4">
                    <span className="text-xs text-slate-500 w-12">语速</span>
                    <input
                      type="range" min="0.5" max="2.0" step="0.1"
                      title="语速调节"
                      value={project.voiceParams.speed}
                      onChange={e => project.setVoiceParams({ speed: parseFloat(e.target.value) })}
                      className="flex-1 h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                    />
                    <span className="text-xs text-slate-700 w-8 text-right">{project.voiceParams.speed}x</span>
                  </div>
                  <div className="flex items-center space-x-4">
                    <span className="text-xs text-slate-500 w-12">音量</span>
                    <input
                      type="range" min="0" max="2" step="0.1"
                      title="音量调节"
                      value={project.voiceParams.volume}
                      onChange={e => project.setVoiceParams({ volume: parseFloat(e.target.value) })}
                      className="flex-1 h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                    />
                    <span className="text-xs text-slate-700 w-8 text-right">{Math.round(project.voiceParams.volume * 100)}%</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        );

      case Step.AVATAR:
        return (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-sm font-medium">选择数字人</h3>
            </div>
            <div className="grid grid-cols-3 gap-4">
              {avatars.map((avatar) => (
                <div
                  key={avatar.id}
                  onClick={() => project.setDigitalHumanId(avatar.id)}
                  className={`group relative aspect-[3/4] rounded-xl overflow-hidden cursor-pointer border-2 transition-all duration-200 active:scale-[0.98] ${
                    project.digitalHumanId === avatar.id
                      ? 'border-indigo-500 ring-2 ring-indigo-200 shadow-md'
                      : 'border-transparent hover:border-slate-300 hover:shadow-lg'
                  }`}
                >
                  {avatar.thumbnail_path ? (
                    <img src={toLocalFileUrl(avatar.thumbnail_path)} alt={avatar.name} className="w-full h-full object-cover transform group-hover:scale-105 transition-transform duration-500" />
                  ) : (
                    <div className="w-full h-full bg-slate-200 flex items-center justify-center text-slate-400">
                      <Users size={32} />
                    </div>
                  )}
                  <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/80 to-transparent p-3 pt-8">
                    <p className="text-white text-sm font-medium">{avatar.name}</p>
                    <span className="text-[10px] bg-white/20 text-white px-1.5 py-0.5 rounded backdrop-blur-sm">{avatar.category}</span>
                  </div>
                  {project.digitalHumanId === avatar.id && (
                    <div className="absolute top-2 right-2 bg-indigo-500 text-white rounded-full p-1">
                      <CheckCircle2 size={16} />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        );

      case Step.SETTINGS:
        return (
          <div className="space-y-6">
            <div className="space-y-3">
              <h3 className="text-sm font-medium text-slate-700">背景设置</h3>
              <div className="grid grid-cols-3 gap-3">
                <button
                  type="button"
                  onClick={() => project.setBackground({ type: 'solid_color', value: '#F5F5F5' })}
                  className={`p-3 rounded-lg border text-sm font-medium transition-all active:scale-95 ${project.background.type === 'solid_color' ? 'border-indigo-500 bg-indigo-50 text-indigo-700 ring-1 ring-indigo-200' : 'border-slate-200 text-slate-600 hover:border-indigo-300'}`}
                >
                  纯色背景
                </button>
                <button
                  type="button"
                  onClick={() => project.setBackground({ type: 'custom_image', value: '' })}
                  className={`p-3 rounded-lg border text-sm font-medium transition-all active:scale-95 ${project.background.type === 'custom_image' ? 'border-indigo-500 bg-indigo-50 text-indigo-700 ring-1 ring-indigo-200' : 'border-slate-200 text-slate-600 hover:border-indigo-300'}`}
                >
                  图片背景
                </button>
              </div>
            </div>

            <div className="space-y-3">
              <h3 className="text-sm font-medium text-slate-700">字幕设置</h3>
              <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg border border-slate-200">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-white rounded-md border border-slate-200 text-slate-500">
                    <Type size={18} />
                  </div>
                  <span className="text-sm font-medium text-slate-700">生成智能字幕</span>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" title="字幕开关" checked={project.subtitle.enabled} onChange={(e) => project.setSubtitle({ enabled: e.target.checked })} className="sr-only peer" />
                  <div className="w-11 h-6 bg-slate-200 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
                </label>
              </div>
            </div>

            <div className="space-y-3">
              <h3 className="text-sm font-medium text-slate-700">画面比例</h3>
              <div className="flex gap-4">
                <div
                  onClick={() => project.setAspectRatio('9:16')}
                  className={`flex-1 p-3 border rounded-lg flex flex-col items-center justify-center cursor-pointer active:scale-95 transition-all ${project.aspectRatio === '9:16' ? 'border-indigo-500 bg-indigo-50 shadow-sm' : 'border-slate-200 hover:bg-slate-50'}`}
                >
                  <div className={`w-6 h-10 border-2 rounded-sm mb-2 bg-white ${project.aspectRatio === '9:16' ? 'border-indigo-600' : 'border-slate-400'}`}></div>
                  <span className={`text-xs font-medium ${project.aspectRatio === '9:16' ? 'text-indigo-700' : 'text-slate-600'}`}>9:16 (竖屏)</span>
                </div>
                <div
                  onClick={() => project.setAspectRatio('16:9')}
                  className={`flex-1 p-3 border rounded-lg flex flex-col items-center justify-center cursor-pointer active:scale-95 transition-all ${project.aspectRatio === '16:9' ? 'border-indigo-500 bg-indigo-50 shadow-sm' : 'border-slate-200 hover:bg-slate-50'}`}
                >
                  <div className={`w-10 h-6 border-2 rounded-sm mb-2 bg-white ${project.aspectRatio === '16:9' ? 'border-indigo-600' : 'border-slate-400'}`}></div>
                  <span className={`text-xs font-medium ${project.aspectRatio === '16:9' ? 'text-indigo-700' : 'text-slate-600'}`}>16:9 (横屏)</span>
                </div>
              </div>
            </div>
          </div>
        );

      case Step.GENERATE:
        return (
          <div className="flex flex-col items-center justify-center h-full py-10 space-y-6">
            {generationError && !isGenerating && !generationDone ? (
              <>
                <div className="w-16 h-16 bg-red-100 text-red-600 rounded-full flex items-center justify-center mb-2">
                  <AlertCircle size={32} />
                </div>
                <h3 className="text-xl font-bold text-slate-800">生成失败</h3>
                <p className="text-slate-500 text-sm">{generationError}</p>
                <button type="button" onClick={() => { project.setCurrentStep(Step.SETTINGS); setGenerationError(''); }} className="px-6 py-2 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 active:scale-95 transition-all">
                  返回修改
                </button>
              </>
            ) : isGenerating ? (
              <>
                <div className="w-20 h-20 relative">
                  <div className="absolute inset-0 rounded-full border-4 border-slate-100"></div>
                  <div className="absolute inset-0 rounded-full border-4 border-indigo-600 border-t-transparent animate-spin"></div>
                  <div className="absolute inset-0 flex items-center justify-center font-bold text-indigo-600">
                    {generationProgress}%
                  </div>
                </div>
                <div className="text-center">
                  <h3 className="text-lg font-bold text-slate-800 animate-pulse">正在生成视频...</h3>
                  <p className="text-sm text-slate-500 mt-1">{generationMessage}</p>
                </div>
                <div className="w-full max-w-xs bg-slate-100 rounded-full h-2 overflow-hidden shadow-inner">
                  <div className="h-full bg-indigo-600 transition-all duration-300 ease-out" style={{ width: `${generationProgress}%` }}></div>
                </div>
                <div className="space-y-1 text-xs text-slate-400 text-center">
                  <p className={generationStep === 'script_optimization' || generationProgress > 20 ? 'text-indigo-600 font-medium' : ''}>
                    {generationProgress > 20 ? '✓' : '○'} 文案优化
                  </p>
                  <p className={generationStep === 'tts' || generationProgress > 40 ? 'text-indigo-600 font-medium' : ''}>
                    {generationProgress > 40 ? '✓' : '○'} 语音合成
                  </p>
                  <p className={generationStep === 'lipsync' || generationProgress > 70 ? 'text-indigo-600 font-medium' : ''}>
                    {generationProgress > 70 ? '✓' : '○'} 口型同步
                  </p>
                  <p className={generationStep === 'synthesis' || generationProgress > 90 ? 'text-indigo-600 font-medium' : ''}>
                    {generationProgress > 90 ? '✓' : '○'} 视频渲染
                  </p>
                </div>
                <button type="button" onClick={cancelGeneration} className="text-sm text-slate-400 hover:text-red-500 mt-4 underline transition-colors">取消生成</button>
              </>
            ) : (
              <>
                <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mb-2">
                  <CheckCircle2 size={32} />
                </div>
                <h3 className="text-2xl font-bold text-slate-800">生成成功！</h3>
                <p className="text-slate-500">视频已保存至作品库</p>
                <div className="flex space-x-4 mt-6">
                  <button type="button" onClick={() => navigate(RoutePath.WORKS)} className="px-6 py-2 bg-white border border-slate-300 rounded-lg text-slate-700 font-medium hover:bg-slate-50 active:scale-95 transition-all shadow-sm">
                    查看作品
                  </button>
                  <button type="button" onClick={() => { project.reset(); setGenerationDone(false); setGenerationError(''); setGenerationProgress(0); setGenerationStep(''); setGenerationMessage(''); setJobId(null); }} className="px-6 py-2 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 active:scale-95 transition-all shadow-md">
                    制作下一条
                  </button>
                </div>
              </>
            )}
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden">
      {/* Left Control Panel */}
      <div className="w-1/2 max-w-xl bg-white border-r border-slate-200 flex flex-col h-full z-10 shadow-lg shadow-slate-200/50">
        {/* Header */}
        <div className="h-16 px-6 border-b border-slate-100 flex items-center justify-between flex-shrink-0">
          <button type="button" onClick={() => navigate(RoutePath.HOME)} className="flex items-center text-slate-500 hover:text-slate-800 transition-colors group">
            <ArrowLeft size={18} className="mr-2 group-hover:-translate-x-1 transition-transform" />
            <span className="font-medium">返回首页</span>
          </button>
          <div className="text-sm text-slate-400">单条视频制作</div>
        </div>

        {/* Step Indicator */}
        <div className="px-6 py-4 bg-slate-50/50" data-testid="step-indicator">
          <div className="flex items-center justify-between relative">
            <div className="absolute top-1/2 left-0 w-full h-0.5 bg-slate-200 -z-10 transform -translate-y-1/2"></div>
            {[Step.TEXT, Step.VOICE, Step.AVATAR, Step.SETTINGS, Step.GENERATE].map((s) => (
              <div key={s} className="flex flex-col items-center bg-white px-2 z-10">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-300 ${
                  project.currentStep >= s ? 'bg-indigo-600 text-white scale-110 shadow-md' : 'bg-slate-200 text-slate-500'
                }`}>
                  {s}
                </div>
                <span className={`text-[10px] mt-1 font-medium transition-colors duration-300 ${project.currentStep >= s ? 'text-indigo-600' : 'text-slate-400'}`}>
                  {s === 1 ? '文案输入' : s === 2 ? '语音选择' : s === 3 ? '数字人选择' : s === 4 ? '视频设置' : '生成视频'}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto p-6 scroll-smooth">
          {renderStepContent()}
        </div>

        {/* Footer Actions */}
        {project.currentStep !== Step.GENERATE && (
          <div className="h-20 px-6 border-t border-slate-100 flex items-center justify-between flex-shrink-0 bg-white">
            <button
              type="button"
              disabled={project.currentStep === Step.TEXT}
              onClick={() => handleStepChange('prev')}
              className={`px-6 py-2.5 rounded-lg text-sm font-medium border border-slate-200 transition-all ${
                project.currentStep === Step.TEXT
                  ? 'opacity-50 cursor-not-allowed bg-slate-50'
                  : 'hover:bg-slate-50 text-slate-700 hover:border-slate-300 active:scale-95'
              }`}
            >
              上一步
            </button>
            <button
              type="button"
              onClick={() => project.currentStep === Step.SETTINGS ? startGeneration() : handleStepChange('next')}
              className="px-8 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium shadow-md shadow-indigo-200 flex items-center active:scale-95 transition-all hover:shadow-lg"
            >
              {project.currentStep === Step.SETTINGS ? '开始生成' : '下一步'}
              {project.currentStep !== Step.SETTINGS && <ChevronRight size={16} className="ml-1" />}
            </button>
          </div>
        )}
      </div>

      {/* Right Preview Panel */}
      <div className="flex-1 bg-slate-100 flex flex-col items-center justify-center p-8">
        <div className="relative w-[320px] h-[568px] bg-black rounded-[32px] shadow-2xl overflow-hidden border-8 border-slate-800 ring-4 ring-slate-200/50">
          <div className="absolute inset-0 z-0 bg-slate-900 flex items-center justify-center">
            {currentAvatar?.thumbnail_path ? (
              <img src={toLocalFileUrl(currentAvatar.thumbnail_path)} alt="Avatar" className="w-full h-full object-cover opacity-90" />
            ) : (
              <div className="text-slate-500 flex flex-col items-center">
                <Users size={32} className="mb-2 opacity-50" />
                <span className="text-xs">选择数字人预览</span>
              </div>
            )}
          </div>

          {project.subtitle.enabled && project.script && (
            <div className="absolute bottom-20 left-4 right-4 text-center z-10">
              <span className="inline-block bg-black/50 backdrop-blur-sm text-white px-3 py-1.5 rounded-lg text-sm font-medium shadow-sm">
                {project.script.length > 20 ? project.script.substring(0, 20) + '...' : project.script || '字幕预览区域'}
              </span>
            </div>
          )}

          <div className="absolute bottom-8 left-0 right-0 flex justify-center z-20">
            <button type="button" title="播放预览" className="w-12 h-12 bg-white/20 backdrop-blur-md rounded-full flex items-center justify-center text-white hover:bg-white/30 hover:scale-110 active:scale-95 transition-all">
              <Play fill="white" size={20} />
            </button>
          </div>
        </div>
        <div className="mt-6 text-slate-400 text-xs flex items-center">
          <AlertCircle size={12} className="mr-1.5" />
          预览效果仅供参考，请以最终生成视频为准
        </div>
      </div>
    </div>
  );
};

export default SingleCreation;
