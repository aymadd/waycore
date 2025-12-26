from __future__ import annotations

import asyncio
import logging
import os
import signal
from pathlib import Path
from typing import Any

import uvicorn
import yaml
from device.libs.database import AsyncSQLite
from device.libs.messaging.mqtt_bus import MQTTBus

from .api import create_app
from .mesh.service import init_mesh_service
from .service import CommsBridgeService

logger = logging.getLogger(__name__)


def load_config() -> dict[str, Any]:
    config_path = os.environ.get(
        "COMMS_BRIDGE_CONFIG", "device/services/comms_bridge/config/default.yaml"
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
    service = CommsBridgeService(cfg, bus=bus)
    await service.start()

    # Initialize database for mesh message persistence
    db_path = str(cfg.get("database_path", "data/waycore.sqlite3"))
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    db = AsyncSQLite(db_path)
    await db.open()
    logger.info(f"Database opened at {db_path}")

    # Initialize mesh service with database
    mesh_service = init_mesh_service(db=db)
    await mesh_service.load_history_from_db(limit=500)

    app = create_app(service)

    use_uds = os.getenv("USE_UNIX_SOCKET", "true").lower() == "true"
    if use_uds:
        socket_dir = Path("/tmp/waycore")
        socket_dir.mkdir(parents=True, exist_ok=True)
        uds_path = socket_dir / "comms-bridge.sock"
        if uds_path.exists():
            uds_path.unlink()
        config = uvicorn.Config(app=app, uds=str(uds_path), log_level="info")
    else:
        config = uvicorn.Config(
            app=app, host="0.0.0.0", port=int(cfg.get("port", 8003)), log_level="info"
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
    await db.close()
    await bus.disconnect()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
