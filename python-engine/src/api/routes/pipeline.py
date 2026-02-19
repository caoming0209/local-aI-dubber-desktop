"""Video generation pipeline routes with SSE progress streaming."""

import asyncio
import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from src.utils.progress import job_manager
from src.utils.dev_mode import is_dev_mode
from src.core.tts_engine import tts_engine
from src.core.lipsync_engine import lipsync_engine
from src.core.video_synthesizer import video_synthesizer
from src.core.model_manager import model_manager
from src.storage.works_repo import works_repo
from src.storage.settings_store import settings_store

router = APIRouter(tags=["pipeline"])

# In-memory cancellation flags
_cancel_flags: dict[str, bool] = {}
_pause_flags: dict[str, asyncio.Event] = {}


def _new_job_id(prefix: str = "job") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


async def _run_single_pipeline(job_id: str, body: dict) -> None:
    """Execute the single video generation pipeline."""
    emitter = job_manager.get_emitter(job_id)
    if not emitter:
        return

    settings = settings_store.read()
    save_dir = settings.get("defaultVideoSavePath", "")
    if not save_dir:
        save_dir = os.path.join(os.path.expanduser("~"), "Documents", "智影口播", "作品")
    os.makedirs(save_dir, exist_ok=True)

    try:
        job_manager.update_state(job_id, status="running")

        # Pre-check: verify voice model is ready
        voice_id = body.get("voice_id", "")
        if voice_id:
            check = model_manager.check_model_ready(voice_id, quick=True)
            if not check.ok:
                await emitter.emit("failed", 0, 0, check.message,
                                   error={"code": check.error_code, "message": check.message})
                job_manager.update_state(job_id, status="failed")
                await emitter.complete()
                _cancel_flags.pop(job_id, None)
                _pause_flags.pop(job_id, None)
                return

        # Pre-check: verify lipsync model is ready
        lipsync_check = model_manager.check_lipsync_model_ready()
        if not lipsync_check.ok:
            await emitter.emit("failed", 0, 0, lipsync_check.message,
                               error={"code": lipsync_check.error_code, "message": lipsync_check.message})
            job_manager.update_state(job_id, status="failed")
            await emitter.complete()
            _cancel_flags.pop(job_id, None)
            _pause_flags.pop(job_id, None)
            return

        # Step 1: Script optimization
        await _check_cancel(job_id)
        await emitter.emit("script_optimization", 1, 0.1, "文案优化中...")
        job_manager.update_state(job_id, current_step="script_optimization", step_index=1, progress=0.1)
        await asyncio.sleep(0.5)  # Simulate processing
        script = body.get("script", "")
        await emitter.emit("script_optimization", 1, 0.2, "文案优化完成")

        # Step 2: TTS
        await _check_cancel(job_id)
        await _wait_if_paused(job_id)
        await emitter.emit("tts", 2, 0.3, "语音合成中...")
        job_manager.update_state(job_id, current_step="tts", step_index=2, progress=0.3)

        voice_params = body.get("voice_params", {})
        tts_path = await asyncio.to_thread(
            tts_engine.synthesize,
            text=script,
            voice_id=body.get("voice_id", ""),
            speed=voice_params.get("speed", 1.0),
            volume=voice_params.get("volume", 1.0),
            emotion=voice_params.get("emotion", 0.5),
        )
        await emitter.emit("tts", 2, 0.4, "语音合成完成")

        # Resample to 16kHz for Wav2Lip
        resampled_path = tts_path.replace(".wav", "_16k.wav")
        await asyncio.to_thread(
            video_synthesizer.resample_audio, tts_path, resampled_path, 16000
        )

        # Step 3: Lipsync
        await _check_cancel(job_id)
        await _wait_if_paused(job_id)
        await emitter.emit("lipsync", 3, 0.5, "口型同步中...")
        job_manager.update_state(job_id, current_step="lipsync", step_index=3, progress=0.5)

        dh_video = _get_digital_human_video(body.get("digital_human_id", ""))
        lipsync_path = await asyncio.to_thread(
            lipsync_engine.process, dh_video, resampled_path
        )
        await emitter.emit("lipsync", 3, 0.7, "口型同步完成")

        # Step 4: Video synthesis
        await _check_cancel(job_id)
        await _wait_if_paused(job_id)
        await emitter.emit("synthesis", 4, 0.8, "视频合成中...")
        job_manager.update_state(job_id, current_step="synthesis", step_index=4, progress=0.8)

        output_name = body.get("output_name", f"video_{uuid.uuid4().hex[:6]}")
        output_path = os.path.join(save_dir, f"{output_name}.mp4")

        await asyncio.to_thread(
            video_synthesizer.synthesize,
            lipsync_video_path=lipsync_path,
            audio_path=tts_path,
            output_path=output_path,
            background=body.get("background"),
            subtitle=body.get("subtitle"),
            bgm=body.get("bgm"),
            aspect_ratio=body.get("aspect_ratio", "9:16"),
        )

        # Extract thumbnail
        thumb_dir = os.path.join(save_dir, ".thumbs")
        os.makedirs(thumb_dir, exist_ok=True)
        thumb_path = os.path.join(thumb_dir, f"{output_name}.jpg")
        await asyncio.to_thread(
            video_synthesizer.extract_thumbnail, output_path, thumb_path
        )

        # Get duration
        from src.utils.file_utils import get_video_duration, get_file_size
        duration = get_video_duration(output_path) or 0.0
        file_size = get_file_size(output_path) or 0

        # Determine watermark: trial mode adds watermark unless dev mode
        add_watermark = False
        if not is_dev_mode():
            from src.license.store import license_store
            lic_status = license_store.get_status()
            if lic_status["type"] == "trial":
                add_watermark = True
                license_store.consume_trial()

        # Save to works library
        work = works_repo.create({
            "name": output_name,
            "file_path": output_path,
            "thumbnail_path": thumb_path,
            "duration_seconds": duration,
            "aspect_ratio": body.get("aspect_ratio", "9:16"),
            "file_size_bytes": file_size,
            "is_trial_watermark": add_watermark,
            "project_config": {
                "script": script,
                "voice_id": body.get("voice_id", ""),
                "voice_speed": voice_params.get("speed", 1.0),
                "voice_volume": voice_params.get("volume", 1.0),
                "voice_emotion": voice_params.get("emotion", 0.5),
                "digital_human_id": body.get("digital_human_id", ""),
                "background_type": body.get("background", {}).get("type", "solid_color"),
                "background_value": body.get("background", {}).get("value", "#F5F5F5"),
                "aspect_ratio": body.get("aspect_ratio", "9:16"),
                "subtitle_enabled": body.get("subtitle", {}).get("enabled", True),
                "subtitle_config": None,
                "bgm_enabled": body.get("bgm", {}).get("enabled", False),
                "bgm_id": body.get("bgm", {}).get("bgm_id"),
                "bgm_custom_path": body.get("bgm", {}).get("custom_path"),
                "voice_volume_ratio": body.get("bgm", {}).get("voice_volume", 1.0),
                "bgm_volume_ratio": body.get("bgm", {}).get("bgm_volume", 0.5),
            },
        })

        work_id = work["id"] if work else "unknown"

        await emitter.emit("completed", 4, 1.0, "生成完成", result={
            "work_id": work_id,
            "file_path": output_path,
            "duration_seconds": duration,
        })
        job_manager.update_state(job_id, status="completed", progress=1.0)

    except asyncio.CancelledError:
        await emitter.emit("failed", 0, 0, "任务已取消", error={"code": "CANCELLED", "message": "任务已取消"})
        job_manager.update_state(job_id, status="cancelled")
    except _CancelledByUser:
        await emitter.emit("failed", 0, 0, "任务已取消", error={"code": "CANCELLED", "message": "任务已取消"})
        job_manager.update_state(job_id, status="cancelled")
    except Exception as e:
        await emitter.emit("failed", 0, 0, str(e), error={"code": "INTERNAL_ERROR", "message": str(e)})
        job_manager.update_state(job_id, status="failed")
    finally:
        await emitter.complete()
        _cancel_flags.pop(job_id, None)
        _pause_flags.pop(job_id, None)


class _CancelledByUser(Exception):
    pass


async def _check_cancel(job_id: str) -> None:
    if _cancel_flags.get(job_id):
        raise _CancelledByUser()


async def _wait_if_paused(job_id: str) -> None:
    event = _pause_flags.get(job_id)
    if event and not event.is_set():
        job_manager.update_state(job_id, status="paused")
        await event.wait()
        job_manager.update_state(job_id, status="running")


def _get_digital_human_video(dh_id: str) -> str:
    """Get digital human video path from database. Returns placeholder if not found."""
    from src.storage.database import get_connection
    conn = get_connection()
    row = conn.execute(
        "SELECT preview_video_path, adapted_video_path FROM digital_humans WHERE id = ?",
        (dh_id,),
    ).fetchone()
    if row:
        return row["adapted_video_path"] or row["preview_video_path"]
    return ""


# ─── Route handlers ──────────────────────────────────────────────

@router.post("/pipeline/single", status_code=202)
async def create_single_job(body: dict):
    script = body.get("script", "").strip()
    if not script or len(script) < 2:
        return {"success": False, "error": {"code": "INVALID_SCRIPT", "message": "文案不能为空且至少2个字符"}}

    # License check (skipped in dev mode)
    if not is_dev_mode():
        from src.license.store import license_store
        status = license_store.get_status()
        if status["type"] == "trial" and status.get("remaining_trial_count", 0) <= 0:
            return {"success": False, "error": {"code": "LICENSE_TRIAL_EXHAUSTED", "message": "试用次数已用完，请激活后继续使用"}}

    job_id = _new_job_id()
    emitter = job_manager.create_job(job_id, total_steps=4)
    _pause_flags[job_id] = asyncio.Event()
    _pause_flags[job_id].set()  # Not paused initially

    asyncio.create_task(_run_single_pipeline(job_id, body))

    return {"success": True, "data": {"job_id": job_id, "estimated_steps": 4}}


@router.get("/pipeline/progress/{job_id}")
async def get_progress(job_id: str):
    emitter = job_manager.get_emitter(job_id)
    if not emitter:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "Job not found"}}

    return EventSourceResponse(emitter.events())


@router.get("/jobs/{job_id}/state")
async def get_job_state(job_id: str):
    state = job_manager.get_state(job_id)
    if not state:
        return {"success": True, "data": {"job_id": job_id, "status": "not_found"}}
    return {"success": True, "data": state}


@router.post("/pipeline/pause/{job_id}")
async def pause_job(job_id: str):
    event = _pause_flags.get(job_id)
    if not event:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "Job not found"}}
    event.clear()
    return {"success": True, "data": {"status": "paused"}}


@router.post("/pipeline/resume/{job_id}")
async def resume_job(job_id: str):
    event = _pause_flags.get(job_id)
    if not event:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "Job not found"}}
    event.set()
    return {"success": True, "data": {"status": "running"}}


@router.post("/pipeline/cancel/{job_id}")
async def cancel_job(job_id: str):
    if job_id not in _cancel_flags and job_id not in _pause_flags:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "Job not found"}}
    _cancel_flags[job_id] = True
    # Unpause if paused so the task can check cancellation
    event = _pause_flags.get(job_id)
    if event:
        event.set()
    return {"success": True, "data": {"status": "cancelled"}}


@router.post("/pipeline/batch", status_code=202)
async def create_batch_job(body: dict):
    """Batch pipeline — implemented in Phase 4."""
    scripts = body.get("scripts", [])
    if not scripts:
        return {"success": False, "error": {"code": "INVALID_SCRIPT", "message": "批量文案不能为空"}}

    job_id = _new_job_id("batch")
    total = len(scripts)
    emitter = job_manager.create_job(job_id, total_steps=total * 4)
    _pause_flags[job_id] = asyncio.Event()
    _pause_flags[job_id].set()

    asyncio.create_task(_run_batch_pipeline(job_id, body))

    return {"success": True, "data": {"job_id": job_id, "total_count": total}}


async def _run_batch_pipeline(job_id: str, body: dict) -> None:
    """Execute batch pipeline: serial execution of each script."""
    emitter = job_manager.get_emitter(job_id)
    if not emitter:
        return

    scripts = body.get("scripts", [])
    shared_config = body.get("shared_config", {})
    output_settings = body.get("output_settings", {})
    settings = settings_store.read()
    total = len(scripts)
    succeeded = 0
    failed = 0
    failed_indices = []

    try:
        job_manager.update_state(job_id, status="running")

        for i, script_item in enumerate(scripts):
            await _check_cancel(job_id)
            await _wait_if_paused(job_id)

            await emitter.emit_batch("batch_item_start", item_index=i, total=total,
                                     message=f"正在生成第 {i+1} 条 / 共 {total} 条")

            try:
                single_body = {
                    **shared_config,
                    "script": script_item.get("content", ""),
                    "output_name": f"{output_settings.get('name_prefix', '视频')}_{i+1:03d}",
                }

                # TTS
                await emitter.emit_batch("batch_item_progress", item_index=i, step="tts", progress=0.3)
                voice_params = single_body.get("voice_params", {})
                tts_path = await asyncio.to_thread(
                    tts_engine.synthesize,
                    text=single_body["script"],
                    voice_id=single_body.get("voice_id", ""),
                    speed=voice_params.get("speed", 1.0),
                    volume=voice_params.get("volume", 1.0),
                    emotion=voice_params.get("emotion", 0.5),
                )

                # Resample
                resampled_path = tts_path.replace(".wav", "_16k.wav")
                await asyncio.to_thread(
                    video_synthesizer.resample_audio, tts_path, resampled_path, 16000
                )

                # Lipsync
                await emitter.emit_batch("batch_item_progress", item_index=i, step="lipsync", progress=0.6)
                dh_video = _get_digital_human_video(single_body.get("digital_human_id", ""))
                lipsync_path = await asyncio.to_thread(
                    lipsync_engine.process, dh_video, resampled_path
                )

                # Synthesis
                await emitter.emit_batch("batch_item_progress", item_index=i, step="synthesis", progress=0.9)
                batch_save_dir = settings.get("defaultVideoSavePath", "")
                if not batch_save_dir:
                    batch_save_dir = os.path.join(os.path.expanduser("~"), "Documents", "智影口播", "作品")
                os.makedirs(batch_save_dir, exist_ok=True)
                out_name = single_body["output_name"]
                out_path = os.path.join(batch_save_dir, f"{out_name}.mp4")
                await asyncio.to_thread(
                    video_synthesizer.synthesize,
                    lipsync_video_path=lipsync_path,
                    audio_path=tts_path,
                    output_path=out_path,
                    background=single_body.get("background"),
                    subtitle=single_body.get("subtitle"),
                    bgm=single_body.get("bgm"),
                    aspect_ratio=single_body.get("aspect_ratio", "9:16"),
                )

                # Thumbnail + save to works
                thumb_dir = os.path.join(batch_save_dir, ".thumbs")
                os.makedirs(thumb_dir, exist_ok=True)
                thumb_path = os.path.join(thumb_dir, f"{out_name}.jpg")
                await asyncio.to_thread(
                    video_synthesizer.extract_thumbnail, out_path, thumb_path
                )

                from src.utils.file_utils import get_video_duration, get_file_size
                duration = get_video_duration(out_path) or 0.0
                file_size = get_file_size(out_path) or 0

                work = works_repo.create({
                    "name": out_name,
                    "file_path": out_path,
                    "thumbnail_path": thumb_path,
                    "duration_seconds": duration,
                    "aspect_ratio": single_body.get("aspect_ratio", "9:16"),
                    "file_size_bytes": file_size,
                    "is_trial_watermark": False,
                    "project_config": {
                        "script": single_body["script"],
                        "voice_id": single_body.get("voice_id", ""),
                        "digital_human_id": single_body.get("digital_human_id", ""),
                        "aspect_ratio": single_body.get("aspect_ratio", "9:16"),
                    },
                })
                work_id = work["id"] if work else f"work_{uuid.uuid4().hex[:8]}"

                await emitter.emit_batch("batch_item_done", item_index=i, work_id=work_id)
                succeeded += 1

            except Exception as e:
                await emitter.emit_batch("batch_item_failed", item_index=i,
                                         error={"code": "INTERNAL_ERROR", "message": str(e)})
                failed += 1
                failed_indices.append(i)

        await emitter.emit_batch("batch_completed", total=total, succeeded=succeeded,
                                 failed=failed, failed_indices=failed_indices)
        job_manager.update_state(job_id, status="completed", progress=1.0)

    except (_CancelledByUser, asyncio.CancelledError):
        await emitter.emit_batch("batch_completed", total=total, succeeded=succeeded,
                                 failed=total - succeeded, failed_indices=failed_indices)
        job_manager.update_state(job_id, status="cancelled")
    except Exception as e:
        await emitter.emit_batch("batch_completed", total=total, succeeded=succeeded,
                                 failed=total - succeeded, failed_indices=failed_indices)
        job_manager.update_state(job_id, status="failed")
    finally:
        await emitter.complete()
        _cancel_flags.pop(job_id, None)
        _pause_flags.pop(job_id, None)
