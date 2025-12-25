from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from .service import DataLoggerService


class PreferenceUpdate(BaseModel):
    """Request body for updating a preference."""

    value: str


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

    # --- Preferences Endpoints ---

    @app.get("/api/preferences")  # type: ignore[misc]
    async def get_all_preferences() -> dict[str, str]:
        """Get all user preferences."""
        return await service.get_all_preferences()

    @app.get("/api/preferences/{key}")  # type: ignore[misc]
    async def get_preference(key: str) -> dict[str, Any]:
        """Get a single preference by key."""
        value = await service.get_preference(key)
        if value is None:
            raise HTTPException(status_code=404, detail=f"Preference '{key}' not found")
        return {"key": key, "value": value}

    @app.put("/api/preferences/{key}")  # type: ignore[misc]
    async def set_preference(key: str, body: PreferenceUpdate) -> dict[str, Any]:
        """Update a preference value."""
        success = await service.set_preference(key, body.value)
        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid value '{body.value}' for preference '{key}'",
            )
        return {"key": key, "value": body.value, "success": True}

    @app.post("/api/preferences/reset")  # type: ignore[misc]
    async def reset_preferences() -> dict[str, Any]:
        """Reset all preferences to default values."""
        await service.reset_preferences()
        prefs = await service.get_all_preferences()
        return {"success": True, "preferences": prefs}

    return app
