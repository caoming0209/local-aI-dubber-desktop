"""Voice model management routes."""

import asyncio
from fastapi import APIRouter
from fastapi.responses import Response

from src.storage.voice_models_repo import voice_models_repo
from src.core.tts_engine import tts_engine
from src.core.model_manager import model_manager

router = APIRouter(tags=["voices"])

# Track active download tasks for pause/cancel
_download_tasks: dict[str, asyncio.Task] = {}
_download_cancel_flags: dict[str, bool] = {}


@router.get("/voices")
async def list_voices(search: str = "", category: str = "", download_status: str = ""):
    data = voice_models_repo.list(search=search, category=category, download_status=download_status)
    return {"success": True, "data": data}


@router.post("/voices/{voice_id}/favorite")
async def toggle_favorite(voice_id: str):
    result = voice_models_repo.toggle_favorite(voice_id)
    if not result:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "音色不存在"}}
    return {"success": True, "data": {"is_favorited": bool(result["is_favorited"])}}


@router.post("/voices/{voice_id}/download")
async def start_download(voice_id: str):
    voice = voice_models_repo.get_by_id(voice_id)
    if not voice:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "音色不存在"}}
    if voice["download_status"] == "downloaded":
        return {"success": True, "data": {"status": "already_downloaded"}}

    # Cancel any existing download for this voice
    if voice_id in _download_tasks:
        _download_cancel_flags[voice_id] = True
        _download_tasks[voice_id].cancel()

    voice_models_repo.update_download_status(voice_id, "downloading", 0)
    _download_cancel_flags[voice_id] = False

    # Launch async download task
    task = asyncio.create_task(_download_model(voice_id))
    _download_tasks[voice_id] = task

    return {"success": True, "data": {"status": "downloading"}}


async def _download_model(voice_id: str) -> None:
    """Download CosyVoice2 base model via huggingface_hub.

    All voice models share the same CosyVoice2-0.5B base model.
    Individual voice prompt files are small and bundled separately.
    """
    try:
        models_dir = model_manager.get_models_dir()
        cosyvoice_dir = __import__("os").path.join(models_dir, "cosyvoice2", "CosyVoice2-0.5B")

        # Check if base model already exists
        if __import__("os").path.isdir(cosyvoice_dir):
            yaml_path = __import__("os").path.join(cosyvoice_dir, "cosyvoice2.yaml")
            if __import__("os").path.isfile(yaml_path):
                # Base model exists, just mark as downloaded
                voice = voice_models_repo.get_by_id(voice_id)
                model_path = cosyvoice_dir
                voice_models_repo.update_download_status(voice_id, "downloaded", 1.0, model_path)
                model_manager.verify_on_download_complete(voice_id, model_path)
                return

        # Download from HuggingFace
        voice_models_repo.update_download_status(voice_id, "downloading", 0.1)

        def _do_download():
            from huggingface_hub import snapshot_download
            return snapshot_download(
                repo_id="FunAudioLLM/CosyVoice2-0.5B",
                local_dir=cosyvoice_dir,
                resume_download=True,
            )

        # Run blocking download in thread
        result_dir = await asyncio.to_thread(_do_download)

        if _download_cancel_flags.get(voice_id):
            voice_models_repo.update_download_status(voice_id, "not_downloaded", 0)
            return

        voice_models_repo.update_download_status(voice_id, "downloading", 0.9)

        # Verify and finalize
        model_manager.verify_on_download_complete(voice_id, result_dir)

    except asyncio.CancelledError:
        voice_models_repo.update_download_status(voice_id, "not_downloaded", 0)
    except Exception as e:
        print(f"[voices] Download failed for {voice_id}: {e}")
        voice_models_repo.update_download_status(voice_id, "not_downloaded", 0)
    finally:
        _download_tasks.pop(voice_id, None)
        _download_cancel_flags.pop(voice_id, None)


@router.post("/voices/{voice_id}/download/pause")
async def pause_download(voice_id: str):
    voice = voice_models_repo.get_by_id(voice_id)
    if not voice:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "音色不存在"}}

    task = _download_tasks.get(voice_id)
    if task:
        _download_cancel_flags[voice_id] = True
        task.cancel()
        voice_models_repo.update_download_status(voice_id, "paused", voice.get("download_progress", 0))

    return {"success": True, "data": {"status": "paused"}}


@router.post("/voices/{voice_id}/download/resume")
async def resume_download(voice_id: str):
    voice = voice_models_repo.get_by_id(voice_id)
    if not voice:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "音色不存在"}}

    # Re-trigger download (huggingface_hub supports resume_download)
    _download_cancel_flags[voice_id] = False
    voice_models_repo.update_download_status(voice_id, "downloading", voice.get("download_progress", 0))

    task = asyncio.create_task(_download_model(voice_id))
    _download_tasks[voice_id] = task

    return {"success": True, "data": {"status": "downloading"}}


@router.delete("/voices/{voice_id}/model")
async def delete_model(voice_id: str):
    ok = voice_models_repo.delete_model(voice_id)
    if not ok:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "音色不存在或未下载"}}
    return {"success": True, "data": {"deleted": True}}


@router.post("/voices/{voice_id}/preview")
async def preview_voice(voice_id: str, body: dict):
    voice = voice_models_repo.get_by_id(voice_id)
    if not voice:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "音色不存在"}}

    text = body.get("text", "大家好，欢迎使用智影口播助手")
    speed = body.get("speed", 1.0)
    volume = body.get("volume", 1.0)
    emotion = body.get("emotion", 0.5)

    try:
        audio_bytes = await asyncio.to_thread(
            tts_engine.preview, text, voice_id, speed, volume, emotion
        )
        return Response(content=audio_bytes, media_type="audio/wav")
    except Exception as e:
        return {"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(e)}}
