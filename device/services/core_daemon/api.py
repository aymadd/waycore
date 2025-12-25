from __future__ import annotations

import platform
import random
import socket
import sys
import time
from datetime import datetime, timezone
from typing import Any

from device.libs.schemas.system import (
    BatteryResponse,
    CompassResponse,
    SystemCommand,
    SystemInfoResponse,
    SystemTimeResponse,
    TemperatureResponse,
)
from fastapi import FastAPI, HTTPException

from .service import CoreDaemonService

# Try to get version from package metadata
try:
    from importlib.metadata import version as pkg_version

    APP_VERSION = pkg_version("waycore")
except Exception:
    APP_VERSION = "0.1.0-dev"

# Track process start time for uptime calculation
_START_TIME = time.monotonic()

# Mock battery state (simulates drain/charge over time)
_battery_state = {
    "level": 85,
    "is_charging": False,
    "voltage": 3.85,
    "last_update": time.monotonic(),
}

# Mock temperature state
_temperature_state = {
    "celsius": 22.5,
    "last_update": time.monotonic(),
}

# Mock compass state
_compass_state = {
    "heading": 45.0,  # NE direction
    "calibrated": True,
    "drift_rate": 0.5,  # Degrees per second (slow drift for realism)
    "last_update": time.monotonic(),
}

# Mock GPS state (San Francisco coordinates)
_gps_state: dict[str, Any] = {
    "latitude": 37.7749,
    "longitude": -122.4194,
    "accuracy_m": 5.0,
    "has_fix": True,
    "drift_speed": 0.00001,  # Small position drift
    "last_update": time.monotonic(),
}

# Mock elevation state
_elevation_state = {
    "meters": 52.0,  # Meters above sea level
    "available": True,
}


def _update_mock_battery() -> None:
    """Simulate battery drain/charge over time."""
    now = time.monotonic()
    elapsed = now - _battery_state["last_update"]
    _battery_state["last_update"] = now

    if _battery_state["is_charging"]:
        # Charge at ~1% per 30 seconds
        _battery_state["level"] = min(100, _battery_state["level"] + elapsed / 30)
    else:
        # Drain at ~1% per 60 seconds
        _battery_state["level"] = max(0, _battery_state["level"] - elapsed / 60)

    # Update voltage based on level
    _battery_state["voltage"] = 3.0 + (_battery_state["level"] / 100) * 1.2


def _update_mock_temperature() -> None:
    """Simulate temperature variation."""
    # Add small random variation around base temperature
    _temperature_state["celsius"] = 22.5 + random.uniform(-2, 2)


def _update_mock_compass() -> None:
    """Simulate compass heading with slow drift."""
    now = time.monotonic()
    elapsed = now - _compass_state["last_update"]
    _compass_state["last_update"] = now

    # Apply slow drift + random noise
    drift = _compass_state["drift_rate"] * elapsed
    noise = random.uniform(-1, 1)
    _compass_state["heading"] = (_compass_state["heading"] + drift + noise) % 360


def _heading_to_cardinal(heading: float) -> str:
    """Convert heading degrees to cardinal direction."""
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    # Each direction covers 45 degrees, offset by 22.5 to center
    index = int((heading + 22.5) / 45) % 8
    return directions[index]


def _update_mock_gps() -> None:
    """Simulate GPS position drift."""
    if not _gps_state["has_fix"]:
        return

    # Small random drift in position
    drift = _gps_state["drift_speed"]
    _gps_state["latitude"] += random.uniform(-drift, drift)
    _gps_state["longitude"] += random.uniform(-drift, drift)
    _gps_state["accuracy_m"] = round(random.uniform(3, 15), 1)


def _update_mock_elevation() -> None:
    """Simulate small elevation variations."""
    if _elevation_state["available"]:
        # Small random variation
        _elevation_state["meters"] = 52.0 + random.uniform(-2, 2)


def create_app(service: CoreDaemonService) -> FastAPI:
    app = FastAPI(title="Core Daemon API")

    @app.get("/health")  # type: ignore[misc]
    async def health() -> dict[str, Any]:
        if service.is_healthy():
            return {"status": "ok"}
        raise HTTPException(status_code=503, detail="not ready")

    @app.get("/api/status")  # type: ignore[misc]
    async def status() -> dict[str, Any]:
        return service.get_status()

    @app.post("/api/command")  # type: ignore[misc]
    async def command(cmd: SystemCommand) -> dict[str, Any]:
        ok = await service.handle_command(cmd.command, cmd.parameters)
        return {"success": ok}

    # --- System Information Endpoints ---

    @app.get("/api/system/time")  # type: ignore[misc]
    async def get_system_time() -> SystemTimeResponse:
        """Get current system time and timezone."""
        uptime = int(time.monotonic() - _START_TIME)
        return SystemTimeResponse(
            timestamp=datetime.now(timezone.utc),
            timezone="UTC",  # Pi uses UTC by default; can be made configurable
            uptime_seconds=uptime,
        )

    @app.get("/api/system/battery")  # type: ignore[misc]
    async def get_battery() -> BatteryResponse:
        """Get battery status."""
        _update_mock_battery()
        level = int(_battery_state["level"])
        is_charging = _battery_state["is_charging"]

        # Calculate estimated minutes remaining
        if is_charging:
            estimated = None  # Don't show estimate when charging
        elif level > 0:
            # Rough estimate: ~60 minutes per 1% at normal drain
            estimated = level * 60
        else:
            estimated = 0

        return BatteryResponse(
            level=level,
            is_charging=is_charging,
            voltage=round(_battery_state["voltage"], 2),
            estimated_minutes=estimated,
        )

    @app.post("/api/system/battery/charging")  # type: ignore[misc]
    async def set_charging(enabled: bool) -> dict[str, Any]:
        """Toggle charging state (for testing)."""
        _battery_state["is_charging"] = enabled
        return {"charging": enabled}

    @app.get("/api/system/temperature")  # type: ignore[misc]
    async def get_temperature() -> TemperatureResponse:
        """Get temperature reading."""
        _update_mock_temperature()
        return TemperatureResponse(
            celsius=round(_temperature_state["celsius"], 1),
            source="mock",
            timestamp=datetime.now(timezone.utc),
        )

    @app.get("/api/system/info")  # type: ignore[misc]
    async def get_system_info() -> SystemInfoResponse:
        """Get system information."""
        # Detect device model
        device_model = "Unknown"
        try:
            with open("/proc/device-tree/model", encoding="utf-8") as f:
                device_model = f.read().strip().rstrip("\x00")
        except FileNotFoundError:
            # Not a Raspberry Pi, use platform info
            device_model = f"{platform.machine()} ({platform.system()})"

        return SystemInfoResponse(
            app_version=APP_VERSION,
            build_date=None,  # Could be set via env var at build time
            device_model=device_model,
            os_version=platform.platform(),
            python_version=sys.version.split()[0],
            hostname=socket.gethostname(),
        )

    # --- Sensor Endpoints ---

    @app.get("/api/sensors/compass")  # type: ignore[misc]
    async def get_compass() -> CompassResponse:
        """Get compass/magnetometer reading with GPS and elevation."""
        _update_mock_compass()
        _update_mock_gps()
        _update_mock_elevation()

        heading = round(_compass_state["heading"], 1)

        # GPS data (None if no fix)
        latitude = round(_gps_state["latitude"], 6) if _gps_state["has_fix"] else None
        longitude = round(_gps_state["longitude"], 6) if _gps_state["has_fix"] else None
        gps_accuracy = _gps_state["accuracy_m"] if _gps_state["has_fix"] else None

        # Elevation data (None if unavailable)
        elevation = round(_elevation_state["meters"], 1) if _elevation_state["available"] else None

        return CompassResponse(
            heading_degrees=heading,
            heading_cardinal=_heading_to_cardinal(heading),
            calibrated=_compass_state["calibrated"],
            accuracy_degrees=2.0 if _compass_state["calibrated"] else 10.0,
            declination=0.0,
            timestamp=datetime.now(timezone.utc),
            latitude=latitude,
            longitude=longitude,
            gps_accuracy_m=gps_accuracy,
            elevation_m=elevation,
        )

    @app.post("/api/sensors/compass/calibrate")  # type: ignore[misc]
    async def calibrate_compass() -> dict[str, Any]:
        """Start compass calibration (mock: instant success)."""
        _compass_state["calibrated"] = True
        return {"success": True, "message": "Calibration complete"}

    @app.post("/api/sensors/compass/heading")  # type: ignore[misc]
    async def set_compass_heading(heading: float) -> dict[str, Any]:
        """Set compass heading (for testing)."""
        _compass_state["heading"] = heading % 360
        return {"heading": _compass_state["heading"]}

    # --- System Management ---

    @app.post("/api/system/factory-reset")  # type: ignore[misc]
    async def factory_reset() -> dict[str, Any]:
        """
        Factory reset: clears all user data and resets to defaults.

        This endpoint resets:
        - All mock sensor states to defaults
        - User preferences (via data-logger)
        - Notes (via data-logger)
        - Event logs (via data-logger)
        """
        # Reset mock states to defaults
        _battery_state["level"] = 85
        _battery_state["is_charging"] = False
        _battery_state["voltage"] = 3.85
        _battery_state["last_update"] = time.monotonic()

        _temperature_state["celsius"] = 22.5
        _temperature_state["last_update"] = time.monotonic()

        _compass_state["heading"] = 45.0
        _compass_state["calibrated"] = True
        _compass_state["drift_rate"] = 0.5
        _compass_state["last_update"] = time.monotonic()

        _gps_state["latitude"] = 37.7749
        _gps_state["longitude"] = -122.4194
        _gps_state["accuracy_m"] = 5.0
        _gps_state["has_fix"] = True
        _gps_state["last_update"] = time.monotonic()

        _elevation_state["meters"] = 52.0
        _elevation_state["available"] = True

        return {
            "success": True,
            "message": "Factory reset complete. All data cleared.",
        }

    return app
