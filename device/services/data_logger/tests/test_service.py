from __future__ import annotations

import asyncio
from typing import Callable

import pytest

from ....libs.schemas.ai import AIInferenceResponse, InferenceResult, InferenceType
from ....libs.schemas.comms import MessageReceived, Transport
from ..service import DataLoggerService


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
async def test_data_logger_handles_messages_and_logs(tmp_path) -> None:  # type: ignore[no-untyped-def]
    db_path = tmp_path / "db.sqlite3"
    bus = _FakeBus()
    cfg = {
        "database_path": str(db_path),
        "idle_sleep_seconds": 0.01,
    }
    svc = DataLoggerService(cfg, bus=bus)  # type: ignore[arg-type]
    await svc.start()
    try:
        # Simulate comms message
        msg = MessageReceived(
            source="test",
            transport=Transport.lora,
            from_node="a",
            to_node="b",
            content="hello",
            channel="primary",
            rssi=-70.0,
            snr=5.0,
            hop_limit=3,
        )
        bus.simulate("comms/message/received", msg.model_dump_json())

        # Simulate AI inference
        resp = AIInferenceResponse(
            source="test",
            request_id=msg.msg_id,  # reuse id just for linkage
            inference_type=InferenceType.qa,
            model_id="m1",
            results=[InferenceResult(label="ok", confidence=0.0)],
            processing_time_ms=1,
            success=True,
            error_message=None,
        )
        bus.simulate("ai/inference/response", resp.model_dump_json())

        # Simulate generic event
        bus.simulate("system/state/changed", '{"ok": true}')

        # allow tasks to run
        await asyncio.sleep(0.05)

        # Quick sanity: check via service's db
        ai_rows = await svc._db.fetch_latest("ai_inferences", 5)  # type: ignore[attr-defined]
        cm_rows = await svc._db.fetch_latest("comms_messages", 5)  # type: ignore[attr-defined]
        ev_rows = await svc._db.fetch_latest("events", 5)  # type: ignore[attr-defined]
        assert len(ai_rows) >= 1
        assert len(cm_rows) >= 1
        assert len(ev_rows) >= 1
    finally:
        await svc.stop()
