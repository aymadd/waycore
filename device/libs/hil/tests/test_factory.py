from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest
from device.libs.hil.factory import DriverFactory
from device.libs.hil.interfaces.gps import IGPS
from device.libs.hil.interfaces.module_port import IModulePort
from device.libs.hil.interfaces.power import BatteryInfo, IPowerController, PowerBudget
from device.libs.hil.interfaces.radio import IRadio, RadioStatus, RadioType
from device.libs.hil.interfaces.sensor import ISensor


# Minimal dummy implementations to test factory wiring
class DummyGPS(IGPS):
    def __init__(self, _config: Mapping[str, Any]) -> None:
        self._running = False
        self._has_fix = False

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def has_fix(self) -> bool:
        return self._has_fix

    async def start(self) -> None:
        self._running = True

    async def stop(self) -> None:
        self._running = False

    async def get_position(self):
        return None

    def subscribe_position(self, callback):  # type: ignore[no-untyped-def]
        return None

    async def wait_for_fix(self, timeout_seconds: float = 60.0) -> bool:
        return False


class DummyRadio(IRadio):
    def __init__(self, _config: Mapping[str, Any]) -> None:
        self._enabled = False

    @property
    def radio_type(self) -> RadioType:
        return RadioType.lora

    async def start(self) -> None: ...

    async def stop(self) -> None: ...

    async def send_message(self, content: bytes, to_node, channel, want_ack):  # type: ignore[no-untyped-def]
        return True

    def subscribe_messages(self, callback):  # type: ignore[no-untyped-def]
        return None

    async def get_status(self) -> RadioStatus:
        return RadioStatus(enabled=self._enabled, connected=False)

    async def set_power(self, enabled: bool) -> None:
        self._enabled = enabled


class DummySensor(ISensor):
    def __init__(self, config: Mapping[str, Any]) -> None:
        self._ready = False

    async def initialize(self) -> bool:
        self._ready = True
        return True

    async def read(self):
        return None

    async def calibrate(self, reference):
        return True

    @property
    def sensor_id(self) -> str:
        return "dummy"

    @property
    def sensor_type(self) -> str:
        return "test"

    @property
    def is_ready(self) -> bool:
        return self._ready


class DummyModulePort(IModulePort):
    def __init__(self, config: Mapping[str, Any]) -> None: ...

    async def scan_ports(self):
        return []

    async def identify_module(self, port: int):
        return None

    async def enable_module(self, port: int) -> bool:
        return True

    async def disable_module(self, port: int) -> bool:
        return True

    async def read_data(self, port: int):
        return None

    async def write_data(self, port: int, data: bytes) -> bool:
        return True

    async def get_power_draw(self, port: int):
        return 0


class DummyPower(IPowerController):
    def __init__(self, config: Mapping[str, Any]) -> None: ...

    async def get_battery_info(self) -> BatteryInfo:
        return BatteryInfo(voltage=3.9, percent=80, current_ma=-100, charging=False)

    async def get_power_budget(self) -> PowerBudget:
        return PowerBudget(
            total_capacity_mah=5000,
            available_capacity_mah=4000,
            current_draw_ma=200,
            estimated_runtime_min=120,
        )

    async def set_power_mode(self, mode: str) -> bool:
        return True

    async def enable_charging(self, enabled: bool) -> None:
        return None

    def subscribe_battery(self, callback):  # type: ignore[no-untyped-def]
        return None


def test_factory_registration_and_creation() -> None:
    DriverFactory.register_gps("dummy", lambda cfg: DummyGPS(cfg))
    DriverFactory.register_radio("dummy", lambda cfg: DummyRadio(cfg))
    DriverFactory.register_sensor("dummy", lambda cfg: DummySensor(cfg))
    DriverFactory.register_module_port("dummy", lambda cfg: DummyModulePort(cfg))
    DriverFactory.register_power("dummy", lambda cfg: DummyPower(cfg))

    gps = DriverFactory.create_gps("dummy", {})
    radio = DriverFactory.create_radio("dummy", {})
    sensor = DriverFactory.create_sensor("dummy", {})
    modport = DriverFactory.create_module_port("dummy", {})
    power = DriverFactory.create_power("dummy", {})

    assert isinstance(gps, DummyGPS)
    assert radio.radio_type == RadioType.lora
    assert sensor.sensor_id == "dummy"
    assert modport is not None
    assert power is not None


@pytest.mark.parametrize("domain", ["gps", "radio", "sensor", "module_port", "power"])
def test_factory_unknown_driver_raises(domain: str) -> None:
    with pytest.raises(KeyError):
        if domain == "gps":
            DriverFactory.create_gps("unknown")
        elif domain == "radio":
            DriverFactory.create_radio("unknown")
        elif domain == "sensor":
            DriverFactory.create_sensor("unknown")
        elif domain == "module_port":
            DriverFactory.create_module_port("unknown")
        elif domain == "power":
            DriverFactory.create_power("unknown")
