"""Tests for mesh chat API endpoints."""

from __future__ import annotations

import pytest
from device.services.comms_bridge.mesh.service import (
    MeshChatService,
    get_mesh_service,
    reset_mesh_service,
)


@pytest.fixture(autouse=True)
def reset_service() -> None:
    """Reset mesh service before each test."""
    reset_mesh_service()


class TestMeshChatService:
    """Tests for MeshChatService."""

    def test_initialization(self) -> None:
        """Test service initializes correctly."""
        service = MeshChatService()

        assert service.my_node_id == "!00000001"
        assert service.is_connected is True

    def test_get_nodes(self) -> None:
        """Test getting mesh nodes."""
        service = MeshChatService()
        nodes = service.get_nodes()

        assert len(nodes) == 5
        node_ids = [n.node_id for n in nodes]
        assert "!a1b2c3d4" in node_ids

    def test_get_node(self) -> None:
        """Test getting specific node."""
        service = MeshChatService()

        node = service.get_node("!a1b2c3d4")
        assert node is not None
        assert node.short_name == "ALPH"

        assert service.get_node("!00000000") is None

    def test_get_online_nodes(self) -> None:
        """Test getting only online nodes."""
        service = MeshChatService()
        online = service.get_online_nodes()

        # At least some nodes should be online by default
        assert len(online) >= 3

    def test_get_node_count(self) -> None:
        """Test node count summary."""
        service = MeshChatService()
        counts = service.get_node_count()

        assert counts["total"] == 5
        assert "online" in counts
        assert "offline" in counts

    def test_send_message_broadcast(self) -> None:
        """Test sending broadcast message."""
        from device.libs.schemas.meshtastic import MeshMessageCreate

        service = MeshChatService()
        msg_req = MeshMessageCreate(text="Hello mesh!")

        message = service.send_message(msg_req)

        assert message.id.startswith("msg_")
        assert message.text == "Hello mesh!"
        assert message.to_node is None
        assert message.from_node == service.my_node_id

    def test_send_message_direct(self) -> None:
        """Test sending direct message."""
        from device.libs.schemas.meshtastic import MeshMessageCreate

        service = MeshChatService()
        msg_req = MeshMessageCreate(text="Hello Alpha!", to_node="!a1b2c3d4")

        message = service.send_message(msg_req)

        assert message.to_node == "!a1b2c3d4"

    def test_get_messages(self) -> None:
        """Test getting message history."""
        from device.libs.schemas.meshtastic import MeshMessageCreate

        service = MeshChatService()

        # Send some messages
        service.send_message(MeshMessageCreate(text="Message 1"))
        service.send_message(MeshMessageCreate(text="Message 2"))

        messages = service.get_messages()
        assert len(messages) >= 2

    def test_get_status(self) -> None:
        """Test getting network status."""
        service = MeshChatService()
        status = service.get_status()

        assert status["connected"] is True
        assert status["my_node_id"] == "!00000001"
        assert "nodes" in status
        assert "messages" in status

    def test_my_node_info(self) -> None:
        """Test getting own node info."""
        service = MeshChatService()
        info = service.my_node_info

        assert info.node_id == "!00000001"
        assert info.short_name == "WAYC"

    def test_get_conversation(self) -> None:
        """Test getting conversation with a node."""
        from device.libs.schemas.meshtastic import MeshMessageCreate

        service = MeshChatService()

        # Send messages to specific node
        service.send_message(MeshMessageCreate(text="Hi Alpha", to_node="!a1b2c3d4"))

        conversation = service.get_conversation("!a1b2c3d4")
        assert isinstance(conversation, list)


class TestMeshServiceSingleton:
    """Tests for mesh service singleton."""

    def test_singleton_instance(self) -> None:
        """Test singleton returns same instance."""
        reset_mesh_service()

        service1 = get_mesh_service()
        service2 = get_mesh_service()

        assert service1 is service2

    def test_reset_creates_new_instance(self) -> None:
        """Test reset creates new instance."""
        service1 = get_mesh_service()
        reset_mesh_service()
        service2 = get_mesh_service()

        assert service1 is not service2
