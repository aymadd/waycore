from __future__ import annotations

import asyncio

import pytest
from device.drivers.mock.power import MockPowerController


@pytest.mark.asyncio
async def test_mock_power_battery_info_and_charging() -> None:
    p = MockPowerController({"initial_battery_percent": 50, "capacity_mah": 4000})
    info = await p.get_battery_info()
    assert 0 <= info.percent <= 100
    await p.enable_charging(True)
    await asyncio.sleep(0.6)
    info2 = await p.get_battery_info()
    assert info2.percent >= info.percent
    await p.enable_charging(False)
    ok = await p.set_power_mode("low_power")
    assert ok is True
    budget = await p.get_power_budget()
    assert budget.total_capacity_mah == 4000
