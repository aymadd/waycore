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
        """Get compass/magnetometer reading."""
        _update_mock_compass()
        heading = round(_compass_state["heading"], 1)
        return CompassResponse(
            heading_degrees=heading,
            heading_cardinal=_heading_to_cardinal(heading),
            calibrated=_compass_state["calibrated"],
            accuracy_degrees=2.0 if _compass_state["calibrated"] else 10.0,
            declination=0.0,  # Could be configurable per location
            timestamp=datetime.now(timezone.utc),
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

    return app
