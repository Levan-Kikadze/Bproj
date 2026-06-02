"""SQLite-backed persistence for saved Streamlit dashboards."""

from __future__ import annotations

import gzip
import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
DEFAULT_RUNTIME_DIR = Path(__file__).resolve().parents[1] / "runtime"
DEFAULT_DB_PATH = DEFAULT_RUNTIME_DIR / "saved_dashboards.db"


@dataclass(frozen=True)
class SavedDashboardSummary:
    """Lightweight metadata for populating dashboard pickers."""

    name: str
    source_type: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class SavedDashboardRecord:
    """Full persisted dashboard payload."""

    name: str
    source_type: str
    raw_file_name: str | None
    raw_csv_bytes: bytes
    ui_state: dict[str, Any]
    schema_version: int
    created_at: str
    updated_at: str


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _normalize_name(name: str) -> str:
    normalized = name.strip()
    if not normalized:
        raise ValueError("Dashboard name cannot be empty.")
    if len(normalized) > 120:
        raise ValueError("Dashboard name must be 120 characters or fewer.")
    if any(char in normalized for char in "\r\n\t\x00"):
        raise ValueError("Dashboard name cannot contain control characters.")
    return normalized


def _json_default(value: Any) -> Any:
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return sorted(value)
    raise TypeError(f"Unsupported value in dashboard state: {type(value)!r}")


def _serialize_ui_state(ui_state: dict[str, Any]) -> str:
    return json.dumps(ui_state, ensure_ascii=False, sort_keys=True, default=_json_default, separators=(",", ":"))


def _deserialize_ui_state(ui_state_json: str) -> dict[str, Any]:
    loaded = json.loads(ui_state_json)
    if not isinstance(loaded, dict):
        raise ValueError("Stored dashboard state is malformed.")
    return loaded


class DashboardStore:
    """Persist and retrieve saved dashboards from a local SQLite database."""

    def __init__(self, db_path: Path | str | None = None) -> None:
        self.db_path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS dashboards (
                    name TEXT PRIMARY KEY,
                    source_type TEXT NOT NULL,
                    raw_file_name TEXT,
                    raw_csv_gz BLOB NOT NULL,
                    ui_state_json TEXT NOT NULL,
                    schema_version INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def save_dashboard(
        self,
        *,
        name: str,
        source_type: str,
        raw_csv_bytes: bytes,
        ui_state: dict[str, Any],
        raw_file_name: str | None = None,
    ) -> SavedDashboardRecord:
        """Insert or update a dashboard snapshot by name."""
        normalized_name = _normalize_name(name)
        if not raw_csv_bytes:
            raise ValueError("Dashboard snapshots require CSV bytes.")

        now = _now_iso()
        compressed_csv = gzip.compress(raw_csv_bytes)
        serialized_state = _serialize_ui_state(ui_state)

        with self._connect() as connection:
            existing = connection.execute(
                "SELECT created_at FROM dashboards WHERE name = ?",
                (normalized_name,),
            ).fetchone()
            created_at = str(existing["created_at"]) if existing else now
            connection.execute(
                """
                INSERT INTO dashboards (
                    name,
                    source_type,
                    raw_file_name,
                    raw_csv_gz,
                    ui_state_json,
                    schema_version,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    source_type = excluded.source_type,
                    raw_file_name = excluded.raw_file_name,
                    raw_csv_gz = excluded.raw_csv_gz,
                    ui_state_json = excluded.ui_state_json,
                    schema_version = excluded.schema_version,
                    updated_at = excluded.updated_at
                """,
                (
                    normalized_name,
                    source_type,
                    raw_file_name,
                    compressed_csv,
                    serialized_state,
                    SCHEMA_VERSION,
                    created_at,
                    now,
                ),
            )

        return self.load_dashboard(normalized_name)

    def list_dashboards(self) -> list[SavedDashboardSummary]:
        """Return all saved dashboards ordered by most recently updated first."""
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT name, source_type, created_at, updated_at
                FROM dashboards
                ORDER BY updated_at DESC, name ASC
                """
            ).fetchall()

        return [
            SavedDashboardSummary(
                name=str(row["name"]),
                source_type=str(row["source_type"]),
                created_at=str(row["created_at"]),
                updated_at=str(row["updated_at"]),
            )
            for row in rows
        ]

    def load_dashboard(self, name: str) -> SavedDashboardRecord:
        """Load a full dashboard snapshot by name."""
        normalized_name = _normalize_name(name)
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT name, source_type, raw_file_name, raw_csv_gz, ui_state_json, schema_version, created_at, updated_at
                FROM dashboards
                WHERE name = ?
                """,
                (normalized_name,),
            ).fetchone()

        if row is None:
            raise KeyError(f"Dashboard not found: {normalized_name}")

        compressed_csv = bytes(row["raw_csv_gz"])
        return SavedDashboardRecord(
            name=str(row["name"]),
            source_type=str(row["source_type"]),
            raw_file_name=str(row["raw_file_name"]) if row["raw_file_name"] is not None else None,
            raw_csv_bytes=gzip.decompress(compressed_csv),
            ui_state=_deserialize_ui_state(str(row["ui_state_json"])),
            schema_version=int(row["schema_version"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )

    def delete_dashboard(self, name: str) -> bool:
        """Delete a saved dashboard. Returns True when a record was removed."""
        normalized_name = _normalize_name(name)
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM dashboards WHERE name = ?",
                (normalized_name,),
            )
            return cursor.rowcount > 0

