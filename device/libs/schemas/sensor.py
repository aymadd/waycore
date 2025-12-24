from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import Field

from .base import BaseMessage


class FixQuality(str, Enum):
    no_fix = "no_fix"
    gps = "gps"
    dgps = "dgps"
    pps = "pps"
    rtk = "rtk"
    float_rtk = "float_rtk"


class GPSPosition(BaseMessage):
    """
    GPS position update.
    Topic: sensor/gps/position
    """

    latitude: float = Field(..., ge=-90, le=90, description="Latitude in degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in degrees")
    altitude_meters: float | None = Field(default=None, description="Altitude in meters")
    speed_kmh: float | None = Field(default=None, ge=0, description="Speed in km/h")
    heading_degrees: float | None = Field(default=None, ge=0, le=360, description="Heading degrees")
    hdop: float | None = Field(default=None, ge=0, description="Horizontal DOP")
    satellites: int = Field(..., ge=0, le=32, description="Number of satellites")
    fix_quality: FixQuality = Field(..., description="Fix quality")


class SensorData(BaseMessage):
    """
    Generic sensor reading.
    Topic: sensor/{sensor_id}/data
    """

    sensor_id: str = Field(..., min_length=1, description="Unique sensor identifier")
    sensor_type: str = Field(..., min_length=1, description="Sensor type")
    value: float | int | str | bool | list[float] = Field(..., description="Sensor value")
    unit: str = Field(..., min_length=1, description="Measurement unit")
    accuracy: float | None = Field(default=None, ge=0, description="Estimated accuracy")


class SensorStatus(BaseMessage):
    """
    Sensor status change.
    Topic: sensor/{sensor_id}/status
    """

    sensor_id: str = Field(..., min_length=1)
    sensor_type: str = Field(..., min_length=1)
    available: bool = Field(..., description="Sensor available")
    healthy: bool = Field(..., description="Sensor healthy")
    error_message: str | None = Field(default=None, description="Error details")
    last_reading: datetime | None = Field(default=None, description="Timestamp of last reading")
