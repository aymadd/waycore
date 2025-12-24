from __future__ import annotations

from typing import Any

from device.libs.schemas.ai import AIInferenceRequest, AIInferenceResponse, InferenceType
from fastapi import FastAPI, HTTPException

from .engine import run_inference
from .preprocessing import PreprocessingError, preprocess_for_inference
from .service import AIService


def create_app(service: AIService) -> FastAPI:
    app = FastAPI(title="AI Service API")

    @app.get("/health")  # type: ignore[misc]
    async def health() -> dict[str, Any]:
        if service.is_healthy():
            return {"status": "ok"}
        raise HTTPException(status_code=503, detail="not ready")

    # Phase 7.4 will add inference endpoints here
    @app.post("/api/inference")  # type: ignore[misc]
    async def inference(req: AIInferenceRequest) -> AIInferenceResponse:
        try:
            pre = preprocess_for_inference(req)
            return run_inference(req, pre, response_source=service.response_source)
        except PreprocessingError as exc:
            # Return a structured failure response when preprocessing fails
            return AIInferenceResponse(
                source=service.response_source,
                request_id=req.msg_id,
                inference_type=req.inference_type,
                model_id=req.model_id,
                results=[],
                processing_time_ms=0,
                success=False,
                error_message=str(exc),
            )

    @app.post("/api/image/classify")  # type: ignore[misc]
    async def image_classify(body: dict[str, Any]) -> AIInferenceResponse:
        model_id = str(body.get("model_id", "mobilenetv3"))
        input_data = body.get("input_data", {})
        req = AIInferenceRequest(
            source=service.response_source,
            inference_type=InferenceType.image_classification,
            model_id=model_id,
            input_data=input_data,
            options={},
        )
        pre = preprocess_for_inference(req)
        return run_inference(req, pre, response_source=service.response_source)

    @app.post("/api/chat")  # type: ignore[misc]
    async def chat(body: dict[str, Any]) -> AIInferenceResponse:
        model_id = str(body.get("model_id", "phi3-mini"))
        question = str(body.get("question", "")).strip()
        context = body.get("context", "")
        req = AIInferenceRequest(
            source=service.response_source,
            inference_type=InferenceType.qa,
            model_id=model_id,
            input_data={"question": question, "context": context},
            options={},
        )
        pre = preprocess_for_inference(req)
        return run_inference(req, pre, response_source=service.response_source)

    return app
