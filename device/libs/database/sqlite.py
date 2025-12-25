from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import aiosqlite

from device.libs.schemas.ai import AIInferenceResponse
from device.libs.schemas.comms import MessageReceived


class DatabaseError(RuntimeError):
    pass


class AsyncSQLite:
    """
    Lightweight async SQLite wrapper for logging device data.
    """

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = str(db_path)
        self._conn: aiosqlite.Connection | None = None

    async def open(self) -> None:
        try:
            self._conn = await aiosqlite.connect(self._db_path)
            await self._conn.execute("PRAGMA journal_mode=WAL;")
            await self._initialize_schema()
        except Exception as exc:  # noqa: BLE001
            raise DatabaseError(str(exc)) from exc

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    async def _initialize_schema(self) -> None:
        assert self._conn is not None
        await self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                topic TEXT NOT NULL,
                payload TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS comms_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                transport TEXT NOT NULL,
                from_node TEXT,
                to_node TEXT,
                content TEXT NOT NULL,
                channel TEXT,
                rssi REAL,
                snr REAL,
                metadata TEXT
            );

            CREATE TABLE IF NOT EXISTS ai_inferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                request_id TEXT NOT NULL,
                model_id TEXT NOT NULL,
                inference_type TEXT NOT NULL,
                success INTEGER NOT NULL,
                results TEXT NOT NULL,
                error_message TEXT
            );

            CREATE TABLE IF NOT EXISTS user_preferences (
                key TEXT PRIMARY KEY NOT NULL,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
            );
            """
        )
        await self._conn.commit()
        # Initialize default preferences if table is empty
        await self._initialize_default_preferences()

    async def log_event(self, topic: str, payload: str) -> None:
        assert self._conn is not None
        await self._conn.execute(
            "INSERT INTO events (topic, payload) VALUES (?, ?)", (topic, payload)
        )
        await self._conn.commit()

    async def log_comms_message(self, msg: MessageReceived) -> None:
        assert self._conn is not None
        await self._conn.execute(
            """
            INSERT INTO comms_messages
            (transport, from_node, to_node, content, channel, rssi, snr, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                msg.transport.value,
                msg.from_node,
                msg.to_node,
                msg.content,
                msg.channel,
                msg.rssi,
                msg.snr,
                json.dumps(msg.model_dump(mode="json")),
            ),
        )
        await self._conn.commit()

    async def log_ai_inference(self, resp: AIInferenceResponse) -> None:
        assert self._conn is not None
        await self._conn.execute(
            """
            INSERT INTO ai_inferences
            (request_id, model_id, inference_type, success, results, error_message)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(resp.request_id),
                resp.model_id,
                resp.inference_type.value,
                1 if resp.success else 0,
                json.dumps([r.model_dump(mode="json") for r in resp.results]),
                resp.error_message,
            ),
        )
        await self._conn.commit()

    async def fetch_latest(self, table: str, limit: int = 50) -> list[dict[str, Any]]:
        """
        Fetch latest rows from a supported table.
        """
        assert self._conn is not None
        if table not in {"events", "comms_messages", "ai_inferences"}:
            raise DatabaseError(f"Unsupported table: {table}")
        cursor = await self._conn.execute(
            f"SELECT * FROM {table} ORDER BY id DESC LIMIT ?", (int(limit),)
        )
        assert cursor.description is not None
        cols = [c[0] for c in cursor.description]
        rows = await cursor.fetchall()
        await cursor.close()
        return [dict(zip(cols, row)) for row in rows]

    # --- User Preferences ---

    # Default preference values
    DEFAULT_PREFERENCES: dict[str, str] = {
        "units.temperature": "C",  # "C" or "F"
        "units.distance": "km",  # "km" or "mi"
        "units.weight": "kg",  # "kg" or "lb"
    }

    # Valid values for each preference key
    PREFERENCE_VALIDATORS: dict[str, set[str]] = {
        "units.temperature": {"C", "F"},
        "units.distance": {"km", "mi"},
        "units.weight": {"kg", "lb"},
    }

    async def _initialize_default_preferences(self) -> None:
        """Initialize default preferences if not already set."""
        assert self._conn is not None
        for key, value in self.DEFAULT_PREFERENCES.items():
            await self._conn.execute(
                """
                INSERT OR IGNORE INTO user_preferences (key, value)
                VALUES (?, ?)
                """,
                (key, value),
            )
        await self._conn.commit()

    async def get_preference(self, key: str) -> str | None:
        """Get a single preference value by key."""
        assert self._conn is not None
        cursor = await self._conn.execute(
            "SELECT value FROM user_preferences WHERE key = ?", (key,)
        )
        row = await cursor.fetchone()
        await cursor.close()
        return row[0] if row else None

    async def get_all_preferences(self) -> dict[str, str]:
        """Get all preference key-value pairs."""
        assert self._conn is not None
        cursor = await self._conn.execute("SELECT key, value FROM user_preferences")
        rows = await cursor.fetchall()
        await cursor.close()
        return {row[0]: row[1] for row in rows}

    async def set_preference(self, key: str, value: str) -> bool:
        """
        Set a preference value.

        Returns True if successful, False if validation fails.
        """
        assert self._conn is not None

        # Validate value if validator exists
        if key in self.PREFERENCE_VALIDATORS:
            if value not in self.PREFERENCE_VALIDATORS[key]:
                return False

        await self._conn.execute(
            """
            INSERT INTO user_preferences (key, value, updated_at)
            VALUES (?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'))
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
            """,
            (key, value),
        )
        await self._conn.commit()
        return True

    async def reset_preferences(self) -> None:
        """Reset all preferences to defaults."""
        assert self._conn is not None
        await self._conn.execute("DELETE FROM user_preferences")
        await self._initialize_default_preferences()
