from __future__ import annotations

import asyncio
import math
import random
from datetime import datetime, timezone
from typing import Any

from device.libs.hil.interfaces.magnetometer import (
    CalibrationStatus,
    IMagnetometer,
    MagnetometerReading,
)


class MockMagnetometer(IMagnetometer):
    """
    Mock magnetometer that simulates compass heading.

    Supports:
    - Configurable base heading with drift
    - Simulated calibration process
    - Random noise for realism
    """

    def __init__(self, config: dict[str, Any]) -> None:
        # Base heading (can be set externally for testing)
        self._base_heading: float = float(config.get("initial_heading", 0.0))
        # Drift rate in degrees per second (simulates slow rotation)
        self._drift_rate: float = float(config.get("drift_rate", 0.0))
        # Noise amplitude in degrees
        self._noise_amplitude: float = float(config.get("noise_amplitude", 2.0))
        # Magnetic declination (difference between magnetic and true north)
        self._declination: float = float(config.get("declination", 0.0))

        self._ready = False
        self._calibration_status = CalibrationStatus.uncalibrated
        self._calibration_task: asyncio.Task[None] | None = None
        self._last_read_time: float = 0.0

    @property
    def is_ready(self) -> bool:
        return self._ready

    @property
    def calibration_status(self) -> CalibrationStatus:
        return self._calibration_status

    @property
    def magnetic_declination(self) -> float:
        return self._declination

    @magnetic_declination.setter
    def magnetic_declination(self, value: float) -> None:
        self._declination = value

    async def initialize(self) -> bool:
        """Simulate sensor initialization."""
        await asyncio.sleep(0.05)  # Simulate startup time
        self._ready = True
        self._calibration_status = CalibrationStatus.calibrated
        self._last_read_time = asyncio.get_event_loop().time()
        return True

    async def read(self) -> MagnetometerReading | None:
        """Read current heading with simulated drift and noise."""
        if not self._ready:
            return None

        current_time = asyncio.get_event_loop().time()
        elapsed = current_time - self._last_read_time

        # Apply drift
        if self._drift_rate != 0:
            self._base_heading += self._drift_rate * elapsed
            self._base_heading = self._base_heading % 360

        self._last_read_time = current_time

        # Add noise
        noise = random.uniform(-self._noise_amplitude, self._noise_amplitude)
        heading = (self._base_heading + noise) % 360

        # Simulate raw magnetic field values (arbitrary units)
        rad = math.radians(heading)
        x = math.cos(rad) * 100 + random.uniform(-5, 5)
        y = math.sin(rad) * 100 + random.uniform(-5, 5)
        z = random.uniform(-10, 10)  # Vertical component

        return MagnetometerReading(
            timestamp=datetime.now(timezone.utc),
            heading_degrees=round(heading, 1),
            accuracy_degrees=(
                self._noise_amplitude * 2
                if self._calibration_status == CalibrationStatus.calibrated
                else 10.0
            ),
            calibration_status=self._calibration_status,
            x=round(x, 2),
            y=round(y, 2),
            z=round(z, 2),
        )

    async def start_calibration(self) -> bool:
        """Start simulated calibration (takes a few seconds)."""
        if self._calibration_task is not None:
            return False  # Already calibrating

        self._calibration_status = CalibrationStatus.calibrating
        self._calibration_task = asyncio.create_task(self._calibration_loop())
        return True

    async def cancel_calibration(self) -> None:
        """Cancel ongoing calibration."""
        if self._calibration_task is not None:
            self._calibration_task.cancel()
            try:
                await self._calibration_task
            except asyncio.CancelledError:
                pass
            self._calibration_task = None
            self._calibration_status = CalibrationStatus.needs_calibration

    async def _calibration_loop(self) -> None:
        """Simulate calibration process (3 seconds)."""
        try:
            await asyncio.sleep(3.0)  # Simulate calibration time
            self._calibration_status = CalibrationStatus.calibrated
            # Reduce noise after calibration
            self._noise_amplitude = max(0.5, self._noise_amplitude / 2)
        except asyncio.CancelledError:
            raise
        finally:
            self._calibration_task = None

    def set_heading(self, heading: float) -> None:
        """Set the base heading (for testing)."""
        self._base_heading = heading % 360


def register(_: object) -> None:
    from device.libs.hil.factory import DriverFactory

    DriverFactory.register_sensor("mock_magnetometer", lambda cfg: MockMagnetometer(dict(cfg)))
