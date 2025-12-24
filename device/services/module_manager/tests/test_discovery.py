from __future__ import annotations

import asyncio

import pytest
from device.drivers.mock.module_port import MockModulePort
from device.services.module_manager.discovery import DiscoveryManager


@pytest.mark.asyncio
async def test_discovery_detects_modules() -> None:
    port = MockModulePort({"num_ports": 1, "auto_connect_modules": True})
    d = DiscoveryManager(port, scan_interval_seconds=0.05)
    await d.start()
    await asyncio.sleep(0.12)
    mods = d.list_modules()
    await d.stop()
    assert len(mods) >= 1
    assert mods[0].enabled is True
