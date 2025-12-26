from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests
import requests_unixsocket


class APIClient:
    """
    Client for communicating with backend services.

    Tries Unix socket first (for production), falls back to HTTP (for local dev).
    """

    def __init__(self, socket_path: str, http_fallback: str):
        self.socket_path = socket_path
        self.http_fallback = http_fallback
        self._use_socket = Path(socket_path).exists()

        if self._use_socket:
            self.base_url = f"http+unix://{quote(socket_path, safe='')}"
            self.session = requests_unixsocket.Session()
        else:
            self.base_url = http_fallback
            self.session = requests.Session()

    def get(self, endpoint: str, **kwargs: Any) -> dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        response = self.session.get(url, **kwargs)
        response.raise_for_status()
        return response.json()  # type: ignore[no-any-return]

    def post(self, endpoint: str, json: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        response = self.session.post(url, json=json, **kwargs)
        response.raise_for_status()
        return response.json()  # type: ignore[no-any-return]

    def put(self, endpoint: str, json: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        response = self.session.put(url, json=json, **kwargs)
        response.raise_for_status()
        return response.json()  # type: ignore[no-any-return]

    def delete(self, endpoint: str, **kwargs: Any) -> dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        response = self.session.delete(url, **kwargs)
        response.raise_for_status()
        return response.json()  # type: ignore[no-any-return]


# --- Service endpoints ---

CORE_DAEMON_SOCKET = "/tmp/waycore/core-daemon.sock"
CORE_DAEMON_HTTP = os.getenv("CORE_DAEMON_URL", "http://localhost:8000")

DATA_LOGGER_SOCKET = "/tmp/waycore/data-logger.sock"
DATA_LOGGER_HTTP = os.getenv("DATA_LOGGER_URL", "http://localhost:8002")

COMMS_BRIDGE_SOCKET = "/tmp/waycore/comms-bridge.sock"
COMMS_BRIDGE_HTTP = os.getenv("COMMS_BRIDGE_URL", "http://localhost:8003")

AI_SERVICE_SOCKET = "/tmp/waycore/ai-service.sock"
AI_SERVICE_HTTP = os.getenv("AI_SERVICE_URL", "http://localhost:8010")


class CoreDaemonClient(APIClient):
    """Client for Core Daemon service."""

    def __init__(self) -> None:
        super().__init__(CORE_DAEMON_SOCKET, CORE_DAEMON_HTTP)

    def get_time(self) -> dict[str, Any]:
        """Get current system time."""
        return self.get("/api/system/time")

    def get_battery(self) -> dict[str, Any]:
        """Get battery status."""
        return self.get("/api/system/battery")

    def get_temperature(self) -> dict[str, Any]:
        """Get temperature reading."""
        return self.get("/api/system/temperature")

    def get_system_info(self) -> dict[str, Any]:
        """Get system information (version, etc.)."""
        return self.get("/api/system/info")

    def get_compass(self) -> dict[str, Any]:
        """Get compass/magnetometer reading."""
        return self.get("/api/sensors/compass")

    def calibrate_compass(self) -> dict[str, Any]:
        """Start compass calibration."""
        return self.post("/api/sensors/compass/calibrate", json={})

    def factory_reset(self) -> dict[str, Any]:
        """Trigger factory reset."""
        return self.post("/api/system/factory-reset", json={})

    def get_storage_status(self) -> dict[str, Any]:
        """Get storage usage information."""
        return self.get("/api/system/storage")

    # --- Sensor Registry ---

    def get_all_sensors(self) -> list[dict[str, Any]]:
        """Get all registered sensors from the registry."""
        return self.get("/api/sensors/registry")  # type: ignore[return-value]

    def get_sensor(self, sensor_id: str) -> dict[str, Any]:
        """Get a specific sensor by ID."""
        return self.get(f"/api/sensors/registry/{sensor_id}")

    def get_sensors_by_type(self, sensor_type: str) -> list[dict[str, Any]]:
        """Get all sensors of a specific type."""
        return self.get(f"/api/sensors/registry/type/{sensor_type}")  # type: ignore[return-value]

    def discover_sensors(self) -> dict[str, Any]:
        """Run sensor discovery."""
        return self.post("/api/sensors/registry/discover", json={})


class DataLoggerClient(APIClient):
    """Client for Data Logger service (preferences, history, notes)."""

    def __init__(self) -> None:
        super().__init__(DATA_LOGGER_SOCKET, DATA_LOGGER_HTTP)

    # --- Preferences ---

    def get_all_preferences(self) -> dict[str, str]:
        """Get all user preferences."""
        return self.get("/api/preferences")

    def get_preference(self, key: str) -> dict[str, Any]:
        """Get a single preference by key."""
        return self.get(f"/api/preferences/{key}")

    def set_preference(self, key: str, value: str) -> dict[str, Any]:
        """Update a preference value."""
        return self.put(f"/api/preferences/{key}", json={"value": value})

    def reset_preferences(self) -> dict[str, Any]:
        """Reset all preferences to defaults."""
        return self.post("/api/preferences/reset", json={})

    # --- Notes ---

    def get_all_notes(self) -> list[dict[str, Any]]:
        """Get all notes."""
        return self.get("/api/notes")

    def get_note(self, note_id: int) -> dict[str, Any]:
        """Get a single note."""
        return self.get(f"/api/notes/{note_id}")

    def create_note(self, title: str = "", content: str = "") -> dict[str, Any]:
        """Create a new note."""
        return self.post("/api/notes", json={"title": title, "content": content})

    def update_note(self, note_id: int, title: str, content: str) -> dict[str, Any]:
        """Update a note."""
        return self.put(f"/api/notes/{note_id}", json={"title": title, "content": content})

    def delete_note(self, note_id: int) -> dict[str, Any]:
        """Delete a note."""
        return self.delete(f"/api/notes/{note_id}")

    def factory_reset(self) -> dict[str, Any]:
        """Factory reset: clear all data."""
        return self.post("/api/factory-reset", json={})


class CommsBridgeClient(APIClient):
    """Client for Comms Bridge service (mesh networking)."""

    def __init__(self) -> None:
        super().__init__(COMMS_BRIDGE_SOCKET, COMMS_BRIDGE_HTTP)

    # --- Mesh Status ---

    def get_mesh_status(self) -> dict[str, Any]:
        """Get mesh network status."""
        return self.get("/api/mesh/status")

    # --- Mesh Nodes ---

    def get_mesh_nodes(self, online_only: bool = False) -> dict[str, Any]:
        """Get list of mesh nodes."""
        params = {"online_only": str(online_only).lower()}
        return self.get("/api/mesh/nodes", params=params)

    def get_mesh_node(self, node_id: str) -> dict[str, Any]:
        """Get a specific mesh node."""
        return self.get(f"/api/mesh/nodes/{node_id}")

    # --- Mesh Messages ---

    def get_mesh_messages(
        self,
        limit: int = 100,
        since: str | None = None,
        node_id: str | None = None,
    ) -> dict[str, Any]:
        """Get mesh message history."""
        params: dict[str, Any] = {"limit": limit}
        if since:
            params["since"] = since
        if node_id:
            params["node_id"] = node_id
        return self.get("/api/mesh/messages", params=params)

    def get_mesh_message(self, message_id: str) -> dict[str, Any]:
        """Get a specific mesh message."""
        return self.get(f"/api/mesh/messages/{message_id}")

    def send_mesh_message(
        self,
        text: str,
        to_node: str | None = None,
        channel: int = 0,
        want_ack: bool = True,
    ) -> dict[str, Any]:
        """Send a mesh message."""
        return self.post(
            "/api/mesh/messages",
            json={
                "text": text,
                "to_node": to_node,
                "channel": channel,
                "want_ack": want_ack,
            },
        )

    def get_mesh_conversation(
        self,
        node_id: str,
        limit: int = 50,
    ) -> dict[str, Any]:
        """Get conversation with a specific node."""
        return self.get(f"/api/mesh/conversation/{node_id}", params={"limit": limit})

    def factory_reset(self) -> dict[str, Any]:
        """Clear all mesh data (contacts and messages)."""
        return self.post("/api/factory-reset", json={})


class AIServiceClient(APIClient):
    """Client for AI Service (chat, image classification)."""

    def __init__(self) -> None:
        super().__init__(AI_SERVICE_SOCKET, AI_SERVICE_HTTP)

    def chat(
        self,
        question: str,
        model_id: str = "phi3-mini",
        context: str = "",
    ) -> dict[str, Any]:
        """Send a chat message and get AI response."""
        return self.post(
            "/api/chat",
            json={
                "question": question,
                "model_id": model_id,
                "context": context,
            },
        )

    def classify_image(
        self,
        image_b64: str,
        model_id: str = "mobilenetv3",
    ) -> dict[str, Any]:
        """Classify an image."""
        return self.post(
            "/api/image/classify",
            json={
                "model_id": model_id,
                "input_data": {"image_b64": image_b64},
            },
        )

    def factory_reset(self) -> dict[str, Any]:
        """Factory reset: clear all AI data (conversations, messages, model registry)."""
        return self.post("/api/factory-reset", json={})

    def delete_all_conversations(self) -> dict[str, Any]:
        """Delete all AI conversations and messages."""
        return self.delete("/api/conversations")

    def get_models(self) -> dict[str, Any]:
        """Get list of installed AI models."""
        return self.get("/api/models")

    # --- Conversation & Message Persistence ---

    def get_conversations(self, limit: int = 100) -> dict[str, Any]:
        """Get all conversations."""
        return self.get(f"/api/conversations?limit={limit}")

    def create_conversation(
        self, title: str | None = None, model_id: str = "phi3-mini"
    ) -> dict[str, Any]:
        """Create a new conversation."""
        return self.post(
            "/api/conversations",
            json={"title": title, "model_id": model_id},
        )

    def get_conversation(self, conversation_id: int) -> dict[str, Any]:
        """Get a specific conversation."""
        return self.get(f"/api/conversations/{conversation_id}")

    def update_conversation(
        self,
        conversation_id: int,
        title: str | None = None,
        model_id: str | None = None,
    ) -> dict[str, Any]:
        """Update a conversation."""
        body: dict[str, Any] = {}
        if title is not None:
            body["title"] = title
        if model_id is not None:
            body["model_id"] = model_id
        return self.put(f"/api/conversations/{conversation_id}", json=body)

    def delete_conversation(self, conversation_id: int) -> dict[str, Any]:
        """Delete a conversation."""
        return self.delete(f"/api/conversations/{conversation_id}")

    def get_messages(self, conversation_id: int, limit: int = 100) -> dict[str, Any]:
        """Get messages for a conversation."""
        return self.get(f"/api/conversations/{conversation_id}/messages?limit={limit}")

    def add_message(self, conversation_id: int, role: str, content: str) -> dict[str, Any]:
        """Add a message to a conversation."""
        return self.post(
            f"/api/conversations/{conversation_id}/messages",
            json={"role": role, "content": content},
        )

    def clear_messages(self, conversation_id: int) -> dict[str, Any]:
        """Clear all messages from a conversation."""
        return self.delete(f"/api/conversations/{conversation_id}/messages")

    def rescan_models(self) -> dict[str, Any]:
        """Rescan model directory and sync to database."""
        return self.post("/api/models/rescan", json={})
