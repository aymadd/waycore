from __future__ import annotations

import pytest
from device.drivers.mock.sensor import MockSensor


@pytest.mark.asyncio
async def test_mock_sensor_initialize_read_and_calibrate() -> None:
    s = MockSensor({"sensor_id": "temp1", "sensor_type": "temperature", "initial_value": 21.0})
    assert s.is_ready is False
    ok = await s.initialize()
    assert ok is True and s.is_ready is True
    r1 = await s.read()
    assert r1 is not None
    ok2 = await s.calibrate(22.0)
    assert ok2 is True
    r2 = await s.read()
    assert r2 is not None
    assert abs(float(r2.value) - 22.0) < 1.0
