from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Query

from .service import DataLoggerService


def create_app(service: DataLoggerService) -> FastAPI:
    app = FastAPI(title="Data Logger API")

    @app.get("/health")  # type: ignore[misc]
    async def health() -> dict[str, Any]:
        if service.is_healthy():
            return {"status": "ok"}
        raise HTTPException(status_code=503, detail="not ready")

    @app.get("/api/ai/latest")  # type: ignore[misc]
    async def ai_latest(n: int = Query(50, ge=1, le=500)) -> list[dict[str, Any]]:
        return await service.latest_ai(n)

    @app.get("/api/comms/latest")  # type: ignore[misc]
    async def comms_latest(n: int = Query(50, ge=1, le=500)) -> list[dict[str, Any]]:
        return await service.latest_comms(n)

    @app.get("/api/events/latest")  # type: ignore[misc]
    async def events_latest(n: int = Query(50, ge=1, le=500)) -> list[dict[str, Any]]:
        return await service.latest_events(n)

    return app
