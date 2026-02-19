"""Digital humans management routes."""

import os
import uuid

from fastapi import APIRouter, UploadFile, File, Form

from src.storage.digital_humans_repo import digital_humans_repo

router = APIRouter(tags=["digital-humans"])


@router.get("/digital-humans")
async def list_digital_humans(search: str = "", source: str = "", category: str = ""):
    data = digital_humans_repo.list(search=search, source=source, category=category)
    return {"success": True, "data": data}


@router.post("/digital-humans/upload", status_code=202)
async def upload_digital_human(
    file: UploadFile = File(...),
    name: str = Form(""),
    category: str = Form("other"),
):
    # Validate file size (500MB max)
    contents = await file.read()
    if len(contents) > 500 * 1024 * 1024:
        return {"success": False, "error": {"code": "INTERNAL_ERROR", "message": "文件大小不能超过 500MB"}}

    # Save uploaded file
    from src.storage.settings_store import settings_store
    settings = settings_store.read()
    upload_dir = os.path.join(
        os.path.dirname(settings.get("defaultVideoSavePath", "")),
        "digital_humans", "uploads"
    )
    os.makedirs(upload_dir, exist_ok=True)

    file_ext = os.path.splitext(file.filename or "video.mp4")[1] or ".mp4"
    saved_name = f"{uuid.uuid4().hex[:12]}{file_ext}"
    saved_path = os.path.join(upload_dir, saved_name)

    with open(saved_path, "wb") as f:
        f.write(contents)

    # Create DB record
    dh_name = name or os.path.splitext(file.filename or "自定义数字人")[0]
    dh = digital_humans_repo.create({
        "name": dh_name,
        "category": category,
        "source": "custom",
        "thumbnail_path": "",  # Will be generated during adaptation
        "preview_video_path": saved_path,
        "adaptation_status": "pending",
    })

    # TODO: Trigger async adaptation job (FFmpeg preprocess + Wav2Lip adapt)
    job_id = f"adapt_{uuid.uuid4().hex[:12]}"

    return {
        "success": True,
        "data": {"job_id": job_id, "digital_human_id": dh["id"]},
    }


@router.patch("/digital-humans/{dh_id}")
async def update_digital_human(dh_id: str, body: dict):
    result = digital_humans_repo.update(dh_id, body)
    if not result:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "数字人不存在"}}
    return {"success": True, "data": result}


@router.post("/digital-humans/{dh_id}/favorite")
async def toggle_favorite(dh_id: str):
    result = digital_humans_repo.toggle_favorite(dh_id)
    if not result:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "数字人不存在"}}
    return {"success": True, "data": {"is_favorited": bool(result["is_favorited"])}}


@router.post("/digital-humans/{dh_id}/re-adapt")
async def re_adapt(dh_id: str):
    dh = digital_humans_repo.get_by_id(dh_id)
    if not dh:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "数字人不存在"}}
    digital_humans_repo.update_adaptation(dh_id, "pending")
    # TODO: Trigger async re-adaptation job
    job_id = f"adapt_{uuid.uuid4().hex[:12]}"
    return {"success": True, "data": {"job_id": job_id}}


@router.delete("/digital-humans/{dh_id}")
async def delete_digital_human(dh_id: str):
    ok = digital_humans_repo.delete(dh_id)
    if not ok:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "数字人不存在或为官方数字人"}}
    return {"success": True, "data": {"deleted": True}}
