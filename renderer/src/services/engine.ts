/**
 * API client for communicating with the Python engine via Electron IPC.
 * All requests are proxied through window.electronAPI.engine.request.
 */

import type { ApiResponse } from '@shared/ipc-types';

type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

async function request<T = unknown>(
  method: HttpMethod,
  path: string,
  body?: object,
): Promise<ApiResponse<T>> {
  if (typeof window !== 'undefined' && window.electronAPI) {
    return window.electronAPI.engine.request<T>(method, path, body);
  }

  // Fallback for browser dev mode: direct HTTP to engine
  const port = getDevPort();
  const url = `http://127.0.0.1:${port}${path}`;
  const res = await fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  });
  return res.json();
}

function getDevPort(): number {
  if (typeof window !== 'undefined' && window.electronAPI) {
    return window.electronAPI.getEnginePort();
  }
  // Default dev port — override via env if needed
  return 18432;
}

export const api = {
  get: <T = unknown>(path: string) => request<T>('GET', path),
  post: <T = unknown>(path: string, body?: object) => request<T>('POST', path, body),
  put: <T = unknown>(path: string, body?: object) => request<T>('PUT', path, body),
  patch: <T = unknown>(path: string, body?: object) => request<T>('PATCH', path, body),
  delete: <T = unknown>(path: string, body?: object) => request<T>('DELETE', path, body),
};
