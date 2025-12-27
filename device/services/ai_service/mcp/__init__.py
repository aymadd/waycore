"""MCP (Model Context Protocol) integration for AI Service.

This module provides the infrastructure for connecting to MCP servers
and managing tool calls for agentic AI capabilities.
"""

from __future__ import annotations

from .config import MCPServerConfig, load_mcp_config
from .manager import MCPManager

__all__ = [
    "MCPManager",
    "MCPServerConfig",
    "load_mcp_config",
]
