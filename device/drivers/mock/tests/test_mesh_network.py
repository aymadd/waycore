"""Tests for mock mesh network driver."""

from __future__ import annotations

import time

import pytest
from device.drivers.mock.mesh_network import MockMeshNetwork
from device.libs.schemas.meshtastic import HardwareModel, NodeStatus


class TestMockMeshNetworkInit:
    """Tests for MockMeshNetwork initialization."""

    def test_default_initialization(self) -> None:
        """Test driver initializes with defaults."""
        mesh = MockMeshNetwork(node_churn_enabled=False)

        assert mesh.get_my_node_id() == "!00000001"
        assert mesh.is_connected() is True

    def test_custom_node_id(self) -> None:
        """Test custom node ID."""
        mesh = MockMeshNetwork(
            my_node_id="!deadbeef",
            my_short_name="TEST",
            my_long_name="Test Device",
            node_churn_enabled=False,
        )

        assert mesh.get_my_node_id() == "!deadbeef"
        info = mesh.get_my_node_info()
        assert info.short_name == "TEST"
        assert info.long_name == "Test Device"


class TestMockMeshNetworkNodes:
    """Tests for node discovery and management."""

    def test_default_peers_exist(self) -> None:
        """Test default peer nodes are initialized."""
        mesh = MockMeshNetwork(node_churn_enabled=False)
        nodes = mesh.get_nodes()

        assert len(nodes) == 5
        node_ids = [n.node_id for n in nodes]
        assert "!a1b2c3d4" in node_ids  # Alpha
        assert "!b2c3d4e5" in node_ids  # Bravo

    def test_get_node_by_id(self) -> None:
        """Test getting specific node."""
        mesh = MockMeshNetwork(node_churn_enabled=False)

        node = mesh.get_node("!a1b2c3d4")
        assert node is not None
        assert node.short_name == "ALPH"
        assert node.long_name == "Alpha Base"

    def test_get_nonexistent_node(self) -> None:
        """Test getting node that doesn't exist."""
        mesh = MockMeshNetwork(node_churn_enabled=False)

        node = mesh.get_node("!00000000")
        assert node is None

    def test_node_has_position(self) -> None:
        """Test nodes have position data."""
        mesh = MockMeshNetwork(node_churn_enabled=False)

        node = mesh.get_node("!a1b2c3d4")
        assert node is not None
        assert node.position is not None
        assert node.position.latitude == pytest.approx(37.7749, rel=0.001)

    def test_node_without_position(self) -> None:
        """Test node without GPS."""
        mesh = MockMeshNetwork(node_churn_enabled=False)

        node = mesh.get_node("!e5f6a7b8")  # Echo has no GPS
        assert node is not None
        assert node.position is None

    def test_my_node_info(self) -> None:
        """Test getting own node info."""
        mesh = MockMeshNetwork(node_churn_enabled=False)

        info = mesh.get_my_node_info()
        assert info.node_id == "!00000001"
        assert info.hardware == HardwareModel.WAYCORE
        assert info.status == NodeStatus.ONLINE
        assert info.position is not None


class TestMockMeshNetworkMessages:
    """Tests for message sending and receiving."""

    def test_send_broadcast_message(self) -> None:
        """Test sending broadcast message."""
        mesh = MockMeshNetwork(
            message_delay_ms=(10, 50),
            packet_loss_percent=0,
            node_churn_enabled=False,
        )

        msg_id = mesh.send_message("Hello mesh!")
        assert msg_id.startswith("msg_")

        # Wait for delivery
        time.sleep(0.1)

        msg = mesh.get_message(msg_id)
        assert msg is not None
        assert msg.text == "Hello mesh!"
        assert msg.to_node is None  # Broadcast

    def test_send_direct_message(self) -> None:
        """Test sending direct message to specific node."""
        mesh = MockMeshNetwork(
            message_delay_ms=(10, 50),
            packet_loss_percent=0,
            node_churn_enabled=False,
        )

        msg_id = mesh.send_message("Hello Alpha!", to_node="!a1b2c3d4")
        time.sleep(0.1)

        msg = mesh.get_message(msg_id)
        assert msg is not None
        assert msg.to_node == "!a1b2c3d4"

    def test_message_acknowledged(self) -> None:
        """Test message acknowledgment."""
        mesh = MockMeshNetwork(
            message_delay_ms=(10, 50),
            packet_loss_percent=0,
            node_churn_enabled=False,
        )

        msg_id = mesh.send_message("Test", want_ack=True)
        time.sleep(0.1)

        msg = mesh.get_message(msg_id)
        assert msg is not None
        assert msg.acknowledged is True

    def test_simulate_incoming_message(self) -> None:
        """Test simulating incoming message."""
        mesh = MockMeshNetwork(node_churn_enabled=False)

        msg_id = mesh.simulate_incoming_message(
            from_node="!a1b2c3d4",
            text="Hello from Alpha!",
        )

        msg = mesh.get_message(msg_id)
        assert msg is not None
        assert msg.from_node == "!a1b2c3d4"
        assert msg.text == "Hello from Alpha!"
        assert msg.rx_time is not None

    def test_receive_messages(self) -> None:
        """Test receiving messages."""
        mesh = MockMeshNetwork(node_churn_enabled=False)

        # Simulate incoming messages
        mesh.simulate_incoming_message("!a1b2c3d4", "Message 1")
        mesh.simulate_incoming_message("!b2c3d4e5", "Message 2")

        messages = mesh.receive_messages()
        assert len(messages) >= 2

        texts = [m.text for m in messages]
        assert "Message 1" in texts
        assert "Message 2" in texts


class TestMockMeshNetworkStatus:
    """Tests for connection and node status."""

    def test_connection_status(self) -> None:
        """Test connection status."""
        mesh = MockMeshNetwork(node_churn_enabled=False)

        assert mesh.is_connected() is True

        mesh.set_connected(False)
        assert mesh.is_connected() is False

    def test_set_node_status(self) -> None:
        """Test setting node status manually."""
        mesh = MockMeshNetwork(node_churn_enabled=False)

        mesh.set_node_status("!a1b2c3d4", NodeStatus.OFFLINE)
        node = mesh.get_node("!a1b2c3d4")
        assert node is not None
        assert node.status == NodeStatus.OFFLINE

        mesh.set_node_status("!a1b2c3d4", NodeStatus.ONLINE)
        node = mesh.get_node("!a1b2c3d4")
        assert node is not None
        assert node.status == NodeStatus.ONLINE

    def test_channel_name(self) -> None:
        """Test channel name retrieval."""
        mesh = MockMeshNetwork(node_churn_enabled=False)

        assert mesh.get_channel_name(0) == "LongFast"
        assert mesh.get_channel_name(1) == "Channel 1"


class TestMockMeshNetworkPacketLoss:
    """Tests for simulated packet loss."""

    def test_no_packet_loss(self) -> None:
        """Test with 0% packet loss."""
        mesh = MockMeshNetwork(
            message_delay_ms=(1, 10),
            packet_loss_percent=0,
            node_churn_enabled=False,
        )

        # Send multiple messages
        for _ in range(10):
            mesh.send_message("Test")

        time.sleep(0.1)

        # All messages should be acknowledged
        messages = mesh.get_all_messages()
        acknowledged = [m for m in messages if m.acknowledged]
        assert len(acknowledged) == 10

    def test_high_packet_loss(self) -> None:
        """Test with high packet loss (some messages fail)."""
        mesh = MockMeshNetwork(
            message_delay_ms=(1, 10),
            packet_loss_percent=100,  # All packets lost
            node_churn_enabled=False,
        )

        mesh.send_message("Test")
        time.sleep(0.1)

        messages = mesh.get_all_messages()
        # With 100% loss, message should not be acknowledged
        if messages:
            assert messages[0].acknowledged is False
