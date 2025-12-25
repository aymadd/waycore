from __future__ import annotations

import time
from typing import cast

from device.libs.schemas.ai import (
    AIInferenceRequest,
    AIInferenceResponse,
    InferenceResult,
    InferenceType,
)

from .models.runtime import ModelRunner
from .models.runtime import registry as model_registry
from .preprocessing import ImagePreprocessed, PreprocessedInput, QAPreprocessed


class InferenceEngineError(RuntimeError):
    """
    Raised when inference execution fails for any reason.
    """


def run_inference(
    request: AIInferenceRequest,
    preprocessed: PreprocessedInput,
    *,
    response_source: str = "ai_service",
) -> AIInferenceResponse:
    """
    Execute a minimal/deterministic inference routine for each supported type.
    This is a lightweight, dependency-free placeholder suitable for integration
    and end-to-end plumbing. Real backends should replace the core logic.
    """
    start = time.monotonic()
    try:
        # Try model-specific runner first
        runner: ModelRunner | None = model_registry.get(request.model_id)
        if runner and runner.supports(request.inference_type):
            if request.inference_type in (
                InferenceType.image_classification,
                InferenceType.object_detection,
            ):
                assert isinstance(preprocessed, dict) and preprocessed.get("type") == "image"
                results = runner.infer_image(cast(ImagePreprocessed, preprocessed))
            elif request.inference_type == InferenceType.qa:
                assert isinstance(preprocessed, dict) and preprocessed.get("type") == "qa"
                results = runner.infer_qa(cast(QAPreprocessed, preprocessed))
            else:
                raise InferenceEngineError(f"Unsupported inference_type: {request.inference_type}")
        elif request.inference_type in (
            InferenceType.image_classification,
            InferenceType.object_detection,
        ):
            # Fallback deterministic path
            results = _infer_image_like(preprocessed)
        elif request.inference_type == InferenceType.qa:
            results = _infer_qa(preprocessed)
        else:
            raise InferenceEngineError(f"Unsupported inference_type: {request.inference_type}")

        processing_time_ms = int((time.monotonic() - start) * 1000)
        return AIInferenceResponse(
            source=response_source,
            request_id=request.msg_id,
            inference_type=request.inference_type,
            model_id=request.model_id,
            results=results,
            processing_time_ms=processing_time_ms,
            success=True,
            error_message=None,
        )
    except Exception as exc:  # noqa: BLE001 - surface as response error
        processing_time_ms = int((time.monotonic() - start) * 1000)
        # Create a failure response while preserving request correlation
        return AIInferenceResponse(
            source=response_source,
            request_id=request.msg_id,
            inference_type=request.inference_type,
            model_id=request.model_id,
            results=[],
            processing_time_ms=processing_time_ms,
            success=False,
            error_message=str(exc),
        )


def _infer_image_like(preprocessed: PreprocessedInput) -> list[InferenceResult]:
    if not isinstance(preprocessed, dict) or preprocessed.get("type") != "image":
        raise InferenceEngineError("Preprocessed payload must be of type 'image'")
    # Minimal, deterministic placeholder classification/detection
    source = preprocessed.get("source")
    label = f"image:{source}"
    return [InferenceResult(label=label, confidence=0.0, metadata={"source": source})]


def _infer_qa(preprocessed: PreprocessedInput) -> list[InferenceResult]:
    if not isinstance(preprocessed, dict) or preprocessed.get("type") != "qa":
        raise InferenceEngineError("Preprocessed payload must be of type 'qa'")

    qa = cast(QAPreprocessed, preprocessed)
    question: str = qa["question"]
    context: list[str] = qa["context"]

    # Minimal heuristic: echo back the first non-empty context sentence
    candidate = next((c for c in context if isinstance(c, str) and c.strip()), "N/A")
    # Use the label to carry a simple answer surrogate
    return [
        InferenceResult(
            label=candidate,
            confidence=0.0,
            metadata={"question": question},
        )
    ]
