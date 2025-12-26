"""General database for system settings, notes, and misc app data."""

from __future__ import annotations

from typing import Any

from .base import BaseAsyncDatabase

# Default user preferences
DEFAULT_PREFERENCES: dict[str, str] = {
    "units.temperature": "F",
    "units.distance": "mi",
    "units.weight": "lb",
    "units.pressure": "hPa",
    "units.time_format": "24h",
}


class GeneralDatabase(BaseAsyncDatabase):
    """
    Database for general system and app data.

    Tables:
    - user_preferences: User settings and preferences
    - notes: User notes
    - sensors: Sensor registry
    - events: System event log
    """

    def _get_schema(self) -> str:
        return """
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

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                topic TEXT NOT NULL,
                payload TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts);
            CREATE INDEX IF NOT EXISTS idx_events_topic ON events(topic);
        """

    async def _initialize_schema(self) -> None:
        """Initialize schema and default preferences."""
        await super()._initialize_schema()
        await self._initialize_default_preferences()

    async def _initialize_default_preferences(self) -> None:
        """Initialize default preferences if not set."""
        for key, value in DEFAULT_PREFERENCES.items():
            existing = await self.get_preference(key)
            if existing is None:
                await self.set_preference(key, value)

    # --- Preferences ---

    async def get_preference(self, key: str) -> str | None:
        """Get a single preference value."""
        result = await self.fetchone(
            "SELECT value FROM user_preferences WHERE key = ?",
            (key,),
        )
        return result["value"] if result else None

    async def get_all_preferences(self) -> dict[str, str]:
        """Get all user preferences."""
        rows = await self.fetchall("SELECT key, value FROM user_preferences")
        return {row["key"]: row["value"] for row in rows}

    async def set_preference(self, key: str, value: str) -> bool:
        """Set a preference value."""
        await self.execute(
            """
            INSERT INTO user_preferences (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now')
            """,
            (key, value),
        )
        await self.commit()
        return True

    async def reset_preferences(self) -> None:
        """Reset all preferences to defaults."""
        await self.execute("DELETE FROM user_preferences")
        await self.commit()
        await self._initialize_default_preferences()

    # --- Notes ---

    async def get_all_notes(self) -> list[dict[str, Any]]:
        """Get all notes, ordered by most recently updated."""
        return await self.fetchall("SELECT * FROM notes ORDER BY updated_at DESC")

    async def get_note(self, note_id: int) -> dict[str, Any] | None:
        """Get a single note by ID."""
        return await self.fetchone("SELECT * FROM notes WHERE id = ?", (note_id,))

    async def create_note(self, title: str = "", content: str = "") -> int:
        """Create a new note. Returns the note ID."""
        cursor = await self.execute(
            "INSERT INTO notes (title, content) VALUES (?, ?)",
            (title, content),
        )
        await self.commit()
        assert cursor.lastrowid is not None
        return int(cursor.lastrowid)

    async def update_note(self, note_id: int, title: str, content: str) -> bool:
        """Update a note. Returns True if found and updated."""
        cursor = await self.execute(
            """
            UPDATE notes SET
                title = ?,
                content = ?,
                updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now')
            WHERE id = ?
            """,
            (title, content, note_id),
        )
        await self.commit()
        return bool(cursor.rowcount)

    async def delete_note(self, note_id: int) -> bool:
        """Delete a note. Returns True if found and deleted."""
        cursor = await self.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        await self.commit()
        return bool(cursor.rowcount)

    async def delete_all_notes(self) -> int:
        """Delete all notes. Returns count deleted."""
        cursor = await self.execute("DELETE FROM notes")
        await self.commit()
        return int(cursor.rowcount) if cursor.rowcount else 0

    # --- Sensors ---

    async def get_all_sensors(self) -> list[dict[str, Any]]:
        """Get all registered sensors."""
        return await self.fetchall("SELECT * FROM sensors ORDER BY type, name")

    async def get_sensor(self, sensor_id: str) -> dict[str, Any] | None:
        """Get a sensor by ID."""
        return await self.fetchone("SELECT * FROM sensors WHERE id = ?", (sensor_id,))

    async def get_sensors_by_type(self, sensor_type: str) -> list[dict[str, Any]]:
        """Get sensors of a specific type."""
        return await self.fetchall(
            "SELECT * FROM sensors WHERE type = ? ORDER BY name",
            (sensor_type,),
        )

    async def upsert_sensor(
        self,
        sensor_id: str,
        sensor_type: str,
        name: str,
        driver: str,
        status: str = "unknown",
        last_value: str | None = None,
        config: str | None = None,
    ) -> dict[str, Any]:
        """Create or update a sensor."""
        await self.execute(
            """
            INSERT INTO sensors (id, type, name, driver, status, last_value, config)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                type = excluded.type,
                name = excluded.name,
                driver = excluded.driver,
                status = excluded.status,
                last_value = COALESCE(excluded.last_value, sensors.last_value),
                last_reading_at = CASE
                    WHEN excluded.last_value IS NOT NULL
                    THEN strftime('%Y-%m-%dT%H:%M:%fZ','now')
                    ELSE sensors.last_reading_at
                END,
                config = COALESCE(excluded.config, sensors.config),
                updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now')
            """,
            (sensor_id, sensor_type, name, driver, status, last_value, config),
        )
        await self.commit()
        result = await self.get_sensor(sensor_id)
        assert result is not None
        return result

    async def delete_all_sensors(self) -> int:
        """Delete all sensors. Returns count deleted."""
        cursor = await self.execute("DELETE FROM sensors")
        await self.commit()
        return int(cursor.rowcount) if cursor.rowcount else 0

    # --- Events ---

    async def log_event(self, topic: str, payload: str) -> None:
        """Log a system event."""
        await self.execute(
            "INSERT INTO events (topic, payload) VALUES (?, ?)",
            (topic, payload),
        )
        await self.commit()

    async def get_latest_events(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get most recent events."""
        return await self.fetchall(
            "SELECT * FROM events ORDER BY id DESC LIMIT ?",
            (limit,),
        )

    async def get_events_by_topic(self, topic: str, limit: int = 50) -> list[dict[str, Any]]:
        """Get events for a specific topic."""
        return await self.fetchall(
            "SELECT * FROM events WHERE topic = ? ORDER BY id DESC LIMIT ?",
            (topic, limit),
        )

    async def delete_all_events(self) -> int:
        """Delete all events. Returns count deleted."""
        cursor = await self.execute("DELETE FROM events")
        await self.commit()
        return int(cursor.rowcount) if cursor.rowcount else 0
