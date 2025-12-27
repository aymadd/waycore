"""Tests for OpenAPI MCP server."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from ..generator import ToolGenerator
from ..parser import OpenAPIParser


@pytest.fixture
def sample_spec() -> dict:
    """Create a sample OpenAPI spec."""
    return {
        "openapi": "3.1.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "servers": [{"url": "http://test-service:8000"}],
        "paths": {
            "/api/items": {
                "get": {
                    "operationId": "list_items",
                    "summary": "List items",
                    "responses": {"200": {"description": "OK"}},
                }
            },
            "/api/items/{id}": {
                "get": {
                    "operationId": "get_item",
                    "summary": "Get item",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {"200": {"description": "OK"}},
                }
            },
        },
    }


@pytest.fixture
def spec_dir(sample_spec: dict) -> Path:
    """Create temp directory with spec file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        spec_path = Path(tmpdir) / "test-service.openapi.json"
        with open(spec_path, "w") as f:
            json.dump(sample_spec, f)
        yield Path(tmpdir)


class TestOpenAPIServer:
    """Tests for the OpenAPI MCP server components.

    Note: We test the parser and generator directly rather than the server
    module itself since the server uses global state that's harder to mock.
    """

    def test_parser_loads_specs(self, spec_dir: Path) -> None:
        """Test that parser loads OpenAPI specs from directory."""
        parser = OpenAPIParser(spec_dir)
        endpoints = parser.parse_all()

        # Should find 2 endpoints (list_items and get_item)
        assert len(endpoints) == 2

    def test_generator_creates_tools_from_endpoints(self, spec_dir: Path) -> None:
        """Test that generator creates tools from parsed endpoints."""
        parser = OpenAPIParser(spec_dir)
        endpoints = parser.parse_all()

        generator = ToolGenerator()
        tools = generator.generate_tools(endpoints)

        assert len(tools) == 2
        tool_names = {t.name for t in tools}
        assert "test_service_list_items" in tool_names
        assert "test_service_get_item" in tool_names

    def test_tool_has_correct_schema(self, spec_dir: Path) -> None:
        """Test that generated tools have correct input schemas."""
        parser = OpenAPIParser(spec_dir)
        endpoints = parser.parse_all()

        generator = ToolGenerator()
        tools = generator.generate_tools(endpoints)

        # Find get_item tool
        get_item = next(t for t in tools if "get_item" in t.name)

        assert get_item.inputSchema is not None
        assert "id" in get_item.inputSchema.get("properties", {})
        assert "id" in get_item.inputSchema.get("required", [])

    @pytest.mark.asyncio
    async def test_call_tool_unknown_returns_error(self, spec_dir: Path) -> None:
        """Test that calling unknown tool returns error."""
        # Import the server functions
        from ..server import _endpoints, _tools, call_tool

        # Clear and rebuild tools using our spec
        parser = OpenAPIParser(spec_dir)
        generator = ToolGenerator()
        endpoints = parser.parse_all()

        # Manually populate the server's state
        _endpoints.clear()
        for ep in endpoints:
            tool_name = generator._generate_tool_name(ep)
            _endpoints[tool_name] = ep
        _tools.clear()
        _tools.extend(generator.generate_tools(endpoints))

        # Call with unknown tool
        result = await call_tool("unknown_tool", {})

        assert len(result) == 1
        assert "Unknown tool" in result[0].text

    @pytest.mark.asyncio
    async def test_call_tool_executes_request(self, spec_dir: Path) -> None:
        """Test that calling a tool executes the API request."""
        from .. import server
        from ..server import _endpoints, _tools, call_tool

        # Set up state
        parser = OpenAPIParser(spec_dir)
        generator = ToolGenerator()
        endpoints = parser.parse_all()

        _endpoints.clear()
        for ep in endpoints:
            tool_name = generator._generate_tool_name(ep)
            _endpoints[tool_name] = ep
        _tools.clear()
        _tools.extend(generator.generate_tools(endpoints))

        # Mock the APIExecutor class in the server module
        mock_executor_instance = AsyncMock()
        mock_executor_instance.execute.return_value = {"items": [{"id": "1"}]}

        with patch.object(server, "APIExecutor", return_value=mock_executor_instance):
            result = await call_tool("test_service_list_items", {})

            assert len(result) == 1
            assert "items" in result[0].text

    @pytest.mark.asyncio
    async def test_call_tool_handles_error(self, spec_dir: Path) -> None:
        """Test that tool errors are handled gracefully."""
        from .. import server
        from ..server import _endpoints, _tools, call_tool

        # Set up state
        parser = OpenAPIParser(spec_dir)
        generator = ToolGenerator()
        endpoints = parser.parse_all()

        _endpoints.clear()
        for ep in endpoints:
            tool_name = generator._generate_tool_name(ep)
            _endpoints[tool_name] = ep
        _tools.clear()
        _tools.extend(generator.generate_tools(endpoints))

        mock_executor_instance = AsyncMock()
        mock_executor_instance.execute.return_value = {
            "error": "Connection failed",
            "details": "Service unavailable",
        }

        with patch.object(server, "APIExecutor", return_value=mock_executor_instance):
            result = await call_tool("test_service_list_items", {})

            assert len(result) == 1
            assert "Error" in result[0].text
            assert "Connection failed" in result[0].text
