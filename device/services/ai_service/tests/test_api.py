from __future__ import annotations

from fastapi.testclient import TestClient

from ....libs.schemas.ai import InferenceType
from ..api import create_app
from ..service import AIService


def test_inference_endpoint_sync() -> None:
    service = AIService(config={"response_source": "ai-service-test"})  # type: ignore[arg-type]
    app = create_app(service)
    client = TestClient(app)

    payload = {
        "source": "test-suite",
        "inference_type": InferenceType.qa.value,
        "model_id": "m1",
        "input_data": {"question": "What is Waycore?", "context": "Waycore is a system."},
        "options": {},
    }

    resp = client.post("/api/inference", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["inference_type"] == InferenceType.qa.value
    assert data["model_id"] == "m1"
    assert isinstance(data["processing_time_ms"], int)
    assert len(data["results"]) == 1
