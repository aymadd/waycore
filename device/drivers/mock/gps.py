from __future__ import annotations

import asyncio
import random
from datetime import datetime, timezone
from typing import Any

from device.libs.hil.interfaces.gps import IGPS, GPSFixType, GPSReading


class MockGPS(IGPS):
    """
    Mock GPS that simulates position data.

    Supports:
    - Configurable base position
    - Simulated movement (random walk)
    - Variable fix quality
    """

    def __init__(self, config: dict[str, Any]) -> None:
        # Base position (default: San Francisco)
        self._latitude: float = float(config.get("latitude", 37.7749))
        self._longitude: float = float(config.get("longitude", -122.4194))
        self._altitude: float = float(config.get("altitude", 10.0))

        # Movement simulation
        self._drift_enabled: bool = bool(config.get("drift_enabled", True))
        self._drift_speed: float = float(config.get("drift_speed", 0.0001))  # Degrees per update

        # State
        self._ready = False
        self._has_fix = False
        self._tracking = False
        self._speed = 0.0
        self._heading = 0.0

    @property
    def is_ready(self) -> bool:
        return self._ready

    @property
    def has_fix(self) -> bool:
        return self._has_fix

    async def initialize(self) -> bool:
        """Simulate GPS initialization and acquiring fix."""
        await asyncio.sleep(0.1)  # Simulate startup
        self._ready = True
        self._has_fix = True  # Mock always has fix after init
        return True

    async def read(self) -> GPSReading | None:
        """Read current GPS position."""
        if not self._ready or not self._has_fix:
            return None

        # Apply drift if enabled
        if self._drift_enabled:
            self._latitude += random.uniform(-self._drift_speed, self._drift_speed)
            self._longitude += random.uniform(-self._drift_speed, self._drift_speed)
            self._altitude += random.uniform(-0.5, 0.5)

            # Keep within valid ranges
            self._latitude = max(-90, min(90, self._latitude))
            self._longitude = max(-180, min(180, self._longitude))
            self._altitude = max(0, self._altitude)

        # Simulate speed and heading
        self._speed = random.uniform(0, 2.0) if self._tracking else 0
        self._heading = random.uniform(0, 360)

        return GPSReading(
            timestamp=datetime.now(timezone.utc),
            latitude=round(self._latitude, 6),
            longitude=round(self._longitude, 6),
            altitude_m=round(self._altitude, 1),
            speed_mps=round(self._speed, 2),
            heading=round(self._heading, 1),
            accuracy_m=round(random.uniform(3, 15), 1),
            fix_type=GPSFixType.fix_3d,
            satellites=random.randint(6, 12),
        )

    async def start_tracking(self) -> bool:
        """Start continuous tracking."""
        self._tracking = True
        return True

    async def stop_tracking(self) -> None:
        """Stop continuous tracking."""
        self._tracking = False

    def set_position(self, lat: float, lon: float, alt: float | None = None) -> None:
        """Set position externally (for testing)."""
        self._latitude = lat
        self._longitude = lon
        if alt is not None:
            self._altitude = alt

    def set_fix(self, has_fix: bool) -> None:
        """Set fix status (for testing)."""
        self._has_fix = has_fix


def register(_: object) -> None:
    """Register the mock GPS driver with the factory."""
    # GPS is currently used directly, not via factory
    pass
