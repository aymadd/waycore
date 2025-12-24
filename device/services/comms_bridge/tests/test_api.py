from __future__ import annotations

import pytest
from device.libs.messaging.bus import MessageBus
from device.libs.schemas.comms import Transport
from device.services.comms_bridge.api import create_app
from device.services.comms_bridge.service import CommsBridgeService
from httpx import AsyncClient


class NoBus(MessageBus):
    async def connect(self, broker_url: str) -> None: ...
    async def disconnect(self) -> None: ...
    async def publish(
        self, topic: str, payload: bytes | str, qos: int = 0, retain: bool = False
    ) -> None: ...
    def subscribe(self, topic: str, handler, qos: int = 0):  # type: ignore[no-untyped-def]
        return lambda: None


@pytest.mark.asyncio
async def test_comms_api_health_radios_send() -> None:
    svc = CommsBridgeService(config={"status_interval_seconds": 0.05}, bus=NoBus())
    await svc.start()
    app = create_app(svc)
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.get("/health")
        assert r.status_code == 200
        r2 = await ac.get("/api/radios")
        assert r2.status_code == 200
        r3 = await ac.post(
            "/api/send",
            json={
                "source": "ui",
                "version": "1.0.0",
                "transport": Transport.lora.value,
                "content": "hi",
            },
        )
        assert r3.status_code == 200
    await svc.stop()
