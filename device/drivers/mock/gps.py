from __future__ import annotations

import asyncio
import contextlib
import random
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from device.libs.hil.interfaces.gps import IGPS, GPSFix


class MockGPS(IGPS):
    def __init__(self, config: dict[str, Any]) -> None:
        self._running = False
        self._has_fix = False
        self._callbacks: list[Callable[[GPSFix], None]] = []
        self._task: asyncio.Task[None] | None = None

        self._lat: float = float(config.get("start_lat", 30.2672))
        self._lon: float = float(config.get("start_lon", -97.7431))
        self._fix_time_seconds: int = int(config.get("fix_time_seconds", 4))
        self._update_rate_hz: float = float(config.get("update_rate_hz", 1.0))
        self._satellites: int = 0
        random.seed(0)

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def has_fix(self) -> bool:
        return self._has_fix

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def get_position(self) -> GPSFix | None:
        if not self._has_fix:
            return None
        return self._make_fix()

    def subscribe_position(self, callback: Callable[[GPSFix], None]) -> None:
        self._callbacks.append(callback)

    async def wait_for_fix(self, timeout_seconds: float = 60.0) -> bool:
        start = datetime.now(timezone.utc).timestamp()
        while (
            not self._has_fix and (datetime.now(timezone.utc).timestamp() - start) < timeout_seconds
        ):
            await asyncio.sleep(0.05)
        return self._has_fix

    async def _loop(self) -> None:
        interval = 1.0 / max(self._update_rate_hz, 0.1)
        elapsed = 0.0
        while self._running:
            await asyncio.sleep(interval)
            elapsed += interval
            # Satellites ramp up until fix
            if not self._has_fix:
                self._satellites = min(self._satellites + 1, 8)
                if elapsed >= self._fix_time_seconds and self._satellites >= 4:
                    self._has_fix = True
            # Drift position slightly when fixed
            if self._has_fix:
                self._lat += random.uniform(-0.00005, 0.00005)
                self._lon += random.uniform(-0.00005, 0.00005)
                fix = self._make_fix()
                for cb in list(self._callbacks):
                    try:
                        cb(fix)
                    except Exception:
                        pass

    def _make_fix(self) -> GPSFix:
        return GPSFix(
            timestamp=datetime.now(timezone.utc),
            latitude=self._lat,
            longitude=self._lon,
            altitude_m=None,
            speed_kmh=0.0,
            heading_deg=0.0,
            satellites=self._satellites,
            hdop=0.8 if self._has_fix else None,
            fix_quality="gps" if self._has_fix else "no_fix",
        )


def register(_: object) -> None:
    from device.libs.hil.factory import DriverFactory

    DriverFactory.register_gps("mock", lambda cfg: MockGPS(dict(cfg)))
