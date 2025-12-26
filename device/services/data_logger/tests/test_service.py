from __future__ import annotations

import asyncio
from typing import Callable

import pytest
from device.libs.schemas.ai import AIInferenceResponse, InferenceResult, InferenceType
from device.services.data_logger.service import DataLoggerService


class _FakeBus:
    def __init__(self) -> None:
        self._subs: dict[str, Callable[[str, bytes], None]] = {}

    async def connect(self, broker_url: str) -> None: ...

    async def disconnect(self) -> None: ...

    async def publish(
        self, topic: str, payload: bytes | str, qos: int = 0, retain: bool = False
    ) -> None: ...

    def subscribe(self, topic: str, handler, qos: int = 0):  # type: ignore[no-untyped-def]
        self._subs[topic] = handler

        def _unsub() -> None:
            self._subs.pop(topic, None)

        return _unsub

    def simulate(self, topic: str, payload_str: str) -> None:
        if topic in self._subs:
            self._subs[topic](topic, payload_str.encode("utf-8"))


@pytest.mark.asyncio
async def test_data_logger_handles_ai_and_events(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Test that data logger handles AI inferences and system events."""
    bus = _FakeBus()
    cfg = {
        "database_dir": str(tmp_path),
        "idle_sleep_seconds": 0.01,
    }
    svc = DataLoggerService(cfg, bus=bus)  # type: ignore[arg-type]
    await svc.start()
    try:
        # Simulate AI inference
        import uuid

        resp = AIInferenceResponse(
            source="test",
            request_id=uuid.uuid4(),
            inference_type=InferenceType.qa,
            model_id="m1",
            results=[InferenceResult(label="ok", confidence=0.9)],
            processing_time_ms=100,
            success=True,
            error_message=None,
        )
        bus.simulate("ai/inference/response", resp.model_dump_json())

        # Simulate generic event
        bus.simulate("system/state/changed", '{"ok": true}')

        # allow tasks to run
        await asyncio.sleep(0.05)

        # Check AI inferences were logged
        ai_rows = await svc.latest_ai(5)
        assert len(ai_rows) >= 1
        assert ai_rows[0]["model_id"] == "m1"

        # Check events were logged
        ev_rows = await svc.latest_events(5)
        assert len(ev_rows) >= 1
    finally:
        await svc.stop()


@pytest.mark.asyncio
async def test_data_logger_preferences(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Test preferences are stored and retrieved correctly."""
    cfg = {
        "database_dir": str(tmp_path),
        "idle_sleep_seconds": 0.01,
    }
    svc = DataLoggerService(cfg, bus=None)
    await svc.start()
    try:
        # Default preferences should be set
        prefs = await svc.get_all_preferences()
        assert "units.temperature" in prefs

        # Set a preference
        await svc.set_preference("test.key", "test_value")
        value = await svc.get_preference("test.key")
        assert value == "test_value"

        # Reset should restore defaults
        await svc.reset_preferences()
        value = await svc.get_preference("test.key")
        assert value is None
    finally:
        await svc.stop()


@pytest.mark.asyncio
async def test_data_logger_notes(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Test notes CRUD operations."""
    cfg = {
        "database_dir": str(tmp_path),
        "idle_sleep_seconds": 0.01,
    }
    svc = DataLoggerService(cfg, bus=None)
    await svc.start()
    try:
        # Create a note
        note_id = await svc.create_note("Test Title", "Test Content")
        assert note_id > 0

        # Get the note
        note = await svc.get_note(note_id)
        assert note is not None
        assert note["title"] == "Test Title"
        assert note["content"] == "Test Content"

        # Update the note
        updated = await svc.update_note(note_id, "Updated Title", "Updated Content")
        assert updated is True

        # Delete the note
        deleted = await svc.delete_note(note_id)
        assert deleted is True

        # Verify deleted
        note = await svc.get_note(note_id)
        assert note is None
    finally:
        await svc.stop()
