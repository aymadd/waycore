from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import Field, ValidationInfo, field_validator

from .base import BaseMessage


class Transport(str, Enum):
    lora = "lora"
    wifi = "wifi"
    lte = "lte"
    bluetooth = "bluetooth"


class Priority(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"
    urgent = "urgent"


class MessageReceived(BaseMessage):
    """
    Incoming message from radio.
    Topic: comms/message/received
    """

    transport: Transport = Field(..., description="Transport type")
    from_node: str = Field(..., min_length=1, description="Sender node ID")
    to_node: str | None = Field(default=None, description="Recipient node ID (None=broadcast)")
    content: str = Field(..., min_length=1, description="Message text")
    channel: str = Field(default="primary", min_length=1, description="Channel name")
    rssi: int | None = Field(default=None, description="Signal strength (RSSI)")
    snr: float | None = Field(default=None, description="Signal-to-noise ratio")
    hop_limit: int = Field(default=3, ge=0, description="Remaining hops")

    @field_validator("content")
    @classmethod
    def _validate_lora_length(cls, value: str, info: ValidationInfo) -> str:
        # Enforce LoRa payload size recommendation if transport is LoRa
        transport: Transport | None = info.data.get("transport")
        if transport == Transport.lora and len(value) > 237:
            msg = "content exceeds LoRa payload limit of 237 characters"
            raise ValueError(msg)
        return value


class SendMessageRequest(BaseMessage):
    """
    Request to send a message via a radio.
    Topic: comms/message/send
    """

    transport: Transport = Field(..., description="Transport type")
    to_node: str | None = Field(default=None, description="Recipient (None=broadcast)")
    content: str = Field(..., min_length=1, description="Message text")
    channel: str = Field(default="primary", min_length=1, description="Channel name")
    priority: Priority = Field(default=Priority.normal, description="Message priority")
    want_ack: bool = Field(default=False, description="Request acknowledgment")

    @field_validator("content")
    @classmethod
    def _validate_lora_length(cls, value: str, info: ValidationInfo) -> str:
        transport: Transport | None = info.data.get("transport")
        if transport == Transport.lora and len(value) > 237:
            msg = "content exceeds LoRa payload limit of 237 characters"
            raise ValueError(msg)
        return value


class CommsStatusChanged(BaseMessage):
    """
    Radio status update.
    Topic: comms/status/changed
    """

    transport: Transport = Field(..., description="Transport type")
    enabled: bool = Field(..., description="Radio enabled")
    connected: bool = Field(..., description="Radio connected")
    signal_strength: int | None = Field(default=None, description="RSSI")
    error: str | None = Field(default=None, description="Error message, if any")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional context")
