from __future__ import annotations

from ....libs.schemas.ai import AIInferenceRequest, InferenceType
from ..engine import run_inference
from ..preprocessing import preprocess_for_inference


def test_phi3_mini_runner_qa() -> None:
    req = AIInferenceRequest(
        source="test-suite",
        inference_type=InferenceType.qa,
        model_id="phi3-mini",
        input_data={"question": "What is Waycore?", "context": "Waycore is a system."},
        options={},
    )
    pre = preprocess_for_inference(req)
    resp = run_inference(req, pre)
    assert resp.success is True
    assert len(resp.results) == 1
    assert resp.results[0].label.startswith("phi3-mini:")
