"""FastAPI server entry point.

Binds to 127.0.0.1 on a random available port.
Outputs {"status": "ready", "port": N} to stdout for Electron to read.
"""

import sys
import os

# CRITICAL: Set UTF-8 encoding BEFORE any other imports
# This must happen before CosyVoice modules initialize their logging
if sys.platform == "win32":
    # Reconfigure stdio separately from locale so locale failure doesn't
    # prevent UTF-8 streams from being set up.
    for _stream_name in ("stdout", "stderr"):
        try:
            getattr(sys, _stream_name).reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    try:
        import locale
        # Windows may not have 'en_US.UTF-8'; try generic '.UTF-8' fallback
        try:
            locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        except locale.Error:
            try:
                locale.setlocale(locale.LC_ALL, '.UTF-8')
            except locale.Error:
                pass
    except Exception:
        pass

# Force UTF-8 mode for all file I/O and string operations
os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

import logging as _logging


def _fix_logging_handler_encoding():
    """Ensure all existing logging StreamHandlers write UTF-8.

    CosyVoice's file_utils.py calls logging.basicConfig() on import, which
    creates a StreamHandler.  On Windows the handler's stream may default to
    the system code page (e.g. GBK/cp936) causing Chinese text to appear
    garbled.  This function patches every StreamHandler on the root logger
    so it explicitly uses UTF-8.
    """
    import io
    for handler in _logging.root.handlers:
        if isinstance(handler, _logging.StreamHandler):
            stream = handler.stream
            if hasattr(stream, "reconfigure"):
                try:
                    stream.reconfigure(encoding="utf-8", errors="replace")
                except Exception:
                    pass
            elif hasattr(stream, "buffer"):
                # Replace with a new UTF-8 TextIOWrapper around the buffer
                try:
                    handler.stream = io.TextIOWrapper(
                        stream.buffer, encoding="utf-8", errors="replace"
                    )
                except Exception:
                    pass


# Debug: Print encoding info at startup
print(f"[server] Python startup - sys.flags.utf8_mode: {sys.flags.utf8_mode}", file=sys.stderr, flush=True)
print(f"[server] sys.stdout.encoding: {sys.stdout.encoding}", file=sys.stderr, flush=True)
print(f"[server] sys.stderr.encoding: {sys.stderr.encoding}", file=sys.stderr, flush=True)

import json
import socket
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
        for _stream_name in ("stdout", "stderr"):
            try:
                getattr(sys, _stream_name).reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass

    port = find_free_port()

    # Signal readiness to Electron via stdout
    ready_signal = json.dumps({"status": "ready", "port": port})
    sys.stdout.write(ready_signal + "\n")
    sys.stdout.flush()

    # Fix any logging handlers that were created before UTF-8 was configured
    _fix_logging_handler_encoding()

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=port,
        log_level="info",
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "()": "uvicorn.logging.DefaultFormatter",
                    "fmt": "%(levelprefix)s %(message)s",
                    "use_colors": None,
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stderr",
                },
            },
            "loggers": {
                "uvicorn": {"handlers": ["default"], "level": "INFO"},
                "uvicorn.error": {"level": "INFO"},
                "uvicorn.access": {"handlers": ["default"], "level": "INFO", "propagate": False},
            },
        },
    )


if __name__ == "__main__":
    # Running directly (not spawned by Electron) → enable dev mode
    os.environ.setdefault("DEV_MODE", "1")
    main()
