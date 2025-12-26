from __future__ import annotations

import asyncio
import json
from typing import Any, Callable

from device.libs.common.base_service import BaseService
from device.libs.database import AIDatabase, GeneralDatabase
from device.libs.messaging.bus import MessageBus
from device.libs.schemas.ai import AIInferenceResponse


class DataLoggerService(BaseService):
    """
    Service for logging and persisting application data.

    Uses separate databases for different domains:
    - GeneralDatabase: preferences, notes, sensors, events
    - AIDatabase: inference logs
    """

    def __init__(self, config: dict[str, Any], bus: MessageBus | None = None) -> None:
        super().__init__(config, bus)
        db_dir = str(config.get("database_dir", "data"))

        # Initialize domain-specific databases
        self._general_db = GeneralDatabase(f"{db_dir}/general.sqlite3")
        self._ai_db = AIDatabase(f"{db_dir}/ai.sqlite3")

        self._healthy = False
        self._idle_sleep_s = float(config.get("idle_sleep_seconds", 0.1))
        self._unsubs: list[Callable[[], None]] = []

    async def _setup(self) -> None:
        await self._general_db.open()
        await self._ai_db.open()
        self._healthy = True
        if self.bus:
            self._unsubs.append(self.bus.subscribe("ai/inference/response", self._on_ai))
            self._unsubs.append(self.bus.subscribe("system/state/changed", self._on_generic))

    async def _run(self) -> None:
        while not self.should_stop():
            await asyncio.sleep(self._idle_sleep_s)

    async def _cleanup(self) -> None:
        for u in self._unsubs:
            try:
                u()
            except Exception:
                pass
        self._unsubs.clear()
        await self._general_db.close()
        await self._ai_db.close()
        self._healthy = False

    def is_healthy(self) -> bool:
        return self._healthy

    async def latest_ai(self, n: int = 50) -> list[dict[str, Any]]:
        return await self._ai_db.get_latest_inferences(n)

    async def latest_events(self, n: int = 50) -> list[dict[str, Any]]:
        return await self._general_db.get_latest_events(n)

    # --- Preferences ---

    async def get_all_preferences(self) -> dict[str, str]:
        """Get all user preferences."""
        return await self._general_db.get_all_preferences()

    async def get_preference(self, key: str) -> str | None:
        """Get a single preference value."""
        return await self._general_db.get_preference(key)

    async def set_preference(self, key: str, value: str) -> bool:
        """Set a preference value. Returns False if validation fails."""
        return await self._general_db.set_preference(key, value)

    async def reset_preferences(self) -> None:
        """Reset all preferences to defaults."""
        await self._general_db.reset_preferences()

    # --- Notes ---

    async def get_all_notes(self) -> list[dict[str, Any]]:
        """Get all notes, ordered by most recently updated."""
        return await self._general_db.get_all_notes()

    async def get_note(self, note_id: int) -> dict[str, Any] | None:
        """Get a single note by ID."""
        return await self._general_db.get_note(note_id)

    async def create_note(self, title: str = "", content: str = "") -> int:
        """Create a new note. Returns the note ID."""
        return await self._general_db.create_note(title, content)

    async def update_note(self, note_id: int, title: str, content: str) -> bool:
        """Update a note. Returns True if found and updated."""
        return await self._general_db.update_note(note_id, title, content)

    async def delete_note(self, note_id: int) -> bool:
        """Delete a note. Returns True if found and deleted."""
        return await self._general_db.delete_note(note_id)

    async def delete_all_notes(self) -> int:
        """Delete all notes (for factory reset). Returns count."""
        return await self._general_db.delete_all_notes()

    # --- Factory Reset ---

    async def factory_reset(self) -> dict[str, int]:
        """
        Clear all user data from general and AI databases.

        Returns counts of deleted items.
        """
        notes_deleted = await self._general_db.delete_all_notes()
        events_deleted = await self._general_db.delete_all_events()
        sensors_deleted = await self._general_db.delete_all_sensors()
        ai_deleted = await self._ai_db.delete_all_inferences()
        await self._general_db.reset_preferences()

        return {
            "notes": notes_deleted,
            "events": events_deleted,
            "sensors": sensors_deleted,
            "ai_inferences": ai_deleted,
        }

    # --- Sensors ---

    async def get_all_sensors(self) -> list[dict[str, Any]]:
        """Get all registered sensors."""
        return await self._general_db.get_all_sensors()

    async def get_sensor(self, sensor_id: str) -> dict[str, Any] | None:
        """Get a sensor by ID."""
        return await self._general_db.get_sensor(sensor_id)

    # Handlers

    def _on_ai(self, topic: str, payload: bytes) -> None:
        try:
            resp = AIInferenceResponse.model_validate_json(payload.decode("utf-8"))
        except Exception:
            return
        asyncio.create_task(self._ai_db.log_inference(resp))

    def _on_generic(self, topic: str, payload: bytes) -> None:
        try:
            s = payload.decode("utf-8")
            json.loads(s)  # validate it's json
        except Exception:
            return
        asyncio.create_task(self._general_db.log_event(topic, s))
