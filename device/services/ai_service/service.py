from __future__ import annotations

import asyncio
from typing import Any, Callable

from device.libs.common.base_service import BaseService
from device.libs.messaging.bus import MessageBus
from device.libs.schemas.ai import AIInferenceRequest

from .engine import run_inference
from .preprocessing import PreprocessingError, preprocess_for_inference


class AIService(BaseService):
    def __init__(self, config: dict[str, Any], bus: MessageBus | None = None) -> None:
        super().__init__(config, bus)
        self._healthy = False
        self._unsubscribe: Callable[[], None] | None = None
        self._idle_sleep_s = float(config.get("idle_sleep_seconds", 0.1))
        self._response_source = str(config.get("response_source", "ai-service"))

    @property
    def response_source(self) -> str:
        return self._response_source

    async def _setup(self) -> None:
        self._healthy = True
        if self.bus:
            self._unsubscribe = self.bus.subscribe("ai/inference/request", self._on_request)

    async def _run(self) -> None:
        # Event-driven; idle loop to allow graceful stop
        while not self.should_stop():
            await asyncio.sleep(self._idle_sleep_s)

    async def _cleanup(self) -> None:
        self._healthy = False
        if self._unsubscribe:
            try:
                self._unsubscribe()
            finally:
                self._unsubscribe = None

    def is_healthy(self) -> bool:
        return self._healthy

    def _on_request(self, topic: str, payload: bytes) -> None:
        # Parse, preprocess, run inference, publish response (fire-and-forget)
        if not self.bus:
            return
        bus = self.bus
        try:
            req = AIInferenceRequest.model_validate_json(payload.decode("utf-8"))
        except Exception:
            # Ignore malformed requests
            return

        async def _process() -> None:
            try:
                pre = preprocess_for_inference(req)
                resp = run_inference(req, pre, response_source=self._response_source)
            except PreprocessingError as exc:
                from device.libs.schemas.ai import AIInferenceResponse

                # Return a structured failure response when preprocessing fails
                resp = AIInferenceResponse(
                    source=self._response_source,
                    request_id=req.msg_id,
                    inference_type=req.inference_type,
                    model_id=req.model_id,
                    results=[],
                    processing_time_ms=0,
                    success=False,
                    error_message=str(exc),
                )
            assert bus is not None
            await bus.publish("ai/inference/response", resp.model_dump_json())

        asyncio.create_task(_process())
