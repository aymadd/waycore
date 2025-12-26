from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from device.libs.common.base_service import BaseService
from device.libs.hil.interfaces.camera import CameraState, ICamera
from device.libs.messaging.bus import MessageBus
from device.libs.schemas.camera import PhotoMetadata


class CameraService(BaseService):
    """
    Service for camera operations and photo management.

    Provides camera control, photo capture, and photo storage management.
    """

    def __init__(
        self,
        config: dict[str, Any],
        camera: ICamera,
        bus: MessageBus | None = None,
    ) -> None:
        super().__init__(config, bus)
        self._camera = camera

        # Configuration
        camera_config = config.get("camera", {})
        self._photos_dir = Path(camera_config.get("photos_dir", "data/photos"))
        self._idle_sleep_s = float(config.get("idle_sleep_seconds", 0.1))

        self._healthy = False

    async def _setup(self) -> None:
        """Initialize the camera and photo storage."""
        # Ensure photos directory exists
        self._photos_dir.mkdir(parents=True, exist_ok=True)

        # Initialize camera
        success = await self._camera.initialize()
        if not success:
            raise RuntimeError("Failed to initialize camera")

        self._healthy = True

    async def _run(self) -> None:
        """Main service loop."""
        while not self.should_stop():
            await asyncio.sleep(self._idle_sleep_s)

    async def _cleanup(self) -> None:
        """Cleanup camera resources."""
        await self._camera.release()
        self._healthy = False

    def is_healthy(self) -> bool:
        """Check if service is healthy."""
        return self._healthy

    # --- Camera Control ---

    async def get_camera_status(self) -> dict[str, Any]:
        """Get current camera status."""
        status = await self._camera.get_status()
        return {
            "state": status.state.value,
            "is_ready": status.state == CameraState.READY,
            "resolution": status.current_resolution,
            "is_front_camera": status.is_front_camera,
            "error_message": status.error_message,
        }

    async def get_camera_settings(self) -> dict[str, Any]:
        """Get current camera settings."""
        status = await self._camera.get_status()
        capabilities = self._camera.get_capabilities()
        return {
            "resolution_width": status.current_resolution[0],
            "resolution_height": status.current_resolution[1],
            "is_front_camera": status.is_front_camera,
            "available_resolutions": list(capabilities.resolutions),
        }

    async def update_camera_settings(
        self,
        resolution_width: int | None = None,
        resolution_height: int | None = None,
        use_front_camera: bool | None = None,
    ) -> dict[str, Any]:
        """Update camera settings."""
        errors: list[str] = []

        if resolution_width is not None and resolution_height is not None:
            success = await self._camera.set_resolution(resolution_width, resolution_height)
            if not success:
                errors.append(f"Invalid resolution: {resolution_width}x{resolution_height}")

        if use_front_camera is not None:
            success = await self._camera.switch_camera(use_front_camera)
            if not success:
                errors.append("Failed to switch camera")

        settings = await self.get_camera_settings()
        settings["errors"] = errors if errors else None
        return settings

    # --- Photo Capture ---

    async def capture_photo(self) -> dict[str, Any]:
        """Capture a photo."""
        result = await self._camera.capture(str(self._photos_dir))

        if not result.success:
            return {
                "success": False,
                "photo": None,
                "error": result.error_message,
            }

        # Build photo metadata
        photo = PhotoMetadata(
            id=Path(result.filename).stem if result.filename else "",
            filename=result.filename or "",
            filepath=result.filepath or "",
            timestamp=result.timestamp or datetime.now(timezone.utc),
            width=result.width or 0,
            height=result.height or 0,
            size_bytes=result.size_bytes or 0,
        )

        return {
            "success": True,
            "photo": photo.model_dump(),
            "error": None,
        }

    # --- Photo Management ---

    async def list_photos(self) -> list[dict[str, Any]]:
        """List all photos sorted by date (newest first)."""
        photos: list[dict[str, Any]] = []

        if not self._photos_dir.exists():
            return photos

        for filepath in self._photos_dir.iterdir():
            if filepath.suffix.lower() in (".jpg", ".jpeg", ".png"):
                try:
                    stat = filepath.stat()
                    photos.append(
                        {
                            "id": filepath.stem,
                            "filename": filepath.name,
                            "filepath": str(filepath),
                            "timestamp": datetime.fromtimestamp(
                                stat.st_mtime, tz=timezone.utc
                            ).isoformat(),
                            "width": 0,  # Would need to read image to get this
                            "height": 0,
                            "size_bytes": stat.st_size,
                        }
                    )
                except OSError:
                    continue

        # Sort by timestamp descending (newest first)
        photos.sort(key=lambda p: p["timestamp"], reverse=True)
        return photos

    async def get_photo(self, photo_id: str) -> dict[str, Any] | None:
        """Get photo metadata by ID."""
        for ext in (".jpg", ".jpeg", ".png"):
            filepath = self._photos_dir / f"{photo_id}{ext}"
            if filepath.exists():
                try:
                    stat = filepath.stat()
                    return {
                        "id": photo_id,
                        "filename": filepath.name,
                        "filepath": str(filepath),
                        "timestamp": datetime.fromtimestamp(
                            stat.st_mtime, tz=timezone.utc
                        ).isoformat(),
                        "width": 0,
                        "height": 0,
                        "size_bytes": stat.st_size,
                    }
                except OSError:
                    return None
        return None

    async def get_photo_file(self, photo_id: str) -> bytes | None:
        """Get photo file contents by ID."""
        for ext in (".jpg", ".jpeg", ".png"):
            filepath = self._photos_dir / f"{photo_id}{ext}"
            if filepath.exists():
                try:
                    return filepath.read_bytes()
                except OSError:
                    return None
        return None

    def get_photo_filepath(self, photo_id: str) -> Path | None:
        """Get photo file path by ID."""
        for ext in (".jpg", ".jpeg", ".png"):
            filepath = self._photos_dir / f"{photo_id}{ext}"
            if filepath.exists():
                return filepath
        return None

    async def delete_photo(self, photo_id: str) -> bool:
        """Delete a photo by ID. Returns True if deleted."""
        for ext in (".jpg", ".jpeg", ".png"):
            filepath = self._photos_dir / f"{photo_id}{ext}"
            if filepath.exists():
                try:
                    filepath.unlink()
                    return True
                except OSError:
                    return False
        return False
