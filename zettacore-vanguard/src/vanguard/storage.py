"""Small, parameterized SQLite repository for locally managed assets."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any


def default_database_path() -> Path:
    """Return an OS-appropriate per-user data path without writing to the source tree."""
    if os.name == "nt":
        root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return root / "ZettaCore" / "Vanguard" / "vanguard.sqlite3"
    if os.sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "ZettaCore" / "Vanguard" / "vanguard.sqlite3"
    root = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return root / "zettacore" / "vanguard" / "vanguard.sqlite3"


class AssetStore:
    """CRUD operations for assets; no network scanning is performed."""

    def __init__(self, database_path: str | Path | None = None) -> None:
        self.path = Path(database_path) if database_path else default_database_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS assets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    asset_type TEXT NOT NULL,
                    environment TEXT NOT NULL DEFAULT 'unknown',
                    owner TEXT NOT NULL DEFAULT '',
                    authorization_note TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def add_asset(
        self,
        name: str,
        asset_type: str,
        environment: str = "unknown",
        owner: str = "",
        authorization_note: str = "",
    ) -> int:
        clean_name = name.strip()
        clean_type = asset_type.strip()
        if not clean_name:
            raise ValueError("Asset name is required.")
        if not clean_type:
            raise ValueError("Asset type is required.")
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO assets (name, asset_type, environment, owner, authorization_note)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    clean_name,
                    clean_type,
                    environment.strip() or "unknown",
                    owner.strip(),
                    authorization_note.strip(),
                ),
            )
            return int(cursor.lastrowid)

    def list_assets(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, name, asset_type, environment, owner, authorization_note, created_at
                FROM assets
                ORDER BY id DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def delete_asset(self, asset_id: int) -> bool:
        with self._connect() as connection:
            cursor = connection.execute("DELETE FROM assets WHERE id = ?", (asset_id,))
            return cursor.rowcount > 0
