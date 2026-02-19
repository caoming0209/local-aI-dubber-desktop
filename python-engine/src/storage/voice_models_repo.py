"""Voice models data access layer."""

import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from src.storage.database import get_connection


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class VoiceModelsRepo:
    def list(self, search: str = "", category: str = "", download_status: str = "") -> list[dict]:
        conn = get_connection()
        conditions = []
        params = []

        if search:
            conditions.append("name LIKE ?")
            params.append(f"%{search}%")
        if category:
            conditions.append("category = ?")
            params.append(category)
        if download_status:
            conditions.append("download_status = ?")
            params.append(download_status)

        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        rows = conn.execute(
            f"SELECT * FROM voice_models {where} ORDER BY sort_order ASC, name ASC",
            params,
        ).fetchall()
        return [dict(r) for r in rows]

    def get_by_id(self, voice_id: str) -> Optional[dict]:
        conn = get_connection()
        row = conn.execute("SELECT * FROM voice_models WHERE id = ?", (voice_id,)).fetchone()
        return dict(row) if row else None

    def toggle_favorite(self, voice_id: str) -> Optional[dict]:
        conn = get_connection()
        row = self.get_by_id(voice_id)
        if not row:
            return None
        new_fav = 0 if row["is_favorited"] else 1
        fav_at = _now_iso() if new_fav else None
        conn.execute(
            "UPDATE voice_models SET is_favorited = ?, favorited_at = ? WHERE id = ?",
            (new_fav, fav_at, voice_id),
        )
        conn.commit()
        return self.get_by_id(voice_id)

    def update_download_status(
        self, voice_id: str, status: str, progress: float = 0, model_path: str = ""
    ) -> None:
        conn = get_connection()
        if model_path:
            conn.execute(
                "UPDATE voice_models SET download_status = ?, download_progress = ?, model_path = ? WHERE id = ?",
                (status, progress, model_path, voice_id),
            )
        else:
            conn.execute(
                "UPDATE voice_models SET download_status = ?, download_progress = ? WHERE id = ?",
                (status, progress, voice_id),
            )
        conn.commit()

    def delete_model(self, voice_id: str) -> bool:
        """Delete model files but keep DB record."""
        row = self.get_by_id(voice_id)
        if not row or not row.get("model_path"):
            return False

        model_path = row["model_path"]
        if os.path.isdir(model_path):
            import shutil
            shutil.rmtree(model_path, ignore_errors=True)
        elif os.path.isfile(model_path):
            try:
                os.remove(model_path)
            except OSError:
                pass

        self.update_download_status(voice_id, "not_downloaded", 0, "")
        return True


voice_models_repo = VoiceModelsRepo()
