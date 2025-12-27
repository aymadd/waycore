from __future__ import annotations

import base64

from device.libs.schemas.ai import AIInferenceRequest, InferenceType
from device.services.ai_service.engine import run_inference
from device.services.ai_service.preprocessing import preprocess_for_inference


def _mk_req(model_id: str, inference_type: InferenceType, input_data: dict) -> AIInferenceRequest:  # type: ignore[no-redeclare]
    return AIInferenceRequest(
        source="test-suite",
        inference_type=inference_type,
        model_id=model_id,
        input_data=input_data,
        options={},
    )


def test_mobilenetv3_runner_path_used() -> None:
    raw = b"img"
    b64 = base64.b64encode(raw).decode("ascii")
    req = _mk_req("mobilenetv3", InferenceType.image_classification, {"image_b64": b64})
    pre = preprocess_for_inference(req)
    resp = run_inference(req, pre)
    assert resp.success is True
    assert len(resp.results) == 1
    # Should carry mobilenet stub prefix
    assert resp.results[0].label.startswith("mobilenetv3:")
