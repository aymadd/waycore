"""
Camera Bridge - QML interface to the camera service.

Provides camera status, capture, and photo management functionality to QML.
"""

from __future__ import annotations

import os
from typing import Any

from PySide6.QtCore import Property, QObject, Signal, Slot

from .api_client import APIClient

# Camera service connection settings
CAMERA_SERVICE_SOCKET = "/tmp/waycore/camera-service.sock"
CAMERA_SERVICE_HTTP = os.getenv("CAMERA_SERVICE_URL", "http://localhost:8006")


class CameraServiceClient(APIClient):
    """Client for Camera Service."""

    def __init__(self) -> None:
        super().__init__(CAMERA_SERVICE_SOCKET, CAMERA_SERVICE_HTTP)

    def get_status(self) -> dict[str, Any]:
        """Get camera status."""
        return self.get("/api/camera/status")

    def get_settings(self) -> dict[str, Any]:
        """Get camera settings."""
        return self.get("/api/camera/settings")

    def update_settings(
        self,
        resolution_width: int | None = None,
        resolution_height: int | None = None,
        use_front_camera: bool | None = None,
    ) -> dict[str, Any]:
        """Update camera settings."""
        payload: dict[str, Any] = {}
        if resolution_width is not None:
            payload["resolution_width"] = resolution_width
        if resolution_height is not None:
            payload["resolution_height"] = resolution_height
        if use_front_camera is not None:
            payload["use_front_camera"] = use_front_camera
        return self.put("/api/camera/settings", json=payload)

    def capture(self) -> dict[str, Any]:
        """Capture a photo."""
        return self.post("/api/camera/capture", json={})

    def get_photos(self) -> dict[str, Any]:
        """Get list of photos."""
        return self.get("/api/photos")

    def get_photo(self, photo_id: str) -> dict[str, Any]:
        """Get photo metadata."""
        return self.get(f"/api/photos/{photo_id}")

    def get_photo_url(self, photo_id: str) -> str:
        """Get URL to photo file."""
        return f"{self.base_url}/api/photos/{photo_id}/file"

    def delete_photo(self, photo_id: str) -> dict[str, Any]:
        """Delete a photo."""
        return self.delete(f"/api/photos/{photo_id}")

    def factory_reset(self) -> dict[str, Any]:
        """Factory reset: clear all photos."""
        return self.post("/api/factory-reset", json={})


class CameraBridge(QObject):
    """
    Bridge between QML and the camera service.

    Exposes camera status, capture functionality, and photo management to QML.
    """

    # Signals
    statusChanged = Signal()
    captureStarted = Signal()
    captureCompleted = Signal(str)  # photo_id
    captureFailed = Signal(str)  # error message
    photosChanged = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._client = CameraServiceClient()

        # State
        self._state = "unknown"
        self._is_ready = False
        self._resolution_width = 0
        self._resolution_height = 0
        self._is_front_camera = False
        self._error_message: str | None = None
        self._last_photo_id: str | None = None
        self._is_capturing = False
        self._photos: list[dict[str, Any]] = []
        self._connected = False

        # Try initial connection
        self.refreshStatus()
        self.refreshPhotos()

    # --- Properties ---

    @Property(str, notify=statusChanged)  # type: ignore[arg-type]
    def state(self) -> str:
        """Current camera state."""
        return self._state

    @Property(bool, notify=statusChanged)  # type: ignore[arg-type]
    def isReady(self) -> bool:
        """Whether camera is ready for capture."""
        return self._is_ready

    @Property(int, notify=statusChanged)  # type: ignore[arg-type]
    def resolutionWidth(self) -> int:
        """Current resolution width."""
        return self._resolution_width

    @Property(int, notify=statusChanged)  # type: ignore[arg-type]
    def resolutionHeight(self) -> int:
        """Current resolution height."""
        return self._resolution_height

    @Property(bool, notify=statusChanged)  # type: ignore[arg-type]
    def isFrontCamera(self) -> bool:
        """Whether front camera is active."""
        return self._is_front_camera

    @Property(str, notify=statusChanged)  # type: ignore[arg-type]
    def errorMessage(self) -> str:
        """Error message if any."""
        return self._error_message or ""

    @Property(str, notify=captureCompleted)  # type: ignore[arg-type]
    def lastPhotoId(self) -> str:
        """ID of the last captured photo."""
        return self._last_photo_id or ""

    @Property(bool, notify=captureStarted)  # type: ignore[arg-type]
    def isCapturing(self) -> bool:
        """Whether a capture is in progress."""
        return self._is_capturing

    @Property(bool, notify=statusChanged)  # type: ignore[arg-type]
    def connected(self) -> bool:
        """Whether connected to camera service."""
        return self._connected

    @Property(int, notify=photosChanged)  # type: ignore[arg-type]
    def photoCount(self) -> int:
        """Number of photos."""
        return len(self._photos)

    # --- Slots ---

    @Slot()
    def refreshStatus(self) -> None:
        """Refresh camera status from service."""
        try:
            status = self._client.get_status()
            self._state = status.get("state", "unknown")
            self._is_ready = status.get("is_ready", False)
            resolution = status.get("resolution", [0, 0])
            self._resolution_width = resolution[0] if isinstance(resolution, list) else 0
            self._resolution_height = resolution[1] if isinstance(resolution, list) else 0
            self._is_front_camera = status.get("is_front_camera", False)
            self._error_message = status.get("error_message")
            self._connected = True
        except Exception as e:
            self._state = "error"
            self._is_ready = False
            self._connected = False
            self._error_message = str(e)

        self.statusChanged.emit()

    @Slot()
    def refreshPhotos(self) -> None:
        """Refresh photo list from service."""
        try:
            result = self._client.get_photos()
            self._photos = result.get("photos", [])
        except Exception:
            self._photos = []

        self.photosChanged.emit()

    @Slot()
    def capture(self) -> None:
        """Capture a photo."""
        if self._is_capturing:
            return

        self._is_capturing = True
        self.captureStarted.emit()

        try:
            result = self._client.capture()
            if result.get("success"):
                photo = result.get("photo", {})
                self._last_photo_id = photo.get("id", "")
                self.captureCompleted.emit(self._last_photo_id)
                self.refreshPhotos()
            else:
                error = result.get("error", "Unknown error")
                self.captureFailed.emit(error)
        except Exception as e:
            self.captureFailed.emit(str(e))
        finally:
            self._is_capturing = False

    @Slot(bool)
    def switchCamera(self, use_front: bool) -> None:
        """Switch between front and back camera."""
        try:
            self._client.update_settings(use_front_camera=use_front)
            self.refreshStatus()
        except Exception:
            pass

    @Slot(int, int)
    def setResolution(self, width: int, height: int) -> None:
        """Set camera resolution."""
        try:
            self._client.update_settings(resolution_width=width, resolution_height=height)
            self.refreshStatus()
        except Exception:
            pass

    @Slot(result=list)  # type: ignore[arg-type]
    def getPhotos(self) -> list[dict[str, Any]]:
        """Get list of photos."""
        return self._photos

    @Slot(str, result=str)  # type: ignore[arg-type]
    def getPhotoUrl(self, photo_id: str) -> str:
        """Get URL to photo file."""
        return self._client.get_photo_url(photo_id)

    @Slot(str, result=bool)  # type: ignore[arg-type]
    def deletePhoto(self, photo_id: str) -> bool:
        """Delete a photo."""
        try:
            result = self._client.delete_photo(photo_id)
            if result.get("success"):
                self.refreshPhotos()
                return True
        except Exception:
            pass
        return False

    @Slot(result=str)  # type: ignore[arg-type]
    def getLastPhotoUrl(self) -> str:
        """Get URL to the last captured photo."""
        if self._last_photo_id:
            return self._client.get_photo_url(self._last_photo_id)
        if self._photos:
            return self._client.get_photo_url(self._photos[0].get("id", ""))
        return ""
