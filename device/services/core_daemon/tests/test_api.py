from __future__ import annotations

import pytest
from device.libs.messaging.bus import MessageBus
from device.libs.schemas.system import CommandType
from device.services.core_daemon.api import create_app
from device.services.core_daemon.service import CoreDaemonService
from httpx import AsyncClient


class NoopBus(MessageBus):
    async def connect(self, broker_url: str) -> None: ...
    async def disconnect(self) -> None: ...
    async def publish(
        self, topic: str, payload: bytes | str, qos: int = 0, retain: bool = False
    ) -> None: ...
    def subscribe(self, topic: str, handler, qos: int = 0):  # type: ignore[no-untyped-def]
        return lambda: None


@pytest.mark.asyncio
async def test_api_health_status_and_command() -> None:
    svc = CoreDaemonService(config={"publish_interval_seconds": 0.05}, bus=NoopBus())
    await svc.start()
    app = create_app(svc)
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # health
        resp = await ac.get("/health")
        assert resp.status_code == 200
        # status
        resp2 = await ac.get("/api/status")
        assert resp2.status_code == 200
        body = resp2.json()
        assert "mode" in body
        # command
        cmd = {"command": CommandType.sos_trigger.value, "parameters": {}}
        resp3 = await ac.post("/api/command", json={"source": "ui", "version": "1.0.0", **cmd})
        assert resp3.status_code == 200
    await svc.stop()
