"""SQLite database connection and migration framework.

Uses PRAGMA user_version for schema versioning.
Scans migrations/ directory and executes scripts in order.
"""

import os
import re
import sqlite3
from pathlib import Path
from typing import Optional

_db_path: Optional[str] = None
_connection: Optional[sqlite3.Connection] = None

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def get_db_path() -> str:
    global _db_path
    if _db_path:
        return _db_path
    user_data = os.environ.get("APPDATA", os.path.expanduser("~"))
    db_dir = os.path.join(user_data, "local-aI-dubber-desktop")
    os.makedirs(db_dir, exist_ok=True)
    _db_path = os.path.join(db_dir, "dubber.db")
    return _db_path


def get_connection() -> sqlite3.Connection:
    global _connection
    if _connection is None:
        _connection = sqlite3.connect(get_db_path(), check_same_thread=False)
        _connection.row_factory = sqlite3.Row
        _connection.execute("PRAGMA journal_mode=WAL")
        _connection.execute("PRAGMA foreign_keys=ON")
    return _connection


def get_user_version(conn: sqlite3.Connection) -> int:
    return conn.execute("PRAGMA user_version").fetchone()[0]


def set_user_version(conn: sqlite3.Connection, version: int) -> None:
    conn.execute(f"PRAGMA user_version = {version}")


def get_migration_files() -> list[tuple[int, Path]]:
    """Scan migrations directory and return sorted (version, path) tuples."""
    if not MIGRATIONS_DIR.exists():
        return []

    pattern = re.compile(r"^V(\d{3})__.*\.sql$")
    migrations = []
    for f in MIGRATIONS_DIR.iterdir():
        match = pattern.match(f.name)
        if match:
            version = int(match.group(1))
            migrations.append((version, f))
    return sorted(migrations, key=lambda x: x[0])


def run_migrations(conn: sqlite3.Connection) -> None:
    """Execute pending migration scripts."""
    current_version = get_user_version(conn)
    migrations = get_migration_files()

    for version, path in migrations:
        if version <= current_version:
            continue

        sql = path.read_text(encoding="utf-8")
        try:
            conn.executescript(sql)
            set_user_version(conn, version)
            conn.commit()
            print(f"[database] Applied migration V{version:03d}: {path.name}")
        except Exception as e:
            conn.rollback()
            raise RuntimeError(
                f"Migration V{version:03d} failed: {path.name}\n{e}"
            ) from e


async def init_db() -> None:
    """Initialize database connection and run migrations."""
    conn = get_connection()
    run_migrations(conn)
    print(f"[database] Ready at {get_db_path()}")


async def close_db() -> None:
    """Close database connection."""
    global _connection
    if _connection:
        _connection.close()
        _connection = None
