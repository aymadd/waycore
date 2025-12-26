from __future__ import annotations

import json
from uuid import uuid4

import pytest
from device.libs.database import AsyncSQLite
from device.libs.schemas.ai import AIInferenceResponse, InferenceResult, InferenceType


@pytest.mark.asyncio
async def test_sqlite_open_insert_fetch(tmp_path) -> None:  # type: ignore[no-untyped-def]
    dbfile = tmp_path / "db.sqlite3"
    db = AsyncSQLite(dbfile)
    await db.open()
    try:
        await db.log_event("test/topic", '{"hello":"world"}')
        ev = await db.fetch_latest("events", limit=1)
        assert len(ev) == 1
        assert ev[0]["topic"] == "test/topic"

        resp = AIInferenceResponse(
            source="test",
            request_id=uuid4(),
            inference_type=InferenceType.qa,
            model_id="m1",
            results=[InferenceResult(label="answer", confidence=0.1)],
            processing_time_ms=5,
            success=True,
            error_message=None,
        )
        await db.log_ai_inference(resp)
        ai = await db.fetch_latest("ai_inferences", limit=1)
        assert len(ai) == 1
        assert ai[0]["model_id"] == "m1"
        results = json.loads(ai[0]["results"])
        assert results[0]["label"] == "answer"
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_preferences_default_values(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Test that default preferences are initialized on database open."""
    dbfile = tmp_path / "db.sqlite3"
    db = AsyncSQLite(dbfile)
    await db.open()
    try:
        prefs = await db.get_all_preferences()
        # Defaults are US units
        assert prefs["units.temperature"] == "F"
        assert prefs["units.distance"] == "mi"
        assert prefs["units.weight"] == "lb"
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_preferences_get_set(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Test getting and setting preferences."""
    dbfile = tmp_path / "db.sqlite3"
    db = AsyncSQLite(dbfile)
    await db.open()
    try:
        # Get default value (now Fahrenheit)
        temp_unit = await db.get_preference("units.temperature")
        assert temp_unit == "F"

        # Set to Celsius
        success = await db.set_preference("units.temperature", "C")
        assert success is True

        # Verify new value
        temp_unit = await db.get_preference("units.temperature")
        assert temp_unit == "C"
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_preferences_validation(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Test that invalid preference values are rejected."""
    dbfile = tmp_path / "db.sqlite3"
    db = AsyncSQLite(dbfile)
    await db.open()
    try:
        # Try to set invalid value
        success = await db.set_preference("units.temperature", "K")  # Kelvin not allowed
        assert success is False

        # Value should still be default (Fahrenheit)
        temp_unit = await db.get_preference("units.temperature")
        assert temp_unit == "F"
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_preferences_reset(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Test resetting preferences to defaults."""
    dbfile = tmp_path / "db.sqlite3"
    db = AsyncSQLite(dbfile)
    await db.open()
    try:
        # Change a preference from defaults
        await db.set_preference("units.temperature", "C")
        await db.set_preference("units.distance", "km")

        # Reset all
        await db.reset_preferences()

        # Verify defaults restored (US units)
        prefs = await db.get_all_preferences()
        assert prefs["units.temperature"] == "F"
        assert prefs["units.distance"] == "mi"
    finally:
        await db.close()
