from __future__ import annotations

import asyncio
from typing import Any

import pytest
from device.libs.common.base_service import BaseService


class DummyService(BaseService):
    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        self.started = False
        self.cleaned = False
        self.looped = 0

    async def _setup(self) -> None:
        self.started = True

    async def _run(self) -> None:
        # Run small loop until stop requested
        while not self.should_stop():
            self.looped += 1
            await asyncio.sleep(0.01)

    async def _cleanup(self) -> None:
        self.cleaned = True


@pytest.mark.asyncio
async def test_base_service_start_stop() -> None:
    svc = DummyService(config={})
    await svc.start()
    await asyncio.sleep(0.03)
    await svc.stop()
    assert svc.started is True
    assert svc.cleaned is True
    assert svc.looped > 0
