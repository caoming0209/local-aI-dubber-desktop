import { app, BrowserWindow, ipcMain, shell, dialog, protocol } from 'electron';
import path from 'path';
import fs from 'fs';
import { PythonManager } from './python-manager';
import { setupIpcBridge } from './ipc-bridge';
import { setupAutoUpdater } from './updater';

const pythonManager = new PythonManager();
let mainWindow: BrowserWindow | null = null;

protocol.registerSchemesAsPrivileged([
  {
    scheme: 'local-file',
    privileges: {
      secure: true,
      standard: true,
      supportFetchAPI: true,
      corsEnabled: true,
      bypassCSP: true,
    },
  },
]);

function registerLocalFileProtocol(): void {
  protocol.handle('local-file', (request) => {
    const url = request.url.slice('local-file://'.length);
    try {
      const decodedPath = decodeURIComponent(url);
      const file = fs.readFileSync(decodedPath);
      const ext = path.extname(decodedPath).toLowerCase();
      const mimeTypes: Record<string, string> = {
        '.mp4': 'video/mp4',
        '.webm': 'video/webm',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
      };
      const mimeType = mimeTypes[ext] || 'application/octet-stream';
      return new Response(file, {
        headers: { 'Content-Type': mimeType },
      });
    } catch (error) {
      console.error('[protocol] Failed to read file:', url, error);
      return new Response(null, { status: 404 });
    }
  });
}

function createWindow(): void {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 1024,
    minHeight: 680,
    title: '智影口播 · AI数字人视频助手',
    webPreferences: {
      preload: path.join(__dirname, '..', 'preload', 'index.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      webSecurity: true,
    },
    show: false,
  });

  mainWindow.once('ready-to-show', () => {
    mainWindow?.show();
  });

  if (!app.isPackaged) {
    mainWindow.loadURL('http://localhost:3000');
  } else {
    mainWindow.loadFile(path.join(process.resourcesPath, 'renderer', 'index.html'));
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

async function startEngine(): Promise<void> {
  try {
    const port = await pythonManager.start();
    console.log(`[main] Python engine ready on port ${port}`);
  } catch (err) {
    console.error('[main] Failed to start Python engine:', err);
    dialog.showErrorBox(
      '推理引擎启动失败',
      '无法启动 Python 推理引擎，请检查安装是否完整。\n\n' +
      '您可以尝试重新启动应用。',
    );
  }
}

app.whenReady().then(async () => {
  registerLocalFileProtocol();
  createWindow();
  setupIpcBridge(pythonManager, mainWindow!);
  if (app.isPackaged) {
    setupAutoUpdater(mainWindow!);
  }
  await startEngine();
});

app.on('window-all-closed', async () => {
  await pythonManager.stop();
  app.quit();
});

app.on('before-quit', async () => {
  await pythonManager.stop();
});

// ─── System IPC handlers ──────────────────────────────────────
ipcMain.handle('system:openPath', async (_, filePath: string) => {
  await shell.openPath(filePath);
});

ipcMain.handle('system:showItemInFolder', (_, filePath: string) => {
  shell.showItemInFolder(filePath);
});

ipcMain.handle('system:selectDirectory', async () => {
  if (!mainWindow) return null;
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openDirectory'],
  });
  return result.canceled ? null : result.filePaths[0];
});

ipcMain.handle('system:selectFile', async (_, filters: { name: string; extensions: string[] }[]) => {
  if (!mainWindow) return null;
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openFile'],
    filters,
  });
  return result.canceled ? null : result.filePaths[0];
});

ipcMain.on('engine:getPort', (event) => {
  event.returnValue = pythonManager.enginePort;
});
