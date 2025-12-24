from __future__ import annotations

from typing import Any

from device.libs.schemas.system import SystemCommand
from fastapi import FastAPI, HTTPException

from .service import CoreDaemonService


def create_app(service: CoreDaemonService) -> FastAPI:
    app = FastAPI(title="Core Daemon API")

    @app.get("/health")  # type: ignore[misc]
    async def health() -> dict[str, Any]:
        if service.is_healthy():
            return {"status": "ok"}
        raise HTTPException(status_code=503, detail="not ready")

    @app.get("/api/status")  # type: ignore[misc]
    async def status() -> dict[str, Any]:
        return service.get_status()

    @app.post("/api/command")  # type: ignore[misc]
    async def command(cmd: SystemCommand) -> dict[str, Any]:
        ok = await service.handle_command(cmd.command, cmd.parameters)
        return {"success": ok}

    return app
