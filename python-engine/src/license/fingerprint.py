"""Hardware fingerprint generation for Windows.

Combines CPU ID, motherboard UUID, and primary disk serial number
into a SHA-256 hash for device identification.
"""

import hashlib
import subprocess
from typing import Optional


def _wmic_query(wmic_class: str, field: str) -> Optional[str]:
    """Query WMI via wmic command."""
    try:
        result = subprocess.run(
            ["wmic", wmic_class, "get", field, "/value"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                if "=" in line:
                    value = line.split("=", 1)[1].strip()
                    if value:
                        return value
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass
    return None


def get_cpu_id() -> str:
    return _wmic_query("cpu", "ProcessorId") or "UNKNOWN"


def get_motherboard_uuid() -> str:
    return _wmic_query("csproduct", "UUID") or "UNKNOWN"


def get_disk_serial() -> str:
    return _wmic_query("diskdrive", "SerialNumber") or "UNKNOWN"


def get_fingerprint() -> str:
    """Generate device fingerprint: SHA-256 of CPU|Motherboard|Disk."""
    cpu_id = get_cpu_id()
    mb_uuid = get_motherboard_uuid()
    disk_sn = get_disk_serial()
    raw = f"{cpu_id}|{mb_uuid}|{disk_sn}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]
