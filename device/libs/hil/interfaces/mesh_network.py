"""Hardware interface for mesh network communication."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from device.libs.schemas.meshtastic import MeshMessage, MeshNode


class IMeshNetwork(ABC):
    """
    Hardware abstraction interface for mesh network radios.

    This interface abstracts mesh networking hardware (like Meshtastic/LoRa radios)
    allowing both mock implementations for development and real hardware drivers.
    """

    @abstractmethod
    def get_my_node_id(self) -> str:
        """
        Get this device's node ID.

        Returns:
            Node ID in format !xxxxxxxx (e.g., !12345678)
        """

    @abstractmethod
    def get_my_node_info(self) -> MeshNode:
        """
        Get this device's full node information.

        Returns:
            MeshNode with this device's identity and status
        """

    @abstractmethod
    def get_nodes(self) -> list[MeshNode]:
        """
        Get list of all known nodes on the mesh network.

        Returns:
            List of MeshNode objects for discovered peers
        """

    @abstractmethod
    def get_node(self, node_id: str) -> MeshNode | None:
        """
        Get a specific node by ID.

        Args:
            node_id: Node ID to look up

        Returns:
            MeshNode if found, None otherwise
        """

    @abstractmethod
    def send_message(
        self,
        text: str,
        to_node: str | None = None,
        channel: int = 0,
        want_ack: bool = True,
    ) -> str:
        """
        Send a text message over the mesh network.

        Args:
            text: Message content (max 237 chars)
            to_node: Recipient node ID, or None for broadcast
            channel: Channel index (0-7)
            want_ack: Whether to request delivery acknowledgment

        Returns:
            Message ID for tracking
        """

    @abstractmethod
    def receive_messages(self, since: datetime | None = None) -> list[MeshMessage]:
        """
        Get received messages.

        Args:
            since: Only return messages after this time (optional)

        Returns:
            List of received MeshMessage objects
        """

    @abstractmethod
    def get_message(self, message_id: str) -> MeshMessage | None:
        """
        Get a specific message by ID.

        Args:
            message_id: Message ID to retrieve

        Returns:
            MeshMessage if found, None otherwise
        """

    @abstractmethod
    def is_connected(self) -> bool:
        """
        Check if mesh radio is connected and operational.

        Returns:
            True if radio is ready for communication
        """

    @abstractmethod
    def get_channel_name(self, channel: int = 0) -> str:
        """
        Get the name of a channel.

        Args:
            channel: Channel index (0-7)

        Returns:
            Channel name string
        """
