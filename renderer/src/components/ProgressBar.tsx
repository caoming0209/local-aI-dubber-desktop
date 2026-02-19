import { useState, useEffect } from 'react';
import { X, CheckCircle, AlertCircle, Pause, Play, XCircle } from 'lucide-react';
import { subscribeProgress } from '../services/pipeline';
import type { SingleProgressEvent } from '@shared/ipc-types';

interface ProgressBarProps {
  jobId: string;
  onComplete?: (result: { work_id: string; file_path: string; duration_seconds: number }) => void;
  onError?: (error: { code: string; message: string }) => void;
  onCancel?: () => void;
}

const STEP_LABELS: Record<string, string> = {
  script_optimization: '文案优化',
  tts: '语音合成',
  lipsync: '口型同步',
  synthesis: '视频合成',
  completed: '生成完成',
  failed: '生成失败',
};

export default function ProgressBar({ jobId, onComplete, onError, onCancel }: ProgressBarProps) {
  const [progress, setProgress] = useState(0);
  const [step, setStep] = useState('');
  const [message, setMessage] = useState('准备中...');
  const [status, setStatus] = useState<'running' | 'paused' | 'completed' | 'failed'>('running');
  const [stepIndex, setStepIndex] = useState(0);
  const [totalSteps, setTotalSteps] = useState(4);

  useEffect(() => {
    const unsubscribe = subscribeProgress(
      jobId,
      (data) => {
        const event = data as SingleProgressEvent;
        setProgress(event.progress ?? 0);
        setStep(event.step ?? '');
        setMessage(event.message ?? '');
        setStepIndex(event.step_index ?? 0);
        setTotalSteps(event.total_steps ?? 4);

        if (event.step === 'completed') {
          setStatus('completed');
          onComplete?.(event.result!);
        } else if (event.step === 'failed') {
          setStatus('failed');
          onError?.(event.error!);
        }
      },
      () => {},
      (err) => {
        setStatus('failed');
        setMessage(err.message);
      },
    );

    return unsubscribe;
  }, [jobId]);

  const handlePause = async () => {
    if (typeof window !== 'undefined' && window.electronAPI) {
      await window.electronAPI.engine.request('POST', `/api/pipeline/pause/${jobId}`);
      setStatus('paused');
    }
  };

  const handleResume = async () => {
    if (typeof window !== 'undefined' && window.electronAPI) {
      await window.electronAPI.engine.request('POST', `/api/pipeline/resume/${jobId}`);
      setStatus('running');
    }
  };

  const handleCancel = async () => {
    if (typeof window !== 'undefined' && window.electronAPI) {
      await window.electronAPI.engine.request('POST', `/api/pipeline/cancel/${jobId}`);
      setStatus('failed');
      onCancel?.();
    }
  };

  const pct = Math.round(progress * 100);
  const stepLabel = STEP_LABELS[step] || step;

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          {status === 'completed' && <CheckCircle className="w-5 h-5 text-green-500" />}
          {status === 'failed' && <AlertCircle className="w-5 h-5 text-red-500" />}
          <span className="text-sm font-medium text-gray-700">
            {status === 'completed' ? '生成完成' : status === 'failed' ? '生成失败' : `步骤 ${stepIndex}/${totalSteps}: ${stepLabel}`}
          </span>
        </div>
        <div className="flex items-center gap-1">
          {status === 'running' && (
            <button onClick={handlePause} className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-500" title="暂停">
              <Pause className="w-4 h-4" />
            </button>
          )}
          {status === 'paused' && (
            <button onClick={handleResume} className="p-1.5 rounded-lg hover:bg-gray-100 text-indigo-600" title="继续">
              <Play className="w-4 h-4" />
            </button>
          )}
          {(status === 'running' || status === 'paused') && (
            <button onClick={handleCancel} className="p-1.5 rounded-lg hover:bg-gray-100 text-red-500" title="取消">
              <XCircle className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      <div className="w-full bg-gray-100 rounded-full h-2.5 mb-2">
        <div
          className={`h-2.5 rounded-full transition-all duration-300 ${
            status === 'completed' ? 'bg-green-500' :
            status === 'failed' ? 'bg-red-500' :
            status === 'paused' ? 'bg-yellow-500' :
            'bg-indigo-500'
          }`}
          style={{ width: `${pct}%` }}
        />
      </div>

      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>{message}</span>
        <span>{pct}%</span>
      </div>
    </div>
  );
}
