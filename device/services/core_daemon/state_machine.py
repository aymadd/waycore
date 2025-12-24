from __future__ import annotations

from dataclasses import dataclass

from device.libs.schemas.system import CommandType, SystemMode


@dataclass
class SystemState:
    mode: SystemMode = SystemMode.idle
    gps_locked: bool = False
    radios_enabled: bool = False
    modules_connected: int = 0
    uptime_seconds: int = 0
    battery_percent: int = 100
    battery_voltage: float = 4.0
    charging: bool = False


class StateMachine:
    def __init__(self) -> None:
        self.state = SystemState()

    def boot(self) -> None:
        self.state.mode = SystemMode.idle

    def handle_command(self, command: CommandType) -> bool:
        if command == CommandType.sos_trigger:
            self.state.mode = SystemMode.sos
            return True
        if command == CommandType.sos_cancel:
            if self.state.mode == SystemMode.sos:
                self.state.mode = SystemMode.idle
                return True
            return False
        if command == CommandType.enter_low_power:
            # Respect guard: cannot enter LOW_POWER if charging
            if not self.state.charging:
                self.state.mode = SystemMode.low_power
                return True
            return False
        if command == CommandType.radio_enable:
            self.state.radios_enabled = True
            return True
        if command == CommandType.radio_disable:
            self.state.radios_enabled = False
            return True
        # shutdown/reboot commands are accepted but state not changed here
        if command in (CommandType.shutdown, CommandType.reboot):
            return True
        return False

    def apply_battery_policy(self, low_threshold: int = 15, critical_threshold: int = 5) -> None:
        """
        Update mode based on battery level, observing guards.
        """
        if self.state.charging:
            # Charging guard: do not force low power while charging
            return
        if self.state.battery_percent < critical_threshold:
            # Enter SOS if critically low (as a safe default)
            self.state.mode = SystemMode.sos
        elif self.state.battery_percent < low_threshold:
            self.state.mode = SystemMode.low_power
