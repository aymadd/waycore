"""API executor for OpenAPI tools.

Executes HTTP requests to service APIs based on tool calls.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from .parser import APIEndpoint

logger = logging.getLogger(__name__)


class APIExecutor:
    """Execute API calls for OpenAPI-based tools."""

    def __init__(
        self,
        timeout: float = 10.0,
        use_docker_urls: bool | None = None,
    ) -> None:
        """Initialize the executor.

        Args:
            timeout: Request timeout in seconds.
            use_docker_urls: Whether to use Docker network URLs.
                If None, auto-detect from environment.
        """
        self.timeout = timeout

        # Auto-detect Docker environment
        if use_docker_urls is None:
            # Check if running in Docker (common env vars)
            use_docker_urls = os.getenv("DOCKER_ENV", "").lower() == "true" or os.path.exists(
                "/.dockerenv"
            )
        self.use_docker_urls = use_docker_urls

        # URL overrides from environment
        self._url_overrides: dict[str, str] = {}
        for key, value in os.environ.items():
            if key.endswith("_URL") and value:
                # e.g., CORE_DAEMON_URL -> core-daemon
                service = key[:-4].lower().replace("_", "-")
                self._url_overrides[service] = value

    async def execute(
        self,
        endpoint: APIEndpoint,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute an API call.

        Args:
            endpoint: The API endpoint definition.
            arguments: Tool arguments from the LLM.

        Returns:
            API response as dictionary, or error dict.
        """
        url = self._build_url(endpoint, arguments)
        body = self._build_body(endpoint, arguments)
        query_params = self._get_query_params(endpoint, arguments)

        logger.debug(f"Executing {endpoint.method} {url}")
        logger.debug(f"Query params: {query_params}")
        logger.debug(f"Body: {body}")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                if endpoint.method == "GET":
                    resp = await client.get(url, params=query_params)
                elif endpoint.method == "POST":
                    resp = await client.post(url, json=body, params=query_params)
                elif endpoint.method == "PUT":
                    resp = await client.put(url, json=body, params=query_params)
                elif endpoint.method == "DELETE":
                    resp = await client.delete(url, params=query_params)
                elif endpoint.method == "PATCH":
                    resp = await client.patch(url, json=body, params=query_params)
                else:
                    return {"error": f"Unsupported method: {endpoint.method}"}

                # Handle error responses
                if resp.status_code >= 400:
                    error_detail = resp.text[:500] if resp.text else "No details"
                    return {
                        "error": f"API error: {resp.status_code}",
                        "status_code": resp.status_code,
                        "details": error_detail,
                    }

                # Return response
                if resp.content:
                    try:
                        result: dict[str, Any] = resp.json()
                        return result
                    except Exception:
                        return {"result": resp.text}
                else:
                    return {"success": True}

            except httpx.TimeoutException:
                return {"error": f"Request timed out after {self.timeout}s"}
            except httpx.ConnectError as e:
                return {"error": f"Connection failed: {e}"}
            except Exception as e:
                logger.exception(f"API call failed: {e}")
                return {"error": str(e)}

    def _build_url(
        self,
        endpoint: APIEndpoint,
        arguments: dict[str, Any],
    ) -> str:
        """Build the full URL with path parameters.

        Args:
            endpoint: The API endpoint.
            arguments: Tool arguments.

        Returns:
            Full URL with path parameters substituted.
        """
        # Get base URL (check overrides first)
        base_url = self._url_overrides.get(endpoint.service_name)
        if not base_url:
            base_url = endpoint.service_url
            if not self.use_docker_urls:
                # Convert Docker URLs to localhost for local development
                base_url = self._to_localhost_url(base_url)

        # Start with the path
        path = endpoint.path

        # Replace path parameters
        for param in endpoint.parameters:
            if param.location == "path" and param.name in arguments:
                placeholder = f"{{{param.name}}}"
                value = str(arguments[param.name])
                path = path.replace(placeholder, value)

        return base_url.rstrip("/") + path

    def _to_localhost_url(self, url: str) -> str:
        """Convert Docker network URL to localhost.

        Args:
            url: URL that may use Docker service names.

        Returns:
            URL with localhost instead of service name.
        """
        # Map Docker service names to localhost ports
        port_map = {
            "core-daemon": 8001,
            "data-logger": 8002,
            "comms-bridge": 8003,
            "camera-service": 8004,
            "module-manager": 8005,
        }

        for service, port in port_map.items():
            if f"http://{service}:" in url:
                return url.replace(f"http://{service}:", "http://localhost:")
            if f"http://{service}/" in url or url.endswith(f"http://{service}"):
                return url.replace(f"http://{service}", f"http://localhost:{port}")

        return url

    def _get_query_params(
        self,
        endpoint: APIEndpoint,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        """Extract query parameters from arguments.

        Args:
            endpoint: The API endpoint.
            arguments: Tool arguments.

        Returns:
            Query parameters dictionary.
        """
        query_params: dict[str, Any] = {}

        for param in endpoint.parameters:
            if param.location == "query" and param.name in arguments:
                query_params[param.name] = arguments[param.name]

        return query_params

    def _build_body(
        self,
        endpoint: APIEndpoint,
        arguments: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Build request body from arguments.

        Args:
            endpoint: The API endpoint.
            arguments: Tool arguments.

        Returns:
            Request body dictionary, or None if no body.
        """
        if not endpoint.request_body_schema:
            return None

        # Collect arguments that are body parameters (not path/query)
        path_query_params = {p.name for p in endpoint.parameters}
        body: dict[str, Any] = {}

        for key, value in arguments.items():
            if key not in path_query_params:
                body[key] = value

        return body if body else None
