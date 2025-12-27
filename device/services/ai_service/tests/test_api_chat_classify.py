from __future__ import annotations

from device.services.ai_service.api import create_app
from device.services.ai_service.service import AIService
from fastapi.testclient import TestClient


def test_image_classify_endpoint() -> None:
    app = create_app(AIService(config={"response_source": "ai"}))  # type: ignore[arg-type]
    client = TestClient(app)
    resp = client.post("/api/image/classify", json={"input_data": {"image_b64": "aW1n"}})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["inference_type"] == "image_classification"
    assert data["model_id"] == "mobilenetv3"
    assert len(data["results"]) == 1


def test_chat_endpoint() -> None:
    app = create_app(AIService(config={"response_source": "ai"}))  # type: ignore[arg-type]
    client = TestClient(app)
    resp = client.post(
        "/api/chat",
        json={"question": "Q?", "context": "Some context", "model_id": "phi3-mini"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["inference_type"] == "qa"
    assert data["model_id"] == "phi3-mini"
    assert len(data["results"]) == 1
