"""License and activation routes."""

from fastapi import APIRouter

from src.license.store import license_store
from src.license.validator import validate_format, activate_remote, unbind_remote
from src.utils.dev_mode import is_dev_mode

router = APIRouter(tags=["license"])


@router.get("/license/status")
async def get_license_status():
    if is_dev_mode():
        return {"success": True, "data": {
            "type": "dev",
            "remaining_trial_count": 999,
            "dev_mode": True,
        }}
    data = license_store.get_status()
    return {"success": True, "data": data}


@router.post("/license/activate")
async def activate(body: dict):
    code = body.get("activation_code", "").strip().upper()

    if not code:
        return {"success": False, "error": {"code": "LICENSE_INVALID_CODE", "message": "请输入激活码"}}

    if not validate_format(code):
        return {"success": False, "error": {"code": "LICENSE_INVALID_CODE", "message": "激活码格式不正确，应为 XXXX-XXXX-XXXX-XXXX"}}

    # Check if already activated
    status = license_store.get_status()
    if status["type"] == "activated":
        return {"success": False, "error": {"code": "LICENSE_ALREADY_ACTIVATED", "message": "当前设备已激活"}}

    # Call remote activation server
    result = await activate_remote(code)

    if not result.get("success"):
        error = result.get("error", {})
        return {"success": False, "error": error}

    # Store activation locally
    license_data = result.get("license", {})
    license_store.activate(code, license_data)

    # Build response
    masked = code[:9] + "****-****" if len(code) >= 9 else code
    return {
        "success": True,
        "data": {
            "type": "activated",
            "activated_at": license_data.get("activated_at"),
            "activation_code_masked": masked,
            "device_count": license_data.get("device_count", 1),
            "max_device_count": license_data.get("max_device_count", 2),
        },
    }


@router.post("/license/unbind")
async def unbind():
    status = license_store.get_status()
    if status["type"] != "activated":
        return {"success": False, "error": {"code": "INTERNAL_ERROR", "message": "当前设备未激活"}}

    # Read stored activation code
    state = license_store.read()
    code = state.get("activationCode", "")
    if not code:
        return {"success": False, "error": {"code": "INTERNAL_ERROR", "message": "未找到激活码信息"}}

    # Call remote unbind
    result = await unbind_remote(code)
    if not result.get("success"):
        error = result.get("error", {})
        return {"success": False, "error": error}

    # Reset local state
    license_store.unbind()

    return {
        "success": True,
        "data": {
            "type": "trial",
            "message": "当前设备已解绑，激活码名额已释放，可在新设备激活",
        },
    }


@router.post("/license/consume-trial")
async def consume_trial(body: dict):
    count = body.get("count", 1)
    result = None
    for _ in range(count):
        result = license_store.consume_trial()
    return {"success": True, "data": result}
