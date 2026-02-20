import { ChildProcess, spawn } from 'child_process';
import path from 'path';
import { app } from 'electron';

interface ReadySignal {
  status: 'ready';
  port: number;
}

export class PythonManager {
  private process: ChildProcess | null = null;
  private port: number = 0;
  private restartCount = 0;
  private readonly maxRestarts = 3;
  private readonly startupTimeoutMs = 10_000;

  get enginePort(): number {
    return this.port;
  }

  get isRunning(): boolean {
    return this.process !== null && this.process.exitCode === null;
  }

  async start(): Promise<number> {
    return new Promise((resolve, reject) => {
      const pythonPath = this.getPythonPath();
      const serverScript = this.getServerScript();

      this.process = spawn(pythonPath, [serverScript], {
        cwd: this.getEngineCwd(),
        stdio: ['pipe', 'pipe', 'pipe'],
        env: {
          ...process.env,
          // Pass dev mode flag to Python engine
          ...(app.isPackaged ? {} : { NODE_ENV: 'development', DEV_MODE: '1' }),
        },
      });

      const timeout = setTimeout(() => {
        this.process?.kill();
        reject(new Error('Python engine startup timeout (10s)'));
      }, this.startupTimeoutMs);

      let stdoutBuffer = '';

      this.process.stdout?.on('data', (chunk: Buffer) => {
        stdoutBuffer += chunk.toString();
        const lines = stdoutBuffer.split('\n');
        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed) continue;
          try {
            const signal: ReadySignal = JSON.parse(trimmed);
            if (signal.status === 'ready' && signal.port) {
              clearTimeout(timeout);
              this.port = signal.port;
              this.restartCount = 0;
              resolve(signal.port);
            }
          } catch {
            // Not JSON, ignore
          }
        }
      });

      this.process.stderr?.on('data', (chunk: Buffer) => {
        console.error('[python-engine]', chunk.toString());
      });

      this.process.on('exit', (code) => {
        console.log(`[python-engine] exited with code ${code}`);
        this.process = null;
        if (code !== 0 && code !== null) {
          this.handleCrash();
        }
      });

      this.process.on('error', (err) => {
        clearTimeout(timeout);
        reject(err);
      });
    });
  }

  private async handleCrash(): Promise<void> {
    if (this.restartCount >= this.maxRestarts) {
      console.error('[python-engine] Max restarts reached');
      return;
    }
    this.restartCount++;
    const delay = Math.pow(2, this.restartCount - 1) * 1000; // 1s, 2s, 4s
    console.log(`[python-engine] Restarting in ${delay}ms (attempt ${this.restartCount}/${this.maxRestarts})`);
    await new Promise((r) => setTimeout(r, delay));
    try {
      await this.start();
    } catch (err) {
      console.error('[python-engine] Restart failed:', err);
    }
  }

  async stop(): Promise<void> {
    if (!this.process) return;
    return new Promise((resolve) => {
      const forceKillTimeout = setTimeout(() => {
        this.process?.kill('SIGKILL');
        resolve();
      }, 3000);

      this.process!.on('exit', () => {
        clearTimeout(forceKillTimeout);
        this.process = null;
        resolve();
      });

      this.process!.kill('SIGTERM');
    });
  }

  private getPythonPath(): string {
    if (app.isPackaged) {
      return path.join(process.resourcesPath, 'python-engine', 'server.exe');
    }
    return path.join(__dirname, '..', '..', '..', 'python-engine', '.venv', 'Scripts', 'python.exe');
  }

  private getServerScript(): string {
    if (app.isPackaged) {
      return ''; // PyInstaller exe doesn't need script arg
    }
    return path.join(__dirname, '..', '..', '..', 'python-engine', 'src', 'api', 'server.py');
  }

  private getEngineCwd(): string {
    if (app.isPackaged) {
      return path.join(process.resourcesPath, 'python-engine');
    }
    return path.join(__dirname, '..', '..', '..', 'python-engine');
  }
}
