# Meshtastic Integration Architecture

## Overview

Meshtastic is an open-source mesh networking project that enables long-range, off-grid communication using inexpensive LoRa radios. Our integration provides mesh messaging capabilities for Waycore devices.

## Key Concepts

### Nodes
A **node** is any device on the mesh network. Each node has:
- **Node ID**: Unique 8-character hex identifier (e.g., `!a1b2c3d4`)
- **Short Name**: 4-character display name
- **Long Name**: Full device name
- **Hardware Model**: Device type (T-Beam, T-Echo, Heltec, etc.)
- **Position**: Optional GPS coordinates
- **Last Seen**: Timestamp of last activity
- **Battery Level**: Power status (if available)

### Channels
**Channels** are logical communication groups:
- **Primary Channel (0)**: Default channel for general mesh communication
- **Secondary Channels (1-7)**: Additional encrypted channels for private groups
- Each channel has a name, PSK (pre-shared key), and settings

### Messages
**Messages** are the core communication unit:
- **Text Messages**: User-sent text content
- **Waypoints**: Shared location markers
- **Telemetry**: Device health data (battery, environment)
- **Position Updates**: GPS broadcasts

### Packet Types
| Type | Description | Direction |
|------|-------------|-----------|
| TEXT_MESSAGE_APP | User text messages | Bidirectional |
| POSITION_APP | GPS position broadcasts | Bidirectional |
| NODEINFO_APP | Node discovery/info | Bidirectional |
| TELEMETRY_APP | Device metrics | Outbound |
| WAYPOINT_APP | Shared waypoints | Bidirectional |
| ROUTING_APP | Mesh routing/ACKs | Internal |

## Our Implementation

### MVP Scope (Phase 13)

1. **Mock Mesh Network**: Simulated nodes for development
2. **Text Messaging**: Send/receive messages on primary channel
3. **Node Discovery**: View online nodes with last-seen status
4. **Position Sharing**: Display node positions on compass/map

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                       Waycore Device                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐     ┌──────────────┐     ┌─────────────┐  │
│  │   Mesh UI    │────▶│  Mesh Chat   │────▶│   Comms     │  │
│  │  (QML/Qt)    │     │   Service    │     │   Bridge    │  │
│  └──────────────┘     └──────────────┘     └─────────────┘  │
│         │                    │                    │          │
│         │                    │                    ▼          │
│         │                    │            ┌─────────────┐    │
│         │                    └───────────▶│   Radio     │    │
│         │                                 │   Manager   │    │
│         │                                 └─────────────┘    │
│         │                                        │           │
│         ▼                                        ▼           │
│  ┌──────────────┐                        ┌─────────────┐    │
│  │  Mesh Nodes  │                        │   LoRa      │    │
│  │     UI       │                        │  Driver     │    │
│  └──────────────┘                        └─────────────┘    │
│                                                  │           │
└──────────────────────────────────────────────────┼───────────┘
                                                   │
                                                   ▼
                                          ┌───────────────┐
                                          │  LoRa Radio   │
                                          │  (Hardware)   │
                                          └───────────────┘
```

### Component Responsibilities

#### Mesh Chat Service (`device/services/mesh_chat/`)
- Manages message queue and history
- Handles node presence tracking
- Provides API endpoints for UI
- Communicates with Comms Bridge via MQTT

#### Comms Bridge (`device/services/comms_bridge/`)
- Already exists from Phase 6
- Radio Manager handles LoRa interface
- Routes mesh packets to/from Mesh Chat Service

#### LoRa Driver (`device/drivers/mock/lora.py` → `device/drivers/real/lora.py`)
- Mock: Simulates mesh network behavior
- Real: Interfaces with Meshtastic firmware via serial/USB

### Data Flow

#### Sending a Message
```
1. User types message in UI
2. UI calls Mesh Chat Service API: POST /api/mesh/messages
3. Service creates MeshMessage, publishes to MQTT
4. Comms Bridge receives, sends to Radio Manager
5. Radio Manager serializes and sends via LoRa Driver
6. LoRa Driver transmits over radio
```

#### Receiving a Message
```
1. LoRa Driver receives packet
2. Radio Manager parses MeshPacket
3. Published to MQTT topic: mesh/rx/<node_id>
4. Mesh Chat Service receives, stores in database
5. WebSocket/polling notifies UI
6. UI displays new message
```

### Mock Network Topology

For development, we simulate a 5-node mesh network:

```
          [Alpha]
         /        \
    [Bravo]      [Charlie]
       |     \    /    |
   [Delta]   [Echo]   (our device)
```

Mock Nodes:
| Node ID | Short Name | Long Name | Role |
|---------|------------|-----------|------|
| !a1b2c3d4 | ALPH | Alpha Base | Hub node |
| !b2c3d4e5 | BRVO | Bravo Team | Mobile |
| !c3d4e5f6 | CHRL | Charlie | Fixed relay |
| !d4e5f6a7 | DELT | Delta Scout | Mobile |
| !e5f6a7b8 | ECHO | Echo Watch | Fixed |

### Message Schema

```python
class MeshMessage(BaseModel):
    id: str                    # Unique message ID
    from_node: str             # Sender node ID
    to_node: str | None        # Recipient (None = broadcast)
    channel: int = 0           # Channel index
    text: str                  # Message content
    timestamp: datetime        # When sent
    hop_count: int = 0         # Routing hops
    acknowledged: bool = False # Delivery confirmed
```

### Node Schema

```python
class MeshNode(BaseModel):
    node_id: str               # Unique ID (!hex)
    short_name: str            # 4-char display name
    long_name: str             # Full name
    hardware: str              # Device model
    position: Position | None  # GPS if available
    last_seen: datetime        # Last activity
    battery_level: int | None  # 0-100 if available
    snr: float | None          # Signal-to-noise ratio
    is_online: bool            # Currently reachable
```

## Security Considerations

### Encryption
- All channels use AES-256 encryption
- PSK (Pre-Shared Key) required to join channel
- Default channel uses published key (not secure for private comms)

### Privacy
- Node IDs are pseudonymous but persistent
- Position sharing is optional and user-controlled
- Message history stored locally only

## Future Enhancements (Beyond MVP)

- [ ] Multiple channel support
- [ ] Direct messages (node-to-node)
- [ ] Waypoint sharing
- [ ] Telemetry dashboard
- [ ] Node management (rename, configure)
- [ ] Real Meshtastic hardware integration
- [ ] TAK (Team Awareness Kit) interoperability

## References

- [Meshtastic Documentation](https://meshtastic.org/docs/)
- [Meshtastic Python API](https://github.com/meshtastic/python)
- [LoRa Modulation](https://meshtastic.org/docs/overview/radio-settings)
- [Protocol Buffers Definitions](https://github.com/meshtastic/protobufs)
