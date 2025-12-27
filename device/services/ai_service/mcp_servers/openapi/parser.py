"""OpenAPI specification parser.

Parses OpenAPI JSON specifications and extracts endpoint definitions
that can be converted to MCP tools.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class APIParameter:
    """Parsed API parameter."""

    name: str
    location: str  # "path", "query", "header"
    required: bool
    schema: dict[str, Any]
    description: str = ""


@dataclass
class APIEndpoint:
    """Parsed API endpoint."""

    path: str
    method: str
    operation_id: str
    summary: str
    description: str
    parameters: list[APIParameter] = field(default_factory=list)
    request_body_schema: dict[str, Any] | None = None
    request_body_required: bool = False
    service_name: str = ""
    service_url: str = ""


class OpenAPIParser:
    """Parse OpenAPI specs into endpoint definitions."""

    # Service name to URL mapping
    SERVICE_URLS: dict[str, str] = {
        "core-daemon": "http://core-daemon:8001",
        "data-logger": "http://data-logger:8002",
        "comms-bridge": "http://comms-bridge:8003",
        "camera-service": "http://camera-service:8004",
        "module-manager": "http://module-manager:8005",
    }

    # Specs to skip (avoid recursion, internal-only, etc.)
    EXCLUDED_SPECS: set[str] = {
        "ai-service.openapi.json",  # Avoid AI calling itself
        "combined.openapi.json",  # Skip the combined spec
    }

    def __init__(self, spec_dir: Path | str) -> None:
        """Initialize the parser.

        Args:
            spec_dir: Directory containing OpenAPI JSON specs.
        """
        self.spec_dir = Path(spec_dir)

    def parse_all(self) -> list[APIEndpoint]:
        """Parse all OpenAPI specs in the directory.

        Returns:
            List of all parsed endpoints.
        """
        endpoints: list[APIEndpoint] = []

        if not self.spec_dir.exists():
            logger.warning(f"OpenAPI spec directory not found: {self.spec_dir}")
            return endpoints

        for spec_file in sorted(self.spec_dir.glob("*.json")):
            if spec_file.name in self.EXCLUDED_SPECS:
                logger.debug(f"Skipping excluded spec: {spec_file.name}")
                continue

            try:
                service_endpoints = self.parse_spec(spec_file)
                endpoints.extend(service_endpoints)
                logger.info(f"Parsed {len(service_endpoints)} endpoints from {spec_file.name}")
            except Exception as e:
                logger.error(f"Failed to parse {spec_file.name}: {e}")

        return endpoints

    def parse_spec(self, spec_path: Path) -> list[APIEndpoint]:
        """Parse a single OpenAPI spec file.

        Args:
            spec_path: Path to the OpenAPI JSON file.

        Returns:
            List of endpoints from this spec.
        """
        with open(spec_path, encoding="utf-8") as f:
            spec = json.load(f)

        # Derive service name from filename (e.g., "core-daemon.openapi.json" -> "core-daemon")
        service_name = spec_path.stem.replace(".openapi", "")
        service_url = self._get_service_url(spec, service_name)

        endpoints: list[APIEndpoint] = []
        paths = spec.get("paths", {})

        for path, path_item in paths.items():
            for method in ["get", "post", "put", "delete", "patch"]:
                if method not in path_item:
                    continue

                operation = path_item[method]
                endpoint = self._parse_operation(
                    path=path,
                    method=method.upper(),
                    operation=operation,
                    service_name=service_name,
                    service_url=service_url,
                    components=spec.get("components", {}),
                )
                endpoints.append(endpoint)

        return endpoints

    def _parse_operation(
        self,
        path: str,
        method: str,
        operation: dict[str, Any],
        service_name: str,
        service_url: str,
        components: dict[str, Any],
    ) -> APIEndpoint:
        """Parse a single operation into an APIEndpoint.

        Args:
            path: URL path.
            method: HTTP method.
            operation: OpenAPI operation object.
            service_name: Name of the service.
            service_url: Base URL of the service.
            components: OpenAPI components for resolving $ref.

        Returns:
            Parsed APIEndpoint.
        """
        # Parse parameters
        parameters: list[APIParameter] = []
        for param in operation.get("parameters", []):
            parameters.append(
                APIParameter(
                    name=param["name"],
                    location=param.get("in", "query"),
                    required=param.get("required", False),
                    schema=param.get("schema", {"type": "string"}),
                    description=param.get("description", ""),
                )
            )

        # Parse request body
        request_body_schema = None
        request_body_required = False
        if "requestBody" in operation:
            request_body = operation["requestBody"]
            request_body_required = request_body.get("required", False)
            content = request_body.get("content", {})
            json_content = content.get("application/json", {})
            if "schema" in json_content:
                request_body_schema = self._resolve_schema(json_content["schema"], components)

        # Generate operation ID if not present
        operation_id = operation.get(
            "operationId",
            f"{method.lower()}_{path.replace('/', '_').strip('_')}",
        )

        return APIEndpoint(
            path=path,
            method=method,
            operation_id=operation_id,
            summary=operation.get("summary", ""),
            description=operation.get("description", ""),
            parameters=parameters,
            request_body_schema=request_body_schema,
            request_body_required=request_body_required,
            service_name=service_name,
            service_url=service_url,
        )

    def _resolve_schema(
        self,
        schema: dict[str, Any],
        components: dict[str, Any],
    ) -> dict[str, Any]:
        """Resolve $ref in schema.

        Args:
            schema: Schema that may contain $ref.
            components: OpenAPI components for resolving references.

        Returns:
            Resolved schema.
        """
        if "$ref" not in schema:
            return schema

        # Parse ref like "#/components/schemas/SystemCommand"
        ref = schema["$ref"]
        if not ref.startswith("#/components/schemas/"):
            return schema

        schema_name = ref.split("/")[-1]
        schemas = components.get("schemas", {})
        resolved: dict[str, Any] = schemas.get(schema_name, schema)
        return resolved

    def _get_service_url(self, spec: dict[str, Any], service_name: str) -> str:
        """Get the base URL for a service.

        Args:
            spec: OpenAPI spec (may contain servers section).
            service_name: Service name for fallback lookup.

        Returns:
            Service base URL.
        """
        # Try to get from OpenAPI servers section (prefer Docker network URL)
        servers = spec.get("servers", [])
        for server_info in servers:
            url: str = server_info.get("url", "")
            desc: str = server_info.get("description", "").lower()
            if "docker" in desc or "internal" in desc:
                return url

        # Fallback to known service URLs
        if service_name in self.SERVICE_URLS:
            return self.SERVICE_URLS[service_name]

        # Generic fallback
        return f"http://{service_name}:8000"
