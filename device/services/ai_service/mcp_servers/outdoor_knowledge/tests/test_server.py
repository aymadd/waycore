"""Tests for outdoor knowledge MCP server."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from device.services.ai_service.mcp_servers.outdoor_knowledge.formatters import (
    format_first_aid_results,
    format_plant_results,
    format_search_results,
)
from device.services.ai_service.rag import Category, KnowledgeEntry, SafetyLevel


class TestFormatters:
    """Tests for response formatters."""

    def test_format_search_results_basic(self) -> None:
        """Test basic search result formatting."""
        results = [
            {
                "title": "Fire Starting",
                "category": "survival",
                "content": "Learn how to start a fire.",
                "safety_level": "caution",
                "source_file": "FM21-76.pdf",
                "source_page": 42,
            }
        ]

        formatted = format_search_results(results)

        assert "Fire Starting" in formatted
        assert "survival" in formatted
        assert "fire" in formatted.lower()
        assert "CAUTION" in formatted
        assert "FM21-76.pdf" in formatted
        assert "p.42" in formatted

    def test_format_search_results_multiple(self) -> None:
        """Test formatting multiple search results."""
        results = [
            {"title": "Result 1", "category": "survival", "content": "Content 1"},
            {"title": "Result 2", "category": "navigation", "content": "Content 2"},
        ]

        formatted = format_search_results(results)

        assert "Result 1" in formatted
        assert "Result 2" in formatted
        assert "Found 2" in formatted

    def test_format_plant_results_with_safety(self) -> None:
        """Test plant formatting includes safety warnings."""
        results = [
            {
                "title": "Dandelion",
                "subcategory": "Asteraceae",
                "content": "Common edible plant with yellow flowers.",
                "safety_level": "caution",
                "safety_notes": "Verify identification.",
                "source_url": "https://pfaf.org/",
            }
        ]

        formatted = format_plant_results(results)

        assert "Dandelion" in formatted
        assert "Asteraceae" in formatted
        assert "CAUTION" in formatted
        assert "CRITICAL WARNING" in formatted
        assert "DEADLY look-alikes" in formatted
        assert "NEVER consume" in formatted

    def test_format_plant_results_empty(self) -> None:
        """Test formatting empty plant results."""
        formatted = format_plant_results([])
        assert "No plant information found" in formatted

    def test_format_first_aid_results(self) -> None:
        """Test first aid formatting includes disclaimer."""
        results = [
            {
                "title": "Snake Bite Treatment",
                "content": "Keep the victim calm and immobilize the limb.",
                "source_file": "FM4-25.11.pdf",
                "source_page": 123,
            }
        ]

        formatted = format_first_aid_results(results)

        assert "Snake Bite" in formatted
        assert "calm" in formatted
        assert "MEDICAL DISCLAIMER" in formatted
        assert "EDUCATIONAL" in formatted
        assert "professional medical care" in formatted
        assert "FM4-25.11.pdf" in formatted

    def test_safety_icons(self) -> None:
        """Test that safety icons are correct."""
        from device.services.ai_service.mcp_servers.outdoor_knowledge.formatters import (
            SAFETY_ICONS,
        )

        assert SAFETY_ICONS["safe"] == "✅"
        assert SAFETY_ICONS["caution"] == "⚠️"
        assert SAFETY_ICONS["danger"] == "🚫"
        assert SAFETY_ICONS["lethal"] == "☠️"


class TestServerTools:
    """Tests for MCP server tool handlers."""

    @pytest.fixture
    def temp_dir(self) -> Path:
        """Create temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def sample_entries(self) -> list[KnowledgeEntry]:
        """Create sample entries."""
        return [
            KnowledgeEntry(
                id="fire_1",
                title="Fire Starting Basics",
                content="Learn how to start a fire using friction methods.",
                category=Category.SURVIVAL,
                safety_level=SafetyLevel.CAUTION,
            ),
            KnowledgeEntry(
                id="plant_1",
                title="Dandelion",
                content="Common edible plant with yellow flowers.",
                category=Category.PLANTS,
                safety_level=SafetyLevel.DANGER,
            ),
        ]

    @pytest.mark.asyncio
    async def test_list_tools(self) -> None:
        """Test that list_tools returns expected tools."""
        from device.services.ai_service.mcp_servers.outdoor_knowledge.server import (
            list_tools,
        )

        tools = await list_tools()

        tool_names = [t.name for t in tools]
        assert "search_survival_knowledge" in tool_names
        assert "identify_plant" in tool_names
        assert "get_first_aid" in tool_names
        assert "lookup_knot" in tool_names
        assert "get_weather_signs" in tool_names

    @pytest.mark.asyncio
    async def test_call_tool_unknown(self) -> None:
        """Test calling unknown tool."""
        from device.services.ai_service.mcp_servers.outdoor_knowledge.server import (
            call_tool,
        )

        result = await call_tool("unknown_tool", {})

        assert len(result) == 1
        assert "Unknown tool" in result[0].text

    @pytest.mark.asyncio
    async def test_search_empty_query(self) -> None:
        """Test search with empty query."""
        from device.services.ai_service.mcp_servers.outdoor_knowledge.server import (
            call_tool,
        )

        result = await call_tool("search_survival_knowledge", {"query": ""})

        assert len(result) == 1
        assert "provide a search query" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_plant_id_empty_name(self) -> None:
        """Test plant identification with empty name."""
        from device.services.ai_service.mcp_servers.outdoor_knowledge.server import (
            call_tool,
        )

        result = await call_tool("identify_plant", {"plant_name": ""})

        assert len(result) == 1
        assert "provide a plant name" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_first_aid_empty_condition(self) -> None:
        """Test first aid with empty condition."""
        from device.services.ai_service.mcp_servers.outdoor_knowledge.server import (
            call_tool,
        )

        result = await call_tool("get_first_aid", {"condition": ""})

        assert len(result) == 1
        assert "describe the condition" in result[0].text.lower()
