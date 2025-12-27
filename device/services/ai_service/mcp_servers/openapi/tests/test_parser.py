"""Tests for OpenAPI parser."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from ..parser import OpenAPIParser


@pytest.fixture
def sample_openapi_spec() -> dict:
    """Create a sample OpenAPI spec for testing."""
    return {
        "openapi": "3.1.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "servers": [
            {"url": "http://localhost:8001", "description": "Local"},
            {"url": "http://test-service:8001", "description": "Docker network"},
        ],
        "paths": {
            "/api/items": {
                "get": {
                    "operationId": "list_items",
                    "summary": "List all items",
                    "description": "Returns a list of items",
                    "responses": {"200": {"description": "Success"}},
                },
                "post": {
                    "operationId": "create_item",
                    "summary": "Create an item",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {
                                            "type": "string",
                                            "description": "Item name",
                                        },
                                        "count": {"type": "integer"},
                                    },
                                    "required": ["name"],
                                }
                            }
                        },
                    },
                    "responses": {"201": {"description": "Created"}},
                },
            },
            "/api/items/{item_id}": {
                "get": {
                    "operationId": "get_item",
                    "summary": "Get item by ID",
                    "parameters": [
                        {
                            "name": "item_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "The item ID",
                        }
                    ],
                    "responses": {"200": {"description": "Success"}},
                },
                "delete": {
                    "operationId": "delete_item",
                    "summary": "Delete an item",
                    "parameters": [
                        {
                            "name": "item_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {"204": {"description": "Deleted"}},
                },
            },
            "/api/search": {
                "get": {
                    "operationId": "search_items",
                    "summary": "Search items",
                    "parameters": [
                        {
                            "name": "q",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Search query",
                        },
                        {
                            "name": "limit",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "integer", "default": 10},
                        },
                    ],
                    "responses": {"200": {"description": "Success"}},
                },
            },
            "/health": {
                "get": {
                    "operationId": "health_check",
                    "summary": "Health check",
                    "responses": {"200": {"description": "OK"}},
                },
            },
        },
    }


@pytest.fixture
def spec_dir(sample_openapi_spec: dict) -> Path:
    """Create a temporary directory with a spec file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        spec_path = Path(tmpdir) / "test-service.openapi.json"
        with open(spec_path, "w") as f:
            json.dump(sample_openapi_spec, f)
        yield Path(tmpdir)


class TestOpenAPIParser:
    """Tests for OpenAPIParser."""

    def test_parse_all_finds_specs(self, spec_dir: Path) -> None:
        """Test that parse_all finds and parses spec files."""
        parser = OpenAPIParser(spec_dir)
        endpoints = parser.parse_all()

        # Should find 6 endpoints (2 in /api/items, 2 in /api/items/{id}, 1 search, 1 health)
        assert len(endpoints) == 6

    def test_parse_spec_extracts_endpoints(self, spec_dir: Path) -> None:
        """Test that individual spec parsing works."""
        parser = OpenAPIParser(spec_dir)
        spec_path = spec_dir / "test-service.openapi.json"
        endpoints = parser.parse_spec(spec_path)

        # Check endpoint details
        operation_ids = {e.operation_id for e in endpoints}
        assert "list_items" in operation_ids
        assert "create_item" in operation_ids
        assert "get_item" in operation_ids
        assert "delete_item" in operation_ids
        assert "search_items" in operation_ids

    def test_parse_spec_extracts_parameters(self, spec_dir: Path) -> None:
        """Test that parameters are correctly extracted."""
        parser = OpenAPIParser(spec_dir)
        spec_path = spec_dir / "test-service.openapi.json"
        endpoints = parser.parse_spec(spec_path)

        # Find the get_item endpoint
        get_item = next(e for e in endpoints if e.operation_id == "get_item")
        assert len(get_item.parameters) == 1
        assert get_item.parameters[0].name == "item_id"
        assert get_item.parameters[0].location == "path"
        assert get_item.parameters[0].required is True

    def test_parse_spec_extracts_request_body(self, spec_dir: Path) -> None:
        """Test that request body schema is extracted."""
        parser = OpenAPIParser(spec_dir)
        spec_path = spec_dir / "test-service.openapi.json"
        endpoints = parser.parse_spec(spec_path)

        # Find the create_item endpoint
        create_item = next(e for e in endpoints if e.operation_id == "create_item")
        assert create_item.request_body_schema is not None
        assert create_item.request_body_required is True
        assert "name" in create_item.request_body_schema.get("properties", {})

    def test_parse_spec_assigns_service_info(self, spec_dir: Path) -> None:
        """Test that service name and URL are assigned."""
        parser = OpenAPIParser(spec_dir)
        spec_path = spec_dir / "test-service.openapi.json"
        endpoints = parser.parse_spec(spec_path)

        for endpoint in endpoints:
            assert endpoint.service_name == "test-service"
            # Should prefer Docker network URL
            assert "test-service:8001" in endpoint.service_url

    def test_excluded_specs_are_skipped(self, spec_dir: Path) -> None:
        """Test that excluded specs are not parsed."""
        # Create an excluded spec
        excluded_path = spec_dir / "ai-service.openapi.json"
        with open(excluded_path, "w") as f:
            json.dump(
                {
                    "openapi": "3.1.0",
                    "info": {"title": "AI", "version": "1.0.0"},
                    "paths": {"/api/test": {"get": {"operationId": "ai_test"}}},
                },
                f,
            )

        parser = OpenAPIParser(spec_dir)
        endpoints = parser.parse_all()

        # Should not include ai_test
        operation_ids = {e.operation_id for e in endpoints}
        assert "ai_test" not in operation_ids

    def test_missing_directory_returns_empty(self) -> None:
        """Test that missing spec directory returns empty list."""
        parser = OpenAPIParser("/nonexistent/path")
        endpoints = parser.parse_all()
        assert endpoints == []

    def test_service_url_fallback(self, spec_dir: Path) -> None:
        """Test service URL fallback for unknown services."""
        # Create a spec without servers section
        spec_path = spec_dir / "unknown-service.openapi.json"
        with open(spec_path, "w") as f:
            json.dump(
                {
                    "openapi": "3.1.0",
                    "info": {"title": "Unknown", "version": "1.0.0"},
                    "paths": {"/api/test": {"get": {"operationId": "test"}}},
                },
                f,
            )

        parser = OpenAPIParser(spec_dir)
        spec_endpoints = parser.parse_spec(spec_path)

        assert len(spec_endpoints) == 1
        # Should use generic fallback
        assert "unknown-service" in spec_endpoints[0].service_url
