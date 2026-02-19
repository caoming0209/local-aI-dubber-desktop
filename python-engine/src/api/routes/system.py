"""System and settings API routes."""

from fastapi import APIRouter

from src.storage.settings_store import settings_store

router = APIRouter(tags=["system"])


@router.get("/settings")
async def get_settings():
    data = settings_store.read()
    return {"success": True, "data": data}


@router.put("/settings")
async def update_settings(body: dict):
    data = settings_store.update(body)
    return {"success": True, "data": data}


@router.get("/system/hardware")
async def get_hardware():
    """Return hardware info including GPU detection."""
    import platform
    from src.core.gpu_detector import gpu_detector

    gpu_info = gpu_detector.detect()

    data = {
        "cpu": platform.processor() or "Unknown",
        "memory_gb": 0,
        "gpu": gpu_info["gpu_name"],
        "gpu_vendor": gpu_info["gpu_vendor"],
        "gpu_vram_gb": gpu_info["gpu_vram_gb"],
        "gpu_backend": gpu_info["backend"],
        "disk_free_gb": 0,
        "os": f"{platform.system()} {platform.version()}",
    }

    try:
        import shutil
        total, used, free = shutil.disk_usage("/")
        data["disk_free_gb"] = round(free / (1024**3), 1)
    except Exception:
        pass

    return {"success": True, "data": data}


@router.post("/system/gpu-check")
async def gpu_check():
    """Check GPU compatibility for AI inference."""
    from src.core.gpu_detector import gpu_detector
    return {"success": True, "data": gpu_detector.detect()}


@router.get("/system/cache-info")
async def cache_info():
    return {"success": True, "data": {"size_mb": 0}}


@router.delete("/system/cache")
async def clear_cache():
    return {"success": True, "data": {"cleared_mb": 0}}


@router.get("/system/version")
async def get_version():
    return {
        "success": True,
        "data": {
            "current": "1.0.0",
            "latest": None,
            "update_available": False,
        },
    }


@router.post("/system/check-update")
async def check_update():
    return {
        "success": True,
        "data": {
            "current": "1.0.0",
            "latest": None,
            "update_available": False,
        },
    }
