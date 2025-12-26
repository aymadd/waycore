from __future__ import annotations

import asyncio
import os
import signal
from pathlib import Path
from typing import Any

import device.drivers.mock  # noqa: F401 - Register mock drivers
import uvicorn
import yaml
from device.libs.hil.factory import DriverFactory
from device.libs.messaging.mqtt_bus import MQTTBus

from .api import create_app
from .service import CameraService


def load_config() -> dict[str, Any]:
    """Load configuration from YAML file."""
    config_path = os.environ.get(
        "CAMERA_SERVICE_CONFIG", "device/services/camera_service/config/default.yaml"
    )
    try:
        with open(config_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}


async def run() -> None:
    """Run the camera service."""
    cfg = load_config()

    # Setup MQTT bus
    broker = cfg.get("mqtt_broker_url", "mqtt://localhost:1883")
    bus = MQTTBus()
    try:
        await bus.connect(broker)
    except Exception:
        # Continue without MQTT if not available (local dev)
        bus = None  # type: ignore[assignment]

    # Create camera driver
    camera_cfg = cfg.get("camera", {})
    driver_name = camera_cfg.get("driver", "mock")
    camera = DriverFactory.create_camera(
        driver_name,
        {
            "default_width": camera_cfg.get("default_resolution", {}).get("width", 1280),
            "default_height": camera_cfg.get("default_resolution", {}).get("height", 720),
            "watermark": camera_cfg.get("watermark", True),
        },
    )

    # Create and start service
    service = CameraService(cfg, camera, bus=bus)
    await service.start()

    # Create FastAPI app
    app = create_app(service)

    # Setup server
    use_uds = os.getenv("USE_UNIX_SOCKET", "true").lower() == "true"
    if use_uds:
        socket_dir = Path("/tmp/waycore")
        socket_dir.mkdir(parents=True, exist_ok=True)
        uds_path = socket_dir / "camera-service.sock"
        if uds_path.exists():
            uds_path.unlink()
        config = uvicorn.Config(app=app, uds=str(uds_path), log_level="info")
    else:
        config = uvicorn.Config(
            app=app, host="0.0.0.0", port=int(cfg.get("port", 8006)), log_level="info"
        )
    server = uvicorn.Server(config)

    # Setup signal handlers
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _handle_sig(*_args: object) -> None:
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _handle_sig)

    # Run server
    async def _serve() -> None:
        await server.serve()

    server_task = asyncio.create_task(_serve())
    await stop_event.wait()
    server.should_exit = True
    await server_task

    # Cleanup
    await service.stop()
    if bus:
        await bus.disconnect()


def main() -> None:
    """Main entry point."""
    asyncio.run(run())


if __name__ == "__main__":
    main()
