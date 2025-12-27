from __future__ import annotations

from uuid import UUID

import pytest
from pydantic import ValidationError

from device.libs.schemas.system import (
    CommandType,
    Severity,
    SystemCommand,
    SystemEvent,
    SystemMode,
    SystemStateChanged,
)


def _valid_state_kwargs() -> dict:
    return dict(
        mode=SystemMode.active,
        battery_percent=87,
        battery_voltage=3.92,
        charging=False,
        radios_enabled=True,
        gps_locked=True,
        modules_connected=2,
        uptime_seconds=123,
        metadata={"note": "ok"},
    )


def test_system_state_changed_valid() -> None:
    msg = SystemStateChanged(source="core-daemon", **_valid_state_kwargs())
    assert isinstance(msg.msg_id, UUID)
    assert msg.mode == SystemMode.active
    assert msg.battery_percent == 87
    assert msg.metadata == {"note": "ok"}


@pytest.mark.parametrize("percent", [-1, 101])
def test_system_state_changed_battery_percent_bounds(percent: int) -> None:
    with pytest.raises(ValidationError):
        SystemStateChanged(
            source="core-daemon", **{**_valid_state_kwargs(), "battery_percent": percent}
        )


@pytest.mark.parametrize("voltage", [2.0, 21.0])
def test_system_state_changed_battery_voltage_plausible(voltage: float) -> None:
    with pytest.raises(ValidationError):
        SystemStateChanged(
            source="core-daemon", **{**_valid_state_kwargs(), "battery_voltage": voltage}
        )


def test_system_command_valid() -> None:
    cmd = SystemCommand(source="ui", command=CommandType.sos_trigger, parameters={"timeout": 30})
    assert cmd.command is CommandType.sos_trigger
    assert cmd.parameters["timeout"] == 30


def test_system_event_valid() -> None:
    ev = SystemEvent(
        source="core-daemon",
        event_type="boot",
        event_code="SYS_BOOT",
        message="System booted",
        severity=Severity.info,
    )
    assert ev.severity is Severity.info
    assert ev.event_code == "SYS_BOOT"
