from __future__ import annotations

import asyncio
import io
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from device.libs.hil.interfaces.camera import (
    CameraCapabilities,
    CameraState,
    CameraStatus,
    CaptureResult,
    ICamera,
)

# PIL is optional - we generate simple images without it if not available
try:
    from PIL import Image, ImageDraw

    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class MockCamera(ICamera):
    """Mock camera driver for development and testing.

    Generates placeholder images instead of real camera captures.
    """

    # Supported resolutions for the mock camera
    SUPPORTED_RESOLUTIONS: tuple[tuple[int, int], ...] = (
        (640, 480),
        (1280, 720),
        (1920, 1080),
    )

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize mock camera with configuration.

        Args:
            config: Configuration dictionary with optional keys:
                - default_width: Default image width (default: 1280)
                - default_height: Default image height (default: 720)
                - watermark: Whether to add watermark (default: True)
        """
        self._width: int = int(config.get("default_width", 1280))
        self._height: int = int(config.get("default_height", 720))
        self._watermark: bool = bool(config.get("watermark", True))
        self._is_front: bool = False
        self._state: CameraState = CameraState.UNINITIALIZED
        self._error_message: str | None = None
        self._capture_count: int = 0

    async def initialize(self) -> bool:
        """Initialize the mock camera."""
        await asyncio.sleep(0.05)  # Simulate initialization delay
        self._state = CameraState.READY
        self._error_message = None
        return True

    async def release(self) -> None:
        """Release camera resources."""
        await asyncio.sleep(0.01)  # Simulate cleanup
        self._state = CameraState.UNINITIALIZED
        self._error_message = None

    async def capture(self, output_dir: str) -> CaptureResult:
        """Capture a mock photo and save to output directory."""
        if self._state != CameraState.READY:
            return CaptureResult(
                success=False,
                filepath=None,
                filename=None,
                timestamp=None,
                error_message=f"Camera not ready, state: {self._state.value}",
            )

        self._state = CameraState.CAPTURING
        try:
            # Generate timestamp for filename
            now = datetime.now(timezone.utc)
            timestamp_str = now.strftime("%Y%m%d_%H%M%S")
            self._capture_count += 1
            filename = f"IMG_{timestamp_str}_{self._capture_count:04d}.jpg"

            # Ensure output directory exists
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            filepath = output_path / filename

            # Generate and save the mock image
            await asyncio.sleep(0.1)  # Simulate capture delay
            image_bytes = self._generate_mock_image(now)

            filepath.write_bytes(image_bytes)
            file_size = filepath.stat().st_size

            return CaptureResult(
                success=True,
                filepath=str(filepath),
                filename=filename,
                timestamp=now,
                width=self._width,
                height=self._height,
                size_bytes=file_size,
            )

        except OSError as e:
            self._error_message = str(e)
            return CaptureResult(
                success=False,
                filepath=None,
                filename=None,
                timestamp=None,
                error_message=f"Failed to save photo: {e}",
            )
        finally:
            self._state = CameraState.READY

    async def get_preview_frame(self) -> bytes | None:
        """Get a preview frame for the viewfinder."""
        if self._state not in (CameraState.READY, CameraState.CAPTURING):
            return None

        # Generate a smaller preview frame
        preview_width = min(320, self._width)
        preview_height = int(preview_width * self._height / self._width)

        original_width, original_height = self._width, self._height
        self._width, self._height = preview_width, preview_height

        try:
            return self._generate_mock_image(datetime.now(timezone.utc))
        finally:
            self._width, self._height = original_width, original_height

    async def get_status(self) -> CameraStatus:
        """Get current camera status."""
        return CameraStatus(
            state=self._state,
            current_resolution=(self._width, self._height),
            is_front_camera=self._is_front,
            error_message=self._error_message,
        )

    async def set_resolution(self, width: int, height: int) -> bool:
        """Set camera resolution."""
        if (width, height) not in self.SUPPORTED_RESOLUTIONS:
            return False

        self._width = width
        self._height = height
        return True

    async def switch_camera(self, use_front: bool) -> bool:
        """Switch between front and back camera (simulated)."""
        await asyncio.sleep(0.05)  # Simulate switch delay
        self._is_front = use_front
        return True

    def get_capabilities(self) -> CameraCapabilities:
        """Get camera capabilities."""
        return CameraCapabilities(
            resolutions=self.SUPPORTED_RESOLUTIONS,
            supports_front_back=True,
            max_photo_count=None,
        )

    def _generate_mock_image(self, timestamp: datetime) -> bytes:
        """Generate a mock image with optional watermark.

        Args:
            timestamp: Timestamp to display on the image.

        Returns:
            JPEG-encoded image bytes.
        """
        if HAS_PIL:
            return self._generate_pil_image(timestamp)
        else:
            return self._generate_simple_jpeg()

    def _generate_pil_image(self, timestamp: datetime) -> bytes:
        """Generate a mock image using PIL."""
        # Create a gradient background
        img = Image.new("RGB", (self._width, self._height))

        # Generate gradient based on camera type
        if self._is_front:
            base_color = (73, 109, 137)  # Blue tint for front camera
        else:
            base_color = (73, 137, 109)  # Green tint for back camera

        # Create simple gradient
        for y in range(self._height):
            factor = y / self._height
            r = int(base_color[0] * (1 - factor * 0.3))
            g = int(base_color[1] * (1 - factor * 0.3))
            b = int(base_color[2] * (1 - factor * 0.3))
            for x in range(self._width):
                img.putpixel((x, y), (r, g, b))

        if self._watermark:
            draw = ImageDraw.Draw(img)
            timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
            camera_type = "FRONT" if self._is_front else "BACK"

            # Draw watermark text
            text_lines = [
                "MOCK CAMERA",
                f"Camera: {camera_type}",
                f"Resolution: {self._width}x{self._height}",
                timestamp_str,
            ]

            y_pos = 20
            for line in text_lines:
                draw.text((20, y_pos), line, fill=(255, 255, 255, 200))
                y_pos += 30

        # Convert to JPEG bytes
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        return buffer.getvalue()

    def _generate_simple_jpeg(self) -> bytes:
        """Generate a minimal valid JPEG without PIL.

        This is a fallback for when PIL is not available.
        Returns a minimal 1x1 gray pixel JPEG.
        """
        # Minimal valid JPEG (1x1 gray pixel)
        # This is a placeholder - in production, PIL should be used
        return bytes(
            [
                0xFF,
                0xD8,
                0xFF,
                0xE0,
                0x00,
                0x10,
                0x4A,
                0x46,
                0x49,
                0x46,
                0x00,
                0x01,
                0x01,
                0x00,
                0x00,
                0x01,
                0x00,
                0x01,
                0x00,
                0x00,
                0xFF,
                0xDB,
                0x00,
                0x43,
                0x00,
                0x08,
                0x06,
                0x06,
                0x07,
                0x06,
                0x05,
                0x08,
                0x07,
                0x07,
                0x07,
                0x09,
                0x09,
                0x08,
                0x0A,
                0x0C,
                0x14,
                0x0D,
                0x0C,
                0x0B,
                0x0B,
                0x0C,
                0x19,
                0x12,
                0x13,
                0x0F,
                0x14,
                0x1D,
                0x1A,
                0x1F,
                0x1E,
                0x1D,
                0x1A,
                0x1C,
                0x1C,
                0x20,
                0x24,
                0x2E,
                0x27,
                0x20,
                0x22,
                0x2C,
                0x23,
                0x1C,
                0x1C,
                0x28,
                0x37,
                0x29,
                0x2C,
                0x30,
                0x31,
                0x34,
                0x34,
                0x34,
                0x1F,
                0x27,
                0x39,
                0x3D,
                0x38,
                0x32,
                0x3C,
                0x2E,
                0x33,
                0x34,
                0x32,
                0xFF,
                0xC0,
                0x00,
                0x0B,
                0x08,
                0x00,
                0x01,
                0x00,
                0x01,
                0x01,
                0x01,
                0x11,
                0x00,
                0xFF,
                0xC4,
                0x00,
                0x1F,
                0x00,
                0x00,
                0x01,
                0x05,
                0x01,
                0x01,
                0x01,
                0x01,
                0x01,
                0x01,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x01,
                0x02,
                0x03,
                0x04,
                0x05,
                0x06,
                0x07,
                0x08,
                0x09,
                0x0A,
                0x0B,
                0xFF,
                0xC4,
                0x00,
                0xB5,
                0x10,
                0x00,
                0x02,
                0x01,
                0x03,
                0x03,
                0x02,
                0x04,
                0x03,
                0x05,
                0x05,
                0x04,
                0x04,
                0x00,
                0x00,
                0x01,
                0x7D,
                0x01,
                0x02,
                0x03,
                0x00,
                0x04,
                0x11,
                0x05,
                0x12,
                0x21,
                0x31,
                0x41,
                0x06,
                0x13,
                0x51,
                0x61,
                0x07,
                0x22,
                0x71,
                0x14,
                0x32,
                0x81,
                0x91,
                0xA1,
                0x08,
                0x23,
                0x42,
                0xB1,
                0xC1,
                0x15,
                0x52,
                0xD1,
                0xF0,
                0x24,
                0x33,
                0x62,
                0x72,
                0x82,
                0x09,
                0x0A,
                0x16,
                0x17,
                0x18,
                0x19,
                0x1A,
                0x25,
                0x26,
                0x27,
                0x28,
                0x29,
                0x2A,
                0x34,
                0x35,
                0x36,
                0x37,
                0x38,
                0x39,
                0x3A,
                0x43,
                0x44,
                0x45,
                0x46,
                0x47,
                0x48,
                0x49,
                0x4A,
                0x53,
                0x54,
                0x55,
                0x56,
                0x57,
                0x58,
                0x59,
                0x5A,
                0x63,
                0x64,
                0x65,
                0x66,
                0x67,
                0x68,
                0x69,
                0x6A,
                0x73,
                0x74,
                0x75,
                0x76,
                0x77,
                0x78,
                0x79,
                0x7A,
                0x83,
                0x84,
                0x85,
                0x86,
                0x87,
                0x88,
                0x89,
                0x8A,
                0x92,
                0x93,
                0x94,
                0x95,
                0x96,
                0x97,
                0x98,
                0x99,
                0x9A,
                0xA2,
                0xA3,
                0xA4,
                0xA5,
                0xA6,
                0xA7,
                0xA8,
                0xA9,
                0xAA,
                0xB2,
                0xB3,
                0xB4,
                0xB5,
                0xB6,
                0xB7,
                0xB8,
                0xB9,
                0xBA,
                0xC2,
                0xC3,
                0xC4,
                0xC5,
                0xC6,
                0xC7,
                0xC8,
                0xC9,
                0xCA,
                0xD2,
                0xD3,
                0xD4,
                0xD5,
                0xD6,
                0xD7,
                0xD8,
                0xD9,
                0xDA,
                0xE1,
                0xE2,
                0xE3,
                0xE4,
                0xE5,
                0xE6,
                0xE7,
                0xE8,
                0xE9,
                0xEA,
                0xF1,
                0xF2,
                0xF3,
                0xF4,
                0xF5,
                0xF6,
                0xF7,
                0xF8,
                0xF9,
                0xFA,
                0xFF,
                0xDA,
                0x00,
                0x08,
                0x01,
                0x01,
                0x00,
                0x00,
                0x3F,
                0x00,
                0xFB,
                0xD5,
                0xDB,
                0x20,
                0xA8,
                0xF0,
                0xFF,
                0xD9,
            ]
        )


def register(_: object) -> None:
    """Register mock camera driver with the factory."""
    from device.libs.hil.factory import DriverFactory

    DriverFactory.register_camera("mock", lambda cfg: MockCamera(dict(cfg)))
