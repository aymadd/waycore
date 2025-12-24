from __future__ import annotations

import asyncio
from typing import Callable

import pytest
from device.libs.messaging.bus import MessageBus, MessageHandler
from device.libs.schemas.comms import SendMessageRequest, Transport
from device.services.comms_bridge.service import CommsBridgeService


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
async def test_comms_bridge_publishes_status_and_handles_send() -> None:
    bus = CaptureBus()
    svc = CommsBridgeService(config={"status_interval_seconds": 0.05}, bus=bus)
    await svc.start()
    await asyncio.sleep(0.12)
    # status messages published
    assert any(t == "comms/status/changed" for (t, _) in bus.published)
    # trigger send
    req = SendMessageRequest(source="ui", transport=Transport.lora, to_node=None, content="hello")
    handler = bus.handlers.get("comms/message/send")
    assert handler is not None
    handler("comms/message/send", req.model_dump_json().encode("utf-8"))
    await asyncio.sleep(0.05)
    await svc.stop()
