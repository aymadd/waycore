"""MCP Server for outdoor knowledge RAG search.

This server provides tools for searching survival, navigation, plants,
first aid, and other outdoor knowledge from the indexed knowledge base.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from device.services.ai_service.mcp_servers.base import main_with_server
from device.services.ai_service.rag import (
    Category,
    HybridKnowledgeStore,
    LocalEmbeddings,
)
from mcp.server import Server
from mcp.types import TextContent, Tool

from .formatters import (
    format_first_aid_results,
    format_plant_results,
    format_search_results,
)

logger = logging.getLogger(__name__)

# Create the MCP server
server = Server("waycore-outdoor-knowledge")

# Configuration
DATA_DIR = os.getenv("RAG_DATA_DIR", "/app/data/outdoor")
USE_MOCK = os.getenv("USE_MOCK_DATA", "false").lower() == "true"

# Lazy-loaded resources
_store: HybridKnowledgeStore | None = None
_embeddings: LocalEmbeddings | None = None


def _get_store() -> HybridKnowledgeStore:
    """Get or create the knowledge store."""
    global _store
    if _store is None:
        _store = HybridKnowledgeStore(data_dir=DATA_DIR)
        _store.load_index()
        logger.info(f"Loaded outdoor knowledge store from {DATA_DIR}")
    return _store


def _get_embeddings() -> LocalEmbeddings | None:
    """Get or create embeddings generator."""
    global _embeddings
    if _embeddings is None and not USE_MOCK:
        try:
            _embeddings = LocalEmbeddings()
        except ImportError:
            logger.warning("Embeddings not available, using keyword-only search")
    return _embeddings


def _embed_query(query: str) -> list[float] | None:
    """Generate embedding for a query."""
    embeddings = _get_embeddings()
    if embeddings:
        try:
            return embeddings.embed_query(query)
        except Exception as e:
            logger.warning(f"Failed to embed query: {e}")
    return None


@server.list_tools()  # type: ignore[misc]
async def list_tools() -> list[Tool]:
    """List available outdoor knowledge tools."""
    return [
        Tool(
            name="search_survival_knowledge",
            description=(
                "Search the outdoor survival knowledge base for information about "
                "survival skills, navigation, shelter, fire, water, signaling, and more. "
                "Use this to answer questions about wilderness survival and bushcraft."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": ("Search query (e.g., 'how to start fire without matches')"),
                    },
                    "category": {
                        "type": "string",
                        "enum": [c.value for c in Category],
                        "description": "Optional category filter",
                    },
                    "max_results": {
                        "type": "integer",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 10,
                        "description": "Maximum results to return (1-10)",
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="identify_plant",
            description=(
                "Look up plant information by name. Returns edibility, medicinal uses, "
                "and CRITICAL safety warnings. "
                "ALWAYS recommend expert verification for plant identification. "
                "NEVER encourage consumption without expert confirmation."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "plant_name": {
                        "type": "string",
                        "description": "Common or scientific plant name",
                    },
                },
                "required": ["plant_name"],
            },
        ),
        Tool(
            name="get_first_aid",
            description=(
                "Get wilderness first aid guidance for injuries or emergencies. "
                "Always advise seeking professional medical care when possible. "
                "This is for educational purposes only, not medical advice."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "condition": {
                        "type": "string",
                        "description": (
                            "Injury or condition (e.g., 'snake bite', "
                            "'hypothermia', 'broken bone')"
                        ),
                    },
                },
                "required": ["condition"],
            },
        ),
        Tool(
            name="lookup_knot",
            description=(
                "Look up instructions for tying knots. "
                "Returns step-by-step instructions and use cases."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "knot_name": {
                        "type": "string",
                        "description": (
                            "Name of the knot (e.g., 'bowline', 'clove hitch', " "'figure eight')"
                        ),
                    },
                },
                "required": ["knot_name"],
            },
        ),
        Tool(
            name="get_weather_signs",
            description=(
                "Look up natural weather signs and cloud identification. "
                "Helps predict weather changes without instruments."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "Weather query (e.g., 'signs of approaching storm', "
                            "'cumulus clouds')"
                        ),
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_outdoor_knowledge_status",
            description="Get the status of the outdoor knowledge index",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@server.call_tool()  # type: ignore[misc]
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Execute an outdoor knowledge tool.

    Args:
        name: Tool name.
        arguments: Tool arguments.

    Returns:
        List of TextContent with results.
    """
    if name == "search_survival_knowledge":
        return await _handle_search(arguments)
    elif name == "identify_plant":
        return await _handle_plant_id(arguments)
    elif name == "get_first_aid":
        return await _handle_first_aid(arguments)
    elif name == "lookup_knot":
        return await _handle_knot_lookup(arguments)
    elif name == "get_weather_signs":
        return await _handle_weather(arguments)
    elif name == "get_outdoor_knowledge_status":
        return await _handle_status(arguments)
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def _handle_search(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle general survival knowledge search."""
    query = arguments.get("query", "")
    category = arguments.get("category")
    max_results = min(arguments.get("max_results", 5), 10)

    if not query:
        return [TextContent(type="text", text="Please provide a search query.")]

    store = _get_store()
    query_embedding = _embed_query(query)

    results = store.search(
        query=query,
        query_embedding=query_embedding,
        category=category,
        limit=max_results,
    )

    if not results:
        return [
            TextContent(
                type="text",
                text=(
                    "No relevant information found in the knowledge base. "
                    "Try rephrasing your query or ask about a different topic."
                ),
            )
        ]

    formatted = format_search_results(results)
    return [TextContent(type="text", text=formatted)]


async def _handle_plant_id(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle plant identification lookup."""
    plant_name = arguments.get("plant_name", "")

    if not plant_name:
        return [TextContent(type="text", text="Please provide a plant name.")]

    store = _get_store()
    query_embedding = _embed_query(plant_name)

    results = store.search(
        query=plant_name,
        query_embedding=query_embedding,
        category="plants",
        limit=3,
    )

    if not results:
        return [
            TextContent(
                type="text",
                text=(
                    f"No information found for '{plant_name}'.\n\n"
                    "⚠️ IMPORTANT: Do not consume any plant without positive "
                    "identification from multiple reliable sources AND expert "
                    "verification.\n\n"
                    "Many poisonous plants closely resemble edible ones. "
                    "When in doubt, DO NOT consume."
                ),
            )
        ]

    formatted = format_plant_results(results)
    return [TextContent(type="text", text=formatted)]


async def _handle_first_aid(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle first aid guidance lookup."""
    condition = arguments.get("condition", "")

    if not condition:
        return [TextContent(type="text", text="Please describe the condition.")]

    store = _get_store()
    query = f"first aid treatment {condition}"
    query_embedding = _embed_query(query)

    results = store.search(
        query=condition,
        query_embedding=query_embedding,
        category="first_aid",
        limit=3,
    )

    if not results:
        return [
            TextContent(
                type="text",
                text=(
                    f"No specific guidance found for '{condition}'.\n\n"
                    "⚠️ IMPORTANT: For any serious injury or medical emergency:\n"
                    "1. Call emergency services if possible\n"
                    "2. Activate SOS beacon if in wilderness\n"
                    "3. Keep the person calm and stable\n"
                    "4. Do not move them if spinal injury suspected\n\n"
                    "This is not medical advice. Seek professional care."
                ),
            )
        ]

    formatted = format_first_aid_results(results)
    return [TextContent(type="text", text=formatted)]


async def _handle_knot_lookup(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle knot lookup."""
    knot_name = arguments.get("knot_name", "")

    if not knot_name:
        return [TextContent(type="text", text="Please provide a knot name.")]

    store = _get_store()
    query = f"knot {knot_name}"
    query_embedding = _embed_query(query)

    results = store.search(
        query=knot_name,
        query_embedding=query_embedding,
        category="knots",
        limit=2,
    )

    if not results:
        return [
            TextContent(
                type="text",
                text=f"No instructions found for '{knot_name}' knot.",
            )
        ]

    result = results[0]
    content = result.get("content", "")[:800]
    source = result.get("source_file", "")
    page = result.get("source_page", "")

    source_info = ""
    if source:
        source_info = f"\nSource: {source}"
        if page:
            source_info += f" p.{page}"

    return [
        TextContent(
            type="text",
            text=f"🪢 {result.get('title', knot_name)}\n\n{content}{source_info}",
        )
    ]


async def _handle_weather(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle weather signs lookup."""
    query = arguments.get("query", "")

    if not query:
        return [TextContent(type="text", text="Please provide a weather query.")]

    store = _get_store()
    full_query = f"weather {query}"
    query_embedding = _embed_query(full_query)

    results = store.search(
        query=query,
        query_embedding=query_embedding,
        category="weather",
        limit=3,
    )

    if not results:
        return [
            TextContent(
                type="text",
                text=f"No weather information found for '{query}'.",
            )
        ]

    lines = ["🌦️ Weather Signs\n"]
    for r in results:
        title = r.get("title", "Weather Info")
        content = r.get("content", "")[:400]
        lines.append(f"\n**{title}**\n{content}\n")

    return [TextContent(type="text", text="".join(lines))]


async def _handle_status(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle get_outdoor_knowledge_status tool call."""
    store = _get_store()
    stats = store.get_stats()

    total = stats.get("total_entries", 0)
    if total == 0:
        text = (
            "📚 Outdoor knowledge index is empty.\n"
            "Run scripts/build-rag-index.py to build the index."
        )
    else:
        lines = [
            "📚 Outdoor Knowledge Index Status\n",
            f"Total entries: {total}",
            f"Database size: {stats.get('db_size_mb', 0):.1f} MB",
            f"Vector index: {stats.get('index_size_mb', 0):.1f} MB",
            "\nBy category:",
        ]
        for cat, count in sorted(stats.get("by_category", {}).items()):
            lines.append(f"  • {cat}: {count}")

        text = "\n".join(lines)

    return [TextContent(type="text", text=text)]


if __name__ == "__main__":
    main_with_server(server)
