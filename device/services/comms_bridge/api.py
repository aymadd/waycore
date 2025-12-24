from __future__ import annotations

from typing import Any

from device.libs.schemas.comms import SendMessageRequest
from fastapi import FastAPI, HTTPException

from .service import CommsBridgeService


def create_app(service: CommsBridgeService) -> FastAPI:
    app = FastAPI(title="Comms Bridge API")

    @app.get("/health")  # type: ignore[misc]
    async def health() -> dict[str, Any]:
        if service.is_healthy():
            return {"status": "ok"}
        raise HTTPException(status_code=503, detail="not ready")

    @app.get("/api/radios")  # type: ignore[misc]
    async def radios() -> dict[str, Any]:
        status = await service._manager.get_status()  # deliberately accessing for MVP
        return {"radios": {k: s.__dict__ for k, s in status.items()}}

    @app.post("/api/send")  # type: ignore[misc]
    async def send(req: SendMessageRequest) -> dict[str, Any]:
        ok = await service._manager.send(
            content=req.content.encode("utf-8"),
            transport_hint=req.transport.value,
            to_node=req.to_node,
            channel=req.channel,
            want_ack=req.want_ack,
        )
        return {"success": ok}

    return app
