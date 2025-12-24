from __future__ import annotations

import asyncio
from typing import Callable

import pytest
from device.libs.messaging.bus import MessageBus, MessageHandler
from device.services.module_manager.service import ModuleManagerService


class CaptureBus(MessageBus):
    def __init__(self) -> None:
        self.published: list[tuple[str, bytes]] = []
        self.handlers: dict[str, MessageHandler] = {}

    async def connect(self, broker_url: str) -> None: ...
    async def disconnect(self) -> None: ...
    async def publish(
        self, topic: str, payload: bytes | str, qos: int = 0, retain: bool = False
    ) -> None:
        if isinstance(payload, str):
            payload = payload.encode("utf-8")
        self.published.append((topic, payload))

    def subscribe(self, topic: str, handler: MessageHandler, qos: int = 0) -> Callable[[], None]:
        self.handlers[topic] = handler
        return lambda: None


@pytest.mark.asyncio
async def test_module_manager_discovers_and_publishes() -> None:
    bus = CaptureBus()
    svc = ModuleManagerService(config={"driver_name": "mock", "publish_interval_seconds": 0.05})
    svc.bus = bus
    await svc.start()
    await asyncio.sleep(0.15)
    mods = svc.list_modules()
    assert len(mods) >= 1
    # should have published discovered/status topics
    assert any("/discovered" in t for (t, _) in bus.published)
    assert any("/status" in t for (t, _) in bus.published)
    await svc.stop()
