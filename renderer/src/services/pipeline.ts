/**
 * SSE progress subscription service.
 * Wraps window.electronAPI.pipeline.subscribeProgress for use in components.
 */

import type { SingleProgressEvent, BatchProgressEvent } from '@shared/ipc-types';

type ProgressEvent = SingleProgressEvent | BatchProgressEvent;
type Unsubscribe = () => void;

export function subscribeProgress(
  jobId: string,
  onEvent: (data: ProgressEvent) => void,
  onDone: () => void,
  onError: (err: Error) => void,
): Unsubscribe {
  if (typeof window !== 'undefined' && window.electronAPI) {
    return window.electronAPI.pipeline.subscribeProgress(jobId, onEvent, onDone, onError);
  }

  // Fallback for browser dev mode: direct SSE connection
  const port = window.electronAPI?.getEnginePort() ?? 18432;
  const url = `http://127.0.0.1:${port}/api/pipeline/progress/${jobId}`;
  const eventSource = new EventSource(url);

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onEvent(data);

      if (data.step === 'completed' || data.step === 'failed' || data.type === 'batch_completed') {
        eventSource.close();
        onDone();
      }
    } catch {
      // Ignore malformed data
    }
  };

  eventSource.onerror = () => {
    eventSource.close();
    onError(new Error('SSE connection lost'));
  };

  return () => {
    eventSource.close();
  };
}
