from __future__ import annotations

from datetime import datetime, timezone

import pytest

from device.libs.hil.interfaces.gps import IGPS, GPSReading
from device.libs.hil.interfaces.module_port import IModulePort
from device.libs.hil.interfaces.power import BatteryInfo, IPowerController, PowerBudget
from device.libs.hil.interfaces.radio import IRadio, RadioStatus, RadioType, ReceivedMessage
from device.libs.hil.interfaces.sensor import ISensor


def test_gpsreading_dataclass_fields() -> None:
    now = datetime.now(timezone.utc)
    from device.libs.hil.interfaces.gps import GPSFixType

    reading = GPSReading(
        timestamp=now,
        latitude=1.0,
        longitude=2.0,
        altitude_m=100.0,
        speed_mps=0.0,
        heading=0.0,
        accuracy_m=5.0,
        fix_type=GPSFixType.fix_3d,
        satellites=5,
    )
    assert reading.timestamp == now
    assert reading.satellites == 5


def test_iradio_status_and_message_dataclasses() -> None:
    status = RadioStatus(enabled=True, connected=False)
    assert status.enabled is True and status.connected is False
    msg = ReceivedMessage(
        timestamp=datetime.now(timezone.utc),
        from_node="A",
        to_node=None,
        content=b"hi",
    )
    assert msg.content == b"hi"


def test_interface_cannot_instantiate_without_impl() -> None:
    with pytest.raises(TypeError):
        IRadio()  # type: ignore[abstract]
    with pytest.raises(TypeError):
        IGPS()  # type: ignore[abstract]
    with pytest.raises(TypeError):
        ISensor()  # type: ignore[abstract]
    with pytest.raises(TypeError):
        IModulePort()  # type: ignore[abstract]
    with pytest.raises(TypeError):
        IPowerController()  # type: ignore[abstract]


def test_minimal_concrete_iradio() -> None:
    class DummyRadio(IRadio):
        def __init__(self) -> None:
            self._enabled = False

        @property
        def radio_type(self) -> RadioType:
            return RadioType.lora

        async def start(self) -> None: ...

        async def stop(self) -> None: ...

        async def send_message(
            self, content: bytes, to_node: str | None, channel: str | None, want_ack: bool
        ) -> bool:
            return True

        def subscribe_messages(self, callback):  # type: ignore[no-untyped-def]
            return None

        async def get_status(self) -> RadioStatus:
            return RadioStatus(enabled=self._enabled, connected=False)

        async def set_power(self, enabled: bool) -> None:
            self._enabled = enabled

    r = DummyRadio()
    assert r.radio_type is RadioType.lora


def test_battery_and_budget_dataclasses() -> None:
    b = BatteryInfo(voltage=3.9, percent=80, current_ma=-150, charging=False)
    p = PowerBudget(
        total_capacity_mah=5000,
        available_capacity_mah=4000,
        current_draw_ma=200,
        estimated_runtime_min=120,
    )
    assert b.percent == 80
    assert p.estimated_runtime_min == 120
