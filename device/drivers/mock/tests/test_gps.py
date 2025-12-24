from __future__ import annotations

import asyncio

import pytest
from device.drivers.mock.gps import MockGPS


@pytest.mark.asyncio
async def test_mock_gps_fix_and_callbacks() -> None:
    gps = MockGPS({"fix_time_seconds": 0, "update_rate_hz": 50})
    events: list = []
    gps.subscribe_position(lambda fix: events.append(fix))
    await gps.start()
    ok = await gps.wait_for_fix(1.0)
    assert ok is True
    pos = await gps.get_position()
    assert pos is not None and pos.satellites >= 4
    await asyncio.sleep(0.05)
    await gps.stop()
    assert len(events) > 0
