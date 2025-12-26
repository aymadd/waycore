# Database Schema Documentation

> **Last Updated**: 2024-12-26

This document describes the database structure used in Waycore. The system uses SQLite databases organized by domain for better separation of concerns and modularity.

## Database Architecture

Waycore uses **three separate SQLite databases**, each dedicated to a specific domain:

| Database | File | Purpose | Service Owner |
|----------|------|---------|---------------|
| **General** | `general.sqlite3` | System settings, notes, sensors, events | data-logger |
| **Mesh** | `mesh.sqlite3` | Meshtastic contacts, messages | comms-bridge |
| **AI** | `ai.sqlite3` | AI inference logs | data-logger |

### Design Principles

1. **Domain Separation**: Large/important apps get dedicated databases (mesh, ai, maps in future)
2. **Shared General DB**: Smaller apps and system settings share the general database
3. **WAL Mode**: All databases use SQLite WAL mode for better concurrent access
4. **Docker Volume**: Databases are stored in a Docker named volume (`waycore-data`)

---

## General Database (`general.sqlite3`)

**Owner**: `data-logger` service
**Location**: `/app/data/general.sqlite3`

### Tables

#### `user_preferences`

User settings and configuration values.

| Column | Type | Description |
|--------|------|-------------|
| `key` | TEXT PRIMARY KEY | Preference key (e.g., `units.temperature`) |
| `value` | TEXT | Preference value |
| `updated_at` | TEXT | ISO 8601 timestamp |

**Default Values**:
```
units.temperature = "F"
units.distance = "mi"
units.weight = "lb"
units.pressure = "hPa"
units.time_format = "24h"
```

#### `notes`

User-created text notes.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Auto-incrementing ID |
| `title` | TEXT | Note title |
| `content` | TEXT | Note content/body |
| `created_at` | TEXT | ISO 8601 timestamp |
| `updated_at` | TEXT | ISO 8601 timestamp |

#### `sensors`

Registry of discovered sensors.

| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT PRIMARY KEY | Unique sensor ID |
| `type` | TEXT | Sensor type (temperature, gps, etc.) |
| `name` | TEXT | Human-readable name |
| `driver` | TEXT | Driver class name |
| `status` | TEXT | Current status (unknown, active, error) |
| `last_value` | TEXT | JSON-encoded last reading |
| `last_reading_at` | TEXT | ISO 8601 timestamp |
| `config` | TEXT | JSON-encoded configuration |
| `discovered_at` | TEXT | ISO 8601 timestamp |
| `updated_at` | TEXT | ISO 8601 timestamp |

#### `events`

System event log for debugging and analytics.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Auto-incrementing ID |
| `ts` | TEXT | ISO 8601 timestamp |
| `topic` | TEXT | Event topic/category |
| `payload` | TEXT | JSON-encoded event data |

**Indexes**:
- `idx_events_ts` on `ts`
- `idx_events_topic` on `topic`

---

## Mesh Database (`mesh.sqlite3`)

**Owner**: `comms-bridge` service
**Location**: `/app/data/mesh.sqlite3`

### Tables

#### `mesh_contacts`

Saved mesh node contacts (favorites, aliases, notes).

| Column | Type | Description |
|--------|------|-------------|
| `node_id` | TEXT PRIMARY KEY | Mesh node ID (e.g., `!a1b2c3d4`) |
| `alias` | TEXT | User-defined display name |
| `notes` | TEXT | User notes about this node |
| `is_favorite` | INTEGER | 1 if favorited, 0 otherwise |
| `created_at` | TEXT | ISO 8601 timestamp |
| `updated_at` | TEXT | ISO 8601 timestamp |

#### `mesh_messages`

Message history for mesh network communications.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Auto-incrementing ID |
| `message_id` | TEXT UNIQUE | Unique message identifier |
| `from_node` | TEXT | Sender node ID |
| `to_node` | TEXT | Recipient node ID (NULL for broadcast) |
| `channel` | INTEGER | Channel number (0-7) |
| `content` | TEXT | Message text content |
| `timestamp` | TEXT | ISO 8601 timestamp |
| `rssi` | REAL | Signal strength (dBm) |
| `snr` | REAL | Signal-to-noise ratio |
| `hop_count` | INTEGER | Number of routing hops |
| `acknowledged` | INTEGER | 1 if ACK received, 0 otherwise |
| `delivery_status` | TEXT | Status: pending, sending, sent, delivered, failed |
| `metadata` | TEXT | JSON-encoded additional data |

**Indexes**:
- `idx_mesh_messages_from` on `from_node`
- `idx_mesh_messages_to` on `to_node`
- `idx_mesh_messages_timestamp` on `timestamp`

---

## AI Database (`ai.sqlite3`)

**Owner**: `data-logger` service
**Location**: `/app/data/ai.sqlite3`

### Tables

#### `ai_inferences`

Log of AI/ML inference requests and responses.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Auto-incrementing ID |
| `ts` | TEXT | ISO 8601 timestamp |
| `request_id` | TEXT | UUID of the inference request |
| `model_id` | TEXT | Model identifier |
| `inference_type` | TEXT | Type: qa, classification, etc. |
| `success` | INTEGER | 1 if successful, 0 if failed |
| `results` | TEXT | JSON-encoded results |
| `error_message` | TEXT | Error message if failed |
| `latency_ms` | REAL | Processing time in milliseconds |
| `tokens_used` | INTEGER | Token count (if applicable) |

**Indexes**:
- `idx_ai_inferences_ts` on `ts`
- `idx_ai_inferences_model` on `model_id`

---

## Database Classes

The database operations are implemented in Python classes:

| Class | File | Description |
|-------|------|-------------|
| `GeneralDatabase` | `device/libs/database/general.py` | Preferences, notes, sensors, events |
| `MeshDatabase` | `device/libs/database/mesh.py` | Mesh contacts and messages |
| `AIDatabase` | `device/libs/database/ai.py` | AI inference logging |
| `BaseAsyncDatabase` | `device/libs/database/base.py` | Common async SQLite functionality |

### Usage Example

```python
from device.libs.database import MeshDatabase, GeneralDatabase

# Create and open database
mesh_db = MeshDatabase("data/mesh.sqlite3")
await mesh_db.open()

# Use database methods
await mesh_db.upsert_contact("!a1b2c3d4", alias="My Friend", is_favorite=True)
contacts = await mesh_db.get_all_contacts()

# Close when done
await mesh_db.close()
```

---

## Viewing Databases (Development)

In development mode, databases can be viewed via Datasette at:

- **http://localhost:8080/general** - General database
- **http://localhost:8080/mesh** - Mesh database
- **http://localhost:8080/ai** - AI database

---

## Migration Strategy

Currently, the system uses `CREATE TABLE IF NOT EXISTS` statements that run on service startup. For future migrations:

1. Schema changes should be backwards-compatible when possible
2. New columns should have defaults
3. Complex migrations should use versioned migration scripts

---

## Future Databases

As the system grows, new databases may be added for:

- **maps.sqlite3** - Offline maps and waypoints
- **media.sqlite3** - Media file metadata
- **sync.sqlite3** - Cloud sync state
