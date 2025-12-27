"""Agent controller for orchestrating tool-using AI conversations."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .prompts import format_tool_result, get_tool_system_prompt

if TYPE_CHECKING:
    from device.services.ai_service.mcp.manager import MCPManager

logger = logging.getLogger(__name__)

# Type alias for LLM generation function
LLMGenerateFunc = Callable[[str, str, list[dict[str, str]] | None], str]
LLMFinalResponseFunc = Callable[[str, str, list[dict[str, str]] | None], str]


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
        llm_generate: LLMGenerateFunc | None = None,
        llm_final_response: LLMFinalResponseFunc | None = None,
    ) -> None:
        """Initialize the agent controller.

        Args:
            mcp_manager: MCP manager for tool access.
            llm_generate: Function to generate LLM responses with tool awareness.
            llm_final_response: Function to generate final response after tools.
        """
        self.mcp = mcp_manager
        self.llm_generate = llm_generate
        self.llm_final_response = llm_final_response
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

        This uses a hybrid approach:
        1. First, detect if any tools should be called based on keywords
        2. Execute detected tools
        3. Use LLM to format final response with tool results

        Args:
            user_message: The user's message/query.
            conversation_history: Previous conversation messages.

        Yields:
            AgentResponse objects with content and/or tool information.
        """
        messages = list(conversation_history or [])
        user_lower = user_message.lower()

        # Hybrid approach: First try keyword-based tool detection
        tool_calls = self._detect_tools_from_keywords(user_lower)

        if tool_calls:
            logger.info(f"Detected tools from keywords: {[tc.name for tc in tool_calls]}")

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
                for tc in needs_confirmation:
                    self._pending_confirmations[tc.name] = tc
                return

            # Execute tools
            if auto_execute:
                tool_results = await self._execute_tools(auto_execute)

                # Format results
                result_text = "\n\n".join(
                    format_tool_result(r.tool, r.result, r.error) for r in tool_results
                )

                # Generate final response with LLM if available
                if self.llm_final_response:
                    final_response = self.llm_final_response(user_message, result_text, messages)
                else:
                    final_response = result_text

                yield AgentResponse(
                    content=final_response,
                    tool_calls=auto_execute,
                    is_final=True,
                )
                return

        # No tools detected - fall back to LLM for general response
        if self.llm_generate:
            tool_prompt = self.get_tool_system_prompt()
            llm_response = self.llm_generate(user_message, tool_prompt, messages)

            # Try to extract tool calls from LLM response (for advanced usage)
            llm_tool_calls = self._extract_tool_calls_from_text(llm_response)

            if llm_tool_calls:
                # LLM decided to use tools
                tool_results = await self._execute_tools(llm_tool_calls)
                result_text = "\n\n".join(
                    format_tool_result(r.tool, r.result, r.error) for r in tool_results
                )

                if self.llm_final_response:
                    final_response = self.llm_final_response(user_message, result_text, messages)
                else:
                    final_response = result_text

                yield AgentResponse(
                    content=final_response,
                    tool_calls=llm_tool_calls,
                    is_final=True,
                )
                return

            # No tools, direct response
            yield AgentResponse(
                content=llm_response,
                is_final=True,
            )
        else:
            yield AgentResponse(
                content="AI model not available for processing.",
                is_final=True,
            )

    def _detect_tools_from_keywords(self, user_message: str) -> list[ToolCall]:
        """Detect which tools to call based on keywords in user message.

        This provides reliable tool detection for smaller LLMs that struggle
        with generating proper JSON tool calls.

        Args:
            user_message: Lowercase user message.

        Returns:
            List of ToolCall objects to execute.
        """
        tools: list[ToolCall] = []

        # Temperature keywords
        if any(kw in user_message for kw in ["temperature", "temp", "how hot", "how cold"]):
            tools.append(ToolCall(name="get_temperature", arguments={}))

        # Location keywords
        if any(kw in user_message for kw in ["where am i", "location", "gps", "coordinates"]):
            tools.append(ToolCall(name="get_location", arguments={}))

        # Compass keywords
        if any(
            kw in user_message for kw in ["compass", "heading", "direction", "facing", "which way"]
        ):
            tools.append(ToolCall(name="get_compass_heading", arguments={}))

        # Altitude keywords
        if any(kw in user_message for kw in ["altitude", "elevation", "how high"]):
            tools.append(ToolCall(name="get_altitude", arguments={}))

        # Battery keywords
        if any(kw in user_message for kw in ["battery", "power", "charge"]):
            tools.append(ToolCall(name="get_battery_status", arguments={}))

        # Time keywords
        if any(kw in user_message for kw in ["what time", "current time", "time is it"]):
            tools.append(ToolCall(name="get_device_time", arguments={}))

        # All sensors
        if any(kw in user_message for kw in ["all sensor", "all reading", "everything"]):
            tools.append(ToolCall(name="get_all_sensors", arguments={}))

        # Weather conditions
        if any(kw in user_message for kw in ["weather", "conditions", "pressure"]):
            tools.append(ToolCall(name="get_weather_conditions", arguments={}))

        # Notes keywords
        if any(kw in user_message for kw in ["create note", "save note", "write note"]):
            # Extract note content - simple heuristic
            tools.append(ToolCall(name="create_note", arguments={}))
        elif any(kw in user_message for kw in ["my notes", "list notes", "show notes"]):
            tools.append(ToolCall(name="search_notes", arguments={"query": ""}))

        # Mesh keywords
        if any(kw in user_message for kw in ["mesh", "nodes", "who is on"]):
            tools.append(ToolCall(name="get_mesh_nodes", arguments={}))

        # Survival knowledge keywords
        if any(
            kw in user_message
            for kw in [
                "fire",
                "shelter",
                "water purif",
                "survival",
                "first aid",
                "snake bite",
                "hypothermia",
                "dehydration",
            ]
        ):
            # Extract search query
            tools.append(
                ToolCall(name="search_survival_knowledge", arguments={"query": user_message})
            )

        # Knots
        if any(kw in user_message for kw in ["knot", "tie a", "bowline", "clove"]):
            tools.append(ToolCall(name="lookup_knot", arguments={"name": user_message}))

        # Plants
        if any(
            kw in user_message for kw in ["plant", "edible", "poisonous", "identify", "safe to eat"]
        ):
            tools.append(ToolCall(name="identify_plant", arguments={"description": user_message}))

        # Documentation
        if any(
            kw in user_message
            for kw in ["how do i use", "how to use", "waycore", "app", "settings"]
        ):
            tools.append(ToolCall(name="search_documentation", arguments={"query": user_message}))

        return tools

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
