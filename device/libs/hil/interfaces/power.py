from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class BatteryInfo:
    voltage: float
    percent: int
    current_ma: int
    temperature_c: float | None = None
    charging: bool = False
    time_to_empty_min: int | None = None
    time_to_full_min: int | None = None


@dataclass(frozen=True)
class PowerBudget:
    total_capacity_mah: int
    available_capacity_mah: int
    current_draw_ma: int
    estimated_runtime_min: int


class IPowerController(ABC):
    @abstractmethod
    async def get_battery_info(self) -> BatteryInfo: ...

    @abstractmethod
    async def get_power_budget(self) -> PowerBudget: ...

    @abstractmethod
    async def set_power_mode(self, mode: str) -> bool: ...

    @abstractmethod
    async def enable_charging(self, enabled: bool) -> None: ...

    @abstractmethod
    def subscribe_battery(self, callback: Callable[[BatteryInfo], None]) -> None: ...
