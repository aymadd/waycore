from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from device.drivers.mock.camera import MockCamera
from device.libs.hil.interfaces.camera import CameraState


@pytest.fixture
def camera() -> MockCamera:
    """Create a mock camera instance."""
    return MockCamera({"default_width": 640, "default_height": 480})


@pytest.fixture
def temp_photo_dir() -> Path:
    """Create a temporary directory for photos."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.mark.asyncio
async def test_mock_camera_initialization(camera: MockCamera) -> None:
    """Test camera initialization."""
    status = await camera.get_status()
    assert status.state == CameraState.UNINITIALIZED

    result = await camera.initialize()
    assert result is True

    status = await camera.get_status()
    assert status.state == CameraState.READY


@pytest.mark.asyncio
async def test_mock_camera_release(camera: MockCamera) -> None:
    """Test camera release."""
    await camera.initialize()
    status = await camera.get_status()
    assert status.state == CameraState.READY

    await camera.release()
    status = await camera.get_status()
    assert status.state == CameraState.UNINITIALIZED


@pytest.mark.asyncio
async def test_mock_camera_capture_before_init(camera: MockCamera, temp_photo_dir: Path) -> None:
    """Test capture fails before initialization."""
    result = await camera.capture(str(temp_photo_dir))
    assert result.success is False
    assert result.error_message is not None
    assert "not ready" in result.error_message.lower()


@pytest.mark.asyncio
async def test_mock_camera_capture_success(camera: MockCamera, temp_photo_dir: Path) -> None:
    """Test successful photo capture."""
    await camera.initialize()

    result = await camera.capture(str(temp_photo_dir))

    assert result.success is True
    assert result.filepath is not None
    assert result.filename is not None
    assert result.timestamp is not None
    assert result.width == 640
    assert result.height == 480
    assert result.size_bytes is not None
    assert result.size_bytes > 0

    # Verify file was created
    filepath = Path(result.filepath)
    assert filepath.exists()
    assert filepath.name.startswith("IMG_")
    assert filepath.suffix == ".jpg"


@pytest.mark.asyncio
async def test_mock_camera_capture_multiple(camera: MockCamera, temp_photo_dir: Path) -> None:
    """Test capturing multiple photos."""
    await camera.initialize()

    results = []
    for _ in range(3):
        result = await camera.capture(str(temp_photo_dir))
        results.append(result)

    # All captures should succeed with unique filenames
    assert all(r.success for r in results)
    filenames = [r.filename for r in results]
    assert len(set(filenames)) == 3  # All unique


@pytest.mark.asyncio
async def test_mock_camera_creates_output_dir(camera: MockCamera) -> None:
    """Test that capture creates output directory if it doesn't exist."""
    await camera.initialize()

    with tempfile.TemporaryDirectory() as tmpdir:
        nested_dir = Path(tmpdir) / "nested" / "photo" / "dir"
        assert not nested_dir.exists()

        result = await camera.capture(str(nested_dir))

        assert result.success is True
        assert nested_dir.exists()
        assert Path(result.filepath).exists()


@pytest.mark.asyncio
async def test_mock_camera_status_resolution(camera: MockCamera) -> None:
    """Test status includes correct resolution."""
    await camera.initialize()

    status = await camera.get_status()
    assert status.current_resolution == (640, 480)


@pytest.mark.asyncio
async def test_mock_camera_set_resolution(camera: MockCamera) -> None:
    """Test setting camera resolution."""
    await camera.initialize()

    # Valid resolution
    result = await camera.set_resolution(1920, 1080)
    assert result is True

    status = await camera.get_status()
    assert status.current_resolution == (1920, 1080)


@pytest.mark.asyncio
async def test_mock_camera_set_invalid_resolution(camera: MockCamera) -> None:
    """Test setting invalid resolution fails."""
    await camera.initialize()

    # Invalid resolution
    result = await camera.set_resolution(999, 999)
    assert result is False

    # Should keep old resolution
    status = await camera.get_status()
    assert status.current_resolution == (640, 480)


@pytest.mark.asyncio
async def test_mock_camera_preview_frame(camera: MockCamera) -> None:
    """Test getting preview frame."""
    # No preview before init
    frame = await camera.get_preview_frame()
    assert frame is None

    await camera.initialize()

    frame = await camera.get_preview_frame()
    assert frame is not None
    assert isinstance(frame, bytes)
    assert len(frame) > 0


@pytest.mark.asyncio
async def test_mock_camera_switch_camera(camera: MockCamera) -> None:
    """Test switching between front and back camera."""
    await camera.initialize()

    status = await camera.get_status()
    assert status.is_front_camera is False

    result = await camera.switch_camera(use_front=True)
    assert result is True

    status = await camera.get_status()
    assert status.is_front_camera is True

    result = await camera.switch_camera(use_front=False)
    assert result is True

    status = await camera.get_status()
    assert status.is_front_camera is False


@pytest.mark.asyncio
async def test_mock_camera_capabilities(camera: MockCamera) -> None:
    """Test getting camera capabilities."""
    caps = camera.get_capabilities()

    assert caps.resolutions is not None
    assert len(caps.resolutions) > 0
    assert (640, 480) in caps.resolutions
    assert (1920, 1080) in caps.resolutions
    assert caps.supports_front_back is True


@pytest.mark.asyncio
async def test_mock_camera_state_during_capture(camera: MockCamera, temp_photo_dir: Path) -> None:
    """Test camera state returns to READY after capture."""
    await camera.initialize()

    # Before capture
    status = await camera.get_status()
    assert status.state == CameraState.READY

    # Capture
    result = await camera.capture(str(temp_photo_dir))
    assert result.success is True

    # After capture (should be back to ready)
    status = await camera.get_status()
    assert status.state == CameraState.READY


@pytest.mark.asyncio
async def test_mock_camera_config_defaults() -> None:
    """Test camera uses default config values."""
    camera = MockCamera({})
    await camera.initialize()

    status = await camera.get_status()
    assert status.current_resolution == (1280, 720)  # Default resolution


@pytest.mark.asyncio
async def test_mock_camera_config_custom() -> None:
    """Test camera respects custom config."""
    camera = MockCamera(
        {
            "default_width": 1920,
            "default_height": 1080,
            "watermark": False,
        }
    )
    await camera.initialize()

    status = await camera.get_status()
    assert status.current_resolution == (1920, 1080)


@pytest.mark.asyncio
async def test_mock_camera_factory_registration() -> None:
    """Test camera is registered with factory."""
    # Import triggers registration
    import device.drivers.mock  # noqa: F401
    from device.libs.hil.factory import DriverFactory

    camera = DriverFactory.create_camera("mock", {})
    # Verify it implements ICamera interface
    assert hasattr(camera, "initialize")
    assert hasattr(camera, "capture")
    assert hasattr(camera, "get_status")
    assert hasattr(camera, "release")

    # Verify it works
    result = await camera.initialize()
    assert result is True

    status = await camera.get_status()
    assert status.state.value == "ready"
