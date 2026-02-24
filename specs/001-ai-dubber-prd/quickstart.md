# Quickstart: 智影口播 · AI数字人视频助手（Windows版）V1.3

## Prerequisites

- Node.js 20 LTS
- Python 3.11
- FFmpeg 6.x+ (available in PATH)
- Git
- (Optional) CUDA Toolkit 11.8 for GPU acceleration

## Repository structure

- `electron-app/`: Electron main process
- `renderer/`: React renderer
- `python-engine/`: Python local engine (FastAPI)
- `shared/`: shared TypeScript types

## Setup

### 1) Python engine

```bash
cd python-engine
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
python src/api/server.py
```

Expected output includes:

```json
{"status": "ready", "port": 18432}
```

### 2) Electron app

```bash
cd electron-app
npm install
npm run dev
```

## Smoke test checklist

- Open the app
- Verify engine handshake succeeds and UI becomes interactive
- Run a single-generation workflow with sample image + script
- Confirm output video and subtitle files exist in output folder

## Notes

- Core generation MUST work offline; avoid network actions unless explicitly testing activation/model download/update.
- Batch generation MUST be serial and capped at <= 30 items.
