"""MCP Manager for connecting to and managing MCP servers."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import Tool

from .config import MCPServerConfig

logger = logging.getLogger(__name__)


class MCPManager:
    """Manages MCP server connections via stdio.

    MCP servers run as subprocess of the AI service, communicating
    via stdin/stdout. This provides zero-latency local tool access.
    """

    def __init__(self) -> None:
        """Initialize the MCP manager."""
        self._sessions: dict[str, ClientSession] = {}
        self._stdio_contexts: dict[str, Any] = {}  # Store stdio context managers
        self._session_contexts: dict[str, Any] = {}  # Store session context managers
        self._tools: dict[str, tuple[str, Tool]] = {}  # tool_name -> (server_name, tool)
        self._server_configs: dict[str, MCPServerConfig] = {}
        self._connected = False

    @property
    def is_connected(self) -> bool:
        """Check if any MCP servers are connected."""
        return self._connected and len(self._sessions) > 0

    async def connect_server(self, config: MCPServerConfig) -> bool:
        """Start and connect to an MCP server as subprocess.

        Args:
            config: Server configuration.

        Returns:
            True if connection successful, False otherwise.
        """
        if not config.enabled:
            logger.debug(f"Server {config.name} is disabled, skipping")
            return False

        logger.info(f"Connecting to MCP server: {config.name}")

        try:
            params = StdioServerParameters(
                command=config.command,
                args=config.args,
                env=config.env,
            )

            # Start the subprocess and create session
            stdio_ctx = stdio_client(params)
            read, write = await stdio_ctx.__aenter__()
            self._stdio_contexts[config.name] = stdio_ctx

            session_ctx = ClientSession(read, write)
            session = await session_ctx.__aenter__()
            self._session_contexts[config.name] = session_ctx

            # Initialize the session
            await session.initialize()

            # Discover available tools
            tools_result = await session.list_tools()
            for tool in tools_result.tools:
                self._tools[tool.name] = (config.name, tool)
                logger.info(f"  Registered tool: {tool.name}")

            self._sessions[config.name] = session
            self._server_configs[config.name] = config
            self._connected = True

            logger.info(
                f"Connected to MCP server {config.name} " f"with {len(tools_result.tools)} tools"
            )
            return True

        except FileNotFoundError as e:
            logger.error(f"MCP server command not found for {config.name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to MCP server {config.name}: {e}")
            return False

    async def connect_all(self, configs: list[MCPServerConfig]) -> int:
        """Connect to all configured MCP servers.

        Args:
            configs: List of server configurations.

        Returns:
            Number of successfully connected servers.
        """
        connected = 0
        for config in configs:
            if await self.connect_server(config):
                connected += 1
        return connected

    def list_tools(self) -> list[Tool]:
        """List all available tools across all servers.

        Returns:
            List of Tool objects from all connected servers.
        """
        return [tool for _, tool in self._tools.values()]

    def get_tool(self, name: str) -> Tool | None:
        """Get a tool by name.

        Args:
            name: Tool name.

        Returns:
            Tool object if found, None otherwise.
        """
        if name in self._tools:
            return self._tools[name][1]
        return None

    def get_tools_for_llm(self) -> list[dict[str, Any]]:
        """Get tool definitions formatted for LLM consumption.

        Returns:
            List of tool definitions as dictionaries.
        """
        tools = []
        for tool in self.list_tools():
            tools.append(
                {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.inputSchema or {},
                }
            )
        return tools

    def requires_confirmation(self, tool_name: str) -> bool:
        """Check if a tool requires user confirmation before execution.

        Args:
            tool_name: Name of the tool.

        Returns:
            True if confirmation is required, False otherwise.
        """
        if tool_name not in self._tools:
            return False
        server_name, _ = self._tools[tool_name]
        config = self._server_configs.get(server_name)
        if config and config.requires_confirmation:
            return tool_name in config.requires_confirmation
        return False

    def get_timeout(self, tool_name: str) -> float:
        """Get the timeout for a tool's server.

        Args:
            tool_name: Name of the tool.

        Returns:
            Timeout in seconds.
        """
        if tool_name not in self._tools:
            return 10.0
        server_name, _ = self._tools[tool_name]
        config = self._server_configs.get(server_name)
        return config.timeout_seconds if config else 10.0

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
    ) -> Any:
        """Call a tool on its MCP server.

        Args:
            name: Tool name.
            arguments: Tool arguments.

        Returns:
            Tool result.

        Raises:
            ValueError: If tool is unknown.
            TimeoutError: If tool execution times out.
            Exception: If tool execution fails.
        """
        if name not in self._tools:
            raise ValueError(f"Unknown tool: {name}")

        server_name, _ = self._tools[name]
        session = self._sessions[server_name]
        timeout = self.get_timeout(name)

        logger.debug(f"Calling tool {name} with arguments: {arguments}")

        try:
            result = await asyncio.wait_for(
                session.call_tool(name, arguments or {}),
                timeout=timeout,
            )
            logger.debug(f"Tool {name} returned: {result}")
            return result
        except asyncio.TimeoutError:
            error_msg = f"Tool {name} timed out after {timeout}s"
            logger.warning(error_msg)
            raise TimeoutError(error_msg) from None

    async def close_server(self, name: str) -> None:
        """Close a specific MCP server connection.

        Args:
            name: Server name.
        """
        # Remove tools from this server
        tools_to_remove = [
            tool_name for tool_name, (server_name, _) in self._tools.items() if server_name == name
        ]
        for tool_name in tools_to_remove:
            del self._tools[tool_name]

        # Close session
        if name in self._session_contexts:
            try:
                await self._session_contexts[name].__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"Error closing session for {name}: {e}")
            del self._session_contexts[name]

        # Close stdio
        if name in self._stdio_contexts:
            try:
                await self._stdio_contexts[name].__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"Error closing stdio for {name}: {e}")
            del self._stdio_contexts[name]

        # Remove from tracking
        self._sessions.pop(name, None)
        self._server_configs.pop(name, None)

        logger.info(f"Closed MCP server: {name}")

    async def close_all(self) -> None:
        """Close all MCP server connections."""
        server_names = list(self._sessions.keys())
        for name in server_names:
            await self.close_server(name)

        self._connected = False
        logger.info("Closed all MCP servers")
