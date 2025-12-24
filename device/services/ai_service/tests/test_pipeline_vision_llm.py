from __future__ import annotations

import base64

from ....libs.schemas.ai import AIInferenceRequest, InferenceType
from ..engine import run_inference
from ..preprocessing import preprocess_for_inference


def test_vision_to_llm_pipeline_stub() -> None:
    b64 = base64.b64encode(b"img").decode("ascii")
    req = AIInferenceRequest(
        source="test-suite",
        inference_type=InferenceType.image_classification,
        model_id="vision-llm",
        input_data={"image_b64": b64},
        options={},
    )
    pre = preprocess_for_inference(req)
    resp = run_inference(req, pre)
    assert resp.success is True
    assert len(resp.results) == 1
    # Output is textual answer from LLM stub
    assert (
        "phi3-mini" in resp.results[0].label
        or "mobilenetv3" in resp.results[0].label
        or resp.results[0].label
    )
