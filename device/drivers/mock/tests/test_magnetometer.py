from __future__ import annotations

import pytest
from device.drivers.mock.magnetometer import MockMagnetometer
from device.libs.hil.interfaces.magnetometer import CalibrationStatus


@pytest.mark.asyncio
async def test_magnetometer_initialize() -> None:
    """Test magnetometer initialization."""
    mag = MockMagnetometer({"initial_heading": 45.0})
    assert not mag.is_ready

    result = await mag.initialize()
    assert result is True
    assert mag.is_ready
    assert mag.calibration_status == CalibrationStatus.calibrated


@pytest.mark.asyncio
async def test_magnetometer_read_heading() -> None:
    """Test reading heading values."""
    mag = MockMagnetometer({"initial_heading": 90.0, "noise_amplitude": 0.0})
    await mag.initialize()

    reading = await mag.read()
    assert reading is not None
    assert 89.0 <= reading.heading_degrees <= 91.0  # Allow small variance
    assert reading.calibration_status == CalibrationStatus.calibrated
    assert reading.timestamp is not None


@pytest.mark.asyncio
async def test_magnetometer_heading_range() -> None:
    """Test that heading stays within 0-360 range."""
    mag = MockMagnetometer({"initial_heading": 359.0, "drift_rate": 10.0, "noise_amplitude": 0.0})
    await mag.initialize()

    # Wait for drift to wrap around
    import asyncio

    await asyncio.sleep(0.2)

    reading = await mag.read()
    assert reading is not None
    assert 0 <= reading.heading_degrees < 360


@pytest.mark.asyncio
async def test_magnetometer_calibration() -> None:
    """Test calibration process."""
    mag = MockMagnetometer({})
    await mag.initialize()

    # Start calibration
    started = await mag.start_calibration()
    assert started is True
    assert mag.calibration_status == CalibrationStatus.calibrating

    # Wait for calibration to complete
    import asyncio

    await asyncio.sleep(3.5)

    assert mag.calibration_status == CalibrationStatus.calibrated


@pytest.mark.asyncio
async def test_magnetometer_cancel_calibration() -> None:
    """Test cancelling calibration."""
    mag = MockMagnetometer({})
    await mag.initialize()

    await mag.start_calibration()
    assert mag.calibration_status == CalibrationStatus.calibrating

    await mag.cancel_calibration()
    assert mag.calibration_status == CalibrationStatus.needs_calibration


@pytest.mark.asyncio
async def test_magnetometer_declination() -> None:
    """Test magnetic declination property."""
    mag = MockMagnetometer({"declination": 5.0})
    assert mag.magnetic_declination == 5.0

    mag.magnetic_declination = 10.0
    assert mag.magnetic_declination == 10.0


@pytest.mark.asyncio
async def test_magnetometer_set_heading() -> None:
    """Test setting heading externally."""
    mag = MockMagnetometer({"noise_amplitude": 0.0})
    await mag.initialize()

    mag.set_heading(180.0)
    reading = await mag.read()
    assert reading is not None
    assert 179.0 <= reading.heading_degrees <= 181.0


@pytest.mark.asyncio
async def test_magnetometer_not_ready() -> None:
    """Test reading before initialization returns None."""
    mag = MockMagnetometer({})
    reading = await mag.read()
    assert reading is None
