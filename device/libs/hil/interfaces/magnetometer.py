from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class CalibrationStatus(str, Enum):
    """Magnetometer calibration status."""

    uncalibrated = "uncalibrated"
    calibrating = "calibrating"
    calibrated = "calibrated"
    needs_calibration = "needs_calibration"


@dataclass(frozen=True)
class MagnetometerReading:
    """A single magnetometer reading."""

    timestamp: datetime
    heading_degrees: float  # 0-360, where 0 = magnetic north
    accuracy_degrees: float | None  # Accuracy in degrees
    calibration_status: CalibrationStatus
    # Raw magnetic field components (optional, for debugging)
    x: float | None = None
    y: float | None = None
    z: float | None = None


class IMagnetometer(ABC):
    """Interface for magnetometer/compass sensors."""

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the magnetometer. Returns True if successful."""
        ...

    @abstractmethod
    async def read(self) -> MagnetometerReading | None:
        """Read current heading. Returns None if not ready."""
        ...

    @abstractmethod
    async def start_calibration(self) -> bool:
        """Start calibration process. Returns True if started."""
        ...

    @abstractmethod
    async def cancel_calibration(self) -> None:
        """Cancel ongoing calibration."""
        ...

    @property
    @abstractmethod
    def calibration_status(self) -> CalibrationStatus:
        """Current calibration status."""
        ...

    @property
    @abstractmethod
    def is_ready(self) -> bool:
        """Whether the magnetometer is initialized and ready."""
        ...

    @property
    @abstractmethod
    def magnetic_declination(self) -> float:
        """Magnetic declination in degrees (for true north calculation)."""
        ...

    @magnetic_declination.setter
    @abstractmethod
    def magnetic_declination(self, value: float) -> None:
        """Set magnetic declination for the current location."""
        ...
