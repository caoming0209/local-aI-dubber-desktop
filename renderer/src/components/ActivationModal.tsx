import { useState } from 'react';
import { X, Key, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { useLicenseStore } from '../stores/license';

interface ActivationModalProps {
  open: boolean;
  onClose: () => void;
}

export default function ActivationModal({ open, onClose }: ActivationModalProps) {
  const [code, setCode] = useState('');
  const { activate, loading, error, status } = useLicenseStore();
  const [success, setSuccess] = useState(false);

  if (!open) return null;

  const handleActivate = async () => {
    const formatted = code.trim().toUpperCase();
    if (!formatted) return;
    const ok = await activate(formatted);
    if (ok) {
      setSuccess(true);
      setTimeout(() => {
        onClose();
        setSuccess(false);
        setCode('');
      }, 1500);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !loading) {
      handleActivate();
    }
  };

  const remaining = status?.remaining_trial_count ?? 0;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <Key className="w-5 h-5 text-indigo-600" />
            <h2 className="text-lg font-semibold text-gray-900">激活智影口播</h2>
          </div>
          <button onClick={onClose} className="p-1 rounded-lg hover:bg-gray-100 text-gray-400">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-5 space-y-4">
          {status?.type === 'trial' && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 text-sm text-amber-800">
              试用版剩余 <span className="font-bold">{remaining}</span> 次生成机会
              {remaining === 0 && '，请激活以继续使用'}
            </div>
          )}

          {success ? (
            <div className="flex flex-col items-center py-6 gap-3">
              <CheckCircle className="w-12 h-12 text-green-500" />
              <p className="text-green-700 font-medium">激活成功！</p>
            </div>
          ) : (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">激活码</label>
                <input
                  type="text"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="XXXX-XXXX-XXXX-XXXX"
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-center text-lg tracking-widest font-mono focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                  maxLength={19}
                  disabled={loading}
                />
              </div>

              {error && (
                <div className="flex items-center gap-2 text-sm text-red-600">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span>{error}</span>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        {!success && (
          <div className="px-6 py-4 bg-gray-50 border-t border-gray-100 flex justify-end gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 rounded-lg hover:bg-gray-100"
            >
              取消
            </button>
            <button
              onClick={handleActivate}
              disabled={loading || !code.trim()}
              className="px-5 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {loading && <Loader2 className="w-4 h-4 animate-spin" />}
              {loading ? '验证中...' : '激活'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
