"""Tests for vector retriever."""

from __future__ import annotations

import tempfile

import pytest
from device.services.ai_service.rag.chunker import DocChunk
from device.services.ai_service.rag.retriever import VectorStore


class TestVectorStore:
    """Tests for VectorStore."""

    @pytest.fixture
    def temp_store(self) -> VectorStore:
        """Create a temporary vector store for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = VectorStore(
                persist_dir=tmpdir,
                collection_name="test_collection",
                use_mock=True,  # Use mock embeddings for fast tests
            )
            yield store

    def test_add_chunks(self, temp_store: VectorStore) -> None:
        """Test adding chunks to the store."""
        chunks = [
            DocChunk(
                content="This is test content about navigation.",
                source="test.md",
                section="Navigation",
                chunk_id="test_0",
            ),
            DocChunk(
                content="This is content about settings and configuration.",
                source="test.md",
                section="Settings",
                chunk_id="test_1",
            ),
        ]

        count = temp_store.add_chunks(chunks)

        assert count == 2
        assert temp_store.count() == 2

    def test_add_empty_chunks(self, temp_store: VectorStore) -> None:
        """Test adding empty list of chunks."""
        count = temp_store.add_chunks([])

        assert count == 0
        assert temp_store.count() == 0

    def test_search_basic(self, temp_store: VectorStore) -> None:
        """Test basic search functionality."""
        chunks = [
            DocChunk(
                content="The compass shows your current heading direction.",
                source="compass.md",
                section="Compass",
                chunk_id="compass_0",
            ),
            DocChunk(
                content="The GPS shows your latitude and longitude.",
                source="gps.md",
                section="GPS",
                chunk_id="gps_0",
            ),
        ]
        temp_store.add_chunks(chunks)

        results = temp_store.search("compass heading", n_results=5)

        assert len(results) > 0
        assert all("content" in r for r in results)
        assert all("source" in r for r in results)
        assert all("score" in r for r in results)

    def test_search_empty_store(self, temp_store: VectorStore) -> None:
        """Test searching an empty store."""
        results = temp_store.search("test query")

        assert results == []

    def test_search_n_results(self, temp_store: VectorStore) -> None:
        """Test limiting search results."""
        chunks = [
            DocChunk(content=f"Content {i}", source="test.md", section="Test", chunk_id=f"test_{i}")
            for i in range(10)
        ]
        temp_store.add_chunks(chunks)

        results = temp_store.search("content", n_results=3)

        assert len(results) <= 3

    def test_search_min_score(self, temp_store: VectorStore) -> None:
        """Test minimum score filtering."""
        chunks = [
            DocChunk(
                content="Very relevant content about maps.",
                source="maps.md",
                section="Maps",
                chunk_id="maps_0",
            ),
        ]
        temp_store.add_chunks(chunks)

        # With very high min_score, might filter out results
        results = temp_store.search("maps", n_results=5, min_score=0.99)

        # Results should have high scores or be empty
        for r in results:
            assert r["score"] >= 0.99

    def test_clear(self, temp_store: VectorStore) -> None:
        """Test clearing the store."""
        chunks = [
            DocChunk(content="Test", source="test.md", section="Test", chunk_id="test_0"),
        ]
        temp_store.add_chunks(chunks)
        assert temp_store.count() == 1

        temp_store.clear()

        assert temp_store.count() == 0

    def test_is_indexed(self, temp_store: VectorStore) -> None:
        """Test is_indexed property."""
        assert not temp_store.is_indexed()

        chunks = [
            DocChunk(content="Test", source="test.md", section="Test", chunk_id="test_0"),
        ]
        temp_store.add_chunks(chunks)

        assert temp_store.is_indexed()

    def test_result_structure(self, temp_store: VectorStore) -> None:
        """Test that search results have correct structure."""
        chunks = [
            DocChunk(
                content="Test content for structure check.",
                source="source.md",
                section="Section Name",
                chunk_id="struct_0",
            ),
        ]
        temp_store.add_chunks(chunks)

        # Use default min_score (-1.0) to ensure we get results with mock embeddings
        results = temp_store.search("test")

        assert len(results) >= 1
        result = results[0]

        assert result["content"] == "Test content for structure check."
        assert result["source"] == "source.md"
        assert result["section"] == "Section Name"
        # Score can be negative with mock embeddings (cosine distance)
        assert -1 <= result["score"] <= 1


class TestVectorStorePersistence:
    """Tests for vector store persistence."""

    def test_persists_across_instances(self) -> None:
        """Test that data persists across store instances."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create and populate store
            store1 = VectorStore(
                persist_dir=tmpdir,
                collection_name="persist_test",
                use_mock=True,
            )
            chunks = [
                DocChunk(
                    content="Persistent test content.",
                    source="test.md",
                    section="Test",
                    chunk_id="persist_0",
                ),
            ]
            store1.add_chunks(chunks)
            count1 = store1.count()

            # Create new store instance with same persist_dir
            store2 = VectorStore(
                persist_dir=tmpdir,
                collection_name="persist_test",
                use_mock=True,
            )
            count2 = store2.count()

            assert count1 == count2 == 1
