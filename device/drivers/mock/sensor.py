from __future__ import annotations

import asyncio
import random
from datetime import datetime, timezone
from typing import Any

from device.libs.hil.interfaces.sensor import ISensor, SensorReading


class MockSensor(ISensor):
    def __init__(self, config: dict[str, Any]) -> None:
        self._sensor_id: str = str(config.get("sensor_id", "sensor-1"))
        self._sensor_type: str = str(config.get("sensor_type", "temperature"))
        self._value: float = float(config.get("initial_value", 20.0))
        self._noise_amp: float = float(config.get("noise_amplitude", 0.5))
        self._offset: float = 0.0
        self._ready = False
        random.seed(2)

    @property
    def sensor_id(self) -> str:
        return self._sensor_id

    @property
    def sensor_type(self) -> str:
        return self._sensor_type

    @property
    def is_ready(self) -> bool:
        return self._ready

    async def initialize(self) -> bool:
        await asyncio.sleep(0.01)
        self._ready = True
        return True

    async def read(self) -> SensorReading | None:
        if not self._ready:
            return None
        val = self._value + self._offset + random.uniform(-self._noise_amp, self._noise_amp)
        return SensorReading(
            timestamp=datetime.now(timezone.utc),
            sensor_id=self._sensor_id,
            sensor_type=self._sensor_type,
            value=val,
            unit="celsius" if self._sensor_type == "temperature" else "units",
            accuracy=0.1,
        )

    async def calibrate(self, reference: float | None) -> bool:
        if reference is None:
            return True
        # Adjust offset so that next reading will be near reference
        self._offset = reference - self._value
        return True


def register(_: object) -> None:
    from device.libs.hil.factory import DriverFactory

    DriverFactory.register_sensor("mock", lambda cfg: MockSensor(dict(cfg)))
