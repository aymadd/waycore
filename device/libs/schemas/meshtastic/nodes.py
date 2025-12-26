"""Meshtastic node schemas."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class NodeStatus(str, Enum):
    """Node online status."""

    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


class HardwareModel(str, Enum):
    """Known Meshtastic hardware models."""

    TBEAM = "tbeam"
    TBEAM_V07 = "tbeam_v0.7"
    TECHO = "techo"
    TLORA = "tlora"
    TLORA_V1 = "tlora_v1"
    TLORA_V2 = "tlora_v2"
    TLORA_V2_1_1P6 = "tlora_v2_1_1.6"
    HELTEC = "heltec"
    HELTEC_V2_0 = "heltec_v2.0"
    HELTEC_V2_1 = "heltec_v2.1"
    HELTEC_V3 = "heltec_v3"
    RAK4631 = "rak4631"
    RAK11200 = "rak11200"
    STATION_G1 = "station_g1"
    LORA_RELAY_V1 = "lora_relay_v1"
    NRF52_UNKNOWN = "nrf52_unknown"
    PRIVATE_HW = "private_hw"
    WAYCORE = "waycore"  # Our device
    UNKNOWN = "unknown"


class MeshPosition(BaseModel):
    """GPS position data for a mesh node."""

    latitude: float = Field(ge=-90, le=90, description="Latitude in degrees")
    longitude: float = Field(ge=-180, le=180, description="Longitude in degrees")
    altitude: int | None = Field(default=None, description="Altitude in meters")
    precision_bits: int = Field(default=32, ge=0, le=32, description="Position precision")
    time: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Position timestamp",
    )
    ground_speed: int | None = Field(default=None, ge=0, description="Speed in m/s")
    ground_track: int | None = Field(default=None, ge=0, le=360, description="Heading in degrees")
    sats_in_view: int | None = Field(default=None, ge=0, description="Satellites visible")

    model_config = {"frozen": True}


class MeshNodeCreate(BaseModel):
    """Schema for creating/registering a new mesh node."""

    node_id: str = Field(
        pattern=r"^![0-9a-fA-F]{8}$",
        description="Unique node ID (e.g., !a1b2c3d4)",
    )
    short_name: str = Field(
        min_length=1,
        max_length=4,
        description="Short display name (max 4 chars)",
    )
    long_name: str = Field(
        min_length=1,
        max_length=39,
        description="Full device name",
    )
    hardware: HardwareModel = Field(
        default=HardwareModel.UNKNOWN,
        description="Hardware model",
    )


class MeshNodeUpdate(BaseModel):
    """Schema for updating a mesh node."""

    short_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=4,
        description="Short display name",
    )
    long_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=39,
        description="Full device name",
    )
    position: MeshPosition | None = Field(default=None, description="Updated position")
    battery_level: int | None = Field(default=None, ge=0, le=100, description="Battery percentage")


class MeshNode(BaseModel):
    """A node on the mesh network."""

    node_id: str = Field(
        pattern=r"^![0-9a-fA-F]{8}$",
        description="Unique node ID (e.g., !a1b2c3d4)",
    )
    short_name: str = Field(
        min_length=1,
        max_length=4,
        description="Short display name (max 4 chars)",
    )
    long_name: str = Field(
        min_length=1,
        max_length=39,
        description="Full device name",
    )
    hardware: HardwareModel = Field(
        default=HardwareModel.UNKNOWN,
        description="Hardware model",
    )
    position: MeshPosition | None = Field(default=None, description="Last known position")
    last_seen: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last activity timestamp",
    )
    battery_level: int | None = Field(default=None, ge=0, le=100, description="Battery percentage")
    voltage: float | None = Field(default=None, ge=0, description="Battery voltage")
    snr: float | None = Field(default=None, description="Last signal-to-noise ratio")
    rssi: int | None = Field(default=None, description="Last signal strength")
    status: NodeStatus = Field(default=NodeStatus.UNKNOWN, description="Online status")
    is_favorite: bool = Field(default=False, description="User-marked favorite")
    hops_away: int | None = Field(default=None, ge=0, le=7, description="Routing distance")

    model_config = {"frozen": True}

    def is_online(self, timeout_seconds: int = 900) -> bool:
        """Check if node is considered online (seen within timeout)."""
        now = datetime.now(timezone.utc)
        return (now - self.last_seen).total_seconds() < timeout_seconds


# Mock network nodes for development
MOCK_NODES: list[dict[str, Any]] = [
    {
        "node_id": "!a1b2c3d4",
        "short_name": "ALPH",
        "long_name": "Alpha Base",
        "hardware": HardwareModel.TBEAM,
        "position": {
            "latitude": 37.7749,
            "longitude": -122.4194,
            "altitude": 50,
        },
        "battery_level": 85,
        "status": NodeStatus.ONLINE,
        "hops_away": 1,
    },
    {
        "node_id": "!b2c3d4e5",
        "short_name": "BRVO",
        "long_name": "Bravo Team",
        "hardware": HardwareModel.TLORA_V2,
        "position": {
            "latitude": 37.7851,
            "longitude": -122.4094,
            "altitude": 75,
        },
        "battery_level": 62,
        "status": NodeStatus.ONLINE,
        "hops_away": 2,
    },
    {
        "node_id": "!c3d4e5f6",
        "short_name": "CHRL",
        "long_name": "Charlie Relay",
        "hardware": HardwareModel.HELTEC_V3,
        "position": {
            "latitude": 37.7699,
            "longitude": -122.4294,
            "altitude": 120,
        },
        "battery_level": 100,
        "status": NodeStatus.ONLINE,
        "hops_away": 1,
    },
    {
        "node_id": "!d4e5f6a7",
        "short_name": "DELT",
        "long_name": "Delta Scout",
        "hardware": HardwareModel.RAK4631,
        "position": {
            "latitude": 37.7600,
            "longitude": -122.4350,
            "altitude": 30,
        },
        "battery_level": 45,
        "status": NodeStatus.OFFLINE,
        "hops_away": 3,
    },
    {
        "node_id": "!e5f6a7b8",
        "short_name": "ECHO",
        "long_name": "Echo Watch",
        "hardware": HardwareModel.TECHO,
        "position": None,  # No GPS
        "battery_level": 78,
        "status": NodeStatus.ONLINE,
        "hops_away": 2,
    },
]
