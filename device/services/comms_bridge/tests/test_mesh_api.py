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


class TestMeshContacts:
    """Tests for mesh contacts/favorites."""

    @pytest.mark.asyncio
    async def test_toggle_favorite(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        """Test toggling favorite status."""
        from device.libs.database import AsyncSQLite

        db_path = tmp_path / "test.sqlite3"
        db = AsyncSQLite(str(db_path))
        await db.open()

        # Toggle favorite on (no existing contact)
        result = await db.toggle_favorite("!a1b2c3d4")
        assert result is True

        # Toggle favorite off
        result = await db.toggle_favorite("!a1b2c3d4")
        assert result is False

        # Toggle back on
        result = await db.toggle_favorite("!a1b2c3d4")
        assert result is True

        await db.close()

    @pytest.mark.asyncio
    async def test_contact_alias(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        """Test setting contact alias."""
        from device.libs.database import AsyncSQLite

        db_path = tmp_path / "test.sqlite3"
        db = AsyncSQLite(str(db_path))
        await db.open()

        # Set alias
        contact = await db.upsert_mesh_contact("!a1b2c3d4", alias="My Friend")
        assert contact["alias"] == "My Friend"
        assert contact["is_favorite"] == 0  # Default

        # Update alias
        contact = await db.upsert_mesh_contact("!a1b2c3d4", alias="Best Friend")
        assert contact["alias"] == "Best Friend"

        await db.close()

    @pytest.mark.asyncio
    async def test_get_favorites(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        """Test getting favorite contacts."""
        from device.libs.database import AsyncSQLite

        db_path = tmp_path / "test.sqlite3"
        db = AsyncSQLite(str(db_path))
        await db.open()

        # Add some contacts
        await db.upsert_mesh_contact("!node1", alias="Node 1", is_favorite=True)
        await db.upsert_mesh_contact("!node2", alias="Node 2", is_favorite=False)
        await db.upsert_mesh_contact("!node3", alias="Node 3", is_favorite=True)

        # Get favorites
        favorites = await db.get_favorite_contacts()
        assert len(favorites) == 2
        node_ids = [f["node_id"] for f in favorites]
        assert "!node1" in node_ids
        assert "!node3" in node_ids
        assert "!node2" not in node_ids

        await db.close()

    @pytest.mark.asyncio
    async def test_service_contacts(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        """Test mesh service contact methods."""
        from device.libs.database import AsyncSQLite
        from device.services.comms_bridge.mesh.service import init_mesh_service

        db_path = tmp_path / "test.sqlite3"
        db = AsyncSQLite(str(db_path))
        await db.open()

        service = init_mesh_service(db=db)

        # Toggle favorite
        result = await service.toggle_favorite("!test123")
        assert result is True

        # Get contact
        contact = await service.get_contact("!test123")
        assert contact is not None
        assert contact["is_favorite"] == 1

        # Set alias
        await service.set_contact_alias("!test123", "Test Node")
        contact = await service.get_contact("!test123")
        assert contact["alias"] == "Test Node"

        await db.close()


class TestMeshMessagePersistence:
    """Tests for mesh message database persistence."""

    @pytest.mark.asyncio
    async def test_save_and_load_messages(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        """Test saving and loading messages from database."""
        from device.libs.database import AsyncSQLite
        from device.libs.schemas.meshtastic import MeshMessageCreate
        from device.services.comms_bridge.mesh.service import init_mesh_service

        # Create database
        db_path = tmp_path / "test.sqlite3"
        db = AsyncSQLite(str(db_path))
        await db.open()

        # Initialize service with database
        service = init_mesh_service(db=db)
        assert service._db is not None

        # Send a message
        msg_req = MeshMessageCreate(text="Test message for DB")
        service.send_message(msg_req)

        # Give the async task time to complete
        import asyncio

        await asyncio.sleep(0.1)

        # Check message was saved
        rows = await db.get_mesh_messages(limit=10)
        assert len(rows) >= 1
        assert any(r["content"] == "Test message for DB" for r in rows)

        await db.close()

    @pytest.mark.asyncio
    async def test_load_history_on_init(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        """Test loading message history from database on startup."""
        from device.libs.database import AsyncSQLite

        # Create database and add a message
        db_path = tmp_path / "test.sqlite3"
        db = AsyncSQLite(str(db_path))
        await db.open()

        # Manually insert a message
        await db.save_mesh_message(
            message_id="test_123",
            from_node="!a1b2c3d4",
            to_node=None,
            text="Historical message",
            channel=0,
        )

        # Create new service and load history
        reset_mesh_service()
        service = MeshChatService(db=db)
        await service.load_history_from_db(limit=100)

        # Check message was loaded
        messages = service.get_messages()
        assert len(messages) >= 1
        assert any(m.text == "Historical message" for m in messages)

        await db.close()
