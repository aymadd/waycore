"""Tests for Meshtastic node schemas."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from device.libs.schemas.meshtastic import (
    HardwareModel,
    MeshNode,
    MeshNodeCreate,
    MeshNodeUpdate,
    MeshPosition,
    NodeStatus,
)
from device.libs.schemas.meshtastic.nodes import MOCK_NODES


class TestMeshPosition:
    """Tests for MeshPosition schema."""

    def test_valid_position(self) -> None:
        """Test creating a valid position."""
        pos = MeshPosition(
            latitude=37.7749,
            longitude=-122.4194,
            altitude=50,
        )
        assert pos.latitude == 37.7749
        assert pos.longitude == -122.4194
        assert pos.altitude == 50

    def test_position_with_speed(self) -> None:
        """Test position with ground speed and track."""
        pos = MeshPosition(
            latitude=37.7749,
            longitude=-122.4194,
            ground_speed=5,
            ground_track=270,
        )
        assert pos.ground_speed == 5
        assert pos.ground_track == 270

    def test_invalid_latitude(self) -> None:
        """Test latitude range validation."""
        with pytest.raises(ValidationError):
            MeshPosition(latitude=91, longitude=0)

        with pytest.raises(ValidationError):
            MeshPosition(latitude=-91, longitude=0)

    def test_invalid_longitude(self) -> None:
        """Test longitude range validation."""
        with pytest.raises(ValidationError):
            MeshPosition(latitude=0, longitude=181)

        with pytest.raises(ValidationError):
            MeshPosition(latitude=0, longitude=-181)

    def test_position_has_timestamp(self) -> None:
        """Test position gets default timestamp."""
        pos = MeshPosition(latitude=0, longitude=0)
        assert pos.time is not None
        assert pos.time.tzinfo == timezone.utc


class TestMeshNodeCreate:
    """Tests for MeshNodeCreate schema."""

    def test_valid_node_create(self) -> None:
        """Test creating a new node."""
        node = MeshNodeCreate(
            node_id="!a1b2c3d4",
            short_name="TEST",
            long_name="Test Node",
        )
        assert node.node_id == "!a1b2c3d4"
        assert node.short_name == "TEST"
        assert node.hardware == HardwareModel.UNKNOWN

    def test_node_with_hardware(self) -> None:
        """Test node with specific hardware."""
        node = MeshNodeCreate(
            node_id="!b2c3d4e5",
            short_name="TBEM",
            long_name="T-Beam Node",
            hardware=HardwareModel.TBEAM,
        )
        assert node.hardware == HardwareModel.TBEAM

    def test_invalid_node_id(self) -> None:
        """Test node ID format validation."""
        with pytest.raises(ValidationError):
            MeshNodeCreate(
                node_id="invalid",
                short_name="TEST",
                long_name="Test",
            )

    def test_short_name_too_long(self) -> None:
        """Test short name max length (4 chars)."""
        with pytest.raises(ValidationError):
            MeshNodeCreate(
                node_id="!c3d4e5f6",
                short_name="TOOLONG",
                long_name="Test",
            )

    def test_long_name_too_long(self) -> None:
        """Test long name max length (39 chars)."""
        with pytest.raises(ValidationError):
            MeshNodeCreate(
                node_id="!d4e5f6a7",
                short_name="TEST",
                long_name="x" * 40,
            )


class TestMeshNodeUpdate:
    """Tests for MeshNodeUpdate schema."""

    def test_partial_update(self) -> None:
        """Test partial node update."""
        update = MeshNodeUpdate(short_name="NEW")
        assert update.short_name == "NEW"
        assert update.long_name is None

    def test_update_with_position(self) -> None:
        """Test update with new position."""
        update = MeshNodeUpdate(position=MeshPosition(latitude=38.0, longitude=-123.0))
        assert update.position is not None
        assert update.position.latitude == 38.0

    def test_update_battery(self) -> None:
        """Test battery level update."""
        update = MeshNodeUpdate(battery_level=75)
        assert update.battery_level == 75


class TestMeshNode:
    """Tests for MeshNode schema."""

    def test_full_node(self) -> None:
        """Test creating a complete node."""
        node = MeshNode(
            node_id="!a1b2c3d4",
            short_name="FULL",
            long_name="Full Node Test",
            hardware=HardwareModel.TBEAM,
            position=MeshPosition(latitude=37.7749, longitude=-122.4194),
            battery_level=85,
            status=NodeStatus.ONLINE,
            hops_away=1,
        )
        assert node.node_id == "!a1b2c3d4"
        assert node.position is not None
        assert node.battery_level == 85
        assert node.status == NodeStatus.ONLINE

    def test_node_without_position(self) -> None:
        """Test node without GPS."""
        node = MeshNode(
            node_id="!e5f6a7b8",
            short_name="NPOS",
            long_name="No Position Node",
        )
        assert node.position is None
        assert node.status == NodeStatus.UNKNOWN

    def test_is_online_recently_seen(self) -> None:
        """Test online check for recently seen node."""
        node = MeshNode(
            node_id="!f6a7b8c9",
            short_name="RECN",
            long_name="Recently Seen",
            last_seen=datetime.now(timezone.utc),
        )
        assert node.is_online(timeout_seconds=900) is True

    def test_is_online_stale_node(self) -> None:
        """Test online check for stale node."""
        stale_time = datetime.now(timezone.utc) - timedelta(hours=1)
        node = MeshNode(
            node_id="!a7b8c9d0",
            short_name="STAL",
            long_name="Stale Node",
            last_seen=stale_time,
        )
        assert node.is_online(timeout_seconds=900) is False

    def test_signal_quality(self) -> None:
        """Test SNR and RSSI fields."""
        node = MeshNode(
            node_id="!b8c9d0e1",
            short_name="SIG",
            long_name="Signal Test",
            snr=8.5,
            rssi=-85,
        )
        assert node.snr == 8.5
        assert node.rssi == -85


class TestMockNodes:
    """Tests for mock node data."""

    def test_mock_nodes_count(self) -> None:
        """Test we have expected number of mock nodes."""
        assert len(MOCK_NODES) == 5

    def test_mock_nodes_valid(self) -> None:
        """Test all mock nodes are valid MeshNode objects."""
        for node_data in MOCK_NODES:
            # Add required fields if missing
            if "last_seen" not in node_data:
                node_data["last_seen"] = datetime.now(timezone.utc)
            if node_data.get("position"):
                node_data["position"]["time"] = datetime.now(timezone.utc)

            node = MeshNode(**node_data)
            assert node.node_id.startswith("!")
            assert len(node.short_name) <= 4

    def test_mock_nodes_unique_ids(self) -> None:
        """Test mock nodes have unique IDs."""
        node_ids = [n["node_id"] for n in MOCK_NODES]
        assert len(node_ids) == len(set(node_ids))

    def test_mock_nodes_hardware_variety(self) -> None:
        """Test mock nodes use different hardware models."""
        hardware = {n["hardware"] for n in MOCK_NODES}
        assert len(hardware) >= 4  # At least 4 different models
