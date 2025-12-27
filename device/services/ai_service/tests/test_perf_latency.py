from __future__ import annotations

import base64
import time

from device.libs.schemas.ai import AIInferenceRequest, InferenceType
from device.services.ai_service.engine import run_inference
from device.services.ai_service.preprocessing import preprocess_for_inference


def test_inference_latency_under_100ms() -> None:
    b64 = base64.b64encode(b"img").decode("ascii")
    req = AIInferenceRequest(
        source="test-suite",
        inference_type=InferenceType.image_classification,
        model_id="mobilenetv3",
        input_data={"image_b64": b64},
        options={},
    )
    pre = preprocess_for_inference(req)
    t0 = time.perf_counter()
    resp = run_inference(req, pre)
    t1 = time.perf_counter()
    elapsed_ms = (t1 - t0) * 1000.0
    assert resp.success is True
    assert elapsed_ms < 100.0
