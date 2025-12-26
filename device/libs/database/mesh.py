"""Mesh/Meshtastic database for node contacts and messages."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from .base import BaseAsyncDatabase

if TYPE_CHECKING:
    from device.libs.schemas.meshtastic import MeshMessage


class MeshDatabase(BaseAsyncDatabase):
    """
    Database for Meshtastic/mesh network data.

    Tables:
    - mesh_contacts: Node favorites, aliases, and notes
    - mesh_messages: Message history with signal metadata
    - mesh_nodes: Cached node information (future)
    """

    def _get_schema(self) -> str:
        return """
            CREATE TABLE IF NOT EXISTS mesh_contacts (
                node_id TEXT PRIMARY KEY NOT NULL,
                alias TEXT,
                notes TEXT,
                is_favorite INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
            );

            CREATE TABLE IF NOT EXISTS mesh_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT UNIQUE,
                from_node TEXT NOT NULL,
                to_node TEXT,
                channel INTEGER DEFAULT 0,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                rssi REAL,
                snr REAL,
                hop_count INTEGER,
                acknowledged INTEGER DEFAULT 0,
                delivery_status TEXT DEFAULT 'sent',
                metadata TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_mesh_messages_from ON mesh_messages(from_node);
            CREATE INDEX IF NOT EXISTS idx_mesh_messages_to ON mesh_messages(to_node);
            CREATE INDEX IF NOT EXISTS idx_mesh_messages_timestamp ON mesh_messages(timestamp);
        """

    # --- Contacts ---

    async def get_contact(self, node_id: str) -> dict[str, Any] | None:
        """Get a mesh contact by node ID."""
        return await self.fetchone(
            "SELECT * FROM mesh_contacts WHERE node_id = ?",
            (node_id,),
        )

    async def get_all_contacts(self) -> list[dict[str, Any]]:
        """Get all mesh contacts, favorites first."""
        return await self.fetchall(
            "SELECT * FROM mesh_contacts ORDER BY is_favorite DESC, alias ASC, node_id ASC"
        )

    async def get_favorite_contacts(self) -> list[dict[str, Any]]:
        """Get only favorited contacts."""
        return await self.fetchall(
            "SELECT * FROM mesh_contacts WHERE is_favorite = 1 ORDER BY alias ASC, node_id ASC"
        )

    async def upsert_contact(
        self,
        node_id: str,
        alias: str | None = None,
        notes: str | None = None,
        is_favorite: bool | None = None,
    ) -> dict[str, Any]:
        """Create or update a mesh contact."""
        existing = await self.get_contact(node_id)

        if existing:
            updates = []
            params: list[Any] = []
            if alias is not None:
                updates.append("alias = ?")
                params.append(alias)
            if notes is not None:
                updates.append("notes = ?")
                params.append(notes)
            if is_favorite is not None:
                updates.append("is_favorite = ?")
                params.append(1 if is_favorite else 0)
            if updates:
                updates.append("updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now')")
                params.append(node_id)
                await self.execute(
                    f"UPDATE mesh_contacts SET {', '.join(updates)} WHERE node_id = ?",
                    tuple(params),
                )
                await self.commit()
        else:
            await self.execute(
                """
                INSERT INTO mesh_contacts (node_id, alias, notes, is_favorite)
                VALUES (?, ?, ?, ?)
                """,
                (node_id, alias, notes, 1 if is_favorite else 0),
            )
            await self.commit()

        result = await self.get_contact(node_id)
        assert result is not None
        return result

    async def toggle_favorite(self, node_id: str) -> bool:
        """Toggle favorite status for a node. Returns new favorite state."""
        existing = await self.get_contact(node_id)
        if existing:
            new_state = not bool(existing["is_favorite"])
            await self.execute(
                """
                UPDATE mesh_contacts
                SET is_favorite = ?, updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now')
                WHERE node_id = ?
                """,
                (1 if new_state else 0, node_id),
            )
        else:
            new_state = True
            await self.execute(
                "INSERT INTO mesh_contacts (node_id, is_favorite) VALUES (?, 1)",
                (node_id,),
            )
        await self.commit()
        return new_state

    async def delete_contact(self, node_id: str) -> bool:
        """Delete a mesh contact. Returns True if deleted."""
        cursor = await self.execute(
            "DELETE FROM mesh_contacts WHERE node_id = ?",
            (node_id,),
        )
        await self.commit()
        return bool(cursor.rowcount)

    async def delete_all_contacts(self) -> int:
        """Delete all mesh contacts. Returns count deleted."""
        cursor = await self.execute("DELETE FROM mesh_contacts")
        await self.commit()
        return int(cursor.rowcount) if cursor.rowcount else 0

    # --- Messages ---

    async def save_message(
        self,
        message: MeshMessage | None = None,
        *,
        message_id: str = "",
        from_node: str = "",
        to_node: str | None = None,
        text: str = "",
        channel: int = 0,
        rssi: float | None = None,
        snr: float | None = None,
        hop_count: int | None = None,
        acknowledged: bool = False,
    ) -> None:
        """Save a mesh message."""
        if message is not None:
            message_id = message.id
            from_node = message.from_node
            to_node = message.to_node
            text = message.text
            channel = message.channel
            rssi = float(message.rssi) if message.rssi is not None else None
            snr = message.snr
            hop_count = message.hop_count
            acknowledged = message.acknowledged
            ts = message.timestamp.isoformat() if message.timestamp else None
        else:
            ts = None

        metadata = json.dumps({"message_id": message_id, "channel": channel})
        await self.execute(
            """
            INSERT OR REPLACE INTO mesh_messages
            (message_id, from_node, to_node, channel, content, timestamp, rssi, snr,
             hop_count, acknowledged, metadata)
            VALUES (?, ?, ?, ?, ?, COALESCE(?, strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                    ?, ?, ?, ?, ?)
            """,
            (
                message_id,
                from_node,
                to_node,
                channel,
                text,
                ts,
                rssi,
                snr,
                hop_count,
                1 if acknowledged else 0,
                metadata,
            ),
        )
        await self.commit()

    async def get_messages(
        self,
        limit: int = 100,
        node_id: str | None = None,
        channel: int | None = None,
    ) -> list[dict[str, Any]]:
        """Get mesh messages with optional filters."""
        conditions = []
        params: list[Any] = []

        if node_id:
            conditions.append("(from_node = ? OR to_node = ?)")
            params.extend([node_id, node_id])
        if channel is not None:
            conditions.append("channel = ?")
            params.append(channel)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        params.append(limit)

        return await self.fetchall(
            f"""
            SELECT * FROM mesh_messages
            {where_clause}
            ORDER BY timestamp DESC LIMIT ?
            """,
            tuple(params),
        )

    async def get_conversation(self, node_id: str, limit: int = 50) -> list[dict[str, Any]]:
        """Get conversation with a specific node (DMs only)."""
        return await self.fetchall(
            """
            SELECT * FROM mesh_messages
            WHERE (from_node = ? OR to_node = ?) AND to_node IS NOT NULL
            ORDER BY timestamp DESC LIMIT ?
            """,
            (node_id, node_id, limit),
        )

    async def update_delivery_status(self, message_id: str, status: str) -> bool:
        """Update delivery status for a message."""
        cursor = await self.execute(
            "UPDATE mesh_messages SET delivery_status = ? WHERE message_id = ?",
            (status, message_id),
        )
        await self.commit()
        return bool(cursor.rowcount)

    async def delete_all_messages(self) -> int:
        """Delete all mesh messages. Returns count deleted."""
        cursor = await self.execute("DELETE FROM mesh_messages")
        await self.commit()
        return int(cursor.rowcount) if cursor.rowcount else 0
