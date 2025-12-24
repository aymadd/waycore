from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException

from .service import ModuleManagerService


def create_app(service: ModuleManagerService) -> FastAPI:
    app = FastAPI(title="Module Manager API")

    @app.get("/health")  # type: ignore[misc]
    async def health() -> dict[str, Any]:
        if service.is_healthy():
            return {"status": "ok"}
        raise HTTPException(status_code=503, detail="not ready")

    @app.get("/api/modules")  # type: ignore[misc]
    async def modules() -> dict[str, Any]:
        return {"modules": service.list_modules()}

    return app
