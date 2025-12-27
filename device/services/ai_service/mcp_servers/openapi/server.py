"""MCP Server for OpenAPI-based tools.

This server dynamically generates MCP tools from OpenAPI specifications,
allowing the AI agent to access all Waycore service APIs.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.types import TextContent, Tool

from ..base import main_with_server
from .executor import APIExecutor
from .generator import ToolGenerator
from .parser import APIEndpoint, OpenAPIParser

logger = logging.getLogger(__name__)

# Create the MCP server
server = Server("waycore-openapi")

# Configuration
SPEC_DIR = Path(os.getenv("OPENAPI_SPEC_DIR", "/app/docs/api"))
EXECUTOR_TIMEOUT = float(os.getenv("OPENAPI_EXECUTOR_TIMEOUT", "10.0"))

# Global state for tools and endpoints
_endpoints: dict[str, APIEndpoint] = {}
_tools: list[Tool] = []
_initialized = False


def refresh_tools() -> int:
    """Refresh tools from OpenAPI specs.

    Returns:
        Number of tools generated.
    """
    global _endpoints, _tools, _initialized

    logger.info(f"Loading OpenAPI specs from {SPEC_DIR}")

    parser = OpenAPIParser(SPEC_DIR)
    generator = ToolGenerator()

    # Parse all specs
    endpoints = parser.parse_all()

    # Build lookup by tool name
    _endpoints = {}
    for endpoint in endpoints:
        tool_name = generator._generate_tool_name(endpoint)
        _endpoints[tool_name] = endpoint

    # Generate tools
    _tools = generator.generate_tools(endpoints)
    _initialized = True

    logger.info(f"Loaded {len(_tools)} tools from OpenAPI specs")
    return len(_tools)


async def setup() -> None:
    """Async setup function called before server starts."""
    refresh_tools()


@server.list_tools()  # type: ignore
async def list_tools() -> list[Tool]:
    """List all available OpenAPI tools."""
    if not _initialized:
        refresh_tools()
    return _tools


@server.call_tool()  # type: ignore
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Execute an OpenAPI tool.

    Args:
        name: Tool name.
        arguments: Tool arguments from the LLM.

    Returns:
        List of TextContent with the result.
    """
    if not _initialized:
        refresh_tools()

    # Find the endpoint for this tool
    endpoint = _endpoints.get(name)
    if not endpoint:
        return [
            TextContent(
                type="text",
                text=f"Unknown tool: {name}. Available tools: {list(_endpoints.keys())[:10]}...",
            )
        ]

    # Execute the API call
    executor = APIExecutor(timeout=EXECUTOR_TIMEOUT)
    result = await executor.execute(endpoint, arguments)

    # Format the result
    if "error" in result:
        error_msg = result["error"]
        if "details" in result:
            error_msg += f"\nDetails: {result['details']}"
        return [TextContent(type="text", text=f"Error: {error_msg}")]

    # Format successful result as JSON
    try:
        formatted = json.dumps(result, indent=2, default=str)
    except Exception:
        formatted = str(result)

    return [TextContent(type="text", text=formatted)]


# Entry point for running as subprocess
if __name__ == "__main__":
    main_with_server(server, setup=setup)
