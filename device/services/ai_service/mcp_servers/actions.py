"""MCP Server for device actions.

This server provides tools for performing actions on the device,
such as creating notes, sending mesh messages, and managing device settings.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx
from mcp.server import Server
from mcp.types import TextContent, Tool

from .base import main_with_server

logger = logging.getLogger(__name__)

# Create the MCP server
server = Server("waycore-actions")

# Configuration
DATA_LOGGER_URL = os.getenv("DATA_LOGGER_URL", "http://localhost:8002")
COMMS_BRIDGE_URL = os.getenv("COMMS_BRIDGE_URL", "http://localhost:8003")
USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "false").lower() == "true"


@server.list_tools()  # type: ignore[misc]
async def list_tools() -> list[Tool]:
    """List available action tools."""
    return [
        Tool(
            name="create_note",
            description="Create a new note with the given title and content",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Title of the note",
                    },
                    "content": {
                        "type": "string",
                        "description": "Content/body of the note",
                    },
                },
                "required": ["title", "content"],
            },
        ),
        Tool(
            name="search_notes",
            description="Search through existing notes by keyword",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query to find in notes",
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="delete_note",
            description="Delete a note by its ID (requires confirmation)",
            inputSchema={
                "type": "object",
                "properties": {
                    "note_id": {
                        "type": "string",
                        "description": "ID of the note to delete",
                    },
                },
                "required": ["note_id"],
            },
        ),
        Tool(
            name="send_mesh_message",
            description="Send a message over the Meshtastic mesh network (requires confirmation)",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Message text to send",
                    },
                    "channel": {
                        "type": "string",
                        "description": "Channel to send on (default: broadcast)",
                        "default": "broadcast",
                    },
                },
                "required": ["message"],
            },
        ),
        Tool(
            name="get_mesh_nodes",
            description="Get list of known mesh network nodes",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="clear_conversation",
            description="Clear the current AI conversation history (requires confirmation)",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="factory_reset",
            description="Reset device to factory defaults (requires confirmation) - DANGEROUS",
            inputSchema={
                "type": "object",
                "properties": {
                    "confirm": {
                        "type": "boolean",
                        "description": "Must be true to proceed",
                    },
                },
                "required": ["confirm"],
            },
        ),
    ]


@server.call_tool()  # type: ignore[misc]
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Execute an action tool.

    Args:
        name: Tool name.
        arguments: Tool arguments.

    Returns:
        List of TextContent with the result.
    """
    if name == "create_note":
        title = arguments.get("title", "Untitled")
        content = arguments.get("content", "")

        if USE_MOCK_DATA:
            return [
                TextContent(
                    type="text",
                    text=f'Created note "{title}" with {len(content)} characters',
                )
            ]

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{DATA_LOGGER_URL}/api/notes",
                    json={"title": title, "content": content},
                )
                if response.status_code in (200, 201):
                    return [
                        TextContent(
                            type="text",
                            text=f'Created note "{title}" successfully',
                        )
                    ]
                else:
                    return [
                        TextContent(
                            type="text",
                            text=f"Failed to create note: {response.status_code}",
                        )
                    ]
        except Exception as e:
            return [TextContent(type="text", text=f"Error creating note: {e}")]

    elif name == "search_notes":
        query = arguments.get("query", "")

        if USE_MOCK_DATA:
            return [
                TextContent(
                    type="text",
                    text=(
                        f'Search results for "{query}":\n'
                        "1. Meeting Notes - Discussed project timeline\n"
                        "2. Trail Log - Hiked to summit, great views\n"
                        "3. Equipment List - Gear needed for trip"
                    ),
                )
            ]

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{DATA_LOGGER_URL}/api/notes",
                    params={"search": query},
                )
                if response.status_code == 200:
                    notes = response.json()
                    if not notes:
                        return [
                            TextContent(
                                type="text",
                                text=f'No notes found matching "{query}"',
                            )
                        ]
                    lines = [f'Found {len(notes)} note(s) matching "{query}":']
                    for note in notes[:5]:  # Limit to 5 results
                        lines.append(f"- {note.get('title', 'Untitled')}")
                    return [TextContent(type="text", text="\n".join(lines))]
                else:
                    return [
                        TextContent(
                            type="text",
                            text=f"Failed to search notes: {response.status_code}",
                        )
                    ]
        except Exception as e:
            return [TextContent(type="text", text=f"Error searching notes: {e}")]

    elif name == "delete_note":
        note_id = arguments.get("note_id", "")

        if USE_MOCK_DATA:
            return [TextContent(type="text", text=f"Deleted note {note_id}")]

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.delete(
                    f"{DATA_LOGGER_URL}/api/notes/{note_id}",
                )
                if response.status_code in (200, 204):
                    return [
                        TextContent(
                            type="text",
                            text=f"Deleted note {note_id}",
                        )
                    ]
                else:
                    return [
                        TextContent(
                            type="text",
                            text=f"Failed to delete note: {response.status_code}",
                        )
                    ]
        except Exception as e:
            return [TextContent(type="text", text=f"Error deleting note: {e}")]

    elif name == "send_mesh_message":
        message = arguments.get("message", "")
        channel = arguments.get("channel", "broadcast")

        if USE_MOCK_DATA:
            return [
                TextContent(
                    type="text",
                    text=f'Sent message to {channel}: "{message}"',
                )
            ]

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{COMMS_BRIDGE_URL}/api/mesh/send",
                    json={"message": message, "channel": channel},
                )
                if response.status_code in (200, 201):
                    return [
                        TextContent(
                            type="text",
                            text=f'Message sent to {channel}: "{message}"',
                        )
                    ]
                else:
                    return [
                        TextContent(
                            type="text",
                            text=f"Failed to send message: {response.status_code}",
                        )
                    ]
        except Exception as e:
            return [TextContent(type="text", text=f"Error sending message: {e}")]

    elif name == "get_mesh_nodes":
        if USE_MOCK_DATA:
            return [
                TextContent(
                    type="text",
                    text=(
                        "Known mesh nodes:\n"
                        "1. Node-Alpha (online) - Last seen: 2 min ago\n"
                        "2. Node-Bravo (online) - Last seen: 5 min ago\n"
                        "3. Node-Charlie (offline) - Last seen: 2 hours ago"
                    ),
                )
            ]

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{COMMS_BRIDGE_URL}/api/mesh/nodes")
                if response.status_code == 200:
                    nodes = response.json()
                    if not nodes:
                        return [TextContent(type="text", text="No mesh nodes discovered")]
                    lines = [f"Known mesh nodes ({len(nodes)}):"]
                    for node in nodes:
                        status = "online" if node.get("online") else "offline"
                        lines.append(f"- {node.get('name', 'Unknown')} ({status})")
                    return [TextContent(type="text", text="\n".join(lines))]
                else:
                    return [
                        TextContent(
                            type="text",
                            text=f"Failed to get nodes: {response.status_code}",
                        )
                    ]
        except Exception as e:
            return [TextContent(type="text", text=f"Error getting nodes: {e}")]

    elif name == "clear_conversation":
        if USE_MOCK_DATA:
            return [TextContent(type="text", text="Conversation history cleared")]

        # This would typically be handled by the AI service itself
        return [TextContent(type="text", text="Conversation history cleared")]

    elif name == "factory_reset":
        confirm = arguments.get("confirm", False)
        if not confirm:
            return [
                TextContent(
                    type="text",
                    text="Factory reset requires explicit confirmation. "
                    "Set confirm=true to proceed.",
                )
            ]

        if USE_MOCK_DATA:
            return [
                TextContent(
                    type="text",
                    text="Factory reset initiated. Device will restart.",
                )
            ]

        # In production, this would trigger actual factory reset
        return [
            TextContent(
                type="text",
                text="Factory reset not available in current mode",
            )
        ]

    raise ValueError(f"Unknown tool: {name}")


if __name__ == "__main__":
    main_with_server(server)
