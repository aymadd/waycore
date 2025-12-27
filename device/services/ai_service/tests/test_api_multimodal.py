"""Tests for the multimodal chat endpoint."""

from __future__ import annotations

import base64

import pytest
from device.services.ai_service.api import create_app
from device.services.ai_service.service import AIService
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the AI service."""
    service = AIService(config={"response_source": "ai-service-test"})  # type: ignore[arg-type]
    app = create_app(service)
    return TestClient(app)


@pytest.fixture
def sample_image_b64() -> str:
    """Create a minimal valid PNG image for testing."""
    # 1x1 red pixel PNG
    png_data = bytes(
        [
            0x89,
            0x50,
            0x4E,
            0x47,
            0x0D,
            0x0A,
            0x1A,
            0x0A,  # PNG signature
            0x00,
            0x00,
            0x00,
            0x0D,
            0x49,
            0x48,
            0x44,
            0x52,  # IHDR
            0x00,
            0x00,
            0x00,
            0x01,
            0x00,
            0x00,
            0x00,
            0x01,  # 1x1
            0x08,
            0x02,
            0x00,
            0x00,
            0x00,
            0x90,
            0x77,
            0x53,
            0xDE,
            0x00,
            0x00,
            0x00,
            0x0C,
            0x49,
            0x44,
            0x41,
            0x54,  # IDAT
            0x08,
            0xD7,
            0x63,
            0xF8,
            0xCF,
            0xC0,
            0x00,
            0x00,
            0x01,
            0x01,
            0x01,
            0x00,
            0x18,
            0xDD,
            0x8D,
            0xB5,
            0x00,
            0x00,
            0x00,
            0x00,
            0x49,
            0x45,
            0x4E,
            0x44,  # IEND
            0xAE,
            0x42,
            0x60,
            0x82,
        ]
    )
    return base64.b64encode(png_data).decode("utf-8")


class TestMultimodalEndpoint:
    """Tests for /api/chat/multimodal endpoint."""

    def test_question_only_redirects_to_chat(self, client: TestClient) -> None:
        """Test that question-only request redirects to regular chat."""
        response = client.post(
            "/api/chat/multimodal",
            json={"question": "What is Waycore?"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        # Should have response text
        assert "response" in data or "results" in data

    def test_image_only_returns_classification(
        self, client: TestClient, sample_image_b64: str
    ) -> None:
        """Test that image-only request returns classification."""
        response = client.post(
            "/api/chat/multimodal",
            json={"image_b64": sample_image_b64},
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert data.get("mode") == "classification_only"
        # Should have response text
        assert "response" in data

    def test_multimodal_with_image_and_question(
        self, client: TestClient, sample_image_b64: str
    ) -> None:
        """Test multimodal with both image and question."""
        response = client.post(
            "/api/chat/multimodal",
            json={
                "question": "What is this?",
                "image_b64": sample_image_b64,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert data.get("mode") == "multimodal"
        # Should have vision context
        assert "vision_context" in data
        assert "response" in data

    def test_empty_request_returns_error(self, client: TestClient) -> None:
        """Test that empty request returns error."""
        response = client.post(
            "/api/chat/multimodal",
            json={},
        )

        assert response.status_code == 400
        data = response.json()
        assert "error" in data

    def test_multimodal_includes_safety_warning_context(
        self, client: TestClient, sample_image_b64: str
    ) -> None:
        """Test that safety-related questions get appropriate context."""
        response = client.post(
            "/api/chat/multimodal",
            json={
                "question": "Is this edible?",
                "image_b64": sample_image_b64,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        # Response should contain something (safety warnings in prompt)
        assert "response" in data

    def test_custom_model_id(self, client: TestClient, sample_image_b64: str) -> None:
        """Test using a custom model ID."""
        response = client.post(
            "/api/chat/multimodal",
            json={
                "question": "What is this?",
                "image_b64": sample_image_b64,
                "model_id": "phi3-mini",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
