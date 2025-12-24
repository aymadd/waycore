from __future__ import annotations

import pytest
from device.drivers.mock.module_port import MockModulePort


@pytest.mark.asyncio
async def test_mock_module_port_scan_identify_enable() -> None:
    mp = MockModulePort({"num_ports": 2, "auto_connect_modules": True})
    ports = await mp.scan_ports()
    assert ports == [0, 1]
    info = await mp.identify_module(0)
    assert info is not None and info.module_id == "mod-0"
    ok = await mp.enable_module(0)
    assert ok is True
    power = await mp.get_power_draw(0)
    assert power == 150
    ok2 = await mp.write_data(0, b"ping")
    assert ok2 is True
    await mp.disable_module(0)
    power2 = await mp.get_power_draw(0)
    assert power2 == 0
