"""Works repository: data access layer for the works and project_configs tables."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from src.storage.database import get_connection


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _uuid() -> str:
    return str(uuid.uuid4())


class WorksRepo:
    def list(
        self,
        search: str = "",
        aspect_ratio: str = "",
        date_range: str = "",
        date_from: str = "",
        date_to: str = "",
        sort: str = "created_at_desc",
        page: int = 1,
        page_size: int = 12,
    ) -> dict:
        conn = get_connection()
        conditions = []
        params = []

        if search:
            conditions.append("(w.name LIKE ? OR w.created_at LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%"])

        if aspect_ratio:
            conditions.append("w.aspect_ratio = ?")
            params.append(aspect_ratio)

        if date_from:
            conditions.append("w.created_at >= ?")
            params.append(date_from)

        if date_to:
            conditions.append("w.created_at <= ?")
            params.append(date_to)

        where = "WHERE " + " AND ".join(conditions) if conditions else ""

        order_map = {
            "created_at_desc": "w.created_at DESC",
            "created_at_asc": "w.created_at ASC",
            "duration": "w.duration_seconds DESC",
        }
        order = order_map.get(sort, "w.created_at DESC")

        # Count total
        count_sql = f"SELECT COUNT(*) FROM works w {where}"
        total = conn.execute(count_sql, params).fetchone()[0]

        # Fetch page
        offset = (page - 1) * page_size
        query = f"""
            SELECT w.* FROM works w
            {where}
            ORDER BY {order}
            LIMIT ? OFFSET ?
        """
        rows = conn.execute(query, params + [page_size, offset]).fetchall()

        items = [dict(row) for row in rows]
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    def get_by_id(self, work_id: str) -> Optional[dict]:
        conn = get_connection()
        row = conn.execute("SELECT * FROM works WHERE id = ?", (work_id,)).fetchone()
        if not row:
            return None
        work = dict(row)

        # Attach project_config if exists
        if work.get("project_config_id"):
            config_row = conn.execute(
                "SELECT * FROM project_configs WHERE id = ?",
                (work["project_config_id"],),
            ).fetchone()
            if config_row:
                work["project_config"] = dict(config_row)

        return work

    def create(self, data: dict) -> dict:
        conn = get_connection()
        work_id = data.get("id", _uuid())
        now = _now_iso()

        # Save project config snapshot first
        config_id = None
        if "project_config" in data:
            config = data["project_config"]
            config_id = config.get("id", _uuid())
            conn.execute(
                """INSERT INTO project_configs
                   (id, script, voice_id, voice_speed, voice_volume, voice_emotion,
                    digital_human_id, background_type, background_value, aspect_ratio,
                    subtitle_enabled, subtitle_config, bgm_enabled, bgm_id,
                    bgm_custom_path, voice_volume_ratio, bgm_volume_ratio, created_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    config_id, config["script"], config["voice_id"],
                    config.get("voice_speed", 1.0), config.get("voice_volume", 1.0),
                    config.get("voice_emotion", 0.5), config["digital_human_id"],
                    config["background_type"], config["background_value"],
                    config["aspect_ratio"], int(config.get("subtitle_enabled", True)),
                    config.get("subtitle_config"), int(config.get("bgm_enabled", False)),
                    config.get("bgm_id"), config.get("bgm_custom_path"),
                    config.get("voice_volume_ratio", 1.0),
                    config.get("bgm_volume_ratio", 0.5), now,
                ),
            )

        conn.execute(
            """INSERT INTO works
               (id, name, file_path, thumbnail_path, duration_seconds, resolution,
                aspect_ratio, file_size_bytes, created_at, project_config_id, is_trial_watermark)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                work_id, data["name"], data["file_path"], data["thumbnail_path"],
                data["duration_seconds"], data.get("resolution", "1080P"),
                data["aspect_ratio"], data.get("file_size_bytes"),
                now, config_id, int(data.get("is_trial_watermark", False)),
            ),
        )
        conn.commit()
        return self.get_by_id(work_id)  # type: ignore

    def rename(self, work_id: str, name: str) -> Optional[dict]:
        conn = get_connection()
        conn.execute("UPDATE works SET name = ? WHERE id = ?", (name, work_id))
        conn.commit()
        return self.get_by_id(work_id)

    def delete(self, work_id: str) -> bool:
        conn = get_connection()
        work = self.get_by_id(work_id)
        if not work:
            return False

        # Delete associated files
        import os
        for key in ("file_path", "thumbnail_path"):
            path = work.get(key)
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

        # Delete config snapshot
        if work.get("project_config_id"):
            conn.execute("DELETE FROM project_configs WHERE id = ?", (work["project_config_id"],))

        conn.execute("DELETE FROM works WHERE id = ?", (work_id,))
        conn.commit()
        return True

    def batch_delete(self, ids: list[str]) -> int:
        count = 0
        for work_id in ids:
            if self.delete(work_id):
                count += 1
        return count

    def clear_all(self) -> int:
        conn = get_connection()
        # Get all works for file cleanup
        rows = conn.execute("SELECT id FROM works").fetchall()
        count = len(rows)
        for row in rows:
            self.delete(row["id"])
        return count


works_repo = WorksRepo()
