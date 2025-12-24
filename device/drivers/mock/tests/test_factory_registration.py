from __future__ import annotations

import device.drivers.mock as mockpkg  # noqa: F401 - triggers registration
from device.libs.hil.factory import DriverFactory


def test_factory_creates_mock_drivers() -> None:
    gps = DriverFactory.create_gps("mock", {"start_lat": 1.0, "start_lon": 2.0})
    radio = DriverFactory.create_radio("mock_lora", {"node_id": "!me"})
    sensor = DriverFactory.create_sensor("mock", {"sensor_id": "s1"})
    mod = DriverFactory.create_module_port("mock", {"num_ports": 1})
    power = DriverFactory.create_power("mock", {"initial_battery_percent": 90})

    assert gps is not None
    assert radio is not None
    assert sensor is not None
    assert mod is not None
    assert power is not None
