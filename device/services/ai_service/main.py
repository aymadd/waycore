from __future__ import annotations

import asyncio
import os
import signal
from typing import Any

import uvicorn
import yaml
from device.libs.messaging.mqtt_bus import MQTTBus

from .api import create_app
from .service import AIService


def load_config() -> dict[str, Any]:
    config_path = os.environ.get(
        "AI_SERVICE_CONFIG", "device/services/ai_service/config/default.yaml"
    )
    try:
        with open(config_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}


async def run() -> None:
    cfg = load_config()
    broker = cfg.get("mqtt_broker_url", "mqtt://localhost:1883")
    bus = MQTTBus()
    await bus.connect(broker)
    service = AIService(cfg, bus=bus)
    await service.start()
    app = create_app(service)

    config = uvicorn.Config(
        app=app, host="0.0.0.0", port=int(cfg.get("port", 8010)), log_level="info"
    )
    server = uvicorn.Server(config)

    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _handle_sig(*_args):  # type: ignore[no-untyped-def]
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _handle_sig)

    async def _serve() -> None:
        await server.serve()

    server_task = asyncio.create_task(_serve())
    await stop_event.wait()
    server.should_exit = True
    await server_task
    await service.stop()
    await bus.disconnect()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
