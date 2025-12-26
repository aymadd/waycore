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
