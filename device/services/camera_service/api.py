from __future__ import annotations

from typing import Any

from device.libs.schemas.camera import (
    CameraSettingsResponse,
    CameraSettingsUpdate,
    CameraStatusResponse,
    CaptureResponse,
    DeletePhotoResponse,
    PhotoListResponse,
    PhotoMetadata,
)
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from .service import CameraService


def create_app(service: CameraService) -> FastAPI:
    """Create the FastAPI application for the camera service."""
    app = FastAPI(
        title="Camera Service API",
        description="Camera control and photo management",
        version="1.0.0",
    )

    @app.get("/health")
    async def health() -> dict[str, Any]:
        """Health check endpoint."""
        if service.is_healthy():
            return {"status": "ok"}
        raise HTTPException(status_code=503, detail="not ready")

    # --- Camera Control Endpoints ---

    @app.get("/api/camera/status", response_model=CameraStatusResponse)
    async def get_camera_status() -> CameraStatusResponse:
        """Get current camera status."""
        status = await service.get_camera_status()
        return CameraStatusResponse(
            state=status["state"],
            is_ready=status["is_ready"],
            resolution=status["resolution"],
            is_front_camera=status["is_front_camera"],
            error_message=status["error_message"],
        )

    @app.get("/api/camera/settings", response_model=CameraSettingsResponse)
    async def get_camera_settings() -> CameraSettingsResponse:
        """Get current camera settings."""
        settings = await service.get_camera_settings()
        return CameraSettingsResponse(
            resolution_width=settings["resolution_width"],
            resolution_height=settings["resolution_height"],
            is_front_camera=settings["is_front_camera"],
            available_resolutions=settings["available_resolutions"],
        )

    @app.put("/api/camera/settings", response_model=CameraSettingsResponse)
    async def update_camera_settings(body: CameraSettingsUpdate) -> CameraSettingsResponse:
        """Update camera settings."""
        settings = await service.update_camera_settings(
            resolution_width=body.resolution_width,
            resolution_height=body.resolution_height,
            use_front_camera=body.use_front_camera,
        )

        if settings.get("errors"):
            raise HTTPException(
                status_code=400,
                detail={"errors": settings["errors"]},
            )

        return CameraSettingsResponse(
            resolution_width=settings["resolution_width"],
            resolution_height=settings["resolution_height"],
            is_front_camera=settings["is_front_camera"],
            available_resolutions=settings["available_resolutions"],
        )

    @app.post("/api/camera/capture", response_model=CaptureResponse)
    async def capture_photo() -> CaptureResponse:
        """Capture a photo."""
        result = await service.capture_photo()

        if not result["success"]:
            return CaptureResponse(
                success=False,
                photo=None,
                error=result["error"],
            )

        photo_data = result["photo"]
        return CaptureResponse(
            success=True,
            photo=PhotoMetadata(**photo_data) if photo_data else None,
            error=None,
        )

    # --- Photo Management Endpoints ---

    @app.get("/api/photos", response_model=PhotoListResponse)
    async def list_photos() -> PhotoListResponse:
        """List all photos."""
        photos = await service.list_photos()
        return PhotoListResponse(
            photos=[PhotoMetadata(**p) for p in photos],
            total=len(photos),
        )

    @app.get("/api/photos/{photo_id}")
    async def get_photo(photo_id: str) -> PhotoMetadata:
        """Get photo metadata by ID."""
        photo = await service.get_photo(photo_id)
        if photo is None:
            raise HTTPException(status_code=404, detail="Photo not found")
        return PhotoMetadata(**photo)

    @app.get("/api/photos/{photo_id}/file")
    async def get_photo_file(photo_id: str) -> FileResponse:
        """Get photo file by ID."""
        filepath = service.get_photo_filepath(photo_id)
        if filepath is None:
            raise HTTPException(status_code=404, detail="Photo not found")

        # Determine media type based on extension
        ext = filepath.suffix.lower()
        media_type = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"

        return FileResponse(
            path=filepath,
            media_type=media_type,
            filename=filepath.name,
        )

    @app.delete("/api/photos/{photo_id}", response_model=DeletePhotoResponse)
    async def delete_photo(photo_id: str) -> DeletePhotoResponse:
        """Delete a photo by ID."""
        success = await service.delete_photo(photo_id)
        if not success:
            raise HTTPException(status_code=404, detail="Photo not found")
        return DeletePhotoResponse(success=True, id=photo_id)

    return app
