from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Callable


@dataclass(frozen=True)
class GPSFix:
    timestamp: datetime
    latitude: float
    longitude: float
    altitude_m: float | None = None
    speed_kmh: float | None = None
    heading_deg: float | None = None
    satellites: int = 0
    hdop: float | None = None
    fix_quality: str = "no_fix"


class IGPS(ABC):
    @abstractmethod
    async def start(self) -> None: ...

    @abstractmethod
    async def stop(self) -> None: ...

    @abstractmethod
    async def get_position(self) -> GPSFix | None: ...

    @abstractmethod
    def subscribe_position(self, callback: Callable[[GPSFix], None]) -> None: ...

    @abstractmethod
    async def wait_for_fix(self, timeout_seconds: float = 60.0) -> bool: ...

    @property
    @abstractmethod
    def is_running(self) -> bool: ...

    @property
    @abstractmethod
    def has_fix(self) -> bool: ...
