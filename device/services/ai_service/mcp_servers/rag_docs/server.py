"""MCP Server for RAG documentation search.

This server provides the search_documentation tool that allows
the AI agent to find relevant information in Waycore docs.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from device.services.ai_service.mcp_servers.base import main_with_server
from device.services.ai_service.rag import MarkdownChunker, VectorStore
from mcp.server import Server
from mcp.types import TextContent, Tool

logger = logging.getLogger(__name__)

# Create the MCP server
server = Server("waycore-rag-docs")

# Configuration
DOCS_DIR = os.getenv("DOCS_DIR", "docs")
USE_MOCK = os.getenv("USE_MOCK_DATA", "false").lower() == "true"

# Lazy-loaded store
_store: VectorStore | None = None


def _get_store() -> VectorStore:
    """Get or create the vector store."""
    global _store
    if _store is None:
        _store = VectorStore(use_mock=USE_MOCK)

        # Check if we need to build the index
        if not _store.is_indexed():
            logger.info("Building documentation index...")
            _build_index(_store)

    return _store


def _build_index(store: VectorStore) -> int:
    """Build the RAG index from documentation files.

    Args:
        store: The vector store to populate.

    Returns:
        Number of chunks indexed.
    """
    docs_path = Path(DOCS_DIR)

    if not docs_path.exists():
        logger.warning(f"Documentation directory not found: {docs_path}")
        return 0

    chunker = MarkdownChunker(chunk_size=400, overlap=50)
    total_chunks = 0

    # Index all markdown files
    for md_file in docs_path.rglob("*.md"):
        logger.debug(f"Indexing: {md_file}")
        chunks = chunker.chunk_file(md_file)
        if chunks:
            store.add_chunks(chunks)
            total_chunks += len(chunks)
            logger.debug(f"  Added {len(chunks)} chunks")

    logger.info(f"Indexed {total_chunks} chunks from documentation")
    return total_chunks


@server.list_tools()  # type: ignore[misc]
async def list_tools() -> list[Tool]:
    """List available RAG tools."""
    return [
        Tool(
            name="search_documentation",
            description=(
                "Search Waycore software documentation and user manual. "
                "Use this to answer questions about how to use device features, "
                "app functionality, settings, and troubleshooting."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query about Waycore features or usage",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 3)",
                        "default": 3,
                        "minimum": 1,
                        "maximum": 10,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_documentation_status",
            description="Get the status of the documentation index",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@server.call_tool()  # type: ignore[misc]
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Execute a RAG tool.

    Args:
        name: Tool name.
        arguments: Tool arguments.

    Returns:
        List of TextContent with results.
    """
    if name == "search_documentation":
        return await _handle_search(arguments)
    elif name == "get_documentation_status":
        return await _handle_status(arguments)
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def _handle_search(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle search_documentation tool call."""
    query = arguments.get("query", "")
    max_results = min(arguments.get("max_results", 3), 10)

    if not query:
        return [TextContent(type="text", text="Please provide a search query.")]

    store = _get_store()
    results = store.search(query, n_results=max_results, min_score=0.3)

    if not results:
        return [
            TextContent(
                type="text",
                text=(
                    "No relevant documentation found for this query. "
                    "Try rephrasing your question or ask about a different topic."
                ),
            )
        ]

    # Format results
    lines = [f"📚 Found {len(results)} relevant documentation sections:\n"]

    for i, result in enumerate(results, 1):
        source = Path(result["source"]).name
        section = result["section"]
        score = result["score"]
        content = result["content"]

        lines.append(f"\n### {i}. {section} ({source})")
        lines.append(f"*Relevance: {score:.0%}*\n")
        lines.append(content)
        lines.append("")

    return [TextContent(type="text", text="\n".join(lines))]


async def _handle_status(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle get_documentation_status tool call."""
    store = _get_store()
    count = store.count()

    if count == 0:
        text = "📚 Documentation index is empty. No documents have been indexed."
    else:
        text = f"📚 Documentation index contains {count} chunks."

    return [TextContent(type="text", text=text)]


if __name__ == "__main__":
    main_with_server(server)
