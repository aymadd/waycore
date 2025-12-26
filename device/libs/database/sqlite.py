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

            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL DEFAULT '',
                content TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
            );

            CREATE TABLE IF NOT EXISTS sensors (
                id TEXT PRIMARY KEY NOT NULL,
                type TEXT NOT NULL,
                name TEXT NOT NULL,
                driver TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'unknown',
                last_value TEXT,
                last_reading_at TEXT,
                config TEXT,
                discovered_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
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

    # --- Mesh Messages ---

    async def save_mesh_message(
        self,
        message_id: str,
        from_node: str,
        to_node: str | None,
        text: str,
        channel: int = 0,
        rssi: float | None = None,
        snr: float | None = None,
    ) -> None:
        """Save a mesh network message."""
        assert self._conn is not None
        metadata = json.dumps({"message_id": message_id, "channel": channel})
        await self._conn.execute(
            """
            INSERT INTO comms_messages
            (transport, from_node, to_node, content, channel, rssi, snr, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "mesh",  # transport type
                from_node,
                to_node,
                text,
                str(channel),
                rssi,
                snr,
                metadata,
            ),
        )
        await self._conn.commit()

    async def get_mesh_messages(
        self,
        limit: int = 100,
        node_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get mesh messages from database."""
        assert self._conn is not None

        if node_id:
            cursor = await self._conn.execute(
                """
                SELECT * FROM comms_messages
                WHERE transport = 'mesh' AND (from_node = ? OR to_node = ?)
                ORDER BY id DESC LIMIT ?
                """,
                (node_id, node_id, limit),
            )
        else:
            cursor = await self._conn.execute(
                """
                SELECT * FROM comms_messages
                WHERE transport = 'mesh'
                ORDER BY id DESC LIMIT ?
                """,
                (limit,),
            )

        assert cursor.description is not None
        cols = [c[0] for c in cursor.description]
        rows = await cursor.fetchall()
        await cursor.close()
        return [dict(zip(cols, row)) for row in rows]

    async def delete_mesh_messages(self) -> int:
        """Delete all mesh messages (for factory reset)."""
        assert self._conn is not None
        cursor = await self._conn.execute("DELETE FROM comms_messages WHERE transport = 'mesh'")
        await self._conn.commit()
        return int(cursor.rowcount) if cursor.rowcount else 0

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
        "units.temperature": "F",  # "C" or "F" - default Fahrenheit
        "units.distance": "mi",  # "km" or "mi" - default miles
        "units.weight": "lb",  # "kg" or "lb" - default pounds
        "units.pressure": "hPa",  # "hPa", "inHg", or "mmHg" - default hectopascals
        "units.time_format": "24h",  # "12h" or "24h" - default 24-hour
    }

    # Valid values for each preference key
    PREFERENCE_VALIDATORS: dict[str, set[str]] = {
        "units.temperature": {"C", "F"},
        "units.distance": {"km", "mi"},
        "units.weight": {"kg", "lb"},
        "units.pressure": {"hPa", "inHg", "mmHg"},
        "units.time_format": {"12h", "24h"},
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

    # --- Notes ---

    async def create_note(self, title: str = "", content: str = "") -> int:
        """Create a new note. Returns the note ID."""
        assert self._conn is not None
        cursor = await self._conn.execute(
            """
            INSERT INTO notes (title, content) VALUES (?, ?)
            """,
            (title, content),
        )
        await self._conn.commit()
        return cursor.lastrowid or 0

    async def get_note(self, note_id: int) -> dict[str, Any] | None:
        """Get a single note by ID."""
        assert self._conn is not None
        cursor = await self._conn.execute(
            "SELECT id, title, content, created_at, updated_at FROM notes WHERE id = ?",
            (note_id,),
        )
        row = await cursor.fetchone()
        await cursor.close()
        if row:
            return {
                "id": row[0],
                "title": row[1],
                "content": row[2],
                "created_at": row[3],
                "updated_at": row[4],
            }
        return None

    async def get_all_notes(self) -> list[dict[str, Any]]:
        """Get all notes, ordered by most recently updated."""
        assert self._conn is not None
        cursor = await self._conn.execute(
            """
            SELECT id, title, content, created_at, updated_at
            FROM notes ORDER BY updated_at DESC
            """
        )
        rows = await cursor.fetchall()
        await cursor.close()
        return [
            {
                "id": row[0],
                "title": row[1],
                "content": row[2],
                "created_at": row[3],
                "updated_at": row[4],
            }
            for row in rows
        ]

    async def update_note(self, note_id: int, title: str, content: str) -> bool:
        """Update a note. Returns True if the note existed."""
        assert self._conn is not None
        cursor = await self._conn.execute(
            """
            UPDATE notes SET title = ?, content = ?,
                updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now')
            WHERE id = ?
            """,
            (title, content, note_id),
        )
        await self._conn.commit()
        return bool(cursor.rowcount > 0)

    async def delete_note(self, note_id: int) -> bool:
        """Delete a note. Returns True if the note existed."""
        assert self._conn is not None
        cursor = await self._conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        await self._conn.commit()
        return bool(cursor.rowcount > 0)

    async def delete_all_notes(self) -> int:
        """Delete all notes. Returns number of deleted notes."""
        assert self._conn is not None
        cursor = await self._conn.execute("DELETE FROM notes")
        await self._conn.commit()
        return int(cursor.rowcount)

    # --- Sensors Registry ---

    async def register_sensor(
        self,
        sensor_id: str,
        sensor_type: str,
        name: str,
        driver: str,
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Register a new sensor or update existing one."""
        assert self._conn is not None
        config_json = json.dumps(config) if config else None
        await self._conn.execute(
            """
            INSERT INTO sensors (id, type, name, driver, status, config)
            VALUES (?, ?, ?, ?, 'online', ?)
            ON CONFLICT(id) DO UPDATE SET
                type = excluded.type,
                name = excluded.name,
                driver = excluded.driver,
                config = excluded.config,
                status = 'online',
                updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now')
            """,
            (sensor_id, sensor_type, name, driver, config_json),
        )
        await self._conn.commit()
        return await self.get_sensor(sensor_id) or {}

    async def get_sensor(self, sensor_id: str) -> dict[str, Any] | None:
        """Get a sensor by ID."""
        assert self._conn is not None
        cursor = await self._conn.execute(
            """
            SELECT id, type, name, driver, status, last_value,
                   last_reading_at, config, discovered_at, updated_at
            FROM sensors WHERE id = ?
            """,
            (sensor_id,),
        )
        row = await cursor.fetchone()
        await cursor.close()
        if row:
            return {
                "id": row[0],
                "type": row[1],
                "name": row[2],
                "driver": row[3],
                "status": row[4],
                "last_value": json.loads(row[5]) if row[5] else None,
                "last_reading_at": row[6],
                "config": json.loads(row[7]) if row[7] else None,
                "discovered_at": row[8],
                "updated_at": row[9],
            }
        return None

    async def get_all_sensors(self) -> list[dict[str, Any]]:
        """Get all registered sensors."""
        assert self._conn is not None
        cursor = await self._conn.execute(
            """
            SELECT id, type, name, driver, status, last_value,
                   last_reading_at, config, discovered_at, updated_at
            FROM sensors ORDER BY type, name
            """
        )
        rows = await cursor.fetchall()
        await cursor.close()
        return [
            {
                "id": row[0],
                "type": row[1],
                "name": row[2],
                "driver": row[3],
                "status": row[4],
                "last_value": json.loads(row[5]) if row[5] else None,
                "last_reading_at": row[6],
                "config": json.loads(row[7]) if row[7] else None,
                "discovered_at": row[8],
                "updated_at": row[9],
            }
            for row in rows
        ]

    async def get_sensors_by_type(self, sensor_type: str) -> list[dict[str, Any]]:
        """Get all sensors of a specific type."""
        assert self._conn is not None
        cursor = await self._conn.execute(
            """
            SELECT id, type, name, driver, status, last_value,
                   last_reading_at, config, discovered_at, updated_at
            FROM sensors WHERE type = ? ORDER BY name
            """,
            (sensor_type,),
        )
        rows = await cursor.fetchall()
        await cursor.close()
        return [
            {
                "id": row[0],
                "type": row[1],
                "name": row[2],
                "driver": row[3],
                "status": row[4],
                "last_value": json.loads(row[5]) if row[5] else None,
                "last_reading_at": row[6],
                "config": json.loads(row[7]) if row[7] else None,
                "discovered_at": row[8],
                "updated_at": row[9],
            }
            for row in rows
        ]

    async def update_sensor_reading(
        self, sensor_id: str, value: dict[str, Any], status: str = "online"
    ) -> bool:
        """Update a sensor's last reading."""
        assert self._conn is not None
        cursor = await self._conn.execute(
            """
            UPDATE sensors SET
                last_value = ?,
                last_reading_at = strftime('%Y-%m-%dT%H:%M:%fZ','now'),
                status = ?,
                updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now')
            WHERE id = ?
            """,
            (json.dumps(value), status, sensor_id),
        )
        await self._conn.commit()
        return bool(cursor.rowcount > 0)

    async def update_sensor_status(self, sensor_id: str, status: str) -> bool:
        """Update a sensor's status (online, offline, error, calibrating)."""
        assert self._conn is not None
        cursor = await self._conn.execute(
            """
            UPDATE sensors SET status = ?, updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now')
            WHERE id = ?
            """,
            (status, sensor_id),
        )
        await self._conn.commit()
        return bool(cursor.rowcount > 0)

    async def unregister_sensor(self, sensor_id: str) -> bool:
        """Remove a sensor from the registry."""
        assert self._conn is not None
        cursor = await self._conn.execute("DELETE FROM sensors WHERE id = ?", (sensor_id,))
        await self._conn.commit()
        return bool(cursor.rowcount > 0)

    async def clear_all_sensors(self) -> int:
        """Remove all sensors from the registry."""
        assert self._conn is not None
        cursor = await self._conn.execute("DELETE FROM sensors")
        await self._conn.commit()
        return int(cursor.rowcount)
