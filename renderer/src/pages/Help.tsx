import React from 'react';
import { BookOpen, Video, Layers, Settings, MessageCircle, ExternalLink } from 'lucide-react';

const GUIDE_SECTIONS = [
  {
    icon: Video,
    title: '单条视频制作',
    steps: [
      '在侧边栏点击「新建单条」进入制作页面',
      '输入或粘贴口播文案（支持模板快速填充）',
      '选择音色并调整语速、音量、情感参数',
      '选择数字人形象和背景',
      '配置字幕和背景音乐（可选）',
      '点击「开始生成」，等待视频生成完成',
    ],
  },
  {
    icon: Layers,
    title: '批量制作',
    steps: [
      '在侧边栏点击「批量制作」',
      '在左侧文本框中输入多条文案，每条一行',
      '在右侧统一配置音色、数字人、背景等参数',
      '点击「开始批量生成」，系统将逐条生成',
      '生成过程中可暂停或取消',
    ],
  },
  {
    icon: Settings,
    title: '设置与优化',
    steps: [
      '在「设置」页面可修改作品保存路径和模型存储路径',
      '推理模式建议选择「自动」，有 GPU 时自动加速',
      '首次使用需下载语音模型（约 1-2 GB）',
      '建议预留至少 10GB 磁盘空间用于模型存储',
    ],
  },
];

const FAQ = [
  {
    q: '生成视频需要联网吗？',
    a: '首次使用需要联网下载模型和激活软件。模型下载完成后，视频生成全程离线运行。',
  },
  {
    q: '支持哪些 GPU 加速？',
    a: '支持 NVIDIA CUDA 显卡（GTX 1060 及以上）。无 GPU 时自动使用 CPU 推理，速度较慢但功能完整。',
  },
  {
    q: '试用版有什么限制？',
    a: '试用版可免费生成 5 条视频，生成的视频带有水印。激活后无限制、无水印。',
  },
  {
    q: '如何更换设备？',
    a: '在「设置 → 授权管理」中解绑当前设备，然后在新设备上使用同一激活码重新激活。每个激活码最多绑定 2 台设备。',
  },
  {
    q: '视频生成失败怎么办？',
    a: '请检查：1) 模型是否已下载完成；2) 磁盘空间是否充足；3) 文案是否过短（至少 2 个字符）。如问题持续，尝试重启应用。',
  },
];

const Help: React.FC = () => {
  return (
    <div className="p-8 max-w-4xl mx-auto space-y-8">
      <div className="flex items-center gap-3 mb-2">
        <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
          <BookOpen size={24} />
        </div>
        <h1 className="text-2xl font-bold text-slate-800">帮助与指南</h1>
      </div>

      {/* Quick Start Guides */}
      <div className="space-y-6">
        {GUIDE_SECTIONS.map((section) => (
          <section key={section.title} className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 hover:shadow-md transition-shadow">
            <h2 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
              <section.icon size={20} className="text-indigo-500" />
              {section.title}
            </h2>
            <ol className="space-y-2 ml-1">
              {section.steps.map((step, i) => (
                <li key={i} className="flex items-start gap-3 text-sm text-slate-600">
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center text-xs font-bold">
                    {i + 1}
                  </span>
                  <span className="pt-0.5">{step}</span>
                </li>
              ))}
            </ol>
          </section>
        ))}
      </div>

      {/* FAQ */}
      <section className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <h2 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
          <MessageCircle size={20} className="text-indigo-500" />
          常见问题
        </h2>
        <div className="space-y-4">
          {FAQ.map((item, i) => (
            <div key={i} className="border-b border-slate-100 pb-4 last:border-0 last:pb-0">
              <h3 className="text-sm font-semibold text-slate-800 mb-1">{item.q}</h3>
              <p className="text-sm text-slate-500">{item.a}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Feedback */}
      <section className="bg-blue-50 border border-blue-100 rounded-xl p-6 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold text-blue-900 mb-1">遇到问题或有建议？</h3>
          <p className="text-xs text-blue-700">欢迎通过以下方式联系我们，我们会尽快回复。</p>
        </div>
        <button
          type="button"
          className="px-4 py-2 bg-white text-blue-600 text-sm font-medium rounded-lg shadow-sm border border-blue-200 hover:bg-blue-600 hover:text-white hover:border-blue-600 transition-all active:scale-95 flex items-center gap-1.5"
        >
          <ExternalLink size={14} />
          反馈问题
        </button>
      </section>
    </div>
  );
};

export default Help;
