"""
Sensor Bridge - Exposes backend sensor data to QML.

This module provides a QObject that bridges the Python API client
with QML, allowing the UI to receive real-time sensor data.
"""

from __future__ import annotations

import logging
from datetime import datetime

from PySide6.QtCore import Property, QObject, QTimer, Signal, Slot

from .api_client import CoreDaemonClient

logger = logging.getLogger(__name__)


class SensorBridge(QObject):
    """
    Bridge between Python backend API and QML UI.

    Exposes sensor data (time, battery, temperature) as Qt properties
    that QML can bind to for reactive updates.
    """

    # Signals for property changes
    timeChanged = Signal()
    batteryChanged = Signal()
    temperatureChanged = Signal()
    connectionChanged = Signal()
    systemInfoChanged = Signal()
    compassChanged = Signal()
    sensorsChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)

        # Initialize client (will be None if socket doesn't exist)
        self._client: CoreDaemonClient | None = None
        self._connected = False

        # Data properties
        self._current_time = ""
        self._current_date = ""
        self._uptime_seconds = 0

        self._battery_level = 85  # Default mock value
        self._battery_charging = False
        self._battery_voltage = 3.7

        self._temperature_celsius = 22.5  # Default mock value
        self._temperature_source = "mock"

        # System info
        self._app_version = "0.1.0-dev"
        self._device_model = "Unknown"
        self._os_version = "Unknown"
        self._hostname = "waycore"

        # Compass
        self._compass_heading = 0.0
        self._compass_cardinal = "N"
        self._compass_calibrated = True

        # GPS (None means no fix/data)
        self._gps_latitude: float | None = None
        self._gps_longitude: float | None = None
        self._gps_accuracy: float | None = None

        # Elevation (None means unavailable)
        self._elevation_m: float | None = None

        # Sensor registry (list of discovered sensors)
        self._sensors: list[dict] = []

        # Update timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_all)
        self._timer.start(5000)  # Update every 5 seconds

        # Try initial connection
        self._try_connect()
        self._update_all()
        self._update_system_info()

    def _try_connect(self) -> None:
        """Attempt to connect to the backend."""
        try:
            self._client = CoreDaemonClient()
            # Test connection with a simple call
            self._client.get_time()
            self._connected = True
            logger.info("Connected to Core Daemon")
        except Exception as e:
            logger.debug(f"Backend not available, using mock data: {e}")
            self._client = None
            self._connected = False
        self.connectionChanged.emit()

    @Slot()  # type: ignore[arg-type]
    def _update_all(self) -> None:
        """Update all sensor data from backend or use mock values."""
        self._update_time()
        self._update_battery()
        self._update_temperature()

    def _update_time(self) -> None:
        """Fetch time from backend or use system time."""
        if self._client and self._connected:
            try:
                data = self._client.get_time()
                # Parse ISO timestamp
                ts = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
                self._current_time = ts.strftime("%H:%M")
                self._current_date = ts.strftime("%b %d")
                self._uptime_seconds = data.get("uptime_seconds", 0)
                self.timeChanged.emit()
                return
            except Exception as e:
                logger.debug(f"Failed to get time from backend: {e}")
                self._connected = False
                self.connectionChanged.emit()

        # Fallback to local time
        now = datetime.now()
        self._current_time = now.strftime("%H:%M")
        self._current_date = now.strftime("%b %d")
        self.timeChanged.emit()

    def _update_battery(self) -> None:
        """Fetch battery from backend or use mock values."""
        if self._client and self._connected:
            try:
                data = self._client.get_battery()
                self._battery_level = data["level"]
                self._battery_charging = data["is_charging"]
                self._battery_voltage = data.get("voltage", 3.7)
                self.batteryChanged.emit()
                return
            except Exception:
                pass  # Fall through to mock values

        # Mock values already set in __init__
        self.batteryChanged.emit()

    def _update_temperature(self) -> None:
        """Fetch temperature from backend or use mock values."""
        if self._client and self._connected:
            try:
                data = self._client.get_temperature()
                self._temperature_celsius = data["celsius"]
                self._temperature_source = data.get("source", "backend")
                self.temperatureChanged.emit()
                return
            except Exception:
                pass  # Fall through to mock values

        # Mock values already set in __init__
        self.temperatureChanged.emit()

    def _update_system_info(self) -> None:
        """Fetch system info from backend."""
        if self._client and self._connected:
            try:
                data = self._client.get_system_info()
                self._app_version = data.get("app_version", "0.1.0-dev")
                self._device_model = data.get("device_model", "Unknown")
                self._os_version = data.get("os_version", "Unknown")
                self._hostname = data.get("hostname", "waycore")
                self.systemInfoChanged.emit()
            except Exception:
                pass  # Keep default values

    def _update_compass(self) -> None:
        """Fetch compass data from backend (includes GPS/elevation)."""
        if self._client and self._connected:
            try:
                data = self._client.get_compass()
                self._compass_heading = data["heading_degrees"]
                self._compass_cardinal = data["heading_cardinal"]
                self._compass_calibrated = data["calibrated"]
                # GPS data (may be None)
                self._gps_latitude = data.get("latitude")
                self._gps_longitude = data.get("longitude")
                self._gps_accuracy = data.get("gps_accuracy_m")
                # Elevation (may be None)
                self._elevation_m = data.get("elevation_m")
                self.compassChanged.emit()
                return
            except Exception as e:
                logger.debug(f"Failed to get compass data: {e}")

        # Mock compass (slow rotation for testing)
        import time

        self._compass_heading = (time.time() * 5) % 360  # 5 degrees per second
        self._compass_cardinal = self._heading_to_cardinal(self._compass_heading)
        # Mock GPS (San Francisco)
        self._gps_latitude = 37.7749
        self._gps_longitude = -122.4194
        self._gps_accuracy = 5.0
        # Mock elevation
        self._elevation_m = 52.0
        self.compassChanged.emit()

    @staticmethod
    def _heading_to_cardinal(heading: float) -> str:
        """Convert heading to cardinal direction."""
        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        index = int((heading + 22.5) / 45) % 8
        return directions[index]

    # --- Qt Properties for QML binding ---

    @Property(str, notify=timeChanged)  # type: ignore[arg-type]
    def currentTime(self) -> str:
        return self._current_time

    @Property(str, notify=timeChanged)  # type: ignore[arg-type]
    def currentDate(self) -> str:
        return self._current_date

    @Property(int, notify=timeChanged)  # type: ignore[arg-type]
    def uptimeSeconds(self) -> int:
        return self._uptime_seconds

    @Property(int, notify=batteryChanged)  # type: ignore[arg-type]
    def batteryLevel(self) -> int:
        return self._battery_level

    @Property(bool, notify=batteryChanged)  # type: ignore[arg-type]
    def batteryCharging(self) -> bool:
        return self._battery_charging

    @Property(float, notify=batteryChanged)  # type: ignore[arg-type]
    def batteryVoltage(self) -> float:
        return self._battery_voltage

    @Property(float, notify=temperatureChanged)  # type: ignore[arg-type]
    def temperatureCelsius(self) -> float:
        return self._temperature_celsius

    @Property(str, notify=temperatureChanged)  # type: ignore[arg-type]
    def temperatureSource(self) -> str:
        return self._temperature_source

    @Property(bool, notify=connectionChanged)  # type: ignore[arg-type]
    def connected(self) -> bool:
        return self._connected

    @Property(str, notify=systemInfoChanged)  # type: ignore[arg-type]
    def appVersion(self) -> str:
        return self._app_version

    @Property(str, notify=systemInfoChanged)  # type: ignore[arg-type]
    def deviceModel(self) -> str:
        return self._device_model

    @Property(str, notify=systemInfoChanged)  # type: ignore[arg-type]
    def osVersion(self) -> str:
        return self._os_version

    @Property(str, notify=systemInfoChanged)  # type: ignore[arg-type]
    def hostname(self) -> str:
        return self._hostname

    @Property(float, notify=compassChanged)  # type: ignore[arg-type]
    def compassHeading(self) -> float:
        return self._compass_heading

    @Property(str, notify=compassChanged)  # type: ignore[arg-type]
    def compassCardinal(self) -> str:
        return self._compass_cardinal

    @Property(bool, notify=compassChanged)  # type: ignore[arg-type]
    def compassCalibrated(self) -> bool:
        return self._compass_calibrated

    @Property(float, notify=compassChanged)  # type: ignore[arg-type]
    def gpsLatitude(self) -> float:
        return self._gps_latitude if self._gps_latitude is not None else 0.0

    @Property(float, notify=compassChanged)  # type: ignore[arg-type]
    def gpsLongitude(self) -> float:
        return self._gps_longitude if self._gps_longitude is not None else 0.0

    @Property(bool, notify=compassChanged)  # type: ignore[arg-type]
    def hasGpsFix(self) -> bool:
        return self._gps_latitude is not None and self._gps_longitude is not None

    @Property(float, notify=compassChanged)  # type: ignore[arg-type]
    def gpsAccuracy(self) -> float:
        return self._gps_accuracy if self._gps_accuracy is not None else 0.0

    @Property(float, notify=compassChanged)  # type: ignore[arg-type]
    def elevationMeters(self) -> float:
        return self._elevation_m if self._elevation_m is not None else 0.0

    @Property(bool, notify=compassChanged)  # type: ignore[arg-type]
    def hasElevation(self) -> bool:
        return self._elevation_m is not None

    # --- Slots for QML to call ---

    @Slot()  # type: ignore[arg-type]
    def refresh(self) -> None:
        """Force refresh all data."""
        if not self._connected:
            self._try_connect()
        self._update_all()

    @Slot(result=str)  # type: ignore[arg-type]
    def getBatteryIcon(self) -> str:
        """Get battery icon based on level."""
        if self._battery_charging:
            return "🔌"
        if self._battery_level > 80:
            return "🔋"
        if self._battery_level > 50:
            return "🔋"
        if self._battery_level > 20:
            return "🔋"
        return "🪫"

    @Slot(result=str)  # type: ignore[arg-type]
    def getBatteryColor(self) -> str:
        """Get battery color based on level."""
        if self._battery_charging:
            return "#7A9984"  # info
        if self._battery_level > 50:
            return "#6B9B6F"  # success
        if self._battery_level > 20:
            return "#D4A574"  # warning
        return "#C97064"  # error

    @Slot()  # type: ignore[arg-type]
    def refreshCompass(self) -> None:
        """Refresh compass data (called at higher frequency)."""
        self._update_compass()

    @Slot()  # type: ignore[arg-type]
    def calibrateCompass(self) -> None:
        """Start compass calibration."""
        if self._client and self._connected:
            try:
                self._client.calibrate_compass()
                self._compass_calibrated = True
                self.compassChanged.emit()
                logger.info("Compass calibration started")
            except Exception as e:
                logger.error(f"Failed to calibrate compass: {e}")
        else:
            # Mock calibration
            self._compass_calibrated = True
            self.compassChanged.emit()

    @Slot(result=bool)  # type: ignore[arg-type]
    def factoryReset(self) -> bool:
        """
        Perform factory reset on backend services.
        Clears all user data and resets settings to defaults.
        Returns True if successful.
        """
        from .api_client import DataLoggerClient

        success = True

        # Reset core daemon (sensor states, etc.)
        if self._client and self._connected:
            try:
                self._client.factory_reset()
                logger.info("Core daemon factory reset complete")
            except Exception as e:
                logger.error(f"Core daemon factory reset failed: {e}")
                success = False

        # Reset data logger (notes, preferences, logs)
        try:
            data_client = DataLoggerClient()
            data_client.factory_reset()
            logger.info("Data logger factory reset complete")
        except Exception as e:
            logger.error(f"Data logger factory reset failed: {e}")
            success = False

        return success

    # --- Sensor Registry ---

    @Property("QVariantList", notify=sensorsChanged)  # type: ignore[arg-type]
    def sensors(self) -> list[dict]:
        """Get all registered sensors."""
        return self._sensors

    @Slot()  # type: ignore[arg-type]
    def refreshSensors(self) -> None:
        """Refresh the sensor registry from backend."""
        if self._client and self._connected:
            try:
                self._sensors = self._client.get_all_sensors()
                self.sensorsChanged.emit()
                logger.debug(f"Loaded {len(self._sensors)} sensors from registry")
            except Exception as e:
                logger.error(f"Failed to load sensors: {e}")
                self._use_mock_sensors()
        else:
            self._use_mock_sensors()

    @Slot(result="QVariantList")  # type: ignore[arg-type]
    def getSensorsByType(self, sensor_type: str) -> list[dict]:
        """Get sensors filtered by type."""
        return [s for s in self._sensors if s.get("type") == sensor_type]

    @Slot(result=bool)  # type: ignore[arg-type]
    def discoverSensors(self) -> bool:
        """Run sensor discovery on the backend."""
        if self._client and self._connected:
            try:
                result = self._client.discover_sensors()
                self._sensors = result.get("sensors", [])
                self.sensorsChanged.emit()
                logger.info(f"Discovered {len(self._sensors)} sensors")
                return True
            except Exception as e:
                logger.error(f"Sensor discovery failed: {e}")
        return False

    def _use_mock_sensors(self) -> None:
        """Use mock sensor data when backend is unavailable."""

        now = datetime.now().isoformat()
        self._sensors = [
            {
                "id": "mock_gps",
                "type": "gps",
                "name": "GPS Module",
                "driver": "mock.gps",
                "status": "online",
                "last_value": {
                    "latitude": 37.7749,
                    "longitude": -122.4194,
                    "accuracy_m": 5.0,
                    "has_fix": True,
                },
                "last_reading_at": now,
            },
            {
                "id": "mock_temp",
                "type": "temperature",
                "name": "Temperature Sensor",
                "driver": "mock.temperature",
                "status": "online",
                "last_value": {
                    "celsius": self._temperature_celsius,
                    "fahrenheit": self._temperature_celsius * 9 / 5 + 32,
                },
                "last_reading_at": now,
            },
            {
                "id": "mock_pressure",
                "type": "pressure",
                "name": "Barometer",
                "driver": "mock.pressure",
                "status": "online",
                "last_value": {"hPa": 1013.25, "altitude_m": 52.0},
                "last_reading_at": now,
            },
            {
                "id": "mock_accel",
                "type": "accelerometer",
                "name": "Accelerometer",
                "driver": "mock.accelerometer",
                "status": "online",
                "last_value": {"x": 0.02, "y": -0.01, "z": 1.00, "unit": "g"},
                "last_reading_at": now,
            },
            {
                "id": "mock_mag",
                "type": "magnetometer",
                "name": "Magnetometer",
                "driver": "mock.magnetometer",
                "status": "online" if self._compass_calibrated else "calibrating",
                "last_value": {
                    "heading": self._compass_heading,
                    "cardinal": self._compass_cardinal,
                    "calibrated": self._compass_calibrated,
                },
                "last_reading_at": now,
            },
            {
                "id": "mock_light",
                "type": "light",
                "name": "Light Sensor",
                "driver": "mock.light",
                "status": "online",
                "last_value": {"lux": 350, "condition": "Indoor"},
                "last_reading_at": now,
            },
            {
                "id": "mock_battery",
                "type": "battery",
                "name": "Battery Monitor",
                "driver": "mock.battery",
                "status": "online",
                "last_value": {
                    "level": self._battery_level,
                    "charging": self._battery_charging,
                    "voltage": self._battery_voltage,
                },
                "last_reading_at": now,
            },
        ]
        self.sensorsChanged.emit()
