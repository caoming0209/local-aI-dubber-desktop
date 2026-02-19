"""JSON settings store: read/write {userDataDir}/settings.json with merge updates."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_SETTINGS: dict[str, Any] = {
    "autoStartOnBoot": False,
    "defaultVideoSavePath": str(
        Path.home() / "Documents" / "智影口播" / "作品"
    ),
    "theme": "light",
    "language": "zh-CN",
    "modelStoragePath": str(
        Path.home() / "Documents" / "智影口播" / "models"
    ),
    "downloadSpeedLimitKBps": 0,
    "autoDownloadModels": True,
    "inferenceMode": "auto",
    "cpuUsageLimitPercent": 0,
    "autoClearCacheEnabled": False,
    "autoClearCycleDays": 7,
    "autoCheckUpdate": True,
    "updatedAt": datetime.now(timezone.utc).isoformat(),
}


class SettingsStore:
    def __init__(self, settings_path: str | None = None):
        if settings_path:
            self._path = settings_path
        else:
            user_data = os.environ.get("APPDATA", os.path.expanduser("~"))
            settings_dir = os.path.join(user_data, "ZhiYingKouBo")
            os.makedirs(settings_dir, exist_ok=True)
            self._path = os.path.join(settings_dir, "settings.json")

        self._ensure_defaults()

    def _ensure_defaults(self) -> None:
        """Create settings file with defaults if it doesn't exist."""
        if not os.path.exists(self._path):
            self._write(DEFAULT_SETTINGS.copy())
            # Ensure default directories exist
            for key in ("defaultVideoSavePath", "modelStoragePath"):
                path = DEFAULT_SETTINGS[key]
                os.makedirs(path, exist_ok=True)

    def _read_raw(self) -> dict[str, Any]:
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return DEFAULT_SETTINGS.copy()

    def _write(self, data: dict[str, Any]) -> None:
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def read(self) -> dict[str, Any]:
        """Read full settings, filling missing keys with defaults."""
        stored = self._read_raw()
        merged = {**DEFAULT_SETTINGS, **stored}
        return merged

    def update(self, partial: dict[str, Any]) -> dict[str, Any]:
        """Merge partial update into existing settings."""
        current = self.read()
        current.update(partial)
        current["updatedAt"] = datetime.now(timezone.utc).isoformat()
        self._write(current)
        return current


# Global singleton
settings_store = SettingsStore()
