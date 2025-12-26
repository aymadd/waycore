from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class CameraStateEnum(str, Enum):
    """Camera operational states."""

    UNINITIALIZED = "uninitialized"
    READY = "ready"
    CAPTURING = "capturing"
    ERROR = "error"


class CameraSettingsResponse(BaseModel):
    """Camera settings response."""

    resolution_width: int = Field(description="Current image width in pixels")
    resolution_height: int = Field(description="Current image height in pixels")
    is_front_camera: bool = Field(description="Whether front camera is active")
    available_resolutions: list[tuple[int, int]] = Field(
        description="List of supported resolutions"
    )


class CameraSettingsUpdate(BaseModel):
    """Request body for updating camera settings."""

    resolution_width: int | None = Field(default=None, description="Image width in pixels")
    resolution_height: int | None = Field(default=None, description="Image height in pixels")
    use_front_camera: bool | None = Field(default=None, description="Switch to front camera")


class CameraStatusResponse(BaseModel):
    """Camera status response."""

    state: CameraStateEnum = Field(description="Current camera state")
    is_ready: bool = Field(description="Whether camera is ready for capture")
    resolution: tuple[int, int] = Field(description="Current resolution (width, height)")
    is_front_camera: bool = Field(description="Whether front camera is active")
    error_message: str | None = Field(default=None, description="Error message if any")


class PhotoMetadata(BaseModel):
    """Photo metadata."""

    id: str = Field(description="Unique photo identifier (filename without extension)")
    filename: str = Field(description="Original filename")
    filepath: str = Field(description="Full path to file")
    timestamp: datetime = Field(description="When photo was taken")
    width: int = Field(description="Image width in pixels")
    height: int = Field(description="Image height in pixels")
    size_bytes: int = Field(description="File size in bytes")


class CaptureResponse(BaseModel):
    """Response from photo capture."""

    success: bool = Field(description="Whether capture was successful")
    photo: PhotoMetadata | None = Field(default=None, description="Photo metadata if successful")
    error: str | None = Field(default=None, description="Error message if failed")


class PhotoListResponse(BaseModel):
    """Response for photo listing."""

    photos: list[PhotoMetadata] = Field(description="List of photos")
    total: int = Field(description="Total number of photos")


class DeletePhotoResponse(BaseModel):
    """Response for photo deletion."""

    success: bool = Field(description="Whether deletion was successful")
    id: str = Field(description="ID of deleted photo")
