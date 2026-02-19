"""Digital humans data access layer."""

import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from src.storage.database import get_connection


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class DigitalHumansRepo:
    def list(self, search: str = "", source: str = "", category: str = "") -> list[dict]:
        conn = get_connection()
        conditions = []
        params = []

        if search:
            conditions.append("name LIKE ?")
            params.append(f"%{search}%")
        if source:
            conditions.append("source = ?")
            params.append(source)
        if category:
            conditions.append("category = ?")
            params.append(category)

        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        rows = conn.execute(
            f"SELECT * FROM digital_humans {where} ORDER BY sort_order ASC, created_at DESC",
            params,
        ).fetchall()
        return [dict(r) for r in rows]

    def get_by_id(self, dh_id: str) -> Optional[dict]:
        conn = get_connection()
        row = conn.execute("SELECT * FROM digital_humans WHERE id = ?", (dh_id,)).fetchone()
        return dict(row) if row else None

    def create(self, data: dict) -> dict:
        conn = get_connection()
        dh_id = data.get("id", str(uuid.uuid4()))
        conn.execute(
            """INSERT INTO digital_humans
               (id, name, category, source, thumbnail_path, preview_video_path,
                adapted_video_path, adaptation_status, is_favorited, created_at, sort_order)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                dh_id, data["name"], data.get("category", "other"),
                data.get("source", "custom"), data.get("thumbnail_path", ""),
                data.get("preview_video_path", ""), data.get("adapted_video_path"),
                data.get("adaptation_status", "pending"),
                int(data.get("is_favorited", False)), _now_iso(),
                data.get("sort_order", 0),
            ),
        )
        conn.commit()
        return self.get_by_id(dh_id)  # type: ignore

    def update(self, dh_id: str, data: dict) -> Optional[dict]:
        conn = get_connection()
        fields = []
        params = []
        for key in ("name", "category"):
            if key in data:
                fields.append(f"{key} = ?")
                params.append(data[key])
        if not fields:
            return self.get_by_id(dh_id)
        params.append(dh_id)
        conn.execute(f"UPDATE digital_humans SET {', '.join(fields)} WHERE id = ?", params)
        conn.commit()
        return self.get_by_id(dh_id)

    def toggle_favorite(self, dh_id: str) -> Optional[dict]:
        conn = get_connection()
        row = self.get_by_id(dh_id)
        if not row:
            return None
        new_fav = 0 if row["is_favorited"] else 1
        fav_at = _now_iso() if new_fav else None
        conn.execute(
            "UPDATE digital_humans SET is_favorited = ?, favorited_at = ? WHERE id = ?",
            (new_fav, fav_at, dh_id),
        )
        conn.commit()
        return self.get_by_id(dh_id)

    def update_adaptation(self, dh_id: str, status: str, adapted_path: str = "", error: str = "") -> None:
        conn = get_connection()
        conn.execute(
            "UPDATE digital_humans SET adaptation_status = ?, adapted_video_path = ?, adaptation_error = ? WHERE id = ?",
            (status, adapted_path or None, error or None, dh_id),
        )
        conn.commit()

    def delete(self, dh_id: str) -> bool:
        conn = get_connection()
        row = self.get_by_id(dh_id)
        if not row:
            return False
        if row["source"] == "official":
            return False  # Cannot delete official

        # Delete associated files
        for key in ("adapted_video_path", "thumbnail_path", "preview_video_path"):
            path = row.get(key)
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

        conn.execute("DELETE FROM digital_humans WHERE id = ?", (dh_id,))
        conn.commit()
        return True


digital_humans_repo = DigitalHumansRepo()
