from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class SensorReading:
    timestamp: datetime
    sensor_id: str
    sensor_type: str
    value: Any
    unit: str
    accuracy: float | None = None


class ISensor(ABC):
    @abstractmethod
    async def initialize(self) -> bool: ...

    @abstractmethod
    async def read(self) -> SensorReading | None: ...

    @abstractmethod
    async def calibrate(self, reference: float | None) -> bool: ...

    @property
    @abstractmethod
    def sensor_id(self) -> str: ...

    @property
    @abstractmethod
    def sensor_type(self) -> str: ...

    @property
    @abstractmethod
    def is_ready(self) -> bool: ...
