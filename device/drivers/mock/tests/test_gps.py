from __future__ import annotations

import pytest
from device.drivers.mock.gps import MockGPS
from device.libs.hil.interfaces.gps import GPSFixType


@pytest.mark.asyncio
async def test_gps_initialize() -> None:
    """Test GPS initialization."""
    gps = MockGPS({"latitude": 40.7128, "longitude": -74.0060})
    assert not gps.is_ready
    assert not gps.has_fix

    result = await gps.initialize()
    assert result is True
    assert gps.is_ready
    assert gps.has_fix


@pytest.mark.asyncio
async def test_gps_read_position() -> None:
    """Test reading GPS position."""
    gps = MockGPS(
        {"latitude": 40.7128, "longitude": -74.0060, "altitude": 50.0, "drift_enabled": False}
    )
    await gps.initialize()

    reading = await gps.read()
    assert reading is not None
    assert reading.latitude == 40.7128
    assert reading.longitude == -74.006
    assert reading.altitude_m == 50.0
    assert reading.fix_type == GPSFixType.fix_3d
    assert reading.satellites >= 6


@pytest.mark.asyncio
async def test_gps_no_fix_returns_none() -> None:
    """Test that read returns None when no fix."""
    gps = MockGPS({})
    await gps.initialize()

    gps.set_fix(False)
    reading = await gps.read()
    assert reading is None


@pytest.mark.asyncio
async def test_gps_drift() -> None:
    """Test GPS position drift."""
    gps = MockGPS(
        {"latitude": 40.0, "longitude": -74.0, "drift_enabled": True, "drift_speed": 0.01}
    )
    await gps.initialize()

    # Read multiple times
    readings = [await gps.read() for _ in range(5)]

    # Position should change with drift
    lats = [r.latitude for r in readings if r]
    assert len(set(lats)) > 1  # Not all the same


@pytest.mark.asyncio
async def test_gps_set_position() -> None:
    """Test setting position externally."""
    gps = MockGPS({"drift_enabled": False})
    await gps.initialize()

    gps.set_position(51.5074, -0.1278, 25.0)  # London
    reading = await gps.read()

    assert reading is not None
    assert reading.latitude == 51.5074
    assert reading.longitude == -0.1278
    assert reading.altitude_m == 25.0
