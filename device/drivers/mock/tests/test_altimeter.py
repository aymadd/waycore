from __future__ import annotations

import pytest
from device.drivers.mock.altimeter import MockAltimeter


@pytest.mark.asyncio
async def test_altimeter_initialize() -> None:
    """Test altimeter initialization."""
    alt = MockAltimeter({"altitude": 500.0})
    assert not alt.is_ready

    result = await alt.initialize()
    assert result is True
    assert alt.is_ready
    assert alt.sensor_type == "altimeter"


@pytest.mark.asyncio
async def test_altimeter_read() -> None:
    """Test reading altitude."""
    alt = MockAltimeter({"altitude": 500.0, "noise": 0.0})
    await alt.initialize()

    reading = await alt.read()
    assert reading is not None
    assert reading.value == 500.0
    assert reading.unit == "m"
    assert reading.sensor_type == "altimeter"


@pytest.mark.asyncio
async def test_altimeter_not_ready() -> None:
    """Test reading before init returns None."""
    alt = MockAltimeter({})
    reading = await alt.read()
    assert reading is None


@pytest.mark.asyncio
async def test_altimeter_calibrate() -> None:
    """Test altitude calibration."""
    alt = MockAltimeter({"altitude": 100.0, "noise": 0.0})
    await alt.initialize()

    await alt.calibrate(250.0)
    reading = await alt.read()

    assert reading is not None
    assert reading.value == 250.0


@pytest.mark.asyncio
async def test_altimeter_noise() -> None:
    """Test altitude with noise."""
    alt = MockAltimeter({"altitude": 100.0, "noise": 5.0})
    await alt.initialize()

    readings = [await alt.read() for _ in range(10)]
    values = [r.value for r in readings if r]

    # Should have variation due to noise
    assert max(values) - min(values) > 0
