from __future__ import annotations

import tempfile
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
from device.drivers.mock.camera import MockCamera
from device.services.camera_service.api import create_app
from device.services.camera_service.service import CameraService
from fastapi.testclient import TestClient


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
async def service(temp_photos_dir: Path, camera: MockCamera) -> AsyncGenerator[CameraService, None]:
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


@pytest.fixture
def client(service: CameraService) -> TestClient:
    """Create a test client."""
    app = create_app(service)
    return TestClient(app)


@pytest.mark.asyncio
async def test_health_endpoint(client: TestClient) -> None:
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_get_camera_status(client: TestClient) -> None:
    """Test GET /api/camera/status."""
    response = client.get("/api/camera/status")

    assert response.status_code == 200
    data = response.json()
    assert data["state"] == "ready"
    assert data["is_ready"] is True
    assert data["resolution"] == [640, 480]


@pytest.mark.asyncio
async def test_get_camera_settings(client: TestClient) -> None:
    """Test GET /api/camera/settings."""
    response = client.get("/api/camera/settings")

    assert response.status_code == 200
    data = response.json()
    assert data["resolution_width"] == 640
    assert data["resolution_height"] == 480
    assert "available_resolutions" in data


@pytest.mark.asyncio
async def test_update_camera_settings(client: TestClient) -> None:
    """Test PUT /api/camera/settings."""
    response = client.put(
        "/api/camera/settings",
        json={"resolution_width": 1920, "resolution_height": 1080},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["resolution_width"] == 1920
    assert data["resolution_height"] == 1080


@pytest.mark.asyncio
async def test_update_camera_settings_invalid(client: TestClient) -> None:
    """Test PUT /api/camera/settings with invalid resolution."""
    response = client.put(
        "/api/camera/settings",
        json={"resolution_width": 999, "resolution_height": 999},
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_capture_photo(client: TestClient) -> None:
    """Test POST /api/camera/capture."""
    response = client.post("/api/camera/capture")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["photo"] is not None
    assert data["photo"]["filename"].startswith("IMG_")


@pytest.mark.asyncio
async def test_list_photos_empty(client: TestClient) -> None:
    """Test GET /api/photos when empty."""
    response = client.get("/api/photos")

    assert response.status_code == 200
    data = response.json()
    assert data["photos"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_photos_after_capture(client: TestClient) -> None:
    """Test GET /api/photos after capturing."""
    # Capture photos
    client.post("/api/camera/capture")
    client.post("/api/camera/capture")

    response = client.get("/api/photos")

    assert response.status_code == 200
    data = response.json()
    assert len(data["photos"]) == 2
    assert data["total"] == 2


@pytest.mark.asyncio
async def test_get_photo(client: TestClient) -> None:
    """Test GET /api/photos/{id}."""
    # Capture a photo
    capture_response = client.post("/api/camera/capture")
    photo_id = capture_response.json()["photo"]["id"]

    response = client.get(f"/api/photos/{photo_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == photo_id


@pytest.mark.asyncio
async def test_get_photo_not_found(client: TestClient) -> None:
    """Test GET /api/photos/{id} for non-existent photo."""
    response = client.get("/api/photos/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_photo_file(client: TestClient) -> None:
    """Test GET /api/photos/{id}/file."""
    # Capture a photo
    capture_response = client.post("/api/camera/capture")
    photo_id = capture_response.json()["photo"]["id"]

    response = client.get(f"/api/photos/{photo_id}/file")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/")
    assert len(response.content) > 0


@pytest.mark.asyncio
async def test_get_photo_file_not_found(client: TestClient) -> None:
    """Test GET /api/photos/{id}/file for non-existent photo."""
    response = client.get("/api/photos/nonexistent/file")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_photo(client: TestClient) -> None:
    """Test DELETE /api/photos/{id}."""
    # Capture a photo
    capture_response = client.post("/api/camera/capture")
    photo_id = capture_response.json()["photo"]["id"]

    # Delete it
    response = client.delete(f"/api/photos/{photo_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["id"] == photo_id

    # Verify it's gone
    get_response = client.get(f"/api/photos/{photo_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_photo_not_found(client: TestClient) -> None:
    """Test DELETE /api/photos/{id} for non-existent photo."""
    response = client.delete("/api/photos/nonexistent")
    assert response.status_code == 404
