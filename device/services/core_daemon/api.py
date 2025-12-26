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

    # --- Storage Status ---

    @app.get("/api/system/storage")  # type: ignore[misc]
    async def get_storage_status() -> dict[str, Any]:
        """
        Get storage usage information.

        Returns breakdown of storage by category:
        - total_bytes: Total storage capacity (mocked for dev)
        - system_bytes: OS and system files (mocked)
        - apps_bytes: Application installation size (mocked)
        - data_bytes: User data (calculated from actual files)
        - available_bytes: Free space
        """
        from pathlib import Path

        # Mock total capacity (32GB eMMC typical for Raspberry Pi)
        # In production, use: shutil.disk_usage("/").total
        total_bytes = 32 * 1024 * 1024 * 1024  # 32 GB

        # Mock system/OS size (typical Raspberry Pi OS Lite ~2GB)
        system_bytes = 2 * 1024 * 1024 * 1024  # 2 GB

        # Mock application installation size (~500MB)
        apps_bytes = 500 * 1024 * 1024  # 500 MB

        # Calculate actual data usage from data directories
        data_bytes = 0
        data_breakdown: dict[str, int] = {}

        # Check common data directories
        data_dirs = [
            ("database", Path("/app/data") if Path("/app/data").exists() else Path("data")),
            ("logs", Path("/app/logs") if Path("/app/logs").exists() else Path("logs")),
            ("media", Path("/app/media") if Path("/app/media").exists() else Path("media")),
            ("cache", Path("/app/cache") if Path("/app/cache").exists() else Path("cache")),
        ]

        for name, dir_path in data_dirs:
            dir_size = 0
            if dir_path.exists():
                for f in dir_path.rglob("*"):
                    if f.is_file():
                        try:
                            dir_size += f.stat().st_size
                        except (OSError, PermissionError):
                            pass
            data_breakdown[name] = dir_size
            data_bytes += dir_size

        # Calculate available space
        available_bytes = total_bytes - system_bytes - apps_bytes - data_bytes
        if available_bytes < 0:
            available_bytes = 0

        # Calculate percentages
        used_bytes = system_bytes + apps_bytes + data_bytes
        used_percent = (used_bytes / total_bytes) * 100 if total_bytes > 0 else 0

        return {
            "total_bytes": total_bytes,
            "total_human": _format_bytes(total_bytes),
            "used_bytes": used_bytes,
            "used_human": _format_bytes(used_bytes),
            "used_percent": round(used_percent, 1),
            "available_bytes": available_bytes,
            "available_human": _format_bytes(available_bytes),
            "breakdown": {
                "system": {
                    "bytes": system_bytes,
                    "human": _format_bytes(system_bytes),
                    "description": "Operating system",
                },
                "apps": {
                    "bytes": apps_bytes,
                    "human": _format_bytes(apps_bytes),
                    "description": "Installed applications",
                },
                "data": {
                    "bytes": data_bytes,
                    "human": _format_bytes(data_bytes),
                    "description": "User data (notes, media, logs)",
                    "details": {
                        k: {"bytes": v, "human": _format_bytes(v)}
                        for k, v in data_breakdown.items()
                    },
                },
            },
        }

    def _format_bytes(size_bytes: int) -> str:
        """Format bytes to human-readable string."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

    # --- Sensor Registry ---

    @app.get("/api/sensors/registry")  # type: ignore[misc]
    async def get_all_sensors() -> list[dict[str, Any]]:
        """
        Get all registered sensors.

        Returns a list of sensor info including status, last reading, etc.
        """
        from device.libs.sensors import get_registry

        registry = get_registry()

        # If discovery hasn't run yet, run it now
        if not registry._discovery_complete:
            await registry.discover_sensors()

        # Update readings for each sensor with current mock values
        _update_sensor_readings(registry)

        return [s.to_dict() for s in registry.sensors]

    @app.get("/api/sensors/registry/{sensor_id}")  # type: ignore[misc]
    async def get_sensor(sensor_id: str) -> dict[str, Any]:
        """Get a specific sensor by ID."""
        from device.libs.sensors import get_registry

        registry = get_registry()
        sensor = registry.get_sensor(sensor_id)
        if not sensor:
            raise HTTPException(status_code=404, detail=f"Sensor {sensor_id} not found")
        return sensor.to_dict()

    @app.get("/api/sensors/registry/type/{sensor_type}")  # type: ignore[misc]
    async def get_sensors_by_type(sensor_type: str) -> list[dict[str, Any]]:
        """Get all sensors of a specific type."""
        from device.libs.sensors import SensorType, get_registry

        registry = get_registry()
        try:
            st = SensorType(sensor_type)
        except ValueError as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid sensor type: {sensor_type}"
            ) from e
        return [s.to_dict() for s in registry.get_sensors_by_type(st)]

    @app.post("/api/sensors/registry/discover")  # type: ignore[misc]
    async def discover_sensors() -> dict[str, Any]:
        """
        Run sensor discovery.

        This scans for available sensors and registers them.
        In mock mode, registers mock sensors for development.
        """
        from device.libs.sensors import get_registry

        registry = get_registry()
        registry.clear()  # Clear existing sensors before rediscovery
        discovered = await registry.discover_sensors()
        return {
            "success": True,
            "sensors_discovered": len(discovered),
            "mock_mode": registry.is_mock_mode,
            "sensors": [s.to_dict() for s in discovered],
        }

    def _update_sensor_readings(registry: Any) -> None:
        """Update sensor readings with current mock values."""
        from device.libs.sensors.registry import SensorStatus

        # Update GPS
        _update_mock_gps()
        registry.update_reading(
            "mock_gps",
            {
                "latitude": _gps_state["latitude"],
                "longitude": _gps_state["longitude"],
                "accuracy_m": _gps_state["accuracy_m"],
                "has_fix": _gps_state["has_fix"],
                "satellites": 8,
            },
            SensorStatus.ONLINE if _gps_state["has_fix"] else SensorStatus.ERROR,
        )

        # Update Temperature
        _update_mock_temperature()
        registry.update_reading(
            "mock_temp",
            {
                "celsius": _temperature_state["celsius"],
                "fahrenheit": _temperature_state["celsius"] * 9 / 5 + 32,
            },
            SensorStatus.ONLINE,
        )

        # Update Pressure (barometer)
        registry.update_reading(
            "mock_pressure",
            {"hPa": 1013.25, "altitude_m": _elevation_state["meters"]},
            SensorStatus.ONLINE,
        )

        # Update Accelerometer
        registry.update_reading(
            "mock_accel",
            {"x": 0.02, "y": -0.01, "z": 1.00, "unit": "g"},
            SensorStatus.ONLINE,
        )

        # Update Magnetometer
        _update_mock_compass()
        registry.update_reading(
            "mock_mag",
            {
                "heading": _compass_state["heading"],
                "cardinal": _heading_to_cardinal(_compass_state["heading"]),
                "calibrated": _compass_state["calibrated"],
            },
            SensorStatus.ONLINE if _compass_state["calibrated"] else SensorStatus.CALIBRATING,
        )

        # Update Light sensor
        registry.update_reading(
            "mock_light",
            {"lux": 350, "condition": "Indoor"},
            SensorStatus.ONLINE,
        )

        # Update Battery
        _update_mock_battery()
        registry.update_reading(
            "mock_battery",
            {
                "level": _battery_state["level"],
                "charging": _battery_state["is_charging"],
                "voltage": _battery_state["voltage"],
            },
            SensorStatus.ONLINE,
        )

    return app
