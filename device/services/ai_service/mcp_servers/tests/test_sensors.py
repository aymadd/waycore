"""Tests for sensors MCP server."""

from __future__ import annotations

import os

import pytest

# Set mock data mode for tests
os.environ["USE_MOCK_DATA"] = "true"

from device.services.ai_service.mcp_servers.sensors import (
    _heading_to_cardinal,
    call_tool,
    list_tools,
)


class TestListTools:
    """Tests for list_tools function."""

    @pytest.mark.asyncio
    async def test_lists_all_tools(self) -> None:
        """Test that all expected tools are listed."""
        tools = await list_tools()
        tool_names = [t.name for t in tools]

        assert "get_temperature" in tool_names
        assert "get_location" in tool_names
        assert "get_compass_heading" in tool_names
        assert "get_altitude" in tool_names
        assert "get_battery_status" in tool_names
        assert "get_device_time" in tool_names
        assert "get_all_sensors" in tool_names
        assert "get_weather_conditions" in tool_names

    @pytest.mark.asyncio
    async def test_tools_have_descriptions(self) -> None:
        """Test that all tools have descriptions."""
        tools = await list_tools()
        for tool in tools:
            assert tool.description is not None
            assert len(tool.description) > 0

    @pytest.mark.asyncio
    async def test_tools_have_input_schemas(self) -> None:
        """Test that all tools have input schemas."""
        tools = await list_tools()
        for tool in tools:
            assert tool.inputSchema is not None
            assert tool.inputSchema.get("type") == "object"


class TestHeadingToCardinal:
    """Tests for _heading_to_cardinal helper function."""

    def test_north(self) -> None:
        """Test North direction."""
        assert _heading_to_cardinal(0) == "N"
        assert _heading_to_cardinal(360) == "N"

    def test_south(self) -> None:
        """Test South direction."""
        assert _heading_to_cardinal(180) == "S"

    def test_east(self) -> None:
        """Test East direction."""
        assert _heading_to_cardinal(90) == "E"

    def test_west(self) -> None:
        """Test West direction."""
        assert _heading_to_cardinal(270) == "W"

    def test_northeast(self) -> None:
        """Test Northeast direction."""
        assert _heading_to_cardinal(45) == "NE"

    def test_intermediate_directions(self) -> None:
        """Test intermediate directions (16-point compass)."""
        assert _heading_to_cardinal(22.5) == "NNE"
        assert _heading_to_cardinal(67.5) == "ENE"
        assert _heading_to_cardinal(135) == "SE"


class TestCallTool:
    """Tests for call_tool function."""

    @pytest.mark.asyncio
    async def test_get_temperature_celsius(self) -> None:
        """Test getting temperature in celsius."""
        result = await call_tool("get_temperature", {"unit": "celsius"})

        assert len(result) == 1
        assert "°C" in result[0].text
        assert "temperature" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_get_temperature_fahrenheit(self) -> None:
        """Test getting temperature in fahrenheit."""
        result = await call_tool("get_temperature", {"unit": "fahrenheit"})

        assert len(result) == 1
        assert "°F" in result[0].text
        # Should also include Celsius for reference
        assert "°C" in result[0].text

    @pytest.mark.asyncio
    async def test_get_temperature_default(self) -> None:
        """Test getting temperature with default unit."""
        result = await call_tool("get_temperature", {})

        assert len(result) == 1
        # Default is celsius, which should appear first
        text = result[0].text
        assert "°C" in text

    @pytest.mark.asyncio
    async def test_get_location(self) -> None:
        """Test getting GPS location."""
        result = await call_tool("get_location", {})

        assert len(result) == 1
        text = result[0].text
        assert "Latitude" in text
        assert "Longitude" in text
        assert "location" in text.lower()

    @pytest.mark.asyncio
    async def test_get_location_includes_elevation(self) -> None:
        """Test that location includes elevation when available."""
        result = await call_tool("get_location", {})

        text = result[0].text
        # Mock data includes elevation
        assert "Elevation" in text or "elevation" in text.lower()

    @pytest.mark.asyncio
    async def test_get_compass_heading(self) -> None:
        """Test getting compass heading."""
        result = await call_tool("get_compass_heading", {})

        assert len(result) == 1
        text = result[0].text
        assert "heading" in text.lower()
        # Should include cardinal direction
        assert "°" in text

    @pytest.mark.asyncio
    async def test_get_altitude_meters(self) -> None:
        """Test getting altitude in meters."""
        result = await call_tool("get_altitude", {"unit": "meters"})

        assert len(result) == 1
        text = result[0].text
        assert "Altitude" in text
        assert "m" in text

    @pytest.mark.asyncio
    async def test_get_altitude_feet(self) -> None:
        """Test getting altitude in feet."""
        result = await call_tool("get_altitude", {"unit": "feet"})

        assert len(result) == 1
        text = result[0].text
        assert "ft" in text

    @pytest.mark.asyncio
    async def test_get_altitude_includes_pressure(self) -> None:
        """Test that altitude includes barometric pressure."""
        result = await call_tool("get_altitude", {})

        text = result[0].text
        assert "hPa" in text or "pressure" in text.lower()

    @pytest.mark.asyncio
    async def test_get_battery_status(self) -> None:
        """Test getting battery status."""
        result = await call_tool("get_battery_status", {})

        assert len(result) == 1
        text = result[0].text
        assert "Battery" in text
        assert "%" in text

    @pytest.mark.asyncio
    async def test_get_battery_includes_voltage(self) -> None:
        """Test that battery status includes voltage."""
        result = await call_tool("get_battery_status", {})

        text = result[0].text
        assert "V" in text or "voltage" in text.lower()

    @pytest.mark.asyncio
    async def test_get_device_time(self) -> None:
        """Test getting device time."""
        result = await call_tool("get_device_time", {})

        assert len(result) == 1
        text = result[0].text
        assert "time" in text.lower()
        assert ":" in text  # Time format HH:MM:SS

    @pytest.mark.asyncio
    async def test_get_device_time_includes_date(self) -> None:
        """Test that device time includes date."""
        result = await call_tool("get_device_time", {})

        text = result[0].text
        assert "Date" in text

    @pytest.mark.asyncio
    async def test_get_all_sensors(self) -> None:
        """Test getting all sensor data."""
        result = await call_tool("get_all_sensors", {})

        assert len(result) == 1
        text = result[0].text
        # Should include key sensor readings
        assert "GPS" in text or "gps" in text.lower()
        assert "Compass" in text or "compass" in text.lower()
        assert "Battery" in text or "battery" in text.lower()

    @pytest.mark.asyncio
    async def test_get_all_sensors_formatted(self) -> None:
        """Test that all sensors output is well-formatted."""
        result = await call_tool("get_all_sensors", {})

        text = result[0].text
        # Should have header and separator
        assert "Sensor" in text or "📊" in text

    @pytest.mark.asyncio
    async def test_get_weather_conditions(self) -> None:
        """Test getting weather conditions."""
        result = await call_tool("get_weather_conditions", {})

        assert len(result) == 1
        text = result[0].text
        assert "Temperature" in text

    @pytest.mark.asyncio
    async def test_get_weather_includes_pressure(self) -> None:
        """Test that weather includes pressure."""
        result = await call_tool("get_weather_conditions", {})

        text = result[0].text
        assert "Pressure" in text or "hPa" in text

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_error(self) -> None:
        """Test that unknown tool returns error message."""
        result = await call_tool("nonexistent_tool", {})

        assert len(result) == 1
        assert "Unknown tool" in result[0].text


class TestMockDataConsistency:
    """Tests to verify mock data is consistent and realistic."""

    @pytest.mark.asyncio
    async def test_temperature_in_reasonable_range(self) -> None:
        """Test that mock temperature is in a reasonable range."""
        result = await call_tool("get_temperature", {"unit": "celsius"})

        text = result[0].text
        # Extract temperature value - look for pattern like "23.5°C"
        import re

        match = re.search(r"([\d.]+)°C", text)
        assert match is not None
        temp = float(match.group(1))
        # Reasonable indoor/outdoor temperature range
        assert -40 <= temp <= 60

    @pytest.mark.asyncio
    async def test_battery_percentage_valid(self) -> None:
        """Test that battery percentage is valid (0-100)."""
        result = await call_tool("get_battery_status", {})

        text = result[0].text
        import re

        match = re.search(r"(\d+)%", text)
        assert match is not None
        level = int(match.group(1))
        assert 0 <= level <= 100

    @pytest.mark.asyncio
    async def test_compass_heading_valid(self) -> None:
        """Test that compass heading is valid (0-360)."""
        result = await call_tool("get_compass_heading", {})

        text = result[0].text
        import re

        match = re.search(r"(\d+(?:\.\d+)?)°", text)
        assert match is not None
        heading = float(match.group(1))
        assert 0 <= heading < 360

    @pytest.mark.asyncio
    async def test_gps_coordinates_valid(self) -> None:
        """Test that GPS coordinates are valid."""
        result = await call_tool("get_location", {})

        text = result[0].text
        import re

        # Extract latitude
        lat_match = re.search(r"Latitude:\s*([\d.]+)°", text)
        assert lat_match is not None
        lat = float(lat_match.group(1))
        assert 0 <= lat <= 90

        # Extract longitude
        lon_match = re.search(r"Longitude:\s*([\d.]+)°", text)
        assert lon_match is not None
        lon = float(lon_match.group(1))
        assert 0 <= lon <= 180
