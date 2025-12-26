from __future__ import annotations

from datetime import datetime
from typing import Any

from device.libs.schemas.comms import SendMessageRequest
from device.libs.schemas.meshtastic import MeshMessageCreate
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from .mesh.service import get_mesh_service
from .service import CommsBridgeService


class ContactUpdate(BaseModel):
    """Request body for updating contact info."""

    alias: str | None = Field(default=None, max_length=50)
    notes: str | None = Field(default=None, max_length=500)


def create_app(service: CommsBridgeService) -> FastAPI:
    app = FastAPI(title="Comms Bridge API")

    @app.get("/health")
    async def health() -> dict[str, Any]:
        if service.is_healthy():
            return {"status": "ok"}
        raise HTTPException(status_code=503, detail="not ready")

    @app.get("/api/radios")
    async def radios() -> dict[str, Any]:
        status = await service._manager.get_status()  # deliberately accessing for MVP
        return {"radios": {k: s.__dict__ for k, s in status.items()}}

    @app.post("/api/send")
    async def send(req: SendMessageRequest) -> dict[str, Any]:
        ok = await service._manager.send(
            content=req.content.encode("utf-8"),
            transport_hint=req.transport.value,
            to_node=req.to_node,
            channel=req.channel,
            want_ack=req.want_ack,
        )
        return {"success": ok}

    # --- Mesh Chat Endpoints ---

    @app.get("/api/mesh/status")
    async def mesh_status() -> dict[str, Any]:
        """Get mesh network status."""
        mesh = get_mesh_service()
        return mesh.get_status()

    @app.get("/api/mesh/nodes")
    async def mesh_nodes(
        online_only: bool = Query(False, description="Only return online nodes"),
    ) -> dict[str, Any]:
        """Get list of mesh nodes."""
        mesh = get_mesh_service()

        if online_only:
            nodes = mesh.get_online_nodes()
        else:
            nodes = mesh.get_nodes()

        return {
            "nodes": [_node_to_dict(n) for n in nodes],
            "count": len(nodes),
            "my_node": _node_to_dict(mesh.my_node_info),
        }

    @app.get("/api/mesh/nodes/{node_id}")
    async def mesh_node(node_id: str) -> dict[str, Any]:
        """Get a specific mesh node."""
        mesh = get_mesh_service()
        node = mesh.get_node(node_id)

        if not node:
            raise HTTPException(status_code=404, detail="Node not found")

        return {"node": _node_to_dict(node)}

    @app.get("/api/mesh/messages")
    async def mesh_messages(
        limit: int = Query(100, ge=1, le=500, description="Max messages to return"),
        since: str | None = Query(None, description="ISO timestamp to filter from"),
        node_id: str | None = Query(None, description="Filter by node ID"),
    ) -> dict[str, Any]:
        """Get mesh message history."""
        mesh = get_mesh_service()

        since_dt = None
        if since:
            try:
                since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid timestamp: {e}") from e

        messages = mesh.get_messages(since=since_dt, limit=limit, node_id=node_id)

        return {
            "messages": [_message_to_dict(m) for m in messages],
            "count": len(messages),
        }

    @app.get("/api/mesh/messages/{message_id}")
    async def mesh_message(message_id: str) -> dict[str, Any]:
        """Get a specific message."""
        mesh = get_mesh_service()
        message = mesh.get_message(message_id)

        if not message:
            raise HTTPException(status_code=404, detail="Message not found")

        return {"message": _message_to_dict(message)}

    @app.post("/api/mesh/messages")
    async def send_mesh_message(req: MeshMessageCreate) -> dict[str, Any]:
        """Send a mesh message."""
        mesh = get_mesh_service()

        if not mesh.is_connected:
            raise HTTPException(status_code=503, detail="Mesh network not connected")

        message = mesh.send_message(req)

        return {
            "success": True,
            "message": _message_to_dict(message),
        }

    @app.get("/api/mesh/conversation/{node_id}")
    async def mesh_conversation(
        node_id: str,
        limit: int = Query(50, ge=1, le=200),
    ) -> dict[str, Any]:
        """Get conversation with a specific node."""
        mesh = get_mesh_service()

        node = mesh.get_node(node_id)
        if not node:
            raise HTTPException(status_code=404, detail="Node not found")

        messages = mesh.get_conversation(node_id, limit=limit)

        return {
            "node": _node_to_dict(node),
            "messages": [_message_to_dict(m) for m in messages],
            "count": len(messages),
        }

    # --- Mesh Contacts/Favorites Endpoints ---

    @app.get("/api/mesh/contacts")
    async def get_contacts() -> dict[str, Any]:
        """Get all mesh contacts."""
        mesh = get_mesh_service()
        contacts = await mesh.get_all_contacts()
        return {"contacts": contacts, "count": len(contacts)}

    @app.get("/api/mesh/contacts/favorites")
    async def get_favorites() -> dict[str, Any]:
        """Get favorite contacts only."""
        mesh = get_mesh_service()
        favorites = await mesh.get_favorite_contacts()
        return {"favorites": favorites, "count": len(favorites)}

    @app.get("/api/mesh/contacts/{node_id}")
    async def get_contact(node_id: str) -> dict[str, Any]:
        """Get contact info for a node."""
        mesh = get_mesh_service()
        contact = await mesh.get_contact(node_id)
        if not contact:
            # Return empty contact info if not found
            return {
                "contact": {
                    "node_id": node_id,
                    "alias": None,
                    "notes": None,
                    "is_favorite": False,
                }
            }
        return {"contact": contact}

    @app.post("/api/mesh/contacts/{node_id}/favorite")
    async def toggle_favorite(node_id: str) -> dict[str, Any]:
        """Toggle favorite status for a node."""
        mesh = get_mesh_service()
        new_state = await mesh.toggle_favorite(node_id)
        return {"node_id": node_id, "is_favorite": new_state}

    @app.put("/api/mesh/contacts/{node_id}")
    async def update_contact(node_id: str, update: ContactUpdate) -> dict[str, Any]:
        """Update contact alias or notes."""
        mesh = get_mesh_service()

        if update.alias is not None:
            await mesh.set_contact_alias(node_id, update.alias)
        if update.notes is not None:
            await mesh.set_contact_notes(node_id, update.notes)

        contact = await mesh.get_contact(node_id)
        return {"contact": contact}

    @app.delete("/api/mesh/contacts/{node_id}")
    async def delete_contact(node_id: str) -> dict[str, Any]:
        """Delete a contact."""
        mesh = get_mesh_service()
        deleted = await mesh.delete_contact(node_id)
        return {"deleted": deleted, "node_id": node_id}

    # --- Factory Reset ---

    @app.post("/api/factory-reset")
    async def factory_reset() -> dict[str, Any]:
        """
        Clear all mesh data (contacts and messages).
        """
        mesh = get_mesh_service()
        deleted = await mesh.factory_reset()

        return {
            "success": True,
            "deleted": deleted,
            "message": "All mesh data cleared.",
        }

    @app.get("/api/mesh/nodes/enriched")
    async def get_nodes_with_contacts(
        online_only: bool = Query(False),
    ) -> dict[str, Any]:
        """Get nodes with contact info merged."""
        mesh = get_mesh_service()

        if online_only:
            nodes = mesh.get_online_nodes()
        else:
            nodes = mesh.get_nodes()

        # Merge contact info
        enriched = []
        for node in nodes:
            node_dict = _node_to_dict(node)
            contact = await mesh.get_contact(node.node_id)
            if contact:
                node_dict["is_favorite"] = bool(contact.get("is_favorite"))
                node_dict["alias"] = contact.get("alias")
                node_dict["notes"] = contact.get("notes")
            else:
                node_dict["is_favorite"] = False
                node_dict["alias"] = None
                node_dict["notes"] = None
            enriched.append(node_dict)

        # Sort: favorites first, then by name
        enriched.sort(key=lambda n: (not n["is_favorite"], n["short_name"]))

        return {
            "nodes": enriched,
            "count": len(enriched),
            "my_node": _node_to_dict(mesh.my_node_info),
        }

    return app


# Helper functions for serialization


def _node_to_dict(node: Any) -> dict[str, Any]:
    """Convert MeshNode to dictionary."""
    result = {
        "node_id": node.node_id,
        "short_name": node.short_name,
        "long_name": node.long_name,
        "hardware": node.hardware.value if hasattr(node.hardware, "value") else str(node.hardware),
        "status": node.status.value if hasattr(node.status, "value") else str(node.status),
        "last_seen": node.last_seen.isoformat() if node.last_seen else None,
        "battery_level": node.battery_level,
        "snr": node.snr,
        "rssi": node.rssi,
        "hops_away": node.hops_away,
    }

    if node.position:
        result["position"] = {
            "latitude": node.position.latitude,
            "longitude": node.position.longitude,
            "altitude": node.position.altitude,
        }
    else:
        result["position"] = None

    return result


def _message_to_dict(message: Any) -> dict[str, Any]:
    """Convert MeshMessage to dictionary."""
    return {
        "id": message.id,
        "from_node": message.from_node,
        "to_node": message.to_node,
        "channel": message.channel,
        "text": message.text,
        "timestamp": message.timestamp.isoformat() if message.timestamp else None,
        "rx_time": message.rx_time.isoformat() if message.rx_time else None,
        "hop_count": message.hop_count,
        "acknowledged": message.acknowledged,
        "snr": message.snr,
        "rssi": message.rssi,
    }
