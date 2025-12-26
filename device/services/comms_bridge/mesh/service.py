"""Mesh chat service for managing mesh network communication."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from device.drivers.mock.mesh_network import MockMeshNetwork
from device.libs.hil.interfaces.mesh_network import IMeshNetwork
from device.libs.schemas.meshtastic import (
    MeshMessage,
    MeshMessageCreate,
    MeshNode,
    NodeStatus,
)

logger = logging.getLogger(__name__)


class MeshChatService:
    """
    Service for managing mesh network chat functionality.

    Handles message sending/receiving, node tracking, and message persistence.
    """

    def __init__(
        self,
        mesh_driver: IMeshNetwork | None = None,
        db: Any | None = None,
    ) -> None:
        """
        Initialize mesh chat service.

        Args:
            mesh_driver: Mesh network driver (defaults to MockMeshNetwork)
            db: Database connection for message persistence (optional)
        """
        self._driver = mesh_driver or MockMeshNetwork()
        self._db = db
        self._message_history: list[MeshMessage] = []

        logger.info("MeshChatService initialized")

    @property
    def my_node_id(self) -> str:
        """Get this device's node ID."""
        return self._driver.get_my_node_id()

    @property
    def my_node_info(self) -> MeshNode:
        """Get this device's node info."""
        return self._driver.get_my_node_info()

    @property
    def is_connected(self) -> bool:
        """Check if mesh network is connected."""
        return self._driver.is_connected()

    # Node management

    def get_nodes(self) -> list[MeshNode]:
        """Get all known mesh nodes."""
        return self._driver.get_nodes()

    def get_node(self, node_id: str) -> MeshNode | None:
        """Get a specific node by ID."""
        return self._driver.get_node(node_id)

    def get_online_nodes(self) -> list[MeshNode]:
        """Get only online nodes."""
        return [n for n in self._driver.get_nodes() if n.status == NodeStatus.ONLINE]

    def get_node_count(self) -> dict[str, int]:
        """Get node counts by status."""
        nodes = self._driver.get_nodes()
        return {
            "total": len(nodes),
            "online": len([n for n in nodes if n.status == NodeStatus.ONLINE]),
            "offline": len([n for n in nodes if n.status == NodeStatus.OFFLINE]),
        }

    # Message handling

    def send_message(self, message: MeshMessageCreate) -> MeshMessage:
        """
        Send a message over the mesh network.

        Args:
            message: Message to send

        Returns:
            The sent message with ID and metadata
        """
        msg_id = self._driver.send_message(
            text=message.text,
            to_node=message.to_node,
            channel=message.channel,
            want_ack=message.want_ack,
        )

        # Create message record
        sent_message = MeshMessage(
            id=msg_id,
            from_node=self._driver.get_my_node_id(),
            to_node=message.to_node,
            channel=message.channel,
            text=message.text,
            timestamp=datetime.now(timezone.utc),
            want_ack=message.want_ack,
            acknowledged=False,  # Will be updated later
        )

        self._message_history.append(sent_message)

        # Persist to database if available
        if self._db:
            self._persist_message(sent_message)

        logger.debug(f"Sent message {msg_id} to {message.to_node or 'broadcast'}")
        return sent_message

    def get_messages(
        self,
        since: datetime | None = None,
        limit: int = 100,
        node_id: str | None = None,
    ) -> list[MeshMessage]:
        """
        Get message history.

        Args:
            since: Only return messages after this time
            limit: Maximum number of messages to return
            node_id: Filter by sender/recipient node ID

        Returns:
            List of messages, newest first
        """
        # Get received messages from driver
        received = self._driver.receive_messages(since=since)

        # Add to history
        for msg in received:
            if msg.id not in [m.id for m in self._message_history]:
                self._message_history.append(msg)
                if self._db:
                    self._persist_message(msg)

        # Filter and sort
        messages = self._message_history.copy()

        if since:
            messages = [m for m in messages if m.timestamp > since]

        if node_id:
            messages = [m for m in messages if m.from_node == node_id or m.to_node == node_id]

        # Sort by timestamp descending
        messages = sorted(messages, key=lambda m: m.timestamp, reverse=True)

        return messages[:limit]

    def get_message(self, message_id: str) -> MeshMessage | None:
        """Get a specific message by ID."""
        # Check local history first
        for msg in self._message_history:
            if msg.id == message_id:
                return msg

        # Check driver
        return self._driver.get_message(message_id)

    def get_conversation(
        self,
        node_id: str,
        limit: int = 50,
    ) -> list[MeshMessage]:
        """
        Get conversation with a specific node.

        Args:
            node_id: Node ID to get conversation with
            limit: Maximum number of messages

        Returns:
            List of messages in the conversation
        """
        return self.get_messages(node_id=node_id, limit=limit)

    # Network status

    def get_status(self) -> dict[str, Any]:
        """Get overall mesh network status."""
        nodes = self._driver.get_nodes()
        online_count = len([n for n in nodes if n.status == NodeStatus.ONLINE])

        return {
            "connected": self._driver.is_connected(),
            "my_node_id": self._driver.get_my_node_id(),
            "channel_name": self._driver.get_channel_name(),
            "nodes": {
                "total": len(nodes),
                "online": online_count,
                "offline": len(nodes) - online_count,
            },
            "messages": {
                "total": len(self._message_history),
                "sent": len([m for m in self._message_history if m.from_node == self.my_node_id]),
                "received": len(
                    [m for m in self._message_history if m.from_node != self.my_node_id]
                ),
            },
        }

    # Database persistence

    def _persist_message(self, message: MeshMessage) -> None:
        """Persist a message to the database."""
        if not self._db:
            return

        try:
            # This would use the actual database methods
            # For now, just log
            logger.debug(f"Would persist message {message.id} to database")
        except Exception as e:
            logger.error(f"Failed to persist message: {e}")

    async def load_history_from_db(self, limit: int = 100) -> None:
        """Load message history from database."""
        if not self._db:
            return

        try:
            # This would load from actual database
            logger.debug(f"Would load last {limit} messages from database")
        except Exception as e:
            logger.error(f"Failed to load message history: {e}")


# Singleton instance
_mesh_service: MeshChatService | None = None


def get_mesh_service() -> MeshChatService:
    """Get or create the mesh chat service singleton."""
    global _mesh_service
    if _mesh_service is None:
        _mesh_service = MeshChatService()
    return _mesh_service


def reset_mesh_service() -> None:
    """Reset the mesh service singleton (for testing)."""
    global _mesh_service
    _mesh_service = None
