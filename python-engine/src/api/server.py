"""FastAPI server entry point.

Binds to 127.0.0.1 on a random available port.
Outputs {"status": "ready", "port": N} to stdout for Electron to read.
"""

import json
import os
import socket
import sys
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

# Ensure python-engine root is on sys.path so `src.*` imports work
_engine_root = str(Path(__file__).resolve().parent.parent.parent)
if _engine_root not in sys.path:
    sys.path.insert(0, _engine_root)

# Add third_party paths for CosyVoice and Wav2Lip
_third_party = os.path.join(_engine_root, "third_party")
for _subdir in ["CosyVoice", "Wav2Lip"]:
    _path = os.path.join(_third_party, _subdir)
    if os.path.isdir(_path) and _path not in sys.path:
        sys.path.insert(0, _path)
_matcha = os.path.join(_third_party, "CosyVoice", "third_party", "Matcha-TTS")
if os.path.isdir(_matcha) and _matcha not in sys.path:
    sys.path.insert(0, _matcha)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.storage.database import init_db, close_db
from src.storage.settings_store import SettingsStore
from src.api.routes import system as system_routes
from src.api.routes import pipeline as pipeline_routes
from src.api.routes import works as works_routes
from src.api.routes import digital_humans as digital_humans_routes
from src.api.routes import voices as voices_routes
from src.api.routes import license as license_routes


def find_free_port() -> int:
    # In dev mode, use a fixed port so the browser frontend can connect
    from src.utils.dev_mode import is_dev_mode
    if is_dev_mode():
        return 18432
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    from src.utils.dev_mode import is_dev_mode
    if is_dev_mode():
        print("[server] DEV MODE: license checks disabled, no watermark, unlimited generation")
    await init_db()
    yield
    # Shutdown
    await close_db()


app = FastAPI(title="智影口播引擎", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route blueprints
app.include_router(system_routes.router, prefix="/api")
app.include_router(pipeline_routes.router, prefix="/api")
app.include_router(works_routes.router, prefix="/api")
app.include_router(digital_humans_routes.router, prefix="/api")
app.include_router(voices_routes.router, prefix="/api")
app.include_router(license_routes.router, prefix="/api")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(exc),
            },
        },
    )


def main():
    import uvicorn

    # Ensure UTF-8 console output on Windows (avoid garbled Chinese logs).
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    port = find_free_port()

    # Signal readiness to Electron via stdout
    ready_signal = json.dumps({"status": "ready", "port": port})
    sys.stdout.write(ready_signal + "\n")
    sys.stdout.flush()

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=port,
        log_level="info",
    )


if __name__ == "__main__":
    # Running directly (not spawned by Electron) → enable dev mode
    os.environ.setdefault("DEV_MODE", "1")
    main()
