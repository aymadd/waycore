"""Tests for Meshtastic message schemas."""

from __future__ import annotations

from datetime import timezone

import pytest
from pydantic import ValidationError

from device.libs.schemas.meshtastic import (
    MeshChannel,
    MeshMessage,
    MeshMessageCreate,
    MeshMessageType,
    MeshPacket,
)


class TestMeshChannel:
    """Tests for MeshChannel schema."""

    def test_valid_channel(self) -> None:
        """Test creating a valid channel."""
        channel = MeshChannel(index=0, name="General")
        assert channel.index == 0
        assert channel.name == "General"
        assert channel.psk is None

    def test_channel_with_psk(self) -> None:
        """Test channel with pre-shared key."""
        channel = MeshChannel(index=1, name="Private", psk="base64encodedkey==")
        assert channel.psk == "base64encodedkey=="

    def test_invalid_channel_index(self) -> None:
        """Test channel index validation."""
        with pytest.raises(ValidationError):
            MeshChannel(index=8, name="Invalid")

        with pytest.raises(ValidationError):
            MeshChannel(index=-1, name="Invalid")

    def test_channel_name_too_long(self) -> None:
        """Test channel name length validation."""
        with pytest.raises(ValidationError):
            MeshChannel(index=0, name="ThisNameIsTooLong")


class TestMeshMessageCreate:
    """Tests for MeshMessageCreate schema."""

    def test_broadcast_message(self) -> None:
        """Test creating a broadcast message."""
        msg = MeshMessageCreate(text="Hello mesh!")
        assert msg.text == "Hello mesh!"
        assert msg.to_node is None
        assert msg.channel == 0
        assert msg.want_ack is True

    def test_direct_message(self) -> None:
        """Test creating a direct message."""
        msg = MeshMessageCreate(text="Hello!", to_node="!a1b2c3d4")
        assert msg.to_node == "!a1b2c3d4"

    def test_invalid_node_id_format(self) -> None:
        """Test node ID validation."""
        with pytest.raises(ValidationError):
            MeshMessageCreate(text="Hello", to_node="invalid")

        with pytest.raises(ValidationError):
            MeshMessageCreate(text="Hello", to_node="a1b2c3d4")  # Missing !

        with pytest.raises(ValidationError):
            MeshMessageCreate(text="Hello", to_node="!a1b2c3")  # Too short

    def test_empty_text(self) -> None:
        """Test empty message validation."""
        with pytest.raises(ValidationError):
            MeshMessageCreate(text="")

    def test_text_too_long(self) -> None:
        """Test message length validation (237 char limit)."""
        with pytest.raises(ValidationError):
            MeshMessageCreate(text="x" * 238)


class TestMeshMessage:
    """Tests for MeshMessage schema."""

    def test_full_message(self) -> None:
        """Test creating a complete message."""
        msg = MeshMessage(
            id="msg123",
            from_node="!a1b2c3d4",
            to_node="!b2c3d4e5",
            channel=0,
            text="Test message",
            hop_count=2,
            acknowledged=True,
        )
        assert msg.id == "msg123"
        assert msg.from_node == "!a1b2c3d4"
        assert msg.to_node == "!b2c3d4e5"
        assert msg.hop_count == 2
        assert msg.acknowledged is True

    def test_broadcast_message(self) -> None:
        """Test broadcast message (no to_node)."""
        msg = MeshMessage(
            id="msg456",
            from_node="!c3d4e5f6",
            text="Broadcast test",
        )
        assert msg.to_node is None
        assert msg.message_type == MeshMessageType.TEXT

    def test_message_has_timestamp(self) -> None:
        """Test that messages get default timestamp."""
        msg = MeshMessage(
            id="msg789",
            from_node="!d4e5f6a7",
            text="Timestamp test",
        )
        assert msg.timestamp is not None
        assert msg.timestamp.tzinfo == timezone.utc

    def test_signal_quality_fields(self) -> None:
        """Test SNR and RSSI fields."""
        msg = MeshMessage(
            id="msg999",
            from_node="!e5f6a7b8",
            text="Signal test",
            snr=5.5,
            rssi=-95,
        )
        assert msg.snr == 5.5
        assert msg.rssi == -95


class TestMeshPacket:
    """Tests for MeshPacket schema."""

    def test_text_packet(self) -> None:
        """Test creating a text message packet."""
        packet = MeshPacket(
            id=12345,
            from_id="!a1b2c3d4",
            payload_type=MeshMessageType.TEXT,
            payload={"text": "Hello!"},
        )
        assert packet.id == 12345
        assert packet.from_id == "!a1b2c3d4"
        assert packet.to_id == "^all"  # Default broadcast
        assert packet.payload_type == MeshMessageType.TEXT

    def test_position_packet(self) -> None:
        """Test creating a position packet."""
        packet = MeshPacket(
            id=12346,
            from_id="!b2c3d4e5",
            payload_type=MeshMessageType.POSITION,
            payload={
                "latitude": 37.7749,
                "longitude": -122.4194,
                "altitude": 50,
            },
        )
        assert packet.payload_type == MeshMessageType.POSITION
        assert packet.payload["latitude"] == 37.7749

    def test_packet_priority(self) -> None:
        """Test packet priority settings."""
        packet = MeshPacket(
            id=12347,
            from_id="!c3d4e5f6",
            priority=127,  # Max priority
            payload_type=MeshMessageType.ROUTING,
            payload={},
        )
        assert packet.priority == 127
