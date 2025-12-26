"""Mesh chat service for managing mesh network communication."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from device.drivers.mock.mesh_network import MockMeshNetwork
from device.libs.hil.interfaces.mesh_network import IMeshNetwork
from device.libs.schemas.meshtastic import (
    MeshMessage,
    MeshMessageCreate,
    MeshNode,
    NodeStatus,
)

if TYPE_CHECKING:
    from device.libs.database import MeshDatabase

logger = logging.getLogger(__name__)


class MeshChatService:
    """
    Service for managing mesh network chat functionality.

    Handles message sending/receiving, node tracking, and message persistence.
    """

    def __init__(
        self,
        mesh_driver: IMeshNetwork | None = None,
        db: MeshDatabase | None = None,
    ) -> None:
        """
        Initialize mesh chat service.

        Args:
            mesh_driver: Mesh network driver (defaults to MockMeshNetwork)
            db: MeshDatabase for message/contact persistence (optional)
        """
        self._driver = mesh_driver or MockMeshNetwork()
        self._db: MeshDatabase | None = db
        self._message_history: list[MeshMessage] = []
        self._history_loaded = False

        logger.info("MeshChatService initialized (db=%s)", "connected" if db else "none")

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
        """Persist a message to the database (async via task)."""
        if not self._db:
            return

        async def _save() -> None:
            try:
                assert self._db is not None
                await self._db.save_message(message)
                logger.debug(f"Persisted message {message.id} to database")
            except Exception as e:
                logger.error(f"Failed to persist message: {e}")

        # Schedule the async save
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(_save())
            else:
                loop.run_until_complete(_save())
        except RuntimeError:
            # No event loop available
            logger.warning("No event loop for message persistence")

    async def load_history_from_db(self, limit: int = 100) -> None:
        """Load message history from database."""
        if not self._db or self._history_loaded:
            return

        try:
            rows = await self._db.get_messages(limit=limit)
            logger.info(f"Loading {len(rows)} messages from database")

            for row in rows:
                # Convert database row to MeshMessage
                msg = self._row_to_message(row)
                if msg and msg.id not in [m.id for m in self._message_history]:
                    self._message_history.append(msg)

            self._history_loaded = True
            logger.info(f"Loaded {len(self._message_history)} messages into history")
        except Exception as e:
            logger.error(f"Failed to load message history: {e}")

    def _row_to_message(self, row: dict[str, Any]) -> MeshMessage | None:
        """Convert a database row to a MeshMessage."""
        try:
            return MeshMessage(
                id=str(row.get("message_id") or row.get("id", "")),
                from_node=row.get("from_node", ""),
                to_node=row.get("to_node"),
                channel=row.get("channel") or 0,
                text=row.get("content", ""),
                timestamp=(
                    datetime.fromisoformat(row["timestamp"]) if row.get("timestamp") else None
                ),
                rssi=row.get("rssi"),
                snr=row.get("snr"),
                hop_count=row.get("hop_count") or 0,
                acknowledged=bool(row.get("acknowledged")),
            )
        except Exception as e:
            logger.warning(f"Failed to parse message row: {e}")
            return None

    # Contact management

    async def get_contact(self, node_id: str) -> dict[str, Any] | None:
        """Get contact info for a node."""
        if not self._db:
            return None
        return await self._db.get_contact(node_id)

    async def get_all_contacts(self) -> list[dict[str, Any]]:
        """Get all mesh contacts."""
        if not self._db:
            return []
        return await self._db.get_all_contacts()

    async def get_favorite_contacts(self) -> list[dict[str, Any]]:
        """Get all favorited contacts."""
        if not self._db:
            return []
        return await self._db.get_favorite_contacts()

    async def toggle_favorite(self, node_id: str) -> bool:
        """Toggle favorite status. Returns new state."""
        if not self._db:
            logger.warning("No database for contact persistence")
            return False
        return await self._db.toggle_favorite(node_id)

    async def set_contact_alias(self, node_id: str, alias: str) -> dict[str, Any] | None:
        """Set alias for a contact."""
        if not self._db:
            return None
        return await self._db.upsert_contact(node_id, alias=alias)

    async def set_contact_notes(self, node_id: str, notes: str) -> dict[str, Any] | None:
        """Set notes for a contact."""
        if not self._db:
            return None
        return await self._db.upsert_contact(node_id, notes=notes)

    async def delete_contact(self, node_id: str) -> bool:
        """Delete a contact."""
        if not self._db:
            return False
        return await self._db.delete_contact(node_id)

    async def factory_reset(self) -> dict[str, int]:
        """
        Clear all mesh data (contacts and messages).

        Returns counts of deleted items.
        """
        if not self._db:
            return {"contacts": 0, "messages": 0}

        contacts_deleted = await self._db.delete_all_contacts()
        messages_deleted = await self._db.delete_all_messages()

        # Clear in-memory history
        self._message_history.clear()
        self._history_loaded = False

        return {
            "contacts": contacts_deleted,
            "messages": messages_deleted,
        }

    def get_nodes_with_contacts(self) -> list[dict[str, Any]]:
        """Get nodes with contact info merged (sync version for UI)."""
        nodes = self._driver.get_nodes()
        # Contact info will be loaded async in the API layer
        return [
            {
                **self._node_to_dict(n),
                "is_favorite": False,
                "alias": None,
                "notes": None,
            }
            for n in nodes
        ]

    def _node_to_dict(self, node: MeshNode) -> dict[str, Any]:
        """Convert MeshNode to dictionary."""
        return {
            "node_id": node.node_id,
            "short_name": node.short_name,
            "long_name": node.long_name,
            "hardware": (
                node.hardware.value if hasattr(node.hardware, "value") else str(node.hardware)
            ),
            "status": node.status.value if hasattr(node.status, "value") else str(node.status),
            "last_seen": node.last_seen.isoformat() if node.last_seen else None,
            "battery_level": node.battery_level,
            "snr": node.snr,
            "rssi": node.rssi,
            "hops_away": node.hops_away,
            "position": (
                {
                    "latitude": node.position.latitude,
                    "longitude": node.position.longitude,
                    "altitude": node.position.altitude,
                }
                if node.position
                else None
            ),
        }


# Singleton instance
_mesh_service: MeshChatService | None = None


def get_mesh_service() -> MeshChatService:
    """Get or create the mesh chat service singleton."""
    global _mesh_service
    if _mesh_service is None:
        _mesh_service = MeshChatService()
    return _mesh_service


def init_mesh_service(db: MeshDatabase | None = None) -> MeshChatService:
    """
    Initialize the mesh service singleton with database.

    Args:
        db: MeshDatabase for message/contact persistence

    Returns:
        The initialized mesh service
    """
    global _mesh_service
    _mesh_service = MeshChatService(db=db)
    return _mesh_service


def reset_mesh_service() -> None:
    """Reset the mesh service singleton (for testing)."""
    global _mesh_service
    _mesh_service = None
