"""Works library CRUD routes."""

from fastapi import APIRouter

from src.storage.works_repo import works_repo

router = APIRouter(tags=["works"])


@router.get("/works")
async def list_works(
    search: str = "",
    aspect_ratio: str = "",
    date_range: str = "",
    date_from: str = "",
    date_to: str = "",
    sort: str = "created_at_desc",
    page: int = 1,
    page_size: int = 12,
):
    data = works_repo.list(
        search=search,
        aspect_ratio=aspect_ratio,
        date_range=date_range,
        date_from=date_from,
        date_to=date_to,
        sort=sort,
        page=page,
        page_size=page_size,
    )
    return {"success": True, "data": data}


@router.get("/works/{work_id}")
async def get_work(work_id: str):
    work = works_repo.get_by_id(work_id)
    if not work:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "作品不存在"}}
    return {"success": True, "data": work}


@router.patch("/works/{work_id}")
async def rename_work(work_id: str, body: dict):
    name = body.get("name", "").strip()
    if not name:
        return {"success": False, "error": {"code": "INVALID_SCRIPT", "message": "名称不能为空"}}
    work = works_repo.rename(work_id, name)
    if not work:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "作品不存在"}}
    return {"success": True, "data": work}


@router.delete("/works/{work_id}")
async def delete_work(work_id: str):
    ok = works_repo.delete(work_id)
    if not ok:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "作品不存在"}}
    return {"success": True, "data": {"deleted": True}}


@router.delete("/works")
async def batch_delete_works(body: dict):
    ids = body.get("ids", [])
    count = works_repo.batch_delete(ids)
    return {"success": True, "data": {"deleted_count": count}}


@router.delete("/works/all")
async def clear_all_works(body: dict):
    if not body.get("confirm"):
        return {"success": False, "error": {"code": "INTERNAL_ERROR", "message": "需要 confirm: true"}}
    count = works_repo.clear_all()
    return {"success": True, "data": {"deleted_count": count}}
