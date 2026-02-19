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
    """Return hardware info. Full implementation in Phase 9."""
    import platform

    data = {
        "cpu": platform.processor() or "Unknown",
        "memory_gb": 0,
        "gpu": "Unknown",
        "gpu_vram_gb": 0,
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
    """Check GPU compatibility. Full implementation in Phase 9."""
    return {
        "success": True,
        "data": {
            "gpu_available": False,
            "cuda_version": None,
            "recommendation": "not_detected",
        },
    }


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
