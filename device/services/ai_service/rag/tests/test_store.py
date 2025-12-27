"""Tests for the hybrid knowledge store."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from device.services.ai_service.rag.models import Category, KnowledgeEntry, SafetyLevel
from device.services.ai_service.rag.store import HybridKnowledgeStore


class TestHybridKnowledgeStore:
    """Tests for HybridKnowledgeStore class."""

    @pytest.fixture
    def temp_dir(self) -> Path:
        """Create a temporary directory for test database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def store(self, temp_dir: Path) -> HybridKnowledgeStore:
        """Create a test store."""
        return HybridKnowledgeStore(data_dir=temp_dir)

    @pytest.fixture
    def sample_entries(self) -> list[KnowledgeEntry]:
        """Create sample entries for testing."""
        return [
            KnowledgeEntry(
                id="test_1",
                title="Fire Starting Basics",
                content="Learn how to start a fire using friction methods.",
                category=Category.SURVIVAL,
                subcategory="Fire",
                safety_level=SafetyLevel.CAUTION,
                tags=["fire", "survival"],
                keywords=["fire", "friction", "methods"],
            ),
            KnowledgeEntry(
                id="test_2",
                title="Water Purification",
                content="Methods to purify water in the wilderness.",
                category=Category.SURVIVAL,
                subcategory="Water",
                safety_level=SafetyLevel.SAFE,
                tags=["water", "purification"],
                keywords=["water", "purify", "wilderness"],
            ),
            KnowledgeEntry(
                id="test_3",
                title="Dandelion Identification",
                content="Dandelion is a common edible plant with yellow flowers.",
                category=Category.PLANTS,
                subcategory="Edible",
                safety_level=SafetyLevel.DANGER,
                safety_notes="Verify identification before eating.",
                tags=["plant", "edible", "dandelion"],
                keywords=["dandelion", "edible", "yellow", "flowers"],
            ),
        ]

    def test_init_creates_database(self, temp_dir: Path) -> None:
        """Test that initialization creates the database file."""
        store = HybridKnowledgeStore(data_dir=temp_dir)
        assert store.db_path.exists()
        store.close()

    def test_add_entries(
        self, store: HybridKnowledgeStore, sample_entries: list[KnowledgeEntry]
    ) -> None:
        """Test adding entries to the store."""
        added = store.add_entries(sample_entries)
        assert added == 3

        stats = store.get_stats()
        assert stats["total_entries"] == 3

    def test_fts_search_basic(
        self, store: HybridKnowledgeStore, sample_entries: list[KnowledgeEntry]
    ) -> None:
        """Test basic FTS search."""
        store.add_entries(sample_entries)

        results = store.search("fire", limit=5)
        assert len(results) >= 1
        assert any("fire" in r["content"].lower() for r in results)

    def test_fts_search_with_category(
        self, store: HybridKnowledgeStore, sample_entries: list[KnowledgeEntry]
    ) -> None:
        """Test FTS search with category filter."""
        store.add_entries(sample_entries)

        # Search plants category only
        results = store.search("edible", category="plants", limit=5)
        assert len(results) >= 1
        assert all(r["category"] == "plants" for r in results)

    def test_search_no_results(self, store: HybridKnowledgeStore) -> None:
        """Test search with no matching results."""
        results = store.search("nonexistent query xyz123")
        assert len(results) == 0

    def test_get_stats_empty(self, store: HybridKnowledgeStore) -> None:
        """Test stats on empty store."""
        stats = store.get_stats()
        assert stats["total_entries"] == 0
        assert stats["by_category"] == {}

    def test_get_stats_with_data(
        self, store: HybridKnowledgeStore, sample_entries: list[KnowledgeEntry]
    ) -> None:
        """Test stats after adding data."""
        store.add_entries(sample_entries)
        stats = store.get_stats()

        assert stats["total_entries"] == 3
        assert "survival" in stats["by_category"]
        assert "plants" in stats["by_category"]
        assert stats["by_category"]["survival"] == 2
        assert stats["by_category"]["plants"] == 1

    def test_clear(self, store: HybridKnowledgeStore, sample_entries: list[KnowledgeEntry]) -> None:
        """Test clearing the store."""
        store.add_entries(sample_entries)
        assert store.get_stats()["total_entries"] == 3

        store.clear()
        assert store.get_stats()["total_entries"] == 0

    def test_sanitize_fts_query(self, store: HybridKnowledgeStore) -> None:
        """Test FTS query sanitization."""
        # Normal query
        result = store._sanitize_fts_query("fire starting")
        assert "fire" in result
        assert "starting" in result

        # Query with special characters
        result = store._sanitize_fts_query('fire "starting" (test)')
        assert '"' not in result
        assert "(" not in result
        assert ")" not in result

        # Empty query
        result = store._sanitize_fts_query("   ")
        assert result == ""

    def test_context_manager(self, temp_dir: Path) -> None:
        """Test using store as context manager."""
        with HybridKnowledgeStore(data_dir=temp_dir) as store:
            assert store._conn is not None
        # Connection should be closed after exiting context

    def test_save_and_load_index(
        self, temp_dir: Path, sample_entries: list[KnowledgeEntry]
    ) -> None:
        """Test saving and loading vector index."""
        # Add entries with embeddings
        for entry in sample_entries:
            # Mock embedding (random values)
            entry.embedding = [0.1] * 384

        # Create store, add entries, save index
        store1 = HybridKnowledgeStore(data_dir=temp_dir)
        store1.add_entries(sample_entries)
        store1.save_index()
        store1.close()

        # Create new store and load index
        store2 = HybridKnowledgeStore(data_dir=temp_dir)
        loaded = store2.load_index()

        # Check if hnswlib is available
        try:
            import hnswlib  # noqa: F401

            assert loaded is True
            assert store2._index is not None
        except ImportError:
            # hnswlib not available, index won't load
            assert loaded is False

        store2.close()


class TestHybridKnowledgeStoreIntegration:
    """Integration tests requiring more setup."""

    @pytest.fixture
    def temp_dir(self) -> Path:
        """Create a temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_reciprocal_rank_fusion(self, temp_dir: Path) -> None:
        """Test RRF algorithm combines results correctly."""
        store = HybridKnowledgeStore(data_dir=temp_dir)

        fts_results = [
            {"id": "a", "title": "A", "score": 1.0},
            {"id": "b", "title": "B", "score": 0.8},
            {"id": "c", "title": "C", "score": 0.6},
        ]

        vector_results = [
            {"id": "b", "title": "B", "vector_score": 0.9},
            {"id": "d", "title": "D", "vector_score": 0.7},
            {"id": "a", "title": "A", "vector_score": 0.5},
        ]

        combined = store._reciprocal_rank_fusion(fts_results, vector_results, limit=10)

        # B should be ranked highest (appears in both, good ranks)
        assert combined[0]["id"] == "b"

        # A should also be high (appears in both)
        ids = [r["id"] for r in combined[:3]]
        assert "a" in ids
        assert "b" in ids

        store.close()
