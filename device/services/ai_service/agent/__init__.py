"""Agent module for agentic AI capabilities.

This module provides the agent controller that orchestrates
tool calling and response generation for the AI service.
"""

from __future__ import annotations

from .controller import AgentController, AgentResponse, ToolCall, ToolResult
from .prompts import get_tool_system_prompt

__all__ = [
    "AgentController",
    "AgentResponse",
    "ToolCall",
    "ToolResult",
    "get_tool_system_prompt",
]
