from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import Field, field_validator

from .base import BaseMessage


class SystemMode(str, Enum):
    idle = "idle"
    active = "active"
    low_power = "low_power"
    sos = "sos"
    charging = "charging"


class CommandType(str, Enum):
    sos_trigger = "sos_trigger"
    sos_cancel = "sos_cancel"
    radio_enable = "radio_enable"
    radio_disable = "radio_disable"
    shutdown = "shutdown"
    reboot = "reboot"
    enter_low_power = "enter_low_power"


class Severity(str, Enum):
    critical = "critical"
    error = "error"
    warning = "warning"
    info = "info"
    debug = "debug"


class SystemStateChanged(BaseMessage):
    """
    Published when system state changes.
    Topic: system/state/changed
    """

    mode: SystemMode = Field(..., description="Current system mode")
    battery_percent: int = Field(..., ge=0, le=100, description="Battery level percent (0-100)")
    battery_voltage: float = Field(..., gt=0, description="Battery voltage in volts")
    charging: bool = Field(..., description="Is battery charging")
    radios_enabled: bool = Field(..., description="At least one radio enabled")
    gps_locked: bool = Field(..., description="GPS has a valid fix")
    modules_connected: int = Field(..., ge=0, description="Number of connected modules")
    uptime_seconds: int = Field(..., ge=0, description="Device uptime in seconds")
    metadata: dict[str, Any] | None = Field(default=None, description="Additional data")

    @field_validator("battery_voltage")
    @classmethod
    def _voltage_plausible(cls, value: float) -> float:
        # Plausible consumer device range; generous bounds
        if not (2.5 <= value <= 20.0):
            msg = "battery_voltage is outside plausible range (2.5V - 20V)"
            raise ValueError(msg)
        return value


class SystemCommand(BaseMessage):
    """
    Command directed to the system.
    Topic: system/command/execute
    """

    command: CommandType = Field(..., description="Command type")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Command parameters")


class SystemEvent(BaseMessage):
    """
    Significant system event.
    Topic: system/event/occurred
    """

    event_type: str = Field(
        ..., min_length=1, description="Event type (boot, shutdown, error, ...)"
    )
    event_code: str = Field(..., min_length=1, description="Unique event identifier")
    message: str = Field(..., min_length=1, description="Human-readable description")
    severity: Severity = Field(..., description="Event severity")
    context: dict[str, Any] = Field(default_factory=dict, description="Structured context data")
