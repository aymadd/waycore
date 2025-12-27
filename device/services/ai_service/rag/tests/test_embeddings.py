"""Tests for embeddings module."""

from __future__ import annotations

import pytest
from device.services.ai_service.rag.embeddings import MockEmbeddings


class TestMockEmbeddings:
    """Tests for MockEmbeddings (no real model needed)."""

    def test_embed_single(self) -> None:
        """Test embedding a single text."""
        embeddings = MockEmbeddings(dimension=384)
        result = embeddings.embed(["Hello world"])

        assert len(result) == 1
        assert len(result[0]) == 384

    def test_embed_multiple(self) -> None:
        """Test embedding multiple texts."""
        embeddings = MockEmbeddings(dimension=384)
        result = embeddings.embed(["Hello", "World", "Test"])

        assert len(result) == 3
        for vec in result:
            assert len(vec) == 384

    def test_embed_empty(self) -> None:
        """Test embedding empty list."""
        embeddings = MockEmbeddings()
        result = embeddings.embed([])

        assert result == []

    def test_embed_query(self) -> None:
        """Test embed_query shorthand."""
        embeddings = MockEmbeddings(dimension=384)
        result = embeddings.embed_query("Test query")

        assert len(result) == 384
        assert isinstance(result[0], float)

    def test_deterministic(self) -> None:
        """Test that same text produces same embedding."""
        embeddings = MockEmbeddings()

        result1 = embeddings.embed(["Test text"])
        result2 = embeddings.embed(["Test text"])

        assert result1 == result2

    def test_different_texts_different_embeddings(self) -> None:
        """Test that different texts produce different embeddings."""
        embeddings = MockEmbeddings()

        result1 = embeddings.embed(["Text A"])
        result2 = embeddings.embed(["Text B"])

        assert result1 != result2

    def test_dimension_property(self) -> None:
        """Test dimension property."""
        embeddings = MockEmbeddings(dimension=512)
        assert embeddings.dimension == 512

    def test_normalized(self) -> None:
        """Test that embeddings are normalized."""
        embeddings = MockEmbeddings(dimension=384)
        result = embeddings.embed(["Test text"])[0]

        # Calculate L2 norm
        norm = sum(v * v for v in result) ** 0.5

        # Should be close to 1.0 (normalized)
        assert abs(norm - 1.0) < 0.01


# Note: Tests for LocalEmbeddings require sentence-transformers
# and are skipped if the library is not installed
class TestLocalEmbeddings:
    """Tests for LocalEmbeddings (requires sentence-transformers)."""

    @pytest.fixture
    def skip_if_no_transformers(self) -> None:
        """Skip test if sentence-transformers not installed."""
        try:
            import sentence_transformers  # noqa: F401
        except ImportError:
            pytest.skip("sentence-transformers not installed")

    def test_import(self, skip_if_no_transformers: None) -> None:
        """Test that LocalEmbeddings can be imported."""
        from device.services.ai_service.rag.embeddings import LocalEmbeddings

        embeddings = LocalEmbeddings()
        assert embeddings.model_name is not None
