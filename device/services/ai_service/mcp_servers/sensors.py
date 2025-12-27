"""MCP Server for device sensor access.

This server provides tools for reading sensor data from the device,
including temperature, GPS, compass, battery, and other sensor readings.

The AI agent uses these tools to answer questions like:
- "What's the temperature?"
- "Where am I?"
- "What's the battery level?"
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any

import httpx
from mcp.server import Server
from mcp.types import TextContent, Tool

from .base import main_with_server

logger = logging.getLogger(__name__)

# Create the MCP server
server = Server("waycore-sensors")

# Configuration - Core Daemon provides sensor and system data
CORE_DAEMON_URL = os.getenv("CORE_DAEMON_URL", "http://localhost:8000")
USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "false").lower() == "true"

# HTTP client timeout for sensor requests
REQUEST_TIMEOUT = 5.0


def _heading_to_cardinal(heading: float) -> str:
    """Convert heading degrees to cardinal direction (16-point compass)."""
    directions = [
        "N",
        "NNE",
        "NE",
        "ENE",
        "E",
        "ESE",
        "SE",
        "SSE",
        "S",
        "SSW",
        "SW",
        "WSW",
        "W",
        "WNW",
        "NW",
        "NNW",
    ]
    idx = round(heading / 22.5) % 16
    return directions[idx]


async def _fetch_endpoint(endpoint: str) -> dict[str, Any] | None:
    """Fetch data from a core daemon endpoint.

    Args:
        endpoint: API endpoint path (e.g., "/api/system/temperature").

    Returns:
        Response JSON as dict, or None on error.
    """
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.get(f"{CORE_DAEMON_URL}{endpoint}")
            if response.status_code == 200:
                result: dict[str, Any] = response.json()
                return result
            logger.warning(f"API {endpoint} returned {response.status_code}")
            return None
    except httpx.TimeoutException:
        logger.error(f"Timeout fetching {endpoint}")
        return None
    except Exception as e:
        logger.error(f"Failed to fetch {endpoint}: {e}")
        return None


# --- Mock Data for Development ---


def _get_mock_temperature() -> dict[str, Any]:
    """Get mock temperature data."""
    return {"celsius": 23.5, "source": "mock"}


def _get_mock_compass() -> dict[str, Any]:
    """Get mock compass/GPS/elevation data."""
    return {
        "heading_degrees": 45.0,
        "heading_cardinal": "NE",
        "calibrated": True,
        "latitude": 37.7749,
        "longitude": -122.4194,
        "gps_accuracy_m": 5.0,
        "elevation_m": 52.0,
    }


def _get_mock_battery() -> dict[str, Any]:
    """Get mock battery data."""
    return {
        "level": 85,
        "is_charging": False,
        "voltage": 3.85,
        "estimated_minutes": 85 * 60,  # ~60 min per 1%
    }


def _get_mock_pressure() -> dict[str, Any]:
    """Get mock barometric pressure data."""
    return {"hPa": 1013.25, "altitude_m": 52.0}


@server.list_tools()  # type: ignore[misc]
async def list_tools() -> list[Tool]:
    """List available sensor tools.

    Returns tools for accessing device sensors:
    - Temperature, GPS, compass, altitude
    - Battery status and device time
    - Combined sensor readings
    """
    return [
        Tool(
            name="get_temperature",
            description="Get the current temperature reading from the device sensor",
            inputSchema={
                "type": "object",
                "properties": {
                    "unit": {
                        "type": "string",
                        "description": "Temperature unit (celsius or fahrenheit)",
                        "enum": ["celsius", "fahrenheit"],
                        "default": "celsius",
                    }
                },
            },
        ),
        Tool(
            name="get_location",
            description="Get the current GPS coordinates (latitude, longitude, altitude, accuracy)",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_compass_heading",
            description="Get the current compass heading in degrees and cardinal direction",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_altitude",
            description="Get the current altitude from barometric altimeter (pressure sensor)",
            inputSchema={
                "type": "object",
                "properties": {
                    "unit": {
                        "type": "string",
                        "description": "Altitude unit (meters or feet)",
                        "enum": ["meters", "feet"],
                        "default": "meters",
                    }
                },
            },
        ),
        Tool(
            name="get_battery_status",
            description=(
                "Get the device battery level, charging status, and estimated time remaining"
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_device_time",
            description="Get the current device date, time, and timezone",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_all_sensors",
            description=(
                "Get readings from all available sensors at once "
                "(temperature, GPS, compass, altitude, battery)"
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_weather_conditions",
            description=(
                "Get current weather-related sensor data "
                "(temperature, barometric pressure, altitude)"
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@server.call_tool()  # type: ignore[misc]
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Execute a sensor tool.

    Fetches data from the Core Daemon API or uses mock data in development.

    Args:
        name: Tool name.
        arguments: Tool arguments.

    Returns:
        List of TextContent with the formatted result.
    """
    handlers = {
        "get_temperature": _handle_temperature,
        "get_location": _handle_location,
        "get_compass_heading": _handle_compass,
        "get_altitude": _handle_altitude,
        "get_battery_status": _handle_battery,
        "get_device_time": _handle_time,
        "get_all_sensors": _handle_all_sensors,
        "get_weather_conditions": _handle_weather,
    }

    handler = handlers.get(name)
    if not handler:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

    result = await handler(arguments)
    return [TextContent(type="text", text=result)]


async def _handle_temperature(arguments: dict[str, Any]) -> str:
    """Handle get_temperature tool call."""
    unit = arguments.get("unit", "celsius")

    data: dict[str, Any] | None
    if USE_MOCK_DATA:
        data = _get_mock_temperature()
    else:
        data = await _fetch_endpoint("/api/system/temperature")

    if not data:
        return "Temperature sensor unavailable"

    temp_c = data.get("celsius", 0.0)
    temp_f = temp_c * 9 / 5 + 32

    if unit == "fahrenheit":
        return f"Current temperature: {temp_f:.1f}°F ({temp_c:.1f}°C)"
    return f"Current temperature: {temp_c:.1f}°C ({temp_f:.1f}°F)"


async def _handle_location(arguments: dict[str, Any]) -> str:
    """Handle get_location tool call."""
    data: dict[str, Any] | None
    if USE_MOCK_DATA:
        data = _get_mock_compass()
    else:
        # Compass endpoint includes GPS data
        data = await _fetch_endpoint("/api/sensors/compass")

    if not data:
        return "GPS unavailable"

    lat = data.get("latitude")
    lon = data.get("longitude")

    if lat is None or lon is None:
        return "No GPS fix available"

    # Format coordinates with direction indicators
    lat_dir = "N" if lat >= 0 else "S"
    lon_dir = "E" if lon >= 0 else "W"

    elevation = data.get("elevation_m")
    accuracy = data.get("gps_accuracy_m")

    lines = [
        "Current location:",
        f"  Latitude: {abs(lat):.6f}° {lat_dir}",
        f"  Longitude: {abs(lon):.6f}° {lon_dir}",
    ]

    if elevation is not None:
        lines.append(f"  Elevation: {elevation:.0f}m ({elevation * 3.28084:.0f}ft)")

    if accuracy is not None:
        lines.append(f"  Accuracy: ±{accuracy:.1f}m")

    return "\n".join(lines)


async def _handle_compass(arguments: dict[str, Any]) -> str:
    """Handle get_compass_heading tool call."""
    data: dict[str, Any] | None
    if USE_MOCK_DATA:
        data = _get_mock_compass()
    else:
        data = await _fetch_endpoint("/api/sensors/compass")

    if not data:
        return "Compass unavailable"

    heading = data.get("heading_degrees", 0.0)
    cardinal = data.get("heading_cardinal") or _heading_to_cardinal(heading)
    calibrated = data.get("calibrated", True)

    result = f"Compass heading: {heading:.0f}° ({cardinal})"
    if not calibrated:
        result += "\n⚠️ Compass needs calibration"

    return result


async def _handle_altitude(arguments: dict[str, Any]) -> str:
    """Handle get_altitude tool call."""
    unit = arguments.get("unit", "meters")

    if USE_MOCK_DATA:
        pressure_data = _get_mock_pressure()
        alt_m = pressure_data.get("altitude_m", 0.0)
        pressure = pressure_data.get("hPa", 1013.25)
    else:
        # Get elevation from compass endpoint (which includes GPS altitude)
        data = await _fetch_endpoint("/api/sensors/compass")
        if data and data.get("elevation_m") is not None:
            alt_m = data["elevation_m"]
            pressure = 1013.25  # Default, not provided in compass endpoint
        else:
            return "Altimeter unavailable"

    alt_ft = alt_m * 3.28084

    if unit == "feet":
        return f"Altitude: {alt_ft:.0f}ft ({alt_m:.0f}m)\nBarometric pressure: {pressure:.1f} hPa"
    return f"Altitude: {alt_m:.0f}m ({alt_ft:.0f}ft)\nBarometric pressure: {pressure:.1f} hPa"


async def _handle_battery(arguments: dict[str, Any]) -> str:
    """Handle get_battery_status tool call."""
    data: dict[str, Any] | None
    if USE_MOCK_DATA:
        data = _get_mock_battery()
    else:
        data = await _fetch_endpoint("/api/system/battery")

    if not data:
        return "Battery status unavailable"

    level = data.get("level", 0)
    is_charging = data.get("is_charging", False)
    voltage = data.get("voltage", 0.0)
    estimated_minutes = data.get("estimated_minutes")

    status = "⚡ Charging" if is_charging else "🔋 Discharging"

    lines = [
        f"Battery: {level}%",
        f"Status: {status}",
        f"Voltage: {voltage:.2f}V",
    ]

    if estimated_minutes and not is_charging:
        hours = estimated_minutes / 60
        lines.append(f"Estimated remaining: {hours:.1f} hours")

    return "\n".join(lines)


async def _handle_time(arguments: dict[str, Any]) -> str:
    """Handle get_device_time tool call."""
    if USE_MOCK_DATA:
        now = datetime.now()
        return (
            f"Current time: {now.strftime('%H:%M:%S')}\n"
            f"Date: {now.strftime('%A, %B %d, %Y')}\n"
            f"Timezone: {now.astimezone().tzname() or 'Local'}"
        )

    data = await _fetch_endpoint("/api/system/time")

    if not data:
        # Fallback to local time
        now = datetime.now()
        return (
            f"Current time: {now.strftime('%H:%M:%S')}\n"
            f"Date: {now.strftime('%A, %B %d, %Y')}\n"
            f"Timezone: Local"
        )

    # Parse the timestamp from the API
    timestamp_str = data.get("timestamp", "")
    timezone_name = data.get("timezone", "UTC")
    uptime_seconds = data.get("uptime_seconds", 0)

    try:
        # Handle ISO format timestamp
        if timestamp_str:
            if timestamp_str.endswith("Z"):
                timestamp_str = timestamp_str[:-1] + "+00:00"
            dt = datetime.fromisoformat(timestamp_str)
            time_str = dt.strftime("%H:%M:%S")
            date_str = dt.strftime("%A, %B %d, %Y")
        else:
            now = datetime.now()
            time_str = now.strftime("%H:%M:%S")
            date_str = now.strftime("%A, %B %d, %Y")
    except ValueError:
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        date_str = now.strftime("%A, %B %d, %Y")

    # Format uptime
    uptime_hours = uptime_seconds // 3600
    uptime_minutes = (uptime_seconds % 3600) // 60

    lines = [
        f"Current time: {time_str}",
        f"Date: {date_str}",
        f"Timezone: {timezone_name}",
    ]

    if uptime_seconds > 0:
        lines.append(f"Device uptime: {uptime_hours}h {uptime_minutes}m")

    return "\n".join(lines)


async def _handle_all_sensors(arguments: dict[str, Any]) -> str:
    """Handle get_all_sensors tool call."""
    lines = ["📊 Device Sensor Readings", "─" * 25]

    # Temperature
    temp_result = await _handle_temperature({})
    if "unavailable" not in temp_result.lower():
        temp_value = temp_result.split(":")[1].strip() if ":" in temp_result else temp_result
        lines.append(f"🌡️  {temp_value}")

    # Location
    compass_data: dict[str, Any] | None
    if USE_MOCK_DATA:
        compass_data = _get_mock_compass()
    else:
        compass_data = await _fetch_endpoint("/api/sensors/compass")

    if compass_data:
        lat = compass_data.get("latitude")
        lon = compass_data.get("longitude")
        if lat is not None and lon is not None:
            lat_dir = "N" if lat >= 0 else "S"
            lon_dir = "E" if lon >= 0 else "W"
            lines.append(f"📍 GPS: {abs(lat):.4f}°{lat_dir}, {abs(lon):.4f}°{lon_dir}")

        heading = compass_data.get("heading_degrees", 0)
        cardinal = compass_data.get("heading_cardinal") or _heading_to_cardinal(heading)
        lines.append(f"🧭 Compass: {heading:.0f}° ({cardinal})")

        elevation = compass_data.get("elevation_m")
        if elevation is not None:
            lines.append(f"⛰️  Elevation: {elevation:.0f}m")

    # Battery
    battery_data: dict[str, Any] | None
    if USE_MOCK_DATA:
        battery_data = _get_mock_battery()
    else:
        battery_data = await _fetch_endpoint("/api/system/battery")

    if battery_data:
        level = battery_data.get("level", 0)
        charging = battery_data.get("is_charging", False)
        icon = "⚡" if charging else "🔋"
        lines.append(f"{icon} Battery: {level}%")

    return "\n".join(lines)


async def _handle_weather(arguments: dict[str, Any]) -> str:
    """Handle get_weather_conditions tool call."""
    lines = ["🌤️ Weather Conditions", "─" * 20]

    # Temperature
    temp_data: dict[str, Any] | None
    if USE_MOCK_DATA:
        temp_data = _get_mock_temperature()
    else:
        temp_data = await _fetch_endpoint("/api/system/temperature")

    if temp_data:
        temp_c = temp_data.get("celsius", 0)
        temp_f = temp_c * 9 / 5 + 32
        lines.append(f"Temperature: {temp_c:.1f}°C ({temp_f:.1f}°F)")

    # Pressure/Altitude (from mock or compass endpoint)
    if USE_MOCK_DATA:
        pressure_data = _get_mock_pressure()
    else:
        # We don't have a dedicated pressure endpoint, use compass for elevation
        compass_data = await _fetch_endpoint("/api/sensors/compass")
        pressure_data = {"hPa": 1013.25}  # Default pressure
        if compass_data and compass_data.get("elevation_m"):
            pressure_data["altitude_m"] = compass_data["elevation_m"]

    if pressure_data:
        lines.append(f"Pressure: {pressure_data.get('hPa', 1013.25):.1f} hPa")
        alt = pressure_data.get("altitude_m")
        if alt:
            lines.append(f"Altitude: {alt:.0f}m")

    if len(lines) <= 2:
        return "Weather data unavailable"

    return "\n".join(lines)


if __name__ == "__main__":
    main_with_server(server)
