"""Voice model management routes."""

from fastapi import APIRouter
from fastapi.responses import Response

from src.storage.voice_models_repo import voice_models_repo
from src.core.tts_engine import tts_engine

router = APIRouter(tags=["voices"])


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

    voice_models_repo.update_download_status(voice_id, "downloading", 0)
    # TODO: Trigger async download task with SSE progress
    return {"success": True, "data": {"status": "downloading"}}


@router.post("/voices/{voice_id}/download/pause")
async def pause_download(voice_id: str):
    voice = voice_models_repo.get_by_id(voice_id)
    if not voice:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "音色不存在"}}
    # TODO: Pause actual download task
    return {"success": True, "data": {"status": "paused"}}


@router.post("/voices/{voice_id}/download/resume")
async def resume_download(voice_id: str):
    voice = voice_models_repo.get_by_id(voice_id)
    if not voice:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "音色不存在"}}
    # TODO: Resume actual download task
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
        audio_bytes = tts_engine.preview(text, voice_id, speed, volume, emotion)
        return Response(content=audio_bytes, media_type="audio/wav")
    except Exception as e:
        return {"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(e)}}
