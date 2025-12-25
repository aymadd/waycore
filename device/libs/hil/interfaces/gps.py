from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class GPSFixType(str, Enum):
    """GPS fix quality."""

    no_fix = "no_fix"
    fix_2d = "2d"
    fix_3d = "3d"


@dataclass(frozen=True)
class GPSReading:
    """A single GPS reading."""

    timestamp: datetime
    latitude: float  # Degrees (-90 to 90)
    longitude: float  # Degrees (-180 to 180)
    altitude_m: float | None  # Meters above sea level
    speed_mps: float | None  # Speed in meters per second
    heading: float | None  # Track heading in degrees
    accuracy_m: float  # Horizontal accuracy in meters
    fix_type: GPSFixType
    satellites: int  # Number of satellites used


class IGPS(ABC):
    """Interface for GPS receivers."""

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the GPS. Returns True if successful."""
        ...

    @abstractmethod
    async def read(self) -> GPSReading | None:
        """Read current GPS position. Returns None if no fix."""
        ...

    @abstractmethod
    async def start_tracking(self) -> bool:
        """Start continuous position tracking."""
        ...

    @abstractmethod
    async def stop_tracking(self) -> None:
        """Stop continuous tracking."""
        ...

    @property
    @abstractmethod
    def has_fix(self) -> bool:
        """Whether GPS has a valid fix."""
        ...

    @property
    @abstractmethod
    def is_ready(self) -> bool:
        """Whether GPS is initialized and ready."""
        ...
