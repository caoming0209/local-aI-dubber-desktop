"""Activation code validator: local format check + remote server verification."""

import re
from typing import Optional

import httpx

from src.license.fingerprint import get_fingerprint

# Compiled into binary by Nuitka — not configurable at runtime
ACTIVATION_SERVER = "https://activate.zhiying-koubo.com"
APP_VERSION = "1.0.0"
REQUEST_TIMEOUT = 10


def validate_format(code: str) -> bool:
    """Check activation code format: XXXX-XXXX-XXXX-XXXX (Base32 chars)."""
    pattern = r"^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$"
    return bool(re.match(pattern, code.upper()))


async def activate_remote(activation_code: str) -> dict:
    """Call activation server to verify code and bind device.

    Returns:
        {"success": True, "license": {...}} on success
        {"success": False, "error": {"code": "...", "message": "..."}} on failure
    """
    fingerprint = get_fingerprint()

    try:
        async with httpx.AsyncClient(verify=True, timeout=REQUEST_TIMEOUT) as client:
            resp = await client.post(
                f"{ACTIVATION_SERVER}/api/v1/activate",
                json={
                    "activation_code": activation_code,
                    "device_fingerprint": f"sha256:{fingerprint}",
                    "app_version": APP_VERSION,
                },
            )

            if resp.status_code == 200:
                return resp.json()
            else:
                return {
                    "success": False,
                    "error": {
                        "code": "LICENSE_INVALID_CODE",
                        "message": "激活码无效，请检查输入是否正确",
                    },
                }

    except httpx.TimeoutException:
        return {
            "success": False,
            "error": {
                "code": "LICENSE_NETWORK_ERROR",
                "message": "网络连接超时，请检查网络后重试",
            },
        }
    except httpx.ConnectError:
        return {
            "success": False,
            "error": {
                "code": "LICENSE_NETWORK_ERROR",
                "message": "无法连接到激活服务器，请检查网络连接",
            },
        }
    except Exception as e:
        return {
            "success": False,
            "error": {
                "code": "LICENSE_NETWORK_ERROR",
                "message": f"激活请求失败: {str(e)}",
            },
        }


async def unbind_remote(activation_code: str) -> dict:
    """Call activation server to unbind current device."""
    fingerprint = get_fingerprint()

    try:
        async with httpx.AsyncClient(verify=True, timeout=REQUEST_TIMEOUT) as client:
            resp = await client.post(
                f"{ACTIVATION_SERVER}/api/v1/unbind",
                json={
                    "activation_code": activation_code,
                    "device_fingerprint": f"sha256:{fingerprint}",
                },
            )
            if resp.status_code == 200:
                return resp.json()
            return {
                "success": False,
                "error": {
                    "code": "LICENSE_NETWORK_ERROR",
                    "message": "解绑请求失败",
                },
            }
    except Exception:
        return {
            "success": False,
            "error": {
                "code": "LICENSE_NETWORK_ERROR",
                "message": "解绑需要联网，请检查网络后重试",
            },
        }
