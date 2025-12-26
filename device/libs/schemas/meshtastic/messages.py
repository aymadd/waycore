"""Meshtastic message schemas."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MeshMessageType(str, Enum):
    """Types of mesh messages."""

    TEXT = "text"
    POSITION = "position"
    NODEINFO = "nodeinfo"
    TELEMETRY = "telemetry"
    WAYPOINT = "waypoint"
    ROUTING = "routing"


class DeliveryStatus(str, Enum):
    """Message delivery status."""

    PENDING = "pending"  # Queued locally, not yet transmitted
    SENDING = "sending"  # Being transmitted over radio
    SENT = "sent"  # Transmitted successfully (no ACK requested)
    DELIVERED = "delivered"  # ACK received from recipient
    FAILED = "failed"  # Transmission failed or ACK timeout


class MeshChannel(BaseModel):
    """Mesh network channel configuration."""

    index: int = Field(ge=0, le=7, description="Channel index (0-7)")
    name: str = Field(max_length=12, description="Channel name")
    psk: str | None = Field(default=None, description="Pre-shared key (base64)")
    uplink_enabled: bool = Field(default=False, description="Allow MQTT uplink")
    downlink_enabled: bool = Field(default=False, description="Allow MQTT downlink")

    model_config = {"frozen": True}


class MeshMessageCreate(BaseModel):
    """Schema for creating a new mesh message."""

    text: str = Field(min_length=1, max_length=237, description="Message text")
    to_node: str | None = Field(
        default=None,
        pattern=r"^![0-9a-fA-F]{8}$",
        description="Recipient node ID (None = broadcast)",
    )
    channel: int = Field(default=0, ge=0, le=7, description="Channel index")
    want_ack: bool = Field(default=True, description="Request delivery acknowledgment")


class MeshMessage(BaseModel):
    """A mesh network message."""

    id: str = Field(description="Unique message ID")
    from_node: str = Field(
        pattern=r"^![0-9a-fA-F]{8}$",
        description="Sender node ID",
    )
    to_node: str | None = Field(
        default=None,
        pattern=r"^![0-9a-fA-F]{8}$",
        description="Recipient node ID (None = broadcast)",
    )
    channel: int = Field(default=0, ge=0, le=7, description="Channel index")
    message_type: MeshMessageType = Field(
        default=MeshMessageType.TEXT,
        description="Message type",
    )
    text: str = Field(description="Message content")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When message was sent",
    )
    rx_time: datetime | None = Field(
        default=None,
        description="When message was received locally",
    )
    hop_count: int = Field(default=0, ge=0, le=7, description="Number of routing hops")
    hop_limit: int = Field(default=3, ge=0, le=7, description="Maximum allowed hops")
    want_ack: bool = Field(default=True, description="Acknowledgment requested")
    acknowledged: bool = Field(default=False, description="Delivery confirmed")
    delivery_status: DeliveryStatus = Field(
        default=DeliveryStatus.SENT,
        description="Delivery status",
    )
    snr: float | None = Field(default=None, description="Signal-to-noise ratio")
    rssi: int | None = Field(default=None, description="Received signal strength")

    model_config = {"frozen": True}


class MeshPacket(BaseModel):
    """Low-level mesh packet for transport."""

    id: int = Field(description="Packet ID")
    from_id: str = Field(description="Source node ID")
    to_id: str = Field(default="^all", description="Destination (^all = broadcast)")
    channel: int = Field(default=0, description="Channel index")
    hop_limit: int = Field(default=3, description="Remaining hop limit")
    want_ack: bool = Field(default=False, description="Request ACK")
    priority: int = Field(default=64, description="Packet priority (0-127)")
    payload_type: MeshMessageType = Field(description="Payload type")
    payload: dict[str, Any] = Field(description="Message payload")
    rx_time: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Receive timestamp",
    )
    rx_snr: float | None = Field(default=None, description="SNR at receiver")
    rx_rssi: int | None = Field(default=None, description="RSSI at receiver")
