"""Tests for tool generator."""

from __future__ import annotations

import pytest

from ..generator import ToolGenerator, get_dangerous_tools
from ..parser import APIEndpoint, APIParameter


@pytest.fixture
def sample_endpoints() -> list[APIEndpoint]:
    """Create sample endpoints for testing."""
    return [
        APIEndpoint(
            path="/api/items",
            method="GET",
            operation_id="list_items",
            summary="List all items",
            description="Returns a list of items",
            parameters=[],
            service_name="test-service",
            service_url="http://test-service:8000",
        ),
        APIEndpoint(
            path="/api/items/{item_id}",
            method="GET",
            operation_id="get_item",
            summary="Get item by ID",
            description="",
            parameters=[
                APIParameter(
                    name="item_id",
                    location="path",
                    required=True,
                    schema={"type": "string"},
                    description="The item ID",
                )
            ],
            service_name="test-service",
            service_url="http://test-service:8000",
        ),
        APIEndpoint(
            path="/api/items",
            method="POST",
            operation_id="create_item",
            summary="Create an item",
            description="",
            parameters=[],
            request_body_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Item name"},
                    "count": {"type": "integer"},
                },
                "required": ["name"],
            },
            request_body_required=True,
            service_name="test-service",
            service_url="http://test-service:8000",
        ),
        APIEndpoint(
            path="/api/items/{item_id}",
            method="DELETE",
            operation_id="delete_item",
            summary="Delete an item",
            description="",
            parameters=[
                APIParameter(
                    name="item_id",
                    location="path",
                    required=True,
                    schema={"type": "string"},
                )
            ],
            service_name="test-service",
            service_url="http://test-service:8000",
        ),
        APIEndpoint(
            path="/health",
            method="GET",
            operation_id="health_check",
            summary="Health check",
            description="",
            parameters=[],
            service_name="test-service",
            service_url="http://test-service:8000",
        ),
        APIEndpoint(
            path="/api/search",
            method="GET",
            operation_id="search_items",
            summary="Search items",
            description="",
            parameters=[
                APIParameter(
                    name="q",
                    location="query",
                    required=True,
                    schema={"type": "string"},
                    description="Search query",
                ),
                APIParameter(
                    name="limit",
                    location="query",
                    required=False,
                    schema={"type": "integer", "default": 10},
                ),
            ],
            service_name="test-service",
            service_url="http://test-service:8000",
        ),
    ]


class TestToolGenerator:
    """Tests for ToolGenerator."""

    def test_generate_tools_creates_tools(self, sample_endpoints: list[APIEndpoint]) -> None:
        """Test that tools are generated from endpoints."""
        generator = ToolGenerator()
        tools = generator.generate_tools(sample_endpoints)

        # Should exclude /health
        assert len(tools) == 5

    def test_generate_tools_excludes_health(self, sample_endpoints: list[APIEndpoint]) -> None:
        """Test that health endpoints are excluded."""
        generator = ToolGenerator()
        tools = generator.generate_tools(sample_endpoints)

        tool_names = {t.name for t in tools}
        assert "health_check" not in tool_names
        assert "test_service_health_check" not in tool_names

    def test_tool_name_includes_service_prefix(self, sample_endpoints: list[APIEndpoint]) -> None:
        """Test that tool names are prefixed with service name."""
        generator = ToolGenerator()
        tools = generator.generate_tools(sample_endpoints)

        for tool in tools:
            assert tool.name.startswith("test_service_")

    def test_tool_has_description(self, sample_endpoints: list[APIEndpoint]) -> None:
        """Test that tools have descriptions."""
        generator = ToolGenerator()
        tools = generator.generate_tools(sample_endpoints)

        for tool in tools:
            assert tool.description
            assert "[Service: test-service]" in tool.description

    def test_delete_tool_marked_dangerous(self, sample_endpoints: list[APIEndpoint]) -> None:
        """Test that DELETE tools are marked as dangerous."""
        generator = ToolGenerator()
        tools = generator.generate_tools(sample_endpoints)

        delete_tool = next(t for t in tools if "delete" in t.name)
        assert "⚠️" in delete_tool.description

    def test_input_schema_includes_path_params(self, sample_endpoints: list[APIEndpoint]) -> None:
        """Test that path parameters are in input schema."""
        generator = ToolGenerator()
        tools = generator.generate_tools(sample_endpoints)

        get_item = next(t for t in tools if "get_item" in t.name)
        schema = get_item.inputSchema

        assert "item_id" in schema["properties"]
        assert "item_id" in schema["required"]

    def test_input_schema_includes_query_params(self, sample_endpoints: list[APIEndpoint]) -> None:
        """Test that query parameters are in input schema."""
        generator = ToolGenerator()
        tools = generator.generate_tools(sample_endpoints)

        search_tool = next(t for t in tools if "search" in t.name)
        schema = search_tool.inputSchema

        assert "q" in schema["properties"]
        assert "limit" in schema["properties"]
        assert "q" in schema["required"]
        assert "limit" not in schema["required"]

    def test_input_schema_includes_body_properties(
        self, sample_endpoints: list[APIEndpoint]
    ) -> None:
        """Test that request body properties are in input schema."""
        generator = ToolGenerator()
        tools = generator.generate_tools(sample_endpoints)

        create_tool = next(t for t in tools if "create" in t.name)
        schema = create_tool.inputSchema

        assert "name" in schema["properties"]
        assert "count" in schema["properties"]
        assert "name" in schema["required"]

    def test_custom_exclude_patterns(self, sample_endpoints: list[APIEndpoint]) -> None:
        """Test that custom exclude patterns work."""
        generator = ToolGenerator(exclude_patterns=[r"/api/search"])
        tools = generator.generate_tools(sample_endpoints)

        tool_names = {t.name for t in tools}
        assert "test_service_search_items" not in tool_names


class TestGetDangerousTools:
    """Tests for get_dangerous_tools function."""

    def test_identifies_delete_operations(self, sample_endpoints: list[APIEndpoint]) -> None:
        """Test that DELETE operations are identified as dangerous."""
        dangerous = get_dangerous_tools(sample_endpoints)

        assert any("delete" in name for name in dangerous)

    def test_identifies_factory_reset(self) -> None:
        """Test that factory_reset is identified as dangerous."""
        endpoints = [
            APIEndpoint(
                path="/api/factory-reset",
                method="POST",
                operation_id="factory_reset",
                summary="Reset device",
                description="",
                parameters=[],
                service_name="core-daemon",
                service_url="http://core-daemon:8001",
            )
        ]

        dangerous = get_dangerous_tools(endpoints)
        assert any("factory_reset" in name for name in dangerous)
