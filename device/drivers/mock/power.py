from __future__ import annotations

import asyncio
import contextlib
from typing import Any, Callable

from device.libs.hil.interfaces.power import BatteryInfo, IPowerController, PowerBudget


class MockPowerController(IPowerController):
    def __init__(self, config: dict[str, Any]) -> None:
        self._percent: int = int(config.get("initial_battery_percent", 80))
        self._drain_rate_ma: int = int(config.get("drain_rate_ma", 100))
        self._capacity_mah: int = int(config.get("capacity_mah", 5000))
        self._charging: bool = False
        self._callbacks: list[Callable[[BatteryInfo], None]] = []
        self._task: asyncio.Task[None] | None = None
        self._current_draw_ma: int = 200

    async def get_battery_info(self) -> BatteryInfo:
        return BatteryInfo(
            voltage=3.8 + (self._percent / 100.0) * 0.4,
            percent=self._percent,
            current_ma=(-self._drain_rate_ma if not self._charging else self._drain_rate_ma),
            temperature_c=25.0,
            charging=self._charging,
            time_to_empty_min=(
                round(
                    self._capacity_mah
                    * (self._percent / 100.0)
                    / max(self._current_draw_ma, 1)
                    * 60
                )
                if not self._charging
                else None
            ),
            time_to_full_min=(
                round(
                    ((100 - self._percent) / 100.0)
                    * self._capacity_mah
                    / max(self._drain_rate_ma, 1)
                    * 60
                )
                if self._charging
                else None
            ),
        )

    async def get_power_budget(self) -> PowerBudget:
        available = int(self._capacity_mah * (self._percent / 100.0))
        return PowerBudget(
            total_capacity_mah=self._capacity_mah,
            available_capacity_mah=available,
            current_draw_ma=self._current_draw_ma,
            estimated_runtime_min=round(available / max(self._current_draw_ma, 1) * 60),
        )

    async def set_power_mode(self, mode: str) -> bool:
        if mode == "normal":
            self._current_draw_ma = 200
        elif mode == "low_power":
            self._current_draw_ma = 120
        elif mode == "ultra_low":
            self._current_draw_ma = 80
        else:
            return False
        return True

    async def enable_charging(self, enabled: bool) -> None:
        self._charging = enabled
        if enabled and self._task is None:
            self._task = asyncio.create_task(self._charging_loop())
        elif not enabled and self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    def subscribe_battery(self, callback: Callable[[BatteryInfo], None]) -> None:
        self._callbacks.append(callback)

    async def _charging_loop(self) -> None:
        while self._charging:
            await asyncio.sleep(0.5)
            self._percent = min(100, self._percent + 1)
            info = await self.get_battery_info()
            for cb in list(self._callbacks):
                try:
                    cb(info)
                except Exception:
                    pass


def register(_: object) -> None:
    from device.libs.hil.factory import DriverFactory

    DriverFactory.register_power("mock", lambda cfg: MockPowerController(dict(cfg)))
