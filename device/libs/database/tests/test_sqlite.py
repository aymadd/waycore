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
