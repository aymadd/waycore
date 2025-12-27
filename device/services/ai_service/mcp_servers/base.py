"""Base utilities for MCP servers."""

from __future__ import annotations

import asyncio
import logging
import sys
from collections.abc import Coroutine
from typing import Callable

from mcp.server import Server
from mcp.server.stdio import stdio_server

logger = logging.getLogger(__name__)


async def run_mcp_server(server: Server) -> None:
    """Run an MCP server using stdio transport.

    This is the standard entry point for all MCP servers.

    Args:
        server: The MCP Server instance to run.
    """
    try:
        async with stdio_server() as (read, write):
            await server.run(read, write, server.create_initialization_options())
    except Exception as e:
        logger.error(f"MCP server error: {e}")
        raise


def main_with_server(
    server: Server,
    setup: Callable[[], Coroutine[None, None, None]] | None = None,
) -> None:
    """Main entry point for running an MCP server.

    Args:
        server: The MCP Server instance to run.
        setup: Optional async setup function to call before running.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr,  # Log to stderr, not stdout (stdout is for MCP)
    )

    async def _run() -> None:
        if setup:
            await setup()
        await run_mcp_server(server)

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        logger.info("MCP server stopped by user")
    except Exception as e:
        logger.error(f"MCP server failed: {e}")
        sys.exit(1)
