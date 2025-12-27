"""Tool generator for OpenAPI endpoints.

Converts parsed API endpoints into MCP Tool definitions.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from mcp.types import Tool

from .parser import APIEndpoint

logger = logging.getLogger(__name__)


class ToolGenerator:
    """Generate MCP tools from API endpoints."""

    # Endpoint path patterns to exclude from tool generation
    EXCLUDED_PATTERNS: list[str] = [
        r"^/health$",
        r"^/metrics",
        r"^/internal/",
        r"^/debug/",
        r"^/docs",
        r"^/openapi",
        r"^/redoc",
    ]

    # Operations that are dangerous and should require confirmation
    DANGEROUS_OPERATIONS: set[str] = {
        "factory_reset",
        "delete",
        "clear",
        "remove",
        "send_mesh_message",
    }

    def __init__(self, exclude_patterns: list[str] | None = None) -> None:
        """Initialize the generator.

        Args:
            exclude_patterns: Additional regex patterns for paths to exclude.
        """
        self.exclude_patterns = [re.compile(p) for p in self.EXCLUDED_PATTERNS]
        if exclude_patterns:
            self.exclude_patterns.extend(re.compile(p) for p in exclude_patterns)

    def generate_tools(self, endpoints: list[APIEndpoint]) -> list[Tool]:
        """Generate MCP tools from API endpoints.

        Args:
            endpoints: List of parsed API endpoints.

        Returns:
            List of MCP Tool definitions.
        """
        tools: list[Tool] = []

        for endpoint in endpoints:
            if self._should_exclude(endpoint):
                logger.debug(f"Excluding endpoint: {endpoint.path}")
                continue

            tool = self._create_tool(endpoint)
            tools.append(tool)

        logger.info(f"Generated {len(tools)} tools from {len(endpoints)} endpoints")
        return tools

    def _should_exclude(self, endpoint: APIEndpoint) -> bool:
        """Check if an endpoint should be excluded.

        Args:
            endpoint: The endpoint to check.

        Returns:
            True if the endpoint should be excluded.
        """
        for pattern in self.exclude_patterns:
            if pattern.search(endpoint.path):
                return True
        return False

    def _create_tool(self, endpoint: APIEndpoint) -> Tool:
        """Create an MCP Tool from an API endpoint.

        Args:
            endpoint: The parsed API endpoint.

        Returns:
            MCP Tool definition.
        """
        # Generate a clean tool name
        tool_name = self._generate_tool_name(endpoint)

        # Build description
        description = self._build_description(endpoint)

        # Build input schema from parameters and request body
        input_schema = self._build_input_schema(endpoint)

        return Tool(
            name=tool_name,
            description=description,
            inputSchema=input_schema,
        )

    def _generate_tool_name(self, endpoint: APIEndpoint) -> str:
        """Generate a tool name from an endpoint.

        Args:
            endpoint: The API endpoint.

        Returns:
            Clean tool name.
        """
        # Start with operation ID, which is usually a good name
        name = endpoint.operation_id

        # Prefix with service name to avoid collisions
        # e.g., "get_battery" -> "core_daemon_get_battery"
        service_prefix = endpoint.service_name.replace("-", "_")
        if not name.lower().startswith(service_prefix):
            name = f"{service_prefix}_{name}"

        # Sanitize: replace non-alphanumeric with underscore
        name = re.sub(r"[^a-zA-Z0-9]", "_", name)

        # Remove consecutive underscores and strip
        name = re.sub(r"_+", "_", name).strip("_")

        return name.lower()

    def _build_description(self, endpoint: APIEndpoint) -> str:
        """Build a tool description.

        Args:
            endpoint: The API endpoint.

        Returns:
            Tool description.
        """
        parts: list[str] = []

        # Add summary or description
        if endpoint.summary:
            parts.append(endpoint.summary)
        elif endpoint.description:
            # Truncate long descriptions
            desc = endpoint.description[:200]
            if len(endpoint.description) > 200:
                desc += "..."
            parts.append(desc)
        else:
            parts.append(f"{endpoint.method} {endpoint.path}")

        # Add service info
        parts.append(f"[Service: {endpoint.service_name}]")

        # Add warning for dangerous operations
        if self._is_dangerous(endpoint):
            parts.append("⚠️ This action may be destructive.")

        return " ".join(parts)

    def _is_dangerous(self, endpoint: APIEndpoint) -> bool:
        """Check if an endpoint is potentially dangerous.

        Args:
            endpoint: The API endpoint.

        Returns:
            True if the endpoint is dangerous.
        """
        name_lower = endpoint.operation_id.lower()
        for dangerous in self.DANGEROUS_OPERATIONS:
            if dangerous in name_lower:
                return True

        # DELETE methods are generally dangerous
        if endpoint.method == "DELETE":
            return True

        return False

    def _build_input_schema(self, endpoint: APIEndpoint) -> dict[str, Any]:
        """Build JSON schema for tool input.

        Args:
            endpoint: The API endpoint.

        Returns:
            JSON schema for tool input.
        """
        properties: dict[str, Any] = {}
        required: list[str] = []

        # Add path and query parameters
        for param in endpoint.parameters:
            prop_schema = self._convert_param_schema(param.schema)
            if param.description:
                prop_schema["description"] = param.description

            properties[param.name] = prop_schema

            if param.required:
                required.append(param.name)

        # Add request body properties
        if endpoint.request_body_schema:
            body_schema = endpoint.request_body_schema
            if body_schema.get("type") == "object":
                body_props = body_schema.get("properties", {})
                for prop_name, prop_schema in body_props.items():
                    # Convert complex types to simple ones for LLM
                    properties[prop_name] = self._simplify_schema(prop_schema)

                # Add required fields from body
                body_required = body_schema.get("required", [])
                if endpoint.request_body_required:
                    required.extend(body_required)

        return {
            "type": "object",
            "properties": properties,
            "required": list(set(required)),
        }

    def _convert_param_schema(self, schema: dict[str, Any]) -> dict[str, Any]:
        """Convert a parameter schema to a simple format.

        Args:
            schema: OpenAPI parameter schema.

        Returns:
            Simplified schema.
        """
        result: dict[str, Any] = {}

        # Handle anyOf (nullable types)
        if "anyOf" in schema:
            for option in schema["anyOf"]:
                if option.get("type") != "null":
                    result["type"] = option.get("type", "string")
                    break
            else:
                result["type"] = "string"
        else:
            result["type"] = schema.get("type", "string")

        # Copy over useful constraints
        for key in ["minimum", "maximum", "enum", "default", "format"]:
            if key in schema:
                result[key] = schema[key]

        return result

    def _simplify_schema(self, schema: dict[str, Any]) -> dict[str, Any]:
        """Simplify a complex schema for LLM consumption.

        Args:
            schema: OpenAPI schema.

        Returns:
            Simplified schema.
        """
        result: dict[str, Any] = {}

        # Get type, handling anyOf for nullable
        if "anyOf" in schema:
            for option in schema["anyOf"]:
                if option.get("type") != "null":
                    result["type"] = option.get("type", "string")
                    break
            else:
                result["type"] = "string"
        elif "$ref" in schema:
            # Referenced types become objects or strings
            result["type"] = "object"
        else:
            result["type"] = schema.get("type", "string")

        # Add description
        if "description" in schema:
            result["description"] = schema["description"]

        # Handle enums
        if "enum" in schema:
            result["enum"] = schema["enum"]

        return result


def get_dangerous_tools(endpoints: list[APIEndpoint]) -> list[str]:
    """Get list of tool names that require confirmation.

    Args:
        endpoints: List of parsed API endpoints.

    Returns:
        List of tool names that require confirmation.
    """
    generator = ToolGenerator()
    dangerous: list[str] = []

    for endpoint in endpoints:
        if generator._is_dangerous(endpoint):
            tool_name = generator._generate_tool_name(endpoint)
            dangerous.append(tool_name)

    return dangerous
