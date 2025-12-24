from __future__ import annotations

from device.libs.schemas.system import CommandType, SystemMode
from device.services.core_daemon.state_machine import StateMachine


def test_sos_trigger_and_cancel() -> None:
    sm = StateMachine()
    assert sm.state.mode == SystemMode.idle
    assert sm.handle_command(CommandType.sos_trigger) is True
    assert sm.state.mode == SystemMode.sos
    assert sm.handle_command(CommandType.sos_cancel) is True
    assert sm.state.mode == SystemMode.idle


def test_low_power_guard_when_charging() -> None:
    sm = StateMachine()
    sm.state.charging = True
    sm.state.battery_percent = 10
    sm.apply_battery_policy()
    # Guard prevents changing mode while charging
    assert sm.state.mode == SystemMode.idle


def test_low_power_and_critical() -> None:
    sm = StateMachine()
    sm.state.charging = False
    sm.state.battery_percent = 12
    sm.apply_battery_policy()
    assert sm.state.mode == SystemMode.low_power
    sm.state.battery_percent = 3
    sm.apply_battery_policy()
    assert sm.state.mode == SystemMode.sos
