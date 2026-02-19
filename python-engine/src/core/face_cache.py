"""Face detection result cache for digital human videos.

Caches face bounding boxes per video to avoid redundant detection
when the same digital human is used across multiple generations.
"""

import hashlib
import json
import os
from typing import Optional


class FaceCache:
    def __init__(self):
        self._cache_dir: Optional[str] = None

    def _get_cache_dir(self) -> str:
        """Get or create cache directory."""
        if self._cache_dir and os.path.isdir(self._cache_dir):
            return self._cache_dir
        from src.storage.settings_store import settings_store
        settings = settings_store.read()
        base = settings.get("defaultVideoSavePath", "")
        if not base:
            base = os.path.join(
                os.path.expanduser("~"), "Documents", "智影口播", "作品"
            )
        self._cache_dir = os.path.join(base, ".face_cache")
        os.makedirs(self._cache_dir, exist_ok=True)
        return self._cache_dir

    def _video_key(self, video_path: str) -> str:
        """Generate cache key from video path + modification time."""
        try:
            mtime = os.path.getmtime(video_path)
        except OSError:
            mtime = 0
        raw = f"{os.path.abspath(video_path)}:{mtime}"
        return hashlib.md5(raw.encode()).hexdigest()

    def get(self, video_path: str) -> Optional[list]:
        """Get cached face detection results for a video.

        Returns list of [y1, y2, x1, x2] bounding boxes per frame, or None.
        """
        key = self._video_key(video_path)
        cache_path = os.path.join(self._get_cache_dir(), f"{key}.json")
        if not os.path.exists(cache_path):
            return None
        try:
            with open(cache_path, "r") as f:
                data = json.load(f)
            return data.get("boxes")
        except (json.JSONDecodeError, OSError, KeyError):
            return None

    def put(self, video_path: str, boxes: list) -> None:
        """Cache face detection results for a video."""
        key = self._video_key(video_path)
        cache_path = os.path.join(self._get_cache_dir(), f"{key}.json")
        try:
            with open(cache_path, "w") as f:
                json.dump({
                    "video_path": video_path,
                    "frame_count": len(boxes),
                    "boxes": boxes,
                }, f)
        except OSError:
            pass

    def clear(self) -> int:
        """Clear all cached face detection results. Returns count of removed files."""
        cache_dir = self._get_cache_dir()
        count = 0
        for f in os.listdir(cache_dir):
            if f.endswith(".json"):
                try:
                    os.remove(os.path.join(cache_dir, f))
                    count += 1
                except OSError:
                    pass
        return count


face_cache = FaceCache()
