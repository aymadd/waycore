"""Agent controller for orchestrating tool-using AI conversations."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .prompts import format_tool_result, get_tool_system_prompt

if TYPE_CHECKING:
    from device.services.ai_service.mcp.manager import MCPManager

logger = logging.getLogger(__name__)


@dataclass
class ToolCall:
    """Represents a tool call request from the LLM."""

    name: str
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolResult:
    """Result from executing a tool."""

    tool: str
    success: bool
    result: Any | None = None
    error: str | None = None


@dataclass
class AgentResponse:
    """Response from the agent.

    Attributes:
        content: Text content of the response.
        tool_calls: Tools that were executed in this step.
        requires_confirmation: Tools that need user confirmation before execution.
        is_final: Whether this is the final response.
    """

    content: str
    tool_calls: list[ToolCall] | None = None
    requires_confirmation: list[ToolCall] | None = None
    is_final: bool = False


class AgentController:
    """Controls the agentic AI loop using MCP tools.

    The agent controller manages the conversation flow, deciding when to
    use tools and incorporating tool results into the response.
    """

    MAX_ITERATIONS = 5  # Prevent infinite loops

    def __init__(
        self,
        mcp_manager: MCPManager,
        llm_generate: Any = None,
    ) -> None:
        """Initialize the agent controller.

        Args:
            mcp_manager: MCP manager for tool access.
            llm_generate: Function to generate LLM responses (optional).
        """
        self.mcp = mcp_manager
        self.llm_generate = llm_generate
        self._pending_confirmations: dict[str, ToolCall] = {}

    def get_tool_system_prompt(self) -> str:
        """Get the system prompt section describing available tools.

        Returns:
            System prompt string with tool descriptions.
        """
        tools = self.mcp.get_tools_for_llm()
        return get_tool_system_prompt(tools)

    async def process_message(
        self,
        user_message: str,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> AsyncIterator[AgentResponse]:
        """Process a user message, potentially using tools.

        This is an async generator that yields AgentResponse objects as the
        agent works through the query. This allows for streaming updates
        and handling confirmation requests.

        Args:
            user_message: The user's message/query.
            conversation_history: Previous conversation messages.

        Yields:
            AgentResponse objects with content and/or tool information.
        """
        messages = list(conversation_history or [])
        messages.append({"role": "user", "content": user_message})

        for iteration in range(self.MAX_ITERATIONS):
            logger.debug(f"Agent iteration {iteration + 1}/{self.MAX_ITERATIONS}")

            # Check if we should try to extract tool calls from the user message
            # In a real implementation, this would use the LLM to decide
            tool_calls = self._extract_tool_calls_from_text(user_message)

            if not tool_calls:
                # No tools detected, this is a direct response
                yield AgentResponse(
                    content="",  # LLM would generate this
                    is_final=True,
                )
                return

            # Check for tools requiring confirmation
            needs_confirmation = [
                tc for tc in tool_calls if self.mcp.requires_confirmation(tc.name)
            ]
            auto_execute = [tc for tc in tool_calls if not self.mcp.requires_confirmation(tc.name)]

            # Handle confirmation-required tools
            if needs_confirmation:
                yield AgentResponse(
                    content="I need your permission to proceed with the following action(s).",
                    requires_confirmation=needs_confirmation,
                )
                # Store pending confirmations
                for tc in needs_confirmation:
                    self._pending_confirmations[tc.name] = tc
                return  # Wait for user confirmation

            # Execute tools that don't need confirmation
            if auto_execute:
                tool_results = await self._execute_tools(auto_execute)

                # Format results for context
                result_text = "\n\n".join(
                    format_tool_result(r.tool, r.result, r.error) for r in tool_results
                )

                yield AgentResponse(
                    content=result_text,
                    tool_calls=auto_execute,
                    is_final=True,
                )
                return

        # Max iterations reached
        yield AgentResponse(
            content="I was unable to complete this request. Please try a simpler question.",
            is_final=True,
        )

    async def confirm_tool(self, tool_name: str) -> ToolResult:
        """Execute a previously pending tool after user confirmation.

        Args:
            tool_name: Name of the tool to confirm and execute.

        Returns:
            ToolResult from the execution.
        """
        if tool_name not in self._pending_confirmations:
            return ToolResult(
                tool=tool_name,
                success=False,
                error="No pending confirmation for this tool",
            )

        tool_call = self._pending_confirmations.pop(tool_name)
        results = await self._execute_tools([tool_call])
        return (
            results[0]
            if results
            else ToolResult(
                tool=tool_name,
                success=False,
                error="Execution failed",
            )
        )

    def cancel_tool(self, tool_name: str) -> bool:
        """Cancel a pending tool confirmation.

        Args:
            tool_name: Name of the tool to cancel.

        Returns:
            True if tool was cancelled, False if not found.
        """
        return self._pending_confirmations.pop(tool_name, None) is not None

    def get_pending_confirmations(self) -> list[ToolCall]:
        """Get list of tools waiting for confirmation.

        Returns:
            List of pending ToolCall objects.
        """
        return list(self._pending_confirmations.values())

    async def execute_tool_directly(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
    ) -> ToolResult:
        """Execute a tool directly without going through the agent loop.

        Args:
            tool_name: Name of the tool to execute.
            arguments: Tool arguments.

        Returns:
            ToolResult from the execution.
        """
        tool_call = ToolCall(name=tool_name, arguments=arguments or {})
        results = await self._execute_tools([tool_call])
        return (
            results[0]
            if results
            else ToolResult(
                tool=tool_name,
                success=False,
                error="Execution failed",
            )
        )

    async def _execute_tools(self, tool_calls: list[ToolCall]) -> list[ToolResult]:
        """Execute a list of tool calls via MCP.

        Args:
            tool_calls: List of ToolCall objects.

        Returns:
            List of ToolResult objects.
        """
        results = []
        for call in tool_calls:
            try:
                result = await self.mcp.call_tool(call.name, call.arguments)
                results.append(
                    ToolResult(
                        tool=call.name,
                        success=True,
                        result=result.content if hasattr(result, "content") else result,
                    )
                )
                logger.info(f"Tool {call.name} executed successfully")
            except TimeoutError as e:
                logger.warning(f"Tool {call.name} timed out")
                results.append(
                    ToolResult(
                        tool=call.name,
                        success=False,
                        error=str(e),
                    )
                )
            except ValueError as e:
                logger.warning(f"Tool {call.name} error: {e}")
                results.append(
                    ToolResult(
                        tool=call.name,
                        success=False,
                        error=str(e),
                    )
                )
            except Exception as e:
                logger.error(f"Tool {call.name} failed: {e}")
                results.append(
                    ToolResult(
                        tool=call.name,
                        success=False,
                        error=str(e),
                    )
                )
        return results

    def _extract_tool_calls_from_text(self, text: str) -> list[ToolCall]:
        """Extract tool calls from text (JSON format).

        This looks for JSON objects with "tool" and "arguments" keys
        in the text, which is the format we instruct the LLM to use.

        Args:
            text: Text that may contain tool calls.

        Returns:
            List of extracted ToolCall objects.
        """
        tool_calls = []

        # Look for JSON tool call pattern with nested braces
        # Pattern: {"tool": "name", "arguments": {...}}
        # Use a simple approach: find all { and try to parse as JSON
        start_idx = 0
        while True:
            # Find next opening brace
            brace_pos = text.find("{", start_idx)
            if brace_pos == -1:
                break

            # Try to find matching closing brace by counting
            depth = 0
            end_pos = brace_pos
            for i, char in enumerate(text[brace_pos:], brace_pos):
                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        end_pos = i + 1
                        break

            if end_pos > brace_pos:
                candidate = text[brace_pos:end_pos]
                try:
                    data = json.loads(candidate)
                    if isinstance(data, dict) and "tool" in data:
                        tool_calls.append(
                            ToolCall(
                                name=data["tool"],
                                arguments=data.get("arguments", {}),
                            )
                        )
                except json.JSONDecodeError:
                    pass

            start_idx = brace_pos + 1

        return tool_calls
