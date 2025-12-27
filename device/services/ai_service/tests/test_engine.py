from __future__ import annotations

import base64
from typing import Any

from device.libs.schemas.ai import AIInferenceRequest, InferenceType
from device.services.ai_service.engine import run_inference
from device.services.ai_service.preprocessing import preprocess_for_inference


def _mk_req(inference_type: InferenceType, input_data: dict[str, Any]) -> AIInferenceRequest:
    return AIInferenceRequest(
        source="test-suite",
        inference_type=inference_type,
        model_id="test-model",
        input_data=input_data,
        options={},
    )


def test_engine_image_path_b64() -> None:
    raw = b"img"
    b64 = base64.b64encode(raw).decode("ascii")
    req = _mk_req(InferenceType.image_classification, {"image_b64": b64})
    pre = preprocess_for_inference(req)
    resp = run_inference(req, pre)
    assert resp.success is True
    assert resp.request_id == req.msg_id
    assert resp.inference_type == req.inference_type
    assert resp.model_id == req.model_id
    assert resp.processing_time_ms >= 0
    assert len(resp.results) == 1
    assert resp.results[0].label.startswith("image:")


def test_engine_image_path_bytes() -> None:
    req = _mk_req(InferenceType.object_detection, {"image_bytes": b"\x00\x01"})
    pre = preprocess_for_inference(req)
    resp = run_inference(req, pre)
    assert resp.success is True
    assert len(resp.results) == 1
    assert resp.results[0].label.startswith("image:")


def test_engine_qa_path() -> None:
    req = _mk_req(
        InferenceType.qa,
        {"question": "What is Waycore?", "context": ["Waycore is a system."]},
    )
    pre = preprocess_for_inference(req)
    resp = run_inference(req, pre)
    assert resp.success is True
    assert len(resp.results) == 1
    # Label echoes a context candidate as a stand-in "answer"
    assert "Waycore is a system." in resp.results[0].label
