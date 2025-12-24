from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import Field

from .base import BaseMessage


class ModuleCapability(str, Enum):
    sensor = "sensor"
    power = "power"
    communication = "communication"
    tool = "tool"
    display = "display"


class ModuleRemovedReason(str, Enum):
    user_disconnect = "user_disconnect"
    power_loss = "power_loss"
    error = "error"
    timeout = "timeout"


class ModuleDiscovered(BaseMessage):
    """
    Module plugged in and identified.
    Topic: module/{module_id}/discovered
    """

    module_id: str = Field(..., min_length=1)
    module_type: str = Field(..., min_length=1)
    hardware_version: str = Field(..., min_length=1)
    firmware_version: str = Field(..., min_length=1)
    capabilities: list[ModuleCapability] = Field(default_factory=list)
    power_draw_ma: int = Field(..., ge=0, description="Power draw in milliamps")
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModuleRemoved(BaseMessage):
    """
    Module disconnected.
    Topic: module/{module_id}/removed
    """

    module_id: str = Field(..., min_length=1)
    reason: ModuleRemovedReason = Field(..., description="Removal reason")


class ModuleStatus(BaseMessage):
    """
    Module status update.
    Topic: module/{module_id}/status
    """

    module_id: str = Field(..., min_length=1)
    connected: bool = Field(..., description="Module connected")
    healthy: bool = Field(..., description="Module health")
    error_message: str | None = Field(default=None)
    data: dict[str, Any] = Field(default_factory=dict, description="Module-specific status")


class ModuleData(BaseMessage):
    """
    Data from module.
    Topic: module/{module_id}/data
    """

    module_id: str = Field(..., min_length=1)
    data_type: str = Field(..., min_length=1)
    value: Any = Field(..., description="Module-specific value")
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModuleCommand(BaseMessage):
    """
    Command to module.
    Topic: module/{module_id}/command
    """

    module_id: str = Field(..., min_length=1)
    command: str = Field(..., min_length=1)
    parameters: dict[str, Any] = Field(default_factory=dict)
