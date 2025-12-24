from __future__ import annotations

from fastapi.testclient import TestClient

from ..api import create_app
from ..service import AIService


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
