from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from device.drivers.mock.camera import MockCamera
from device.services.camera_service.service import CameraService


@pytest.fixture
def temp_photos_dir() -> Path:
    """Create a temporary photos directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def camera() -> MockCamera:
    """Create a mock camera."""
    return MockCamera({"default_width": 640, "default_height": 480})


@pytest.fixture
async def service(temp_photos_dir: Path, camera: MockCamera) -> CameraService:
    """Create and start a camera service."""
    config = {
        "camera": {
            "photos_dir": str(temp_photos_dir),
        },
        "idle_sleep_seconds": 0.01,
    }
    svc = CameraService(config, camera, bus=None)
    await svc.start()
    yield svc
    await svc.stop()


@pytest.mark.asyncio
async def test_service_startup_and_health(
    service: CameraService,
) -> None:
    """Test service starts and is healthy."""
    assert service.is_healthy() is True


@pytest.mark.asyncio
async def test_get_camera_status(service: CameraService) -> None:
    """Test getting camera status."""
    status = await service.get_camera_status()

    assert status["state"] == "ready"
    assert status["is_ready"] is True
    assert status["resolution"] == (640, 480)
    assert status["is_front_camera"] is False


@pytest.mark.asyncio
async def test_get_camera_settings(service: CameraService) -> None:
    """Test getting camera settings."""
    settings = await service.get_camera_settings()

    assert settings["resolution_width"] == 640
    assert settings["resolution_height"] == 480
    assert settings["is_front_camera"] is False
    assert len(settings["available_resolutions"]) > 0


@pytest.mark.asyncio
async def test_update_camera_settings_resolution(service: CameraService) -> None:
    """Test updating camera resolution."""
    settings = await service.update_camera_settings(resolution_width=1920, resolution_height=1080)

    assert settings["resolution_width"] == 1920
    assert settings["resolution_height"] == 1080
    assert settings.get("errors") is None


@pytest.mark.asyncio
async def test_update_camera_settings_invalid_resolution(
    service: CameraService,
) -> None:
    """Test updating with invalid resolution returns errors."""
    settings = await service.update_camera_settings(resolution_width=999, resolution_height=999)

    assert settings["errors"] is not None
    assert len(settings["errors"]) > 0


@pytest.mark.asyncio
async def test_update_camera_switch(service: CameraService) -> None:
    """Test switching camera."""
    settings = await service.update_camera_settings(use_front_camera=True)

    assert settings["is_front_camera"] is True


@pytest.mark.asyncio
async def test_capture_photo(service: CameraService, temp_photos_dir: Path) -> None:
    """Test capturing a photo."""
    result = await service.capture_photo()

    assert result["success"] is True
    assert result["photo"] is not None
    assert result["photo"]["filename"].startswith("IMG_")
    assert result["photo"]["size_bytes"] > 0

    # Verify file exists
    filepath = Path(result["photo"]["filepath"])
    assert filepath.exists()


@pytest.mark.asyncio
async def test_list_photos_empty(service: CameraService) -> None:
    """Test listing photos when empty."""
    photos = await service.list_photos()
    assert photos == []


@pytest.mark.asyncio
async def test_list_photos_after_capture(service: CameraService) -> None:
    """Test listing photos after capture."""
    # Capture some photos
    await service.capture_photo()
    await service.capture_photo()

    photos = await service.list_photos()

    assert len(photos) == 2
    # Should be sorted newest first
    assert photos[0]["timestamp"] >= photos[1]["timestamp"]


@pytest.mark.asyncio
async def test_get_photo(service: CameraService) -> None:
    """Test getting a single photo."""
    # Capture a photo
    capture_result = await service.capture_photo()
    photo_id = capture_result["photo"]["id"]

    # Get the photo
    photo = await service.get_photo(photo_id)

    assert photo is not None
    assert photo["id"] == photo_id


@pytest.mark.asyncio
async def test_get_photo_not_found(service: CameraService) -> None:
    """Test getting non-existent photo."""
    photo = await service.get_photo("nonexistent")
    assert photo is None


@pytest.mark.asyncio
async def test_get_photo_file(service: CameraService) -> None:
    """Test getting photo file contents."""
    # Capture a photo
    capture_result = await service.capture_photo()
    photo_id = capture_result["photo"]["id"]

    # Get file contents
    contents = await service.get_photo_file(photo_id)

    assert contents is not None
    assert len(contents) > 0


@pytest.mark.asyncio
async def test_delete_photo(service: CameraService, temp_photos_dir: Path) -> None:
    """Test deleting a photo."""
    # Capture a photo
    capture_result = await service.capture_photo()
    photo_id = capture_result["photo"]["id"]
    filepath = Path(capture_result["photo"]["filepath"])

    assert filepath.exists()

    # Delete the photo
    success = await service.delete_photo(photo_id)

    assert success is True
    assert not filepath.exists()


@pytest.mark.asyncio
async def test_delete_photo_not_found(service: CameraService) -> None:
    """Test deleting non-existent photo."""
    success = await service.delete_photo("nonexistent")
    assert success is False


@pytest.mark.asyncio
async def test_service_cleanup(temp_photos_dir: Path, camera: MockCamera) -> None:
    """Test service cleanup releases camera."""
    config = {"camera": {"photos_dir": str(temp_photos_dir)}}
    svc = CameraService(config, camera, bus=None)

    await svc.start()
    assert svc.is_healthy() is True

    await svc.stop()
    assert svc.is_healthy() is False
