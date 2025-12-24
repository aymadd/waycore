from __future__ import annotations

import asyncio
from typing import Callable

import pytest
from device.libs.messaging.bus import MessageBus, MessageHandler
from device.libs.schemas.system import CommandType
from device.services.core_daemon.service import CoreDaemonService


class FakeBus(MessageBus):
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
        return lambda: self.handlers.pop(topic, None)


@pytest.mark.asyncio
async def test_core_daemon_service_publishes_state_and_handles_commands() -> None:
    bus = FakeBus()
    svc = CoreDaemonService(config={"publish_interval_seconds": 0.01}, bus=bus)
    await svc.start()
    await asyncio.sleep(0.03)
    # Service should have published some state
    assert any(t == "system/state/changed" for (t, _) in bus.published)
    # SOS command updates mode
    ok = await svc.handle_command(CommandType.sos_trigger, {})
    assert ok is True
    await asyncio.sleep(0.02)
    await svc.stop()
