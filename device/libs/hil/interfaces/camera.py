from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class CameraState(str, Enum):
    """Camera operational states."""

    UNINITIALIZED = "uninitialized"
    READY = "ready"
    CAPTURING = "capturing"
    ERROR = "error"


@dataclass(frozen=True)
class CameraCapabilities:
    """Camera hardware capabilities."""

    resolutions: tuple[tuple[int, int], ...]  # (width, height) tuples
    supports_front_back: bool
    max_photo_count: int | None = None  # None = unlimited


@dataclass(frozen=True)
class CameraStatus:
    """Current camera status."""

    state: CameraState
    current_resolution: tuple[int, int]
    is_front_camera: bool
    error_message: str | None = None


@dataclass(frozen=True)
class CaptureResult:
    """Result of a photo capture operation."""

    success: bool
    filepath: str | None
    filename: str | None
    timestamp: datetime | None
    width: int | None = None
    height: int | None = None
    size_bytes: int | None = None
    error_message: str | None = None


class ICamera(ABC):
    """Interface for camera hardware abstraction."""

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the camera hardware.

        Returns:
            True if initialization successful, False otherwise.
        """
        ...

    @abstractmethod
    async def release(self) -> None:
        """Release camera resources and stop the camera."""
        ...

    @abstractmethod
    async def capture(self, output_dir: str) -> CaptureResult:
        """Capture a photo and save it to the specified directory.

        Args:
            output_dir: Directory path where the photo will be saved.

        Returns:
            CaptureResult with file information or error details.
        """
        ...

    @abstractmethod
    async def get_preview_frame(self) -> bytes | None:
        """Get current preview frame data for viewfinder display.

        Returns:
            JPEG-encoded image bytes, or None if not available.
        """
        ...

    @abstractmethod
    async def get_status(self) -> CameraStatus:
        """Get current camera status.

        Returns:
            CameraStatus with current state and configuration.
        """
        ...

    @abstractmethod
    async def set_resolution(self, width: int, height: int) -> bool:
        """Set the camera output resolution.

        Args:
            width: Image width in pixels.
            height: Image height in pixels.

        Returns:
            True if resolution was set successfully, False otherwise.
        """
        ...

    @abstractmethod
    async def switch_camera(self, use_front: bool) -> bool:
        """Switch between front and back cameras.

        Args:
            use_front: True to use front camera, False for back.

        Returns:
            True if switch successful, False otherwise.
        """
        ...

    @abstractmethod
    def get_capabilities(self) -> CameraCapabilities:
        """Get camera hardware capabilities.

        Returns:
            CameraCapabilities describing available features.
        """
        ...
