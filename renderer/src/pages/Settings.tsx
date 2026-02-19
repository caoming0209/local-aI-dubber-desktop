import React, { useEffect, useState } from 'react';
import { Save, RefreshCw, Cpu, Database, Key, Trash2 } from 'lucide-react';
import { useSettingsStore } from '../stores/settings';
import { useLicenseStore } from '../stores/license';
import ActivationModal from '../components/ActivationModal';

const Settings: React.FC = () => {
  const { settings, loading, loadSettings, updateSettings } = useSettingsStore();
  const { status: licenseStatus, loadStatus: loadLicense } = useLicenseStore();
  const [showActivation, setShowActivation] = useState(false);
  const [localSettings, setLocalSettings] = useState(settings);

  useEffect(() => {
    loadSettings();
    loadLicense();
  }, []);

  useEffect(() => {
    setLocalSettings(settings);
  }, [settings]);

  const handleSave = () => {
    updateSettings(localSettings);
  };

  const handleReset = () => {
    setLocalSettings(settings);
  };

  const handleSelectPath = async (key: 'defaultVideoSavePath' | 'modelStoragePath') => {
    if (window.electronAPI) {
      const path = await window.electronAPI.system.selectDirectory();
      if (path) {
        setLocalSettings({ ...localSettings, [key]: path });
      }
    }
  };

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
                <input
                  type="checkbox"
                  title="开机自启动"
                  className="sr-only peer"
                  checked={localSettings.autoStartOnBoot}
                  onChange={(e) => setLocalSettings({ ...localSettings, autoStartOnBoot: e.target.checked })}
                />
                <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
              </label>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-700">自动检查更新</span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  title="自动检查更新"
                  className="sr-only peer"
                  checked={localSettings.autoCheckUpdate}
                  onChange={(e) => setLocalSettings({ ...localSettings, autoCheckUpdate: e.target.checked })}
                />
                <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
              </label>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-700">主题</span>
              <select
                title="主题选择"
                className="p-2 border border-slate-200 rounded-lg text-sm bg-white focus:ring-2 focus:ring-indigo-500 cursor-pointer"
                value={localSettings.theme}
                onChange={(e) => setLocalSettings({ ...localSettings, theme: e.target.value as 'light' | 'dark' })}
              >
                <option value="light">浅色</option>
                <option value="dark">深色</option>
              </select>
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
                <input type="text" title="作品保存路径" value={localSettings.defaultVideoSavePath} readOnly className="flex-1 p-2 bg-slate-50 border border-slate-200 rounded-l-lg text-sm text-slate-500" />
                <button onClick={() => handleSelectPath('defaultVideoSavePath')} className="px-4 py-2 bg-white border border-l-0 border-slate-200 rounded-r-lg text-sm font-medium text-indigo-600 hover:bg-slate-50 transition-colors">修改</button>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">模型存储路径</label>
              <div className="flex">
                <input type="text" title="模型存储路径" value={localSettings.modelStoragePath} readOnly className="flex-1 p-2 bg-slate-50 border border-slate-200 rounded-l-lg text-sm text-slate-500" />
                <button onClick={() => handleSelectPath('modelStoragePath')} className="px-4 py-2 bg-white border border-l-0 border-slate-200 rounded-r-lg text-sm font-medium text-indigo-600 hover:bg-slate-50 transition-colors">修改</button>
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
              <select
                title="推理模式"
                className="p-2 border border-slate-200 rounded-lg text-sm bg-white focus:ring-2 focus:ring-indigo-500 cursor-pointer"
                value={localSettings.inferenceMode}
                onChange={(e) => setLocalSettings({ ...localSettings, inferenceMode: e.target.value as 'auto' | 'cpu' | 'gpu' })}
              >
                <option value="auto">自动选择 (推荐)</option>
                <option value="gpu">GPU (CUDA)</option>
                <option value="cpu">CPU 仅使用</option>
              </select>
            </div>
          </div>
        </section>

        {/* Cache */}
        <section className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 hover:shadow-md transition-shadow">
          <h2 className="text-lg font-bold text-slate-800 mb-4 border-b border-slate-100 pb-2 flex items-center">
            <Trash2 size={20} className="mr-2 text-indigo-500" />缓存管理
          </h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-700">自动清理缓存</span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  title="自动清理缓存"
                  className="sr-only peer"
                  checked={localSettings.autoClearCacheEnabled}
                  onChange={(e) => setLocalSettings({ ...localSettings, autoClearCacheEnabled: e.target.checked })}
                />
                <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
              </label>
            </div>
            {localSettings.autoClearCacheEnabled && (
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-700">清理周期</span>
                <select
                  title="清理周期"
                  className="p-2 border border-slate-200 rounded-lg text-sm bg-white"
                  value={localSettings.autoClearCycleDays}
                  onChange={(e) => setLocalSettings({ ...localSettings, autoClearCycleDays: Number(e.target.value) })}
                >
                  <option value={7}>每 7 天</option>
                  <option value={30}>每 30 天</option>
                </select>
              </div>
            )}
          </div>
        </section>

        {/* License */}
        <section className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 hover:shadow-md transition-shadow">
          <h2 className="text-lg font-bold text-slate-800 mb-4 border-b border-slate-100 pb-2 flex items-center">
            <Key size={20} className="mr-2 text-indigo-500" />授权管理
          </h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-700">授权状态</span>
              <span className={`text-sm font-medium ${licenseStatus?.type === 'activated' ? 'text-green-600' : 'text-amber-600'}`}>
                {licenseStatus?.type === 'activated' ? '已激活' : `试用版 (剩余 ${licenseStatus?.remaining_trial_count ?? 0} 次)`}
              </span>
            </div>
            {licenseStatus?.activation_code_masked && (
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-700">激活码</span>
                <span className="text-sm text-slate-500 font-mono">{licenseStatus.activation_code_masked}</span>
              </div>
            )}
            <div className="pt-2">
              <button
                onClick={() => setShowActivation(true)}
                className="px-4 py-2 text-sm font-medium text-indigo-600 bg-indigo-50 rounded-lg hover:bg-indigo-100 transition-colors"
              >
                {licenseStatus?.type === 'activated' ? '管理授权' : '输入激活码'}
              </button>
            </div>
          </div>
        </section>

        <div className="flex justify-end space-x-4 pt-4">
          <button onClick={handleReset} className="px-6 py-2.5 rounded-lg border border-slate-300 text-slate-600 font-medium hover:bg-slate-50 text-sm flex items-center transition-all active:scale-95">
            <RefreshCw size={16} className="mr-2" /> 重置
          </button>
          <button onClick={handleSave} disabled={loading} className="px-6 py-2.5 rounded-lg bg-indigo-600 text-white font-medium hover:bg-indigo-700 text-sm flex items-center shadow-sm transition-all active:scale-95 disabled:opacity-50">
            <Save size={16} className="mr-2" /> {loading ? '保存中...' : '保存设置'}
          </button>
        </div>
      </div>

      <ActivationModal open={showActivation} onClose={() => setShowActivation(false)} />
    </div>
  );
};

export default Settings;
