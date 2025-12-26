"""Bridge for mesh network data between backend and QML UI."""

from __future__ import annotations

import logging
from typing import Any

from PySide6.QtCore import Property, QObject, Signal, Slot

from .api_client import CommsBridgeClient

logger = logging.getLogger(__name__)


class MeshBridge(QObject):
    """
    Bridge between QML UI and mesh network backend.

    Provides methods for getting nodes, messages, and sending messages.
    """

    # Signals
    statusChanged = Signal()
    nodesChanged = Signal()
    messagesChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._client: CommsBridgeClient | None = None
        self._backend_available = False
        self._status: dict[str, Any] = self._get_mock_status()
        self._nodes: list[dict[str, Any]] = self._get_mock_nodes()
        self._messages: list[dict[str, Any]] = self._get_mock_messages()

        self._init_client()

    def _init_client(self) -> None:
        """Initialize the comms bridge client and test connection."""
        try:
            self._client = CommsBridgeClient()
            # Test if backend is actually available
            self._client.get_mesh_status()
            self._backend_available = True
            logger.info("MeshBridge connected to Comms Bridge backend")
        except Exception as e:
            logger.info(f"Comms Bridge backend not available, using mock data: {e}")
            self._backend_available = False

    # Status

    @Slot(result="QVariant")  # type: ignore[arg-type]
    def getStatus(self) -> dict[str, Any]:
        """Get mesh network status."""
        if not self._backend_available or not self._client:
            logger.debug("Using mock status data")
            return self._status

        try:
            status = self._client.get_mesh_status()
            self._status = status
            return status
        except Exception as e:
            logger.debug(f"Failed to get mesh status: {e}")
            return self._status

    def _get_mock_status(self) -> dict[str, Any]:
        """Return mock status when backend unavailable."""
        return {
            "connected": True,
            "my_node_id": "!00000001",
            "channel_name": "LongFast",
            "nodes": {"total": 5, "online": 4, "offline": 1},
            "messages": {"total": 10, "sent": 5, "received": 5},
        }

    # Nodes

    @Slot(result="QVariant")  # type: ignore[arg-type]
    def getNodes(self) -> dict[str, Any]:
        """Get list of mesh nodes."""
        if not self._backend_available or not self._client:
            logger.debug("Using mock nodes data")
            return {"nodes": self._nodes, "count": len(self._nodes)}

        try:
            result = self._client.get_mesh_nodes()
            self._nodes = result.get("nodes", [])
            return result
        except Exception as e:
            logger.debug(f"Failed to get mesh nodes: {e}")
            return {"nodes": self._nodes, "count": len(self._nodes)}

    def _get_mock_nodes(self) -> list[dict[str, Any]]:
        """Return mock nodes when backend unavailable."""
        return [
            {
                "node_id": "!a1b2c3d4",
                "short_name": "ALPH",
                "long_name": "Alpha",
                "status": "online",
                "battery_level": 85,
                "hops_away": 0,
                "last_seen": "2025-12-25T12:00:00Z",
            },
            {
                "node_id": "!b2c3d4e5",
                "short_name": "BRVO",
                "long_name": "Bravo",
                "status": "online",
                "battery_level": 72,
                "hops_away": 1,
                "last_seen": "2025-12-25T11:55:00Z",
            },
            {
                "node_id": "!c3d4e5f6",
                "short_name": "CHRL",
                "long_name": "Charlie",
                "status": "offline",
                "battery_level": 45,
                "hops_away": 2,
                "last_seen": "2025-12-24T18:00:00Z",
            },
            {
                "node_id": "!d4e5f6g7",
                "short_name": "DELT",
                "long_name": "Delta",
                "status": "online",
                "battery_level": 95,
                "hops_away": 1,
                "last_seen": "2025-12-25T12:00:00Z",
            },
            {
                "node_id": "!e5f6g7h8",
                "short_name": "ECHO",
                "long_name": "Echo",
                "status": "online",
                "battery_level": 60,
                "hops_away": 2,
                "last_seen": "2025-12-25T11:50:00Z",
            },
        ]

    # Messages

    @Slot(int, result="QVariant")  # type: ignore[arg-type]
    def getMessages(self, limit: int = 50) -> dict[str, Any]:
        """Get message history."""
        if not self._backend_available or not self._client:
            logger.debug("Using mock messages data")
            return {"messages": self._messages, "count": len(self._messages)}

        try:
            result = self._client.get_mesh_messages(limit=limit)
            self._messages = result.get("messages", [])

            # Mark which messages are mine
            my_node = self._status.get("my_node_id", "!00000001")
            for msg in self._messages:
                msg["is_mine"] = msg.get("from_node") == my_node

            return result
        except Exception as e:
            logger.debug(f"Failed to get messages: {e}")
            return {"messages": self._messages, "count": len(self._messages)}

    def _get_mock_messages(self) -> list[dict[str, Any]]:
        """Return mock messages when backend unavailable."""
        return [
            {
                "id": "msg_1",
                "from_node": "!a1b2c3d4",
                "from_name": "ALPH",
                "text": "Hello from Alpha!",
                "timestamp": "2025-12-25T11:50:00Z",
                "is_mine": False,
            },
            {
                "id": "msg_2",
                "from_node": "!00000001",
                "from_name": "WAYC",
                "text": "Hey Alpha, good to hear from you!",
                "timestamp": "2025-12-25T11:51:00Z",
                "is_mine": True,
            },
            {
                "id": "msg_3",
                "from_node": "!b2c3d4e5",
                "from_name": "BRVO",
                "text": "Bravo checking in. All good here.",
                "timestamp": "2025-12-25T11:55:00Z",
                "is_mine": False,
            },
        ]

    @Slot(str, result="QVariant")  # type: ignore[arg-type]
    def sendMessage(self, text: str) -> dict[str, Any]:
        """Send a mesh message."""
        if not text.strip():
            return {"success": False, "error": "Empty message"}

        if not self._backend_available or not self._client:
            # Mock success - add message to local list
            from datetime import datetime, timezone

            new_msg = {
                "id": f"mock_{len(self._messages) + 1}",
                "from_node": "!00000001",
                "from_name": "WAYC",
                "text": text,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "is_mine": True,
            }
            self._messages.append(new_msg)
            self.messagesChanged.emit()
            return {"success": True, "mock": True, "message": new_msg}

        try:
            result = self._client.send_mesh_message(text=text)
            self.messagesChanged.emit()
            return result
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return {"success": False, "error": str(e)}

    @Slot(str, str, result="QVariant")  # type: ignore[arg-type]
    def sendDirectMessage(self, text: str, to_node: str) -> dict[str, Any]:
        """Send a direct message to a specific node."""
        if not text.strip():
            return {"success": False, "error": "Empty message"}

        if not self._backend_available or not self._client:
            # Mock success
            from datetime import datetime, timezone

            new_msg = {
                "id": f"mock_{len(self._messages) + 1}",
                "from_node": "!00000001",
                "from_name": "WAYC",
                "to_node": to_node,
                "text": text,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "is_mine": True,
            }
            self._messages.append(new_msg)
            self.messagesChanged.emit()
            return {"success": True, "mock": True}

        try:
            result = self._client.send_mesh_message(text=text, to_node=to_node)
            self.messagesChanged.emit()
            return result
        except Exception as e:
            logger.error(f"Failed to send direct message: {e}")
            return {"success": False, "error": str(e)}

    # Conversation

    @Slot(str, int, result="QVariant")  # type: ignore[arg-type]
    def getConversation(self, node_id: str, limit: int = 50) -> dict[str, Any]:
        """Get conversation with a specific node."""
        if not self._backend_available or not self._client:
            # Filter mock messages for this node
            filtered = [
                m
                for m in self._messages
                if m.get("from_node") == node_id or m.get("to_node") == node_id
            ]
            return {"messages": filtered, "count": len(filtered)}

        try:
            result = self._client.get_mesh_conversation(node_id, limit)
            return result
        except Exception as e:
            logger.debug(f"Failed to get conversation: {e}")
            return {"messages": [], "count": 0}

    # Contacts/Favorites

    @Slot(result="QVariant")  # type: ignore[arg-type]
    def getNodesWithContacts(self) -> dict[str, Any]:
        """Get nodes with contact info merged (favorites, aliases, etc.)."""
        if not self._backend_available or not self._client:
            # Add mock favorite data to nodes
            nodes = self._get_mock_nodes()
            for i, node in enumerate(nodes):
                # Mark first node as favorite for demo
                node["is_favorite"] = i == 0
                node["alias"] = None
                node["notes"] = None
            # Sort favorites first
            nodes.sort(key=lambda n: (not n.get("is_favorite", False), n.get("short_name", "")))
            return {"nodes": nodes, "count": len(nodes)}

        try:
            result = self._client.get("/api/mesh/nodes/enriched")
            self._nodes = result.get("nodes", [])
            return result
        except Exception as e:
            logger.debug(f"Failed to get enriched nodes: {e}")
            return {"nodes": self._nodes, "count": len(self._nodes)}

    @Slot(str, result="QVariant")  # type: ignore[arg-type]
    def toggleFavorite(self, node_id: str) -> dict[str, Any]:
        """Toggle favorite status for a node."""
        if not self._backend_available or not self._client:
            # Update mock data
            for node in self._nodes:
                if node.get("node_id") == node_id:
                    node["is_favorite"] = not node.get("is_favorite", False)
                    self.nodesChanged.emit()
                    return {"node_id": node_id, "is_favorite": node["is_favorite"]}
            return {"node_id": node_id, "is_favorite": False}

        try:
            result = self._client.post(f"/api/mesh/contacts/{node_id}/favorite", json={})
            self.nodesChanged.emit()
            return result
        except Exception as e:
            logger.error(f"Failed to toggle favorite: {e}")
            return {"node_id": node_id, "is_favorite": False, "error": str(e)}

    @Slot(str, result="QVariant")  # type: ignore[arg-type]
    def getContact(self, node_id: str) -> dict[str, Any]:
        """Get contact info for a node."""
        if not self._backend_available or not self._client:
            # Return mock contact
            for node in self._nodes:
                if node.get("node_id") == node_id:
                    return {
                        "contact": {
                            "node_id": node_id,
                            "alias": node.get("alias"),
                            "notes": node.get("notes"),
                            "is_favorite": node.get("is_favorite", False),
                        }
                    }
            return {
                "contact": {"node_id": node_id, "alias": None, "notes": None, "is_favorite": False}
            }

        try:
            return self._client.get(f"/api/mesh/contacts/{node_id}")
        except Exception as e:
            logger.debug(f"Failed to get contact: {e}")
            return {
                "contact": {"node_id": node_id, "alias": None, "notes": None, "is_favorite": False}
            }

    @Slot(str, str, result=bool)  # type: ignore[arg-type]
    def setContactAlias(self, node_id: str, alias: str) -> bool:
        """Set alias for a contact."""
        if not self._backend_available or not self._client:
            for node in self._nodes:
                if node.get("node_id") == node_id:
                    node["alias"] = alias if alias else None
                    self.nodesChanged.emit()
                    return True
            return False

        try:
            self._client.put(f"/api/mesh/contacts/{node_id}", json={"alias": alias})
            self.nodesChanged.emit()
            return True
        except Exception as e:
            logger.error(f"Failed to set alias: {e}")
            return False

    # Properties

    @Property(bool, notify=statusChanged)  # type: ignore[arg-type]
    def isConnected(self) -> bool:
        """Whether connected to mesh network (always True for mock)."""
        return True  # Always show as connected for UX
