from __future__ import annotations

import asyncio
import random
from datetime import datetime, timezone
from typing import Any

from device.libs.hil.interfaces.sensor import ISensor, SensorReading


class MockAltimeter(ISensor):
    """
    Mock altimeter/barometric pressure sensor.

    Provides elevation data based on barometric pressure simulation.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        self._sensor_id = str(config.get("sensor_id", "altimeter_0"))
        self._base_altitude: float = float(config.get("altitude", 100.0))  # Meters
        self._noise: float = float(config.get("noise", 1.0))  # Noise amplitude
        self._ready = False

    @property
    def sensor_id(self) -> str:
        return self._sensor_id

    @property
    def sensor_type(self) -> str:
        return "altimeter"

    @property
    def is_ready(self) -> bool:
        return self._ready

    async def initialize(self) -> bool:
        """Initialize the altimeter."""
        await asyncio.sleep(0.05)
        self._ready = True
        return True

    async def read(self) -> SensorReading | None:
        """Read current altitude."""
        if not self._ready:
            return None

        # Add noise to base altitude
        altitude = self._base_altitude + random.uniform(-self._noise, self._noise)

        return SensorReading(
            timestamp=datetime.now(timezone.utc),
            sensor_id=self._sensor_id,
            sensor_type="altimeter",
            value=round(altitude, 1),
            unit="m",
            accuracy=self._noise * 2,
        )

    async def calibrate(self, reference: float | None) -> bool:
        """Calibrate to a known altitude."""
        if reference is not None:
            self._base_altitude = reference
        return True

    def set_altitude(self, altitude: float) -> None:
        """Set base altitude (for testing)."""
        self._base_altitude = altitude


def register(_: object) -> None:
    """Register the mock altimeter driver with the factory."""
    # Altimeter is currently used directly, not via factory
    pass
