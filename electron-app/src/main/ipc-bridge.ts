import { ipcMain, BrowserWindow } from 'electron';
import http from 'http';
import { PythonManager } from './python-manager';

export function setupIpcBridge(pythonManager: PythonManager, mainWindow: BrowserWindow): void {
  // ─── HTTP request proxy ───────────────────────────────────────
  ipcMain.handle('engine:request', async (_, method: string, path: string, body?: object) => {
    const port = pythonManager.enginePort;
    if (!port) {
      return { success: false, error: { code: 'INTERNAL_ERROR', message: '推理引擎未就绪' } };
    }

    const url = `http://127.0.0.1:${port}${path}`;
    const payload = body ? JSON.stringify(body) : undefined;

    return new Promise((resolve) => {
      const req = http.request(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          ...(payload ? { 'Content-Length': Buffer.byteLength(payload) } : {}),
        },
        timeout: 30_000,
      }, (res) => {
        let data = '';
        res.on('data', (chunk) => { data += chunk; });
        res.on('end', () => {
          try {
            resolve(JSON.parse(data));
          } catch {
            resolve({ success: false, error: { code: 'INTERNAL_ERROR', message: 'Invalid JSON response' } });
          }
        });
      });

      req.on('error', (err) => {
        resolve({ success: false, error: { code: 'INTERNAL_ERROR', message: err.message } });
      });

      req.on('timeout', () => {
        req.destroy();
        resolve({ success: false, error: { code: 'INTERNAL_ERROR', message: 'Request timeout' } });
      });

      if (payload) req.write(payload);
      req.end();
    });
  });

  // ─── SSE progress subscription ────────────────────────────────
  const activeSubscriptions = new Map<string, http.ClientRequest>();

  ipcMain.on('pipeline:subscribe', (event, jobId: string) => {
    const port = pythonManager.enginePort;
    if (!port) return;

    // Clean up existing subscription for this job
    if (activeSubscriptions.has(jobId)) {
      activeSubscriptions.get(jobId)?.destroy();
    }

    const url = `http://127.0.0.1:${port}/api/pipeline/progress/${jobId}`;
    const channel = `pipeline:progress:${jobId}`;

    const req = http.get(url, {
      headers: { Accept: 'text/event-stream' },
    }, (res) => {
      let buffer = '';

      res.on('data', (chunk: Buffer) => {
        buffer += chunk.toString();
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              mainWindow.webContents.send(channel, data);

              if (data.step === 'completed' || data.step === 'failed' || data.type === 'batch_completed') {
                mainWindow.webContents.send(`${channel}:done`);
                activeSubscriptions.delete(jobId);
              }
            } catch {
              // Ignore malformed SSE data
            }
          }
        }
      });

      res.on('end', () => {
        mainWindow.webContents.send(`${channel}:done`);
        activeSubscriptions.delete(jobId);
      });

      res.on('error', (err) => {
        mainWindow.webContents.send(`${channel}:error`, err);
        activeSubscriptions.delete(jobId);
      });
    });

    req.on('error', (err) => {
      mainWindow.webContents.send(`${channel}:error`, err);
    });

    activeSubscriptions.set(jobId, req);
  });

  ipcMain.on('pipeline:unsubscribe', (_, jobId: string) => {
    const req = activeSubscriptions.get(jobId);
    if (req) {
      req.destroy();
      activeSubscriptions.delete(jobId);
    }
  });
}
