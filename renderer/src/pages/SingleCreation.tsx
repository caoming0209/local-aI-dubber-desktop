import React, { useState } from 'react';
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
  Users
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { RoutePath, Step } from '../types';
import { MOCK_AVATARS, MOCK_VOICES, TEXT_TEMPLATES } from '../constants';

const SingleCreation: React.FC = () => {
  const navigate = useNavigate();
  
  // State
  const [currentStep, setCurrentStep] = useState<Step>(Step.TEXT);
  const [text, setText] = useState('');
  const [selectedVoice, setSelectedVoice] = useState<string>('');
  const [selectedAvatar, setSelectedAvatar] = useState<string>('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationProgress, setGenerationProgress] = useState(0);
  
  // Settings State
  const [bgType, setBgType] = useState<'color' | 'image'>('color');
  const [subtitleEnabled, setSubtitleEnabled] = useState(true);
  const [voiceSettings, setVoiceSettings] = useState({ speed: 1.0, pitch: 1.0, volume: 100 });

  // Helpers
  const currentAvatar = MOCK_AVATARS.find(a => a.id === selectedAvatar);
  
  const handleStepChange = (direction: 'next' | 'prev') => {
    if (direction === 'next') {
        if (currentStep === Step.TEXT && text.length < 10) return;
        if (currentStep === Step.VOICE && !selectedVoice) return;
        if (currentStep === Step.AVATAR && !selectedAvatar) return;
        
        if (currentStep < Step.GENERATE) {
            setCurrentStep(prev => prev + 1);
        }
    } else {
        if (currentStep > Step.TEXT) {
            setCurrentStep(prev => prev - 1);
        }
    }
  };

  const startGeneration = () => {
    setCurrentStep(Step.GENERATE);
    setIsGenerating(true);
    let progress = 0;
    const interval = setInterval(() => {
        progress += 5;
        setGenerationProgress(progress);
        if (progress >= 100) {
            clearInterval(interval);
            setIsGenerating(false);
        }
    }, 200);
  };

  // Render Step Content
  const renderStepContent = () => {
    switch (currentStep) {
      case Step.TEXT:
        return (
          <div className="space-y-4">
            <div className="flex justify-between items-center mb-2">
               <label className="text-sm font-medium text-slate-700">输入口播文案</label>
               <span className={`text-xs ${text.length < 10 ? 'text-red-500' : 'text-slate-500'}`}>
                 {text.length} 字 (建议 50-500 字)
               </span>
            </div>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="在此输入或粘贴文案，我们将为您生成数字人口播视频..."
              className="w-full h-64 p-4 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none text-slate-700 transition-shadow duration-200"
            />
            <div className="flex space-x-3">
                <button 
                  onClick={() => setText(prev => prev + "。")} // Mock Polish
                  className="flex items-center px-3 py-1.5 bg-indigo-50 text-indigo-700 rounded-md text-sm font-medium hover:bg-indigo-100 active:scale-95 transition-all"
                >
                    <Wand2 size={16} className="mr-2" /> AI 口语化优化
                </button>
                <button 
                  onClick={() => setText('')}
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
                            key={idx}
                            onClick={() => setText(tpl.content)}
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
                {MOCK_VOICES.map((voice) => (
                    <div 
                        key={voice.id}
                        onClick={() => setSelectedVoice(voice.id)}
                        className={`p-4 rounded-xl border cursor-pointer transition-all duration-200 flex items-center justify-between active:scale-[0.98] ${
                            selectedVoice === voice.id 
                            ? 'border-indigo-500 bg-indigo-50 ring-1 ring-indigo-500 shadow-sm' 
                            : 'border-slate-200 hover:border-indigo-300 hover:shadow-md'
                        }`}
                    >
                        <div>
                            <div className="flex items-center space-x-2">
                                <span className="font-bold text-slate-800">{voice.name}</span>
                                <span className="text-xs px-1.5 py-0.5 bg-slate-100 text-slate-500 rounded">{voice.style}</span>
                            </div>
                            <div className="text-xs text-slate-500 mt-1">{voice.gender === 'male' ? '男声' : '女声'}</div>
                        </div>
                        <div className="flex items-center space-x-2">
                             {!voice.isDownloaded && (
                                 <DownloadCloud size={16} className="text-slate-400" />
                             )}
                             <button className="w-8 h-8 rounded-full bg-white border border-slate-200 flex items-center justify-center text-slate-600 hover:text-indigo-600 hover:border-indigo-300 hover:scale-110 transition-all">
                                 <Play size={14} fill="currentColor" />
                             </button>
                        </div>
                    </div>
                ))}
            </div>

            {selectedVoice && (
                <div className="bg-slate-50 p-4 rounded-lg border border-slate-200 space-y-4 animate-in fade-in slide-in-from-top-2 duration-300">
                    <h4 className="text-sm font-medium text-slate-700 flex items-center">
                        <Volume2 size={16} className="mr-2" /> 语音参数调节
                    </h4>
                    <div className="space-y-3">
                        <div className="flex items-center space-x-4">
                            <span className="text-xs text-slate-500 w-12">语速</span>
                            <input 
                                type="range" min="0.5" max="2.0" step="0.1" 
                                value={voiceSettings.speed}
                                onChange={e => setVoiceSettings({...voiceSettings, speed: parseFloat(e.target.value)})}
                                className="flex-1 h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-indigo-600 hover:bg-slate-300 transition-colors" 
                            />
                            <span className="text-xs text-slate-700 w-8 text-right">{voiceSettings.speed}x</span>
                        </div>
                        <div className="flex items-center space-x-4">
                            <span className="text-xs text-slate-500 w-12">音量</span>
                            <input 
                                type="range" min="0" max="200" step="10"
                                value={voiceSettings.volume}
                                onChange={e => setVoiceSettings({...voiceSettings, volume: parseInt(e.target.value)})}
                                className="flex-1 h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-indigo-600 hover:bg-slate-300 transition-colors" 
                            />
                            <span className="text-xs text-slate-700 w-8 text-right">{voiceSettings.volume}%</span>
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
                  <button className="text-xs text-indigo-600 font-medium hover:underline flex items-center hover:text-indigo-800 transition-colors">
                      + 上传自定义形象
                  </button>
              </div>
              <div className="grid grid-cols-3 gap-4">
                  {MOCK_AVATARS.map((avatar) => (
                      <div 
                        key={avatar.id}
                        onClick={() => setSelectedAvatar(avatar.id)}
                        className={`group relative aspect-[3/4] rounded-xl overflow-hidden cursor-pointer border-2 transition-all duration-200 active:scale-[0.98] ${
                            selectedAvatar === avatar.id 
                            ? 'border-indigo-500 ring-2 ring-indigo-200 shadow-md' 
                            : 'border-transparent hover:border-slate-300 hover:shadow-lg'
                        }`}
                      >
                          <img src={avatar.thumbnail} alt={avatar.name} className="w-full h-full object-cover transform group-hover:scale-105 transition-transform duration-500" />
                          <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/80 to-transparent p-3 pt-8">
                              <p className="text-white text-sm font-medium">{avatar.name}</p>
                              <div className="flex gap-1 mt-1">
                                  {avatar.tags.map(tag => (
                                      <span key={tag} className="text-[10px] bg-white/20 text-white px-1.5 py-0.5 rounded backdrop-blur-sm">{tag}</span>
                                  ))}
                              </div>
                          </div>
                          {selectedAvatar === avatar.id && (
                              <div className="absolute top-2 right-2 bg-indigo-500 text-white rounded-full p-1 animate-in zoom-in duration-200">
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
                            onClick={() => setBgType('color')}
                            className={`p-3 rounded-lg border text-sm font-medium transition-all active:scale-95 ${bgType === 'color' ? 'border-indigo-500 bg-indigo-50 text-indigo-700 ring-1 ring-indigo-200' : 'border-slate-200 text-slate-600 hover:border-indigo-300 hover:bg-slate-50'}`}
                        >
                            纯色背景
                        </button>
                        <button 
                            onClick={() => setBgType('image')}
                            className={`p-3 rounded-lg border text-sm font-medium transition-all active:scale-95 ${bgType === 'image' ? 'border-indigo-500 bg-indigo-50 text-indigo-700 ring-1 ring-indigo-200' : 'border-slate-200 text-slate-600 hover:border-indigo-300 hover:bg-slate-50'}`}
                        >
                            图片背景
                        </button>
                    </div>
                </div>

                <div className="space-y-3">
                    <h3 className="text-sm font-medium text-slate-700">字幕设置</h3>
                    <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg border border-slate-200 hover:border-indigo-200 transition-colors">
                        <div className="flex items-center space-x-3">
                            <div className="p-2 bg-white rounded-md border border-slate-200 text-slate-500">
                                <Type size={18} />
                            </div>
                            <span className="text-sm font-medium text-slate-700">生成智能字幕</span>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                            <input type="checkbox" checked={subtitleEnabled} onChange={(e) => setSubtitleEnabled(e.target.checked)} className="sr-only peer" />
                            <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600 hover:bg-slate-300 peer-checked:hover:bg-indigo-700"></div>
                        </label>
                    </div>
                </div>

                 <div className="space-y-3">
                    <h3 className="text-sm font-medium text-slate-700">画面比例</h3>
                    <div className="flex gap-4">
                        <div className="flex-1 p-3 border border-indigo-500 bg-indigo-50 rounded-lg flex flex-col items-center justify-center cursor-pointer active:scale-95 transition-all shadow-sm">
                            <div className="w-6 h-10 border-2 border-indigo-600 rounded-sm mb-2 bg-white"></div>
                            <span className="text-xs font-medium text-indigo-700">9:16 (竖屏)</span>
                        </div>
                        <div className="flex-1 p-3 border border-slate-200 rounded-lg flex flex-col items-center justify-center cursor-pointer hover:bg-slate-50 hover:border-slate-300 active:scale-95 transition-all">
                            <div className="w-10 h-6 border-2 border-slate-400 rounded-sm mb-2 bg-white"></div>
                            <span className="text-xs font-medium text-slate-600">16:9 (横屏)</span>
                        </div>
                    </div>
                </div>
            </div>
        );
      
      case Step.GENERATE:
        return (
            <div className="flex flex-col items-center justify-center h-full py-10 space-y-6 animate-in fade-in duration-500">
                {isGenerating ? (
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
                            <p className="text-sm text-slate-500 mt-1">本地引擎高速渲染中，请勿关闭软件</p>
                        </div>
                        <div className="w-full max-w-xs bg-slate-100 rounded-full h-2 overflow-hidden shadow-inner">
                             <div 
                                className="h-full bg-indigo-600 transition-all duration-300 ease-out"
                                style={{ width: `${generationProgress}%` }}
                             ></div>
                        </div>
                        <div className="space-y-1 text-xs text-slate-400 text-center">
                            <p>✓ 文案优化完成</p>
                            <p className={`transition-colors duration-300 ${generationProgress > 30 ? 'text-indigo-600 font-medium' : ''}`}>{generationProgress > 30 ? '✓' : '○'} 语音合成中</p>
                            <p className={`transition-colors duration-300 ${generationProgress > 60 ? 'text-indigo-600 font-medium' : ''}`}>{generationProgress > 60 ? '✓' : '○'} 口型同步运算</p>
                            <p className={`transition-colors duration-300 ${generationProgress > 90 ? 'text-indigo-600 font-medium' : ''}`}>{generationProgress > 90 ? '✓' : '○'} 视频渲染导出</p>
                        </div>
                        <button className="text-sm text-slate-400 hover:text-red-500 mt-4 underline transition-colors">取消生成</button>
                    </>
                ) : (
                    <>
                         <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mb-2 animate-bounce">
                             <CheckCircle2 size={32} />
                         </div>
                         <h3 className="text-2xl font-bold text-slate-800">生成成功！</h3>
                         <p className="text-slate-500">视频已保存至作品库</p>
                         <div className="flex space-x-4 mt-6">
                             <button onClick={() => navigate(RoutePath.WORKS)} className="px-6 py-2 bg-white border border-slate-300 rounded-lg text-slate-700 font-medium hover:bg-slate-50 hover:border-slate-400 active:scale-95 transition-all shadow-sm">
                                 查看作品
                             </button>
                             <button onClick={() => { setCurrentStep(Step.TEXT); setText(''); }} className="px-6 py-2 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 active:scale-95 transition-all shadow-md hover:shadow-lg">
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
                <button onClick={() => navigate(RoutePath.HOME)} className="flex items-center text-slate-500 hover:text-slate-800 transition-colors group">
                    <ArrowLeft size={18} className="mr-2 group-hover:-translate-x-1 transition-transform" />
                    <span className="font-medium">返回首页</span>
                </button>
                <div className="text-sm text-slate-400">单条视频制作</div>
            </div>

            {/* Step Indicator */}
            <div className="px-6 py-4 bg-slate-50/50">
                <div className="flex items-center justify-between relative">
                    <div className="absolute top-1/2 left-0 w-full h-0.5 bg-slate-200 -z-10 transform -translate-y-1/2"></div>
                    {[Step.TEXT, Step.VOICE, Step.AVATAR, Step.SETTINGS, Step.GENERATE].map((s) => (
                        <div key={s} className={`flex flex-col items-center bg-white px-2 z-10`}>
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-300 ${
                                currentStep >= s ? 'bg-indigo-600 text-white scale-110 shadow-md' : 'bg-slate-200 text-slate-500'
                            }`}>
                                {s}
                            </div>
                            <span className={`text-[10px] mt-1 font-medium transition-colors duration-300 ${currentStep >= s ? 'text-indigo-600' : 'text-slate-400'}`}>
                                {s === 1 ? '文案' : s === 2 ? '语音' : s === 3 ? '数字人' : s === 4 ? '设置' : '生成'}
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
            {currentStep !== Step.GENERATE && (
                <div className="h-20 px-6 border-t border-slate-100 flex items-center justify-between flex-shrink-0 bg-white">
                    <button 
                        disabled={currentStep === Step.TEXT}
                        onClick={() => handleStepChange('prev')}
                        className={`px-6 py-2.5 rounded-lg text-sm font-medium border border-slate-200 transition-all ${
                            currentStep === Step.TEXT 
                            ? 'opacity-50 cursor-not-allowed bg-slate-50' 
                            : 'hover:bg-slate-50 text-slate-700 hover:border-slate-300 active:scale-95'
                        }`}
                    >
                        上一步
                    </button>
                    <button 
                         onClick={() => currentStep === Step.SETTINGS ? startGeneration() : handleStepChange('next')}
                         className="px-8 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium shadow-md shadow-indigo-200 flex items-center active:scale-95 transition-all hover:shadow-lg"
                    >
                        {currentStep === Step.SETTINGS ? '开始生成' : '下一步'}
                        {currentStep !== Step.SETTINGS && <ChevronRight size={16} className="ml-1" />}
                    </button>
                </div>
            )}
        </div>

        {/* Right Preview Panel */}
        <div className="flex-1 bg-slate-100 flex flex-col items-center justify-center p-8">
            <div className="relative w-[320px] h-[568px] bg-black rounded-[32px] shadow-2xl overflow-hidden border-8 border-slate-800 ring-4 ring-slate-200/50 transform hover:scale-[1.01] transition-transform duration-500">
                {/* Simulated Phone UI Header */}
                <div className="absolute top-0 left-0 right-0 h-6 bg-black/20 z-20 flex justify-between px-4 pt-1">
                   <span className="text-[10px] text-white font-medium">9:41</span>
                   <div className="flex space-x-1">
                       <div className="w-3 h-2 bg-white rounded-sm"></div>
                       <div className="w-1 h-2 bg-white rounded-sm"></div>
                   </div>
                </div>

                {/* Video Content Layer */}
                <div className="absolute inset-0 z-0 bg-slate-900 flex items-center justify-center">
                    {currentAvatar ? (
                        <img src={currentAvatar.thumbnail} alt="Avatar" className="w-full h-full object-cover opacity-90 animate-in fade-in duration-500" />
                    ) : (
                        <div className="text-slate-500 flex flex-col items-center">
                            <Users size={32} className="mb-2 opacity-50" />
                            <span className="text-xs">选择数字人预览</span>
                        </div>
                    )}
                </div>

                {/* Text/Subtitle Layer */}
                {subtitleEnabled && text && (
                     <div className="absolute bottom-20 left-4 right-4 text-center z-10">
                        <span className="inline-block bg-black/50 backdrop-blur-sm text-white px-3 py-1.5 rounded-lg text-sm font-medium shadow-sm animate-in slide-in-from-bottom-2 duration-300">
                            {text.length > 20 ? text.substring(0, 20) + "..." : text || "字幕预览区域"}
                        </span>
                     </div>
                )}
                
                {/* Controls Overlay */}
                <div className="absolute bottom-8 left-0 right-0 flex justify-center z-20">
                     <button className="w-12 h-12 bg-white/20 backdrop-blur-md rounded-full flex items-center justify-center text-white hover:bg-white/30 hover:scale-110 active:scale-95 transition-all">
                        <Play fill="white" size={20} />
                     </button>
                </div>

                {/* Sidebar overlay hint */}
                 <div className="absolute right-2 bottom-24 flex flex-col space-y-3 z-10">
                     <div className="w-8 h-8 rounded-full bg-black/20 flex items-center justify-center backdrop-blur-sm"><div className="w-4 h-4 text-white">❤️</div></div>
                     <div className="w-8 h-8 rounded-full bg-black/20 flex items-center justify-center backdrop-blur-sm"><div className="w-4 h-4 text-white">💬</div></div>
                     <div className="w-8 h-8 rounded-full bg-black/20 flex items-center justify-center backdrop-blur-sm"><div className="w-4 h-4 text-white">↗️</div></div>
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