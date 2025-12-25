"""
Sensor Registry - Dynamic sensor discovery and management.

This module provides a registry for sensors that can be discovered at runtime.
In development mode, it registers mock sensors.
In production, it will scan for actual hardware sensors.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Protocol

logger = logging.getLogger(__name__)


class SensorType(str, Enum):
    """Types of sensors that can be registered."""

    GPS = "gps"
    TEMPERATURE = "temperature"
    PRESSURE = "pressure"
    ACCELEROMETER = "accelerometer"
    MAGNETOMETER = "magnetometer"
    LIGHT = "light"
    HUMIDITY = "humidity"
    BATTERY = "battery"
    # Future sensor types for modules
    CUSTOM = "custom"


class SensorStatus(str, Enum):
    """Possible sensor statuses."""

    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"
    CALIBRATING = "calibrating"
    UNKNOWN = "unknown"


@dataclass
class SensorInfo:
    """Information about a registered sensor."""

    id: str
    type: SensorType
    name: str
    driver: str
    status: SensorStatus = SensorStatus.UNKNOWN
    last_value: dict[str, Any] | None = None
    last_reading_at: datetime | None = None
    config: dict[str, Any] = field(default_factory=dict)
    discovered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "type": self.type.value,
            "name": self.name,
            "driver": self.driver,
            "status": self.status.value,
            "last_value": self.last_value,
            "last_reading_at": self.last_reading_at.isoformat() if self.last_reading_at else None,
            "config": self.config,
            "discovered_at": self.discovered_at.isoformat(),
        }


class SensorDriver(Protocol):
    """Protocol for sensor drivers."""

    async def read(self) -> dict[str, Any]:
        """Read current sensor value."""
        ...

    async def get_status(self) -> SensorStatus:
        """Get current sensor status."""
        ...


class SensorRegistry:
    """
    Registry for managing discovered sensors.

    This class handles sensor discovery, registration, and value updates.
    It can work with both mock sensors (development) and real sensors (production).
    """

    def __init__(self) -> None:
        self._sensors: dict[str, SensorInfo] = {}
        self._drivers: dict[str, SensorDriver] = {}
        self._is_mock_mode = os.environ.get("WAYCORE_MOCK_SENSORS", "true").lower() == "true"
        self._discovery_complete = False

    @property
    def is_mock_mode(self) -> bool:
        """Check if running with mock sensors."""
        return self._is_mock_mode

    @property
    def sensors(self) -> list[SensorInfo]:
        """Get all registered sensors."""
        return list(self._sensors.values())

    def get_sensor(self, sensor_id: str) -> SensorInfo | None:
        """Get a specific sensor by ID."""
        return self._sensors.get(sensor_id)

    def get_sensors_by_type(self, sensor_type: SensorType) -> list[SensorInfo]:
        """Get all sensors of a specific type."""
        return [s for s in self._sensors.values() if s.type == sensor_type]

    def register_sensor(
        self,
        sensor_id: str,
        sensor_type: SensorType,
        name: str,
        driver: str,
        config: dict[str, Any] | None = None,
    ) -> SensorInfo:
        """
        Register a sensor in the registry.

        Args:
            sensor_id: Unique identifier for the sensor
            sensor_type: Type of sensor (GPS, temperature, etc.)
            name: Human-readable name
            driver: Driver identifier (e.g., "mock.gps", "bme280")
            config: Optional configuration for the sensor

        Returns:
            The registered SensorInfo
        """
        info = SensorInfo(
            id=sensor_id,
            type=sensor_type,
            name=name,
            driver=driver,
            status=SensorStatus.ONLINE,
            config=config or {},
        )
        self._sensors[sensor_id] = info
        logger.info(f"Registered sensor: {sensor_id} ({sensor_type.value}) using driver {driver}")
        return info

    def unregister_sensor(self, sensor_id: str) -> bool:
        """Remove a sensor from the registry."""
        if sensor_id in self._sensors:
            del self._sensors[sensor_id]
            if sensor_id in self._drivers:
                del self._drivers[sensor_id]
            logger.info(f"Unregistered sensor: {sensor_id}")
            return True
        return False

    def update_reading(
        self,
        sensor_id: str,
        value: dict[str, Any],
        status: SensorStatus = SensorStatus.ONLINE,
    ) -> bool:
        """Update a sensor's latest reading."""
        if sensor_id not in self._sensors:
            return False

        sensor = self._sensors[sensor_id]
        sensor.last_value = value
        sensor.last_reading_at = datetime.now(timezone.utc)
        sensor.status = status
        return True

    def update_status(self, sensor_id: str, status: SensorStatus) -> bool:
        """Update a sensor's status."""
        if sensor_id not in self._sensors:
            return False
        self._sensors[sensor_id].status = status
        return True

    async def discover_sensors(self) -> list[SensorInfo]:
        """
        Discover and register available sensors.

        In mock mode, registers mock sensors for development.
        In production mode, scans for actual hardware sensors.

        Returns:
            List of discovered sensors
        """
        if self._is_mock_mode:
            return await self._discover_mock_sensors()
        else:
            return await self._discover_hardware_sensors()

    async def _discover_mock_sensors(self) -> list[SensorInfo]:
        """Register mock sensors for development."""
        logger.info("Discovering mock sensors for development mode...")

        mock_sensors: list[tuple[SensorType, str, str, str, dict[str, Any]]] = [
            (SensorType.GPS, "mock_gps", "GPS Module", "mock.gps", {"update_rate_hz": 1}),
            (
                SensorType.TEMPERATURE,
                "mock_temp",
                "Temperature Sensor",
                "mock.temperature",
                {"unit": "celsius"},
            ),
            (
                SensorType.PRESSURE,
                "mock_pressure",
                "Barometer",
                "mock.pressure",
                {"sea_level_hpa": 1013.25},
            ),
            (
                SensorType.ACCELEROMETER,
                "mock_accel",
                "Accelerometer",
                "mock.accelerometer",
                {"range_g": 16},
            ),
            (
                SensorType.MAGNETOMETER,
                "mock_mag",
                "Magnetometer",
                "mock.magnetometer",
                {"declination": 0},
            ),
            (SensorType.LIGHT, "mock_light", "Light Sensor", "mock.light", {"max_lux": 65535}),
            (
                SensorType.BATTERY,
                "mock_battery",
                "Battery Monitor",
                "mock.battery",
                {"chemistry": "li-ion"},
            ),
        ]

        discovered: list[SensorInfo] = []
        for sensor_type, sensor_id, name, driver, config in mock_sensors:
            info = self.register_sensor(sensor_id, sensor_type, name, driver, config)
            discovered.append(info)

        self._discovery_complete = True
        logger.info(f"Discovered {len(discovered)} mock sensors")
        return discovered

    async def _discover_hardware_sensors(self) -> list[SensorInfo]:
        """
        Scan for actual hardware sensors.

        This would scan I2C buses, SPI devices, GPIO pins, etc.
        for connected sensor hardware.
        """
        logger.info("Scanning for hardware sensors...")
        discovered: list[SensorInfo] = []

        # TODO: Implement actual hardware scanning
        # This would include:
        # - I2C bus scan (for BME280, BMP280, MPU6050, etc.)
        # - Serial port scan (for GPS modules)
        # - GPIO pin detection (for simple sensors)
        # - USB device enumeration (for external modules)

        # For now, fall back to mock sensors if no hardware found
        if not discovered:
            logger.warning("No hardware sensors found, using mock sensors")
            return await self._discover_mock_sensors()

        self._discovery_complete = True
        logger.info(f"Discovered {len(discovered)} hardware sensors")
        return discovered

    def clear(self) -> None:
        """Clear all registered sensors."""
        self._sensors.clear()
        self._drivers.clear()
        self._discovery_complete = False
        logger.info("Cleared sensor registry")


# Global registry instance
_registry: SensorRegistry | None = None


def get_registry() -> SensorRegistry:
    """Get the global sensor registry instance."""
    global _registry
    if _registry is None:
        _registry = SensorRegistry()
    return _registry


async def initialize_sensors() -> list[SensorInfo]:
    """
    Initialize the sensor registry and discover sensors.

    This should be called once at application startup.
    """
    registry = get_registry()
    return await registry.discover_sensors()
