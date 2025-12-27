"""Tests for agent controller."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from device.services.ai_service.agent.controller import (
    AgentController,
    AgentResponse,
    ToolCall,
    ToolResult,
)


class TestToolCall:
    """Tests for ToolCall dataclass."""

    def test_basic_tool_call(self) -> None:
        """Test basic tool call creation."""
        tc = ToolCall(name="get_temp", arguments={"unit": "celsius"})
        assert tc.name == "get_temp"
        assert tc.arguments == {"unit": "celsius"}

    def test_empty_arguments(self) -> None:
        """Test tool call with empty arguments."""
        tc = ToolCall(name="get_all")
        assert tc.name == "get_all"
        assert tc.arguments == {}


class TestToolResult:
    """Tests for ToolResult dataclass."""

    def test_successful_result(self) -> None:
        """Test successful tool result."""
        tr = ToolResult(tool="get_temp", success=True, result="23.5°C")
        assert tr.tool == "get_temp"
        assert tr.success is True
        assert tr.result == "23.5°C"
        assert tr.error is None

    def test_error_result(self) -> None:
        """Test error tool result."""
        tr = ToolResult(tool="get_temp", success=False, error="Sensor offline")
        assert tr.success is False
        assert tr.error == "Sensor offline"


class TestAgentResponse:
    """Tests for AgentResponse dataclass."""

    def test_simple_response(self) -> None:
        """Test simple text response."""
        ar = AgentResponse(content="Hello!", is_final=True)
        assert ar.content == "Hello!"
        assert ar.is_final is True
        assert ar.tool_calls is None
        assert ar.requires_confirmation is None

    def test_with_tool_calls(self) -> None:
        """Test response with tool calls."""
        tc = ToolCall(name="get_temp")
        ar = AgentResponse(content="Getting temp...", tool_calls=[tc])
        assert len(ar.tool_calls or []) == 1
        assert ar.tool_calls[0].name == "get_temp"

    def test_with_confirmation_required(self) -> None:
        """Test response requiring confirmation."""
        tc = ToolCall(name="send_message", arguments={"text": "Hi"})
        ar = AgentResponse(
            content="I need permission",
            requires_confirmation=[tc],
        )
        assert len(ar.requires_confirmation or []) == 1


class TestAgentController:
    """Tests for AgentController."""

    @pytest.fixture
    def mock_mcp(self) -> MagicMock:
        """Create a mock MCP manager."""
        mcp = MagicMock()
        mcp.list_tools.return_value = []
        mcp.get_tools_for_llm.return_value = []
        mcp.requires_confirmation.return_value = False
        mcp.call_tool = AsyncMock(return_value=MagicMock(content="result"))
        return mcp

    def test_init(self, mock_mcp: MagicMock) -> None:
        """Test controller initialization."""
        controller = AgentController(mcp_manager=mock_mcp)
        assert controller.mcp is mock_mcp
        assert controller._pending_confirmations == {}

    def test_get_tool_system_prompt(self, mock_mcp: MagicMock) -> None:
        """Test getting tool system prompt."""
        mock_mcp.get_tools_for_llm.return_value = [
            {"name": "test_tool", "description": "A test", "parameters": {}}
        ]
        controller = AgentController(mcp_manager=mock_mcp)
        prompt = controller.get_tool_system_prompt()
        assert "test_tool" in prompt

    def test_pending_confirmations_empty(self, mock_mcp: MagicMock) -> None:
        """Test getting empty pending confirmations."""
        controller = AgentController(mcp_manager=mock_mcp)
        pending = controller.get_pending_confirmations()
        assert pending == []

    def test_cancel_nonexistent_tool(self, mock_mcp: MagicMock) -> None:
        """Test cancelling a tool that doesn't exist."""
        controller = AgentController(mcp_manager=mock_mcp)
        result = controller.cancel_tool("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_execute_tool_directly(self, mock_mcp: MagicMock) -> None:
        """Test direct tool execution."""
        controller = AgentController(mcp_manager=mock_mcp)
        result = await controller.execute_tool_directly("get_temp", {"unit": "celsius"})

        assert result.tool == "get_temp"
        assert result.success is True
        mock_mcp.call_tool.assert_called_once_with("get_temp", {"unit": "celsius"})

    @pytest.mark.asyncio
    async def test_execute_tool_timeout(self, mock_mcp: MagicMock) -> None:
        """Test tool execution with timeout."""
        mock_mcp.call_tool = AsyncMock(side_effect=TimeoutError("Timed out"))
        controller = AgentController(mcp_manager=mock_mcp)
        result = await controller.execute_tool_directly("slow_tool")

        assert result.success is False
        assert "Timed out" in (result.error or "")

    @pytest.mark.asyncio
    async def test_confirm_nonexistent_tool(self, mock_mcp: MagicMock) -> None:
        """Test confirming a tool that wasn't pending."""
        controller = AgentController(mcp_manager=mock_mcp)
        result = await controller.confirm_tool("nonexistent")

        assert result.success is False
        assert "No pending" in (result.error or "")

    def test_extract_tool_calls_from_json(self, mock_mcp: MagicMock) -> None:
        """Test extracting tool calls from JSON in text."""
        controller = AgentController(mcp_manager=mock_mcp)
        text = 'Let me check: {"tool": "get_temp", "arguments": {"unit": "celsius"}}'
        calls = controller._extract_tool_calls_from_text(text)

        assert len(calls) == 1
        assert calls[0].name == "get_temp"
        assert calls[0].arguments == {"unit": "celsius"}

    def test_extract_no_tool_calls(self, mock_mcp: MagicMock) -> None:
        """Test extracting from text with no tool calls."""
        controller = AgentController(mcp_manager=mock_mcp)
        text = "Just a regular message without any tools."
        calls = controller._extract_tool_calls_from_text(text)

        assert calls == []
