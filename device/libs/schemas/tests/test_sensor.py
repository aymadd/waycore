from __future__ import annotations

import pytest
from device.libs.schemas.sensor import FixQuality, GPSPosition, SensorData, SensorStatus
from pydantic import ValidationError


def test_gps_position_valid() -> None:
    pos = GPSPosition(
        source="core-daemon",
        latitude=30.0,
        longitude=-97.7,
        altitude_meters=200.5,
        speed_kmh=12.3,
        heading_degrees=180.0,
        hdop=0.9,
        satellites=8,
        fix_quality=FixQuality.gps,
    )
    assert pos.latitude == 30.0
    assert pos.fix_quality is FixQuality.gps


@pytest.mark.parametrize("lat", [-91.0, 91.0])
def test_gps_position_invalid_latitude(lat: float) -> None:
    with pytest.raises(ValidationError):
        GPSPosition(
            source="core-daemon",
            latitude=lat,
            longitude=0.0,
            satellites=0,
            fix_quality=FixQuality.no_fix,
        )


@pytest.mark.parametrize("lon", [-181.0, 181.0])
def test_gps_position_invalid_longitude(lon: float) -> None:
    with pytest.raises(ValidationError):
        GPSPosition(
            source="core-daemon",
            latitude=0.0,
            longitude=lon,
            satellites=0,
            fix_quality=FixQuality.no_fix,
        )


@pytest.mark.parametrize("heading", [-1.0, 361.0])
def test_gps_position_invalid_heading(heading: float) -> None:
    with pytest.raises(ValidationError):
        GPSPosition(
            source="core-daemon",
            latitude=0.0,
            longitude=0.0,
            heading_degrees=heading,
            satellites=0,
            fix_quality=FixQuality.no_fix,
        )


def test_sensor_data_valid() -> None:
    data = SensorData(
        source="module-manager",
        sensor_id="temp1",
        sensor_type="temperature",
        value=22.5,
        unit="celsius",
        accuracy=0.2,
    )
    assert data.value == 22.5
    assert data.unit == "celsius"


def test_sensor_status_valid() -> None:
    status = SensorStatus(
        source="module-manager",
        sensor_id="temp1",
        sensor_type="temperature",
        available=True,
        healthy=True,
    )
    assert status.available is True
    assert status.healthy is True
