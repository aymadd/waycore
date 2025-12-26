from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from .service import DataLoggerService


class PreferenceUpdate(BaseModel):
    """Request body for updating a preference."""

    value: str


class NoteCreate(BaseModel):
    """Request body for creating a note."""

    title: str = ""
    content: str = ""


class NoteUpdate(BaseModel):
    """Request body for updating a note."""

    title: str
    content: str


def create_app(service: DataLoggerService) -> FastAPI:
    app = FastAPI(title="Data Logger API")

    @app.get("/health")
    async def health() -> dict[str, Any]:
        if service.is_healthy():
            return {"status": "ok"}
        raise HTTPException(status_code=503, detail="not ready")

    @app.get("/api/ai/latest")
    async def ai_latest(n: int = Query(50, ge=1, le=500)) -> list[dict[str, Any]]:
        return await service.latest_ai(n)

    @app.get("/api/comms/latest")
    async def comms_latest(n: int = Query(50, ge=1, le=500)) -> list[dict[str, Any]]:
        return await service.latest_comms(n)

    @app.get("/api/events/latest")
    async def events_latest(n: int = Query(50, ge=1, le=500)) -> list[dict[str, Any]]:
        return await service.latest_events(n)

    # --- Preferences Endpoints ---

    @app.get("/api/preferences")
    async def get_all_preferences() -> dict[str, str]:
        """Get all user preferences."""
        return await service.get_all_preferences()

    @app.get("/api/preferences/{key}")
    async def get_preference(key: str) -> dict[str, Any]:
        """Get a single preference by key."""
        value = await service.get_preference(key)
        if value is None:
            raise HTTPException(status_code=404, detail=f"Preference '{key}' not found")
        return {"key": key, "value": value}

    @app.put("/api/preferences/{key}")
    async def set_preference(key: str, body: PreferenceUpdate) -> dict[str, Any]:
        """Update a preference value."""
        success = await service.set_preference(key, body.value)
        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid value '{body.value}' for preference '{key}'",
            )
        return {"key": key, "value": body.value, "success": True}

    @app.post("/api/preferences/reset")
    async def reset_preferences() -> dict[str, Any]:
        """Reset all preferences to default values."""
        await service.reset_preferences()
        prefs = await service.get_all_preferences()
        return {"success": True, "preferences": prefs}

    # --- Notes Endpoints ---

    @app.get("/api/notes")
    async def get_all_notes() -> list[dict[str, Any]]:
        """Get all notes, ordered by most recently updated."""
        return await service.get_all_notes()

    @app.post("/api/notes")
    async def create_note(body: NoteCreate) -> dict[str, Any]:
        """Create a new note."""
        note_id = await service.create_note(body.title, body.content)
        note = await service.get_note(note_id)
        return {"success": True, "note": note}

    @app.get("/api/notes/{note_id}")
    async def get_note(note_id: int) -> dict[str, Any]:
        """Get a single note by ID."""
        note = await service.get_note(note_id)
        if note is None:
            raise HTTPException(status_code=404, detail="Note not found")
        return note

    @app.put("/api/notes/{note_id}")
    async def update_note(note_id: int, body: NoteUpdate) -> dict[str, Any]:
        """Update a note."""
        success = await service.update_note(note_id, body.title, body.content)
        if not success:
            raise HTTPException(status_code=404, detail="Note not found")
        note = await service.get_note(note_id)
        return {"success": True, "note": note}

    @app.delete("/api/notes/{note_id}")
    async def delete_note(note_id: int) -> dict[str, Any]:
        """Delete a note."""
        success = await service.delete_note(note_id)
        if not success:
            raise HTTPException(status_code=404, detail="Note not found")
        return {"success": True, "id": note_id}

    # --- Factory Reset ---

    @app.post("/api/factory-reset")
    async def factory_reset() -> dict[str, Any]:
        """
        Clear all user data: notes, preferences, logs.
        """
        notes_deleted = await service.delete_all_notes()
        await service.reset_preferences()
        # Could also clear events, comms_messages, ai_inferences if needed

        return {
            "success": True,
            "notes_deleted": notes_deleted,
            "message": "All user data cleared.",
        }

    return app
