from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Callable

from device.libs.common.base_service import BaseService
from device.libs.database import AsyncSQLite
from device.libs.messaging.bus import MessageBus
from device.libs.schemas.ai import AIInferenceResponse
from device.libs.schemas.comms import MessageReceived


class DataLoggerService(BaseService):
    def __init__(self, config: dict[str, Any], bus: MessageBus | None = None) -> None:
        super().__init__(config, bus)
        db_path = str(config.get("database_path", "data/logger.sqlite3"))
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._db = AsyncSQLite(db_path)
        self._healthy = False
        self._idle_sleep_s = float(config.get("idle_sleep_seconds", 0.1))
        self._unsubs: list[Callable[[], None]] = []

    async def _setup(self) -> None:
        await self._db.open()
        self._healthy = True
        if self.bus:
            self._unsubs.append(self.bus.subscribe("comms/message/received", self._on_comms))
            self._unsubs.append(self.bus.subscribe("ai/inference/response", self._on_ai))
            # generic event tap (optional): store anything published here
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
        await self._db.close()
        self._healthy = False

    def is_healthy(self) -> bool:
        return self._healthy

    async def latest_ai(self, n: int = 50) -> list[dict[str, Any]]:
        return await self._db.fetch_latest("ai_inferences", n)

    async def latest_comms(self, n: int = 50) -> list[dict[str, Any]]:
        return await self._db.fetch_latest("comms_messages", n)

    async def latest_events(self, n: int = 50) -> list[dict[str, Any]]:
        return await self._db.fetch_latest("events", n)

    # --- Preferences ---

    async def get_all_preferences(self) -> dict[str, str]:
        """Get all user preferences."""
        return await self._db.get_all_preferences()

    async def get_preference(self, key: str) -> str | None:
        """Get a single preference value."""
        return await self._db.get_preference(key)

    async def set_preference(self, key: str, value: str) -> bool:
        """Set a preference value. Returns False if validation fails."""
        return await self._db.set_preference(key, value)

    async def reset_preferences(self) -> None:
        """Reset all preferences to defaults."""
        await self._db.reset_preferences()

    # Handlers
    def _on_comms(self, topic: str, payload: bytes) -> None:
        try:
            msg = MessageReceived.model_validate_json(payload.decode("utf-8"))
        except Exception:
            return
        asyncio.create_task(self._db.log_comms_message(msg))

    def _on_ai(self, topic: str, payload: bytes) -> None:
        try:
            resp = AIInferenceResponse.model_validate_json(payload.decode("utf-8"))
        except Exception:
            return
        asyncio.create_task(self._db.log_ai_inference(resp))

    def _on_generic(self, topic: str, payload: bytes) -> None:
        try:
            # Store raw event
            s = payload.decode("utf-8")
            json.loads(s)  # validate it's json
        except Exception:
            return
        asyncio.create_task(self._db.log_event(topic, s))
