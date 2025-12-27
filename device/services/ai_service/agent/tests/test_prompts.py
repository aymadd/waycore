"""Tests for agent prompts."""

from __future__ import annotations

from device.services.ai_service.agent.prompts import (
    format_tool_list,
    format_tool_result,
    get_confirmation_prompt,
    get_tool_system_prompt,
)


class TestFormatToolList:
    """Tests for format_tool_list function."""

    def test_empty_tools(self) -> None:
        """Test formatting empty tool list."""
        result = format_tool_list([])
        assert result == "No tools available."

    def test_single_tool(self) -> None:
        """Test formatting single tool."""
        tools = [
            {
                "name": "get_temperature",
                "description": "Get current temperature",
                "parameters": {"properties": {"unit": {"type": "string"}}},
            }
        ]
        result = format_tool_list(tools)
        assert "get_temperature" in result
        assert "Get current temperature" in result
        assert "unit" in result

    def test_multiple_tools(self) -> None:
        """Test formatting multiple tools."""
        tools = [
            {
                "name": "tool_one",
                "description": "First tool",
                "parameters": {"properties": {}},
            },
            {
                "name": "tool_two",
                "description": "Second tool",
                "parameters": {"properties": {"arg1": {}}},
            },
        ]
        result = format_tool_list(tools)
        assert "tool_one" in result
        assert "tool_two" in result
        assert "First tool" in result
        assert "Second tool" in result


class TestGetToolSystemPrompt:
    """Tests for get_tool_system_prompt function."""

    def test_includes_instructions(self) -> None:
        """Test that prompt includes tool usage instructions."""
        prompt = get_tool_system_prompt([])
        assert "tools" in prompt.lower()
        assert "json" in prompt.lower()

    def test_includes_tool_list(self) -> None:
        """Test that prompt includes tool definitions."""
        tools = [
            {
                "name": "get_gps",
                "description": "Get GPS location",
                "parameters": {"properties": {}},
            }
        ]
        prompt = get_tool_system_prompt(tools)
        assert "get_gps" in prompt
        assert "GPS location" in prompt


class TestFormatToolResult:
    """Tests for format_tool_result function."""

    def test_successful_result(self) -> None:
        """Test formatting successful tool result."""
        result = format_tool_result("get_temp", "23.5°C")
        assert "get_temp" in result
        assert "23.5°C" in result
        assert "Error" not in result

    def test_error_result(self) -> None:
        """Test formatting tool error."""
        result = format_tool_result("get_temp", None, error="Sensor offline")
        assert "get_temp" in result
        assert "Error" in result
        assert "Sensor offline" in result

    def test_list_result(self) -> None:
        """Test formatting list result (MCP style)."""

        class MockContent:
            def __init__(self, text: str):
                self.text = text

        result = format_tool_result(
            "get_all",
            [MockContent("Line 1"), MockContent("Line 2")],
        )
        assert "Line 1" in result
        assert "Line 2" in result


class TestGetConfirmationPrompt:
    """Tests for get_confirmation_prompt function."""

    def test_basic_prompt(self) -> None:
        """Test basic confirmation prompt."""
        prompt = get_confirmation_prompt(
            "send_message",
            {"channel": "all", "text": "Hello"},
        )
        assert "send_message" in prompt
        assert "channel" in prompt
        assert "all" in prompt

    def test_with_warning(self) -> None:
        """Test confirmation prompt with warning."""
        prompt = get_confirmation_prompt(
            "factory_reset",
            {"confirm": True},
            warning="This will delete all data!",
        )
        assert "factory_reset" in prompt
        assert "delete all data" in prompt
