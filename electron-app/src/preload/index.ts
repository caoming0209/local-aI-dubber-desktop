import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('electronAPI', {
  engine: {
    request(method: string, path: string, body?: object) {
      return ipcRenderer.invoke('engine:request', method, path, body);
    },
  },

  pipeline: {
    subscribeProgress(
      jobId: string,
      onEvent: (data: object) => void,
      onDone: () => void,
      onError: (err: Error) => void,
    ) {
      const channel = `pipeline:progress:${jobId}`;
      const eventHandler = (_: unknown, data: object) => onEvent(data);
      const doneHandler = () => onDone();
      const errorHandler = (_: unknown, err: Error) => onError(err);

      ipcRenderer.on(channel, eventHandler);
      ipcRenderer.once(`${channel}:done`, doneHandler);
      ipcRenderer.once(`${channel}:error`, errorHandler);

      ipcRenderer.send('pipeline:subscribe', jobId);

      return () => {
        ipcRenderer.removeListener(channel, eventHandler);
        ipcRenderer.removeListener(`${channel}:done`, doneHandler);
        ipcRenderer.removeListener(`${channel}:error`, errorHandler);
        ipcRenderer.send('pipeline:unsubscribe', jobId);
      };
    },
  },

  system: {
    openPath(path: string) {
      return ipcRenderer.invoke('system:openPath', path);
    },
    showItemInFolder(path: string) {
      return ipcRenderer.invoke('system:showItemInFolder', path);
    },
    selectDirectory() {
      return ipcRenderer.invoke('system:selectDirectory');
    },
    selectFile(filters: { name: string; extensions: string[] }[]) {
      return ipcRenderer.invoke('system:selectFile', filters);
    },
  },

  getEnginePort() {
    return ipcRenderer.sendSync('engine:getPort');
  },
});
