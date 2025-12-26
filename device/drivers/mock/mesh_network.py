"""Mock mesh network driver for development and testing."""

from __future__ import annotations

import random
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, cast

from device.libs.hil.interfaces.mesh_network import IMeshNetwork
from device.libs.schemas.meshtastic import (
    HardwareModel,
    MeshMessage,
    MeshMessageType,
    MeshNode,
    MeshPosition,
    NodeStatus,
)


class MockMeshNetwork(IMeshNetwork):
    """
    Mock implementation of mesh network for development.

    Simulates a mesh network with configurable peer nodes, message delivery
    with realistic delays, and node status changes.
    """

    # Default mock node configuration
    DEFAULT_PEERS = [
        {
            "node_id": "!a1b2c3d4",
            "short_name": "ALPH",
            "long_name": "Alpha Base",
            "hardware": HardwareModel.TBEAM,
            "position": {"latitude": 37.7749, "longitude": -122.4194, "altitude": 50},
            "battery_level": 85,
        },
        {
            "node_id": "!b2c3d4e5",
            "short_name": "BRVO",
            "long_name": "Bravo Team",
            "hardware": HardwareModel.TLORA_V2,
            "position": {"latitude": 37.7851, "longitude": -122.4094, "altitude": 75},
            "battery_level": 62,
        },
        {
            "node_id": "!c3d4e5f6",
            "short_name": "CHRL",
            "long_name": "Charlie Relay",
            "hardware": HardwareModel.HELTEC_V3,
            "position": {"latitude": 37.7699, "longitude": -122.4294, "altitude": 120},
            "battery_level": 100,
        },
        {
            "node_id": "!d4e5f6a7",
            "short_name": "DELT",
            "long_name": "Delta Scout",
            "hardware": HardwareModel.RAK4631,
            "position": {"latitude": 37.7600, "longitude": -122.4350, "altitude": 30},
            "battery_level": 45,
        },
        {
            "node_id": "!e5f6a7b8",
            "short_name": "ECHO",
            "long_name": "Echo Watch",
            "hardware": HardwareModel.TECHO,
            "position": None,  # No GPS
            "battery_level": 78,
        },
    ]

    def __init__(
        self,
        my_node_id: str = "!00000001",
        my_short_name: str = "WAYC",
        my_long_name: str = "Waycore Device",
        message_delay_ms: tuple[int, int] = (100, 500),
        packet_loss_percent: float = 5.0,
        node_churn_enabled: bool = True,
    ) -> None:
        """
        Initialize mock mesh network.

        Args:
            my_node_id: This device's node ID
            my_short_name: Short display name (max 4 chars)
            my_long_name: Full device name
            message_delay_ms: (min, max) simulated delivery delay in ms
            packet_loss_percent: Simulated packet loss rate
            node_churn_enabled: Whether nodes randomly go online/offline
        """
        self._my_node_id = my_node_id
        self._my_short_name = my_short_name
        self._my_long_name = my_long_name
        self._message_delay = message_delay_ms
        self._packet_loss = packet_loss_percent / 100
        self._node_churn = node_churn_enabled

        # Internal state
        self._nodes: dict[str, MeshNode] = {}
        self._messages: dict[str, MeshMessage] = {}
        self._pending_acks: dict[str, bool] = {}
        self._connected = True
        self._channel_name = "LongFast"

        # Thread safety
        self._lock = threading.Lock()

        # Initialize peer nodes
        self._initialize_peers()

        # Start background simulation if churn enabled
        if self._node_churn:
            self._start_simulation()

    def _initialize_peers(self) -> None:
        """Initialize mock peer nodes."""
        now = datetime.now(timezone.utc)

        for peer_data in self.DEFAULT_PEERS:
            peer = cast(dict[str, Any], peer_data)
            position = None
            if peer["position"]:
                pos_data = cast(dict[str, Any], peer["position"])
                position = MeshPosition(
                    latitude=pos_data["latitude"],
                    longitude=pos_data["longitude"],
                    altitude=pos_data.get("altitude"),
                    time=now,
                )

            node = MeshNode(
                node_id=peer["node_id"],
                short_name=peer["short_name"],
                long_name=peer["long_name"],
                hardware=peer["hardware"],
                position=position,
                last_seen=now - timedelta(seconds=random.randint(10, 300)),
                battery_level=peer["battery_level"],
                snr=random.uniform(5, 15),
                rssi=random.randint(-100, -60),
                status=NodeStatus.ONLINE,
                hops_away=random.randint(1, 3),
            )
            self._nodes[node.node_id] = node

    def _start_simulation(self) -> None:
        """Start background thread for node status simulation."""

        def simulate() -> None:
            while True:
                time.sleep(30)  # Update every 30 seconds
                with self._lock:
                    self._update_node_statuses()

        thread = threading.Thread(target=simulate, daemon=True)
        thread.start()

    def _update_node_statuses(self) -> None:
        """Randomly update node online/offline status."""
        now = datetime.now(timezone.utc)

        for node_id, node in self._nodes.items():
            # 10% chance to toggle status
            if random.random() < 0.1:
                new_status = (
                    NodeStatus.OFFLINE if node.status == NodeStatus.ONLINE else NodeStatus.ONLINE
                )

                # Create updated node (MeshNode is frozen)
                self._nodes[node_id] = MeshNode(
                    node_id=node.node_id,
                    short_name=node.short_name,
                    long_name=node.long_name,
                    hardware=node.hardware,
                    position=node.position,
                    last_seen=now if new_status == NodeStatus.ONLINE else node.last_seen,
                    battery_level=node.battery_level,
                    snr=node.snr,
                    rssi=node.rssi,
                    status=new_status,
                    hops_away=node.hops_away,
                )

    def get_my_node_id(self) -> str:
        """Get this device's node ID."""
        return self._my_node_id

    def get_my_node_info(self) -> MeshNode:
        """Get this device's full node information."""
        return MeshNode(
            node_id=self._my_node_id,
            short_name=self._my_short_name,
            long_name=self._my_long_name,
            hardware=HardwareModel.WAYCORE,
            position=MeshPosition(
                latitude=37.7749,
                longitude=-122.4194,
                altitude=25,
                time=datetime.now(timezone.utc),
            ),
            last_seen=datetime.now(timezone.utc),
            battery_level=85,
            status=NodeStatus.ONLINE,
        )

    def get_nodes(self) -> list[MeshNode]:
        """Get list of all known nodes on the mesh network."""
        with self._lock:
            return list(self._nodes.values())

    def get_node(self, node_id: str) -> MeshNode | None:
        """Get a specific node by ID."""
        with self._lock:
            return self._nodes.get(node_id)

    def send_message(
        self,
        text: str,
        to_node: str | None = None,
        channel: int = 0,
        want_ack: bool = True,
    ) -> str:
        """Send a text message over the mesh network."""
        message_id = f"msg_{uuid.uuid4().hex[:8]}"

        # Simulate packet loss
        if random.random() < self._packet_loss:
            # Message "lost" - create but mark as not acknowledged
            message = MeshMessage(
                id=message_id,
                from_node=self._my_node_id,
                to_node=to_node,
                channel=channel,
                text=text,
                timestamp=datetime.now(timezone.utc),
                want_ack=want_ack,
                acknowledged=False,
            )
            with self._lock:
                self._messages[message_id] = message
            return message_id

        # Simulate delivery delay
        delay = random.randint(*self._message_delay) / 1000

        def deliver_and_respond() -> None:
            time.sleep(delay)

            # Create outgoing message
            message = MeshMessage(
                id=message_id,
                from_node=self._my_node_id,
                to_node=to_node,
                channel=channel,
                text=text,
                timestamp=datetime.now(timezone.utc),
                want_ack=want_ack,
                acknowledged=True,
                hop_count=random.randint(0, 3),
            )

            with self._lock:
                self._messages[message_id] = message

                # Generate mock response after another delay
                if to_node and random.random() < 0.7:  # 70% response rate
                    self._generate_mock_response(to_node, channel)

        thread = threading.Thread(target=deliver_and_respond, daemon=True)
        thread.start()

        return message_id

    def _generate_mock_response(self, from_node: str, channel: int) -> None:
        """Generate a mock response message from a peer."""
        time.sleep(random.uniform(1, 5))  # Delay before response

        node = self._nodes.get(from_node)
        if not node or node.status != NodeStatus.ONLINE:
            return

        responses = [
            "Copy that!",
            "Roger",
            "10-4",
            "Acknowledged",
            f"This is {node.short_name}, received!",
            "Message received, standing by",
            "Affirmative",
        ]

        response_id = f"msg_{uuid.uuid4().hex[:8]}"
        response = MeshMessage(
            id=response_id,
            from_node=from_node,
            to_node=self._my_node_id,
            channel=channel,
            text=random.choice(responses),
            timestamp=datetime.now(timezone.utc),
            rx_time=datetime.now(timezone.utc),
            acknowledged=True,
            snr=random.uniform(5, 15),
            rssi=random.randint(-100, -60),
        )

        self._messages[response_id] = response

    def receive_messages(self, since: datetime | None = None) -> list[MeshMessage]:
        """Get received messages."""
        with self._lock:
            messages = [
                msg
                for msg in self._messages.values()
                if msg.from_node != self._my_node_id  # Only received messages
            ]

            if since:
                messages = [msg for msg in messages if msg.rx_time and msg.rx_time > since]

            return sorted(messages, key=lambda m: m.timestamp)

    def get_message(self, message_id: str) -> MeshMessage | None:
        """Get a specific message by ID."""
        with self._lock:
            return self._messages.get(message_id)

    def is_connected(self) -> bool:
        """Check if mesh radio is connected and operational."""
        return self._connected

    def get_channel_name(self, channel: int = 0) -> str:
        """Get the name of a channel."""
        if channel == 0:
            return self._channel_name
        return f"Channel {channel}"

    # Mock-specific methods for testing

    def simulate_incoming_message(
        self,
        from_node: str,
        text: str,
        channel: int = 0,
    ) -> str:
        """Simulate receiving a message from a peer (for testing)."""
        message_id = f"msg_{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc)

        message = MeshMessage(
            id=message_id,
            from_node=from_node,
            to_node=self._my_node_id,
            channel=channel,
            message_type=MeshMessageType.TEXT,
            text=text,
            timestamp=now - timedelta(milliseconds=random.randint(100, 500)),
            rx_time=now,
            hop_count=random.randint(0, 3),
            acknowledged=True,
            snr=random.uniform(5, 15),
            rssi=random.randint(-100, -60),
        )

        with self._lock:
            self._messages[message_id] = message

        return message_id

    def set_connected(self, connected: bool) -> None:
        """Set radio connection status (for testing)."""
        self._connected = connected

    def set_node_status(self, node_id: str, status: NodeStatus) -> None:
        """Set a specific node's status (for testing)."""
        with self._lock:
            if node_id in self._nodes:
                node = self._nodes[node_id]
                self._nodes[node_id] = MeshNode(
                    node_id=node.node_id,
                    short_name=node.short_name,
                    long_name=node.long_name,
                    hardware=node.hardware,
                    position=node.position,
                    last_seen=(
                        datetime.now(timezone.utc)
                        if status == NodeStatus.ONLINE
                        else node.last_seen
                    ),
                    battery_level=node.battery_level,
                    snr=node.snr,
                    rssi=node.rssi,
                    status=status,
                    hops_away=node.hops_away,
                )

    def get_all_messages(self) -> list[MeshMessage]:
        """Get all messages including sent (for testing)."""
        with self._lock:
            return sorted(self._messages.values(), key=lambda m: m.timestamp)


def register(_: object) -> None:
    """Register the mock mesh network driver with the factory."""
    from device.libs.hil.factory import DriverFactory

    DriverFactory.register_mesh_network(
        "mock_mesh_network",
        lambda cfg: MockMeshNetwork(**dict(cfg)) if cfg else MockMeshNetwork(),
    )
