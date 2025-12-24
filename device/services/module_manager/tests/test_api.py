from __future__ import annotations

import pytest
from device.libs.messaging.bus import MessageBus
from device.services.module_manager.api import create_app
from device.services.module_manager.service import ModuleManagerService
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
async def test_module_manager_api_health_and_modules() -> None:
    svc = ModuleManagerService(config={"driver_name": "mock", "publish_interval_seconds": 0.05})
    svc.bus = NoBus()
    await svc.start()
    app = create_app(svc)
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/health")
        assert resp.status_code == 200
        resp2 = await ac.get("/api/modules")
        assert resp2.status_code == 200
    await svc.stop()
