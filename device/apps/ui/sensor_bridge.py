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
