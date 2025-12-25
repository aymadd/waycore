from __future__ import annotations

from typing import Any
from urllib.parse import quote

import requests_unixsocket


class UnixSocketClient:
    """
    Client for communicating with local FastAPI services over Unix domain sockets.
    """

    def __init__(self, socket_path: str):
        self.socket_path = socket_path
        self.base_url = f"http+unix://{quote(socket_path, safe='')}"
        self.session = requests_unixsocket.Session()

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


# --- Service-specific clients ---

CORE_DAEMON_SOCKET = "/tmp/waycore/core-daemon.sock"
DATA_LOGGER_SOCKET = "/tmp/waycore/data-logger.sock"


class CoreDaemonClient(UnixSocketClient):
    """Client for Core Daemon service."""

    def __init__(self, socket_path: str = CORE_DAEMON_SOCKET):
        super().__init__(socket_path)

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


class DataLoggerClient(UnixSocketClient):
    """Client for Data Logger service (preferences, history)."""

    def __init__(self, socket_path: str = DATA_LOGGER_SOCKET):
        super().__init__(socket_path)

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
