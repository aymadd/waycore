"""Tests for API executor."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ..executor import APIExecutor
from ..parser import APIEndpoint, APIParameter


@pytest.fixture
def sample_endpoint() -> APIEndpoint:
    """Create a sample endpoint for testing."""
    return APIEndpoint(
        path="/api/items/{item_id}",
        method="GET",
        operation_id="get_item",
        summary="Get item by ID",
        description="",
        parameters=[
            APIParameter(
                name="item_id",
                location="path",
                required=True,
                schema={"type": "string"},
            ),
            APIParameter(
                name="include_details",
                location="query",
                required=False,
                schema={"type": "boolean"},
            ),
        ],
        service_name="core-daemon",  # Use a known service
        service_url="http://core-daemon:8001",
    )


@pytest.fixture
def post_endpoint() -> APIEndpoint:
    """Create a POST endpoint for testing."""
    return APIEndpoint(
        path="/api/items",
        method="POST",
        operation_id="create_item",
        summary="Create an item",
        description="",
        parameters=[],
        request_body_schema={
            "type": "object",
            "properties": {"name": {"type": "string"}, "count": {"type": "integer"}},
        },
        request_body_required=True,
        service_name="core-daemon",
        service_url="http://core-daemon:8001",
    )


class TestAPIExecutor:
    """Tests for APIExecutor."""

    def test_build_url_substitutes_path_params(self, sample_endpoint: APIEndpoint) -> None:
        """Test that path parameters are substituted in URL."""
        executor = APIExecutor(use_docker_urls=True)
        url = executor._build_url(sample_endpoint, {"item_id": "abc123"})

        assert url == "http://core-daemon:8001/api/items/abc123"

    def test_build_url_converts_to_localhost(self, sample_endpoint: APIEndpoint) -> None:
        """Test that Docker URLs are converted to localhost."""
        executor = APIExecutor(use_docker_urls=False)
        url = executor._build_url(sample_endpoint, {"item_id": "abc123"})

        assert "localhost" in url
        assert "abc123" in url

    def test_get_query_params_extracts_query(self, sample_endpoint: APIEndpoint) -> None:
        """Test that query parameters are extracted."""
        executor = APIExecutor()
        params = executor._get_query_params(
            sample_endpoint, {"item_id": "123", "include_details": True}
        )

        assert params == {"include_details": True}
        assert "item_id" not in params

    def test_build_body_extracts_non_params(self, post_endpoint: APIEndpoint) -> None:
        """Test that body is built from non-parameter arguments."""
        executor = APIExecutor()
        body = executor._build_body(post_endpoint, {"name": "Test Item", "count": 5})

        assert body == {"name": "Test Item", "count": 5}

    def test_build_body_returns_none_for_no_body(self, sample_endpoint: APIEndpoint) -> None:
        """Test that None is returned when no request body schema."""
        executor = APIExecutor()
        body = executor._build_body(sample_endpoint, {"item_id": "123"})

        assert body is None

    @pytest.mark.asyncio
    async def test_execute_get_success(self, sample_endpoint: APIEndpoint) -> None:
        """Test successful GET request execution."""
        executor = APIExecutor(use_docker_urls=False)

        # Use MagicMock for synchronous attributes, but make async methods work
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{"id": "123", "name": "Test"}'
        mock_response.json.return_value = {"id": "123", "name": "Test"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance

            result = await executor.execute(
                sample_endpoint, {"item_id": "123", "include_details": True}
            )

        assert result == {"id": "123", "name": "Test"}
        mock_instance.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_post_success(self, post_endpoint: APIEndpoint) -> None:
        """Test successful POST request execution."""
        executor = APIExecutor(use_docker_urls=False)

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.content = b'{"id": "new123"}'
        mock_response.json.return_value = {"id": "new123"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance

            result = await executor.execute(post_endpoint, {"name": "New Item", "count": 10})

        assert result == {"id": "new123"}
        mock_instance.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_handles_error_response(self, sample_endpoint: APIEndpoint) -> None:
        """Test handling of error responses."""
        executor = APIExecutor(use_docker_urls=False)

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not found"

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance

            result = await executor.execute(sample_endpoint, {"item_id": "999"})

        assert "error" in result
        assert "404" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_handles_timeout(self, sample_endpoint: APIEndpoint) -> None:
        """Test handling of timeout errors."""
        import httpx

        executor = APIExecutor(timeout=0.1, use_docker_urls=False)

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.side_effect = httpx.TimeoutException("Timeout")
            mock_client.return_value.__aenter__.return_value = mock_instance

            result = await executor.execute(sample_endpoint, {"item_id": "123"})

        assert "error" in result
        assert "timed out" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_handles_connection_error(self, sample_endpoint: APIEndpoint) -> None:
        """Test handling of connection errors."""
        import httpx

        executor = APIExecutor(use_docker_urls=False)

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.side_effect = httpx.ConnectError("Connection refused")
            mock_client.return_value.__aenter__.return_value = mock_instance

            result = await executor.execute(sample_endpoint, {"item_id": "123"})

        assert "error" in result
        assert "Connection failed" in result["error"]

    def test_url_override_from_env(self) -> None:
        """Test that URL overrides from environment work."""
        with patch.dict("os.environ", {"TEST_SERVICE_URL": "http://custom:9000"}):
            executor = APIExecutor()
            assert executor._url_overrides.get("test-service") == "http://custom:9000"

    @pytest.mark.asyncio
    async def test_execute_empty_response(self, sample_endpoint: APIEndpoint) -> None:
        """Test handling of empty response body."""
        executor = APIExecutor(use_docker_urls=False)

        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_response.content = b""

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance

            result = await executor.execute(sample_endpoint, {"item_id": "123"})

        assert result == {"success": True}
