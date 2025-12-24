from __future__ import annotations

import asyncio
from typing import Callable

import pytest

from ....libs.schemas.ai import AIInferenceRequest, AIInferenceResponse, InferenceType
from ..service import AIService


class _FakeBus:
    def __init__(self) -> None:
        self.published: list[tuple[str, str]] = []
        self._subs: dict[str, Callable[[str, bytes], None]] = {}

    async def connect(self, broker_url: str) -> None: ...

    async def disconnect(self) -> None: ...

    async def publish(
        self, topic: str, payload: bytes | str, qos: int = 0, retain: bool = False
    ) -> None:
        if isinstance(payload, bytes):
            data = payload.decode("utf-8")
        else:
            data = payload
        self.published.append((topic, data))

    def subscribe(self, topic: str, handler, qos: int = 0):  # type: ignore[no-untyped-def]
        self._subs[topic] = handler

        def _unsub() -> None:
            self._subs.pop(topic, None)

        return _unsub

    # helper to simulate incoming message
    def simulate_message(self, topic: str, payload: str) -> None:
        if topic in self._subs:
            self._subs[topic](topic, payload.encode("utf-8"))


@pytest.mark.asyncio
async def test_ai_service_processes_request_and_publishes_response() -> None:
    bus = _FakeBus()
    svc = AIService(config={}, bus=bus)  # type: ignore[arg-type]
    await svc.start()
    try:
        req = AIInferenceRequest(
            source="test-suite",
            inference_type=InferenceType.qa,
            model_id="m1",
            input_data={"question": "What is Waycore?", "context": "Waycore is a system."},
            options={},
        )
        bus.simulate_message("ai/inference/request", req.model_dump_json())
        # Allow background task to run
        await asyncio.sleep(0.05)
        # Assert a response was published
        pubs = [p for p in bus.published if p[0] == "ai/inference/response"]
        assert len(pubs) >= 1
        topic, data = pubs[-1]
        resp = AIInferenceResponse.model_validate_json(data)
        assert resp.request_id == req.msg_id
        assert resp.success is True
        assert len(resp.results) == 1
    finally:
        await svc.stop()
