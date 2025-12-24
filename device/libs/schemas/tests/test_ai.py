from __future__ import annotations

from uuid import uuid4

import pytest
from device.libs.schemas.ai import (
    AIInferenceRequest,
    AIInferenceResponse,
    InferenceResult,
    InferenceType,
)
from pydantic import ValidationError


def test_ai_inference_request_valid() -> None:
    req = AIInferenceRequest(
        source="ui",
        inference_type=InferenceType.image_classification,
        model_id="mobilenet",
        input_data={"image_path": "/tmp/x.jpg", "top_k": 3},
        options={"min_confidence": 0.2},
    )
    assert req.inference_type is InferenceType.image_classification
    assert req.model_id == "mobilenet"


def test_ai_inference_response_success_valid() -> None:
    request_id = uuid4()
    resp = AIInferenceResponse(
        source="ai-service",
        request_id=request_id,
        inference_type=InferenceType.image_classification,
        model_id="mobilenet",
        results=[
            InferenceResult(label="cat", confidence=0.92),
            InferenceResult(label="animal", confidence=0.12),
        ],
        processing_time_ms=321,
        success=True,
    )
    assert resp.success is True
    assert resp.results[0].label == "cat"


def test_ai_inference_response_failure_requires_error_message() -> None:
    request_id = uuid4()
    with pytest.raises(ValidationError):
        AIInferenceResponse(
            source="ai-service",
            request_id=request_id,
            inference_type=InferenceType.image_classification,
            model_id="mobilenet",
            results=[],
            processing_time_ms=10,
            success=False,
        )
