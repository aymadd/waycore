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
