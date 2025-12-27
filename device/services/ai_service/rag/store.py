"""Hybrid knowledge store combining SQLite FTS5 and Hnswlib vector search.

This module provides efficient storage and retrieval for the outdoor
knowledge base, using:
- SQLite with FTS5 for keyword/phrase matching and metadata filtering
- Hnswlib for semantic similarity search
- Reciprocal Rank Fusion (RRF) for combining results
"""

from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import hnswlib

from .models import Category, KnowledgeEntry, SafetyLevel

logger = logging.getLogger(__name__)

# Default paths
DEFAULT_DATA_DIR = Path("/app/data/outdoor")


class HybridKnowledgeStore:
    """Hybrid storage combining SQLite FTS5 and Hnswlib vector search.

    SQLite FTS5 provides:
    - Fast keyword/phrase matching
    - Metadata filtering (category, safety level)
    - Persistent storage

    Hnswlib provides:
    - Semantic similarity search
    - Sub-10ms query latency
    - Cosine distance with 384-dim vectors

    Results are combined using Reciprocal Rank Fusion (RRF).
    """

    EMBEDDING_DIM = 384  # all-MiniLM-L6-v2 dimension

    def __init__(
        self,
        db_path: str | Path | None = None,
        data_dir: str | Path | None = None,
    ) -> None:
        """Initialize the hybrid knowledge store.

        Args:
            db_path: Path to SQLite database. If None, uses data_dir/knowledge.db.
            data_dir: Base directory for data files. Defaults to /app/data/outdoor.
        """
        if data_dir is not None:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = DEFAULT_DATA_DIR

        if db_path is not None:
            self.db_path = Path(db_path)
        else:
            self.db_path = self.data_dir / "knowledge.db"

        self.index_path = self.db_path.with_suffix(".idx")

        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._conn: sqlite3.Connection | None = None
        self._index: hnswlib.Index | None = None

        self._init_database()

    def _init_database(self) -> None:
        """Initialize SQLite database with FTS5."""
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row

        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS entries (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT,
                safety_level TEXT DEFAULT 'safe',
                safety_notes TEXT,
                source_file TEXT,
                source_page INTEGER,
                source_url TEXT,
                license TEXT,
                tags TEXT,
                keywords TEXT,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS entries_fts USING fts5(
                id, title, content, tags, keywords,
                content='entries',
                content_rowid='rowid'
            );

            -- Trigger to keep FTS index in sync
            CREATE TRIGGER IF NOT EXISTS entries_ai AFTER INSERT ON entries BEGIN
                INSERT INTO entries_fts(rowid, id, title, content, tags, keywords)
                VALUES (new.rowid, new.id, new.title, new.content, new.tags, new.keywords);
            END;

            CREATE TRIGGER IF NOT EXISTS entries_ad AFTER DELETE ON entries BEGIN
                INSERT INTO entries_fts(
                    entries_fts, rowid, id, title, content, tags, keywords
                )
                VALUES (
                    'delete', old.rowid, old.id, old.title, old.content,
                    old.tags, old.keywords
                );
            END;

            CREATE TRIGGER IF NOT EXISTS entries_au AFTER UPDATE ON entries BEGIN
                INSERT INTO entries_fts(
                    entries_fts, rowid, id, title, content, tags, keywords
                )
                VALUES (
                    'delete', old.rowid, old.id, old.title, old.content,
                    old.tags, old.keywords
                );
                INSERT INTO entries_fts(rowid, id, title, content, tags, keywords)
                VALUES (new.rowid, new.id, new.title, new.content, new.tags, new.keywords);
            END;

            CREATE INDEX IF NOT EXISTS idx_entries_category ON entries(category);
            CREATE INDEX IF NOT EXISTS idx_entries_safety ON entries(safety_level);
        """
        )
        self._conn.commit()

    def _init_vector_index(self, max_elements: int = 20000) -> None:
        """Initialize Hnswlib vector index.

        Args:
            max_elements: Maximum number of elements the index can hold.
        """
        try:
            import hnswlib
        except ImportError as e:
            raise ImportError(
                "hnswlib required for vector search. Install with: poetry add hnswlib"
            ) from e

        self._index = hnswlib.Index(space="cosine", dim=self.EMBEDDING_DIM)
        self._index.init_index(
            max_elements=max_elements,
            ef_construction=100,
            M=16,
        )
        self._index.set_ef(50)  # Search quality vs speed tradeoff

    def add_entries(self, entries: list[KnowledgeEntry]) -> int:
        """Add entries to both SQLite and vector index.

        Args:
            entries: List of KnowledgeEntry objects to add.

        Returns:
            Number of entries added.
        """
        if not entries:
            return 0

        if self._conn is None:
            self._init_database()
        assert self._conn is not None  # mypy: ensured by _init_database

        # Initialize vector index if needed
        if self._index is None:
            self._init_vector_index(len(entries) + 10000)

        added = 0
        for entry in entries:
            # Insert into SQLite
            try:
                self._conn.execute(
                    """
                    INSERT OR REPLACE INTO entries
                    (id, title, content, category, subcategory, safety_level,
                     safety_notes, source_file, source_page, source_url, license,
                     tags, keywords, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        entry.id,
                        entry.title,
                        entry.content,
                        (
                            entry.category.value
                            if isinstance(entry.category, Category)
                            else entry.category
                        ),
                        entry.subcategory,
                        (
                            entry.safety_level.value
                            if isinstance(entry.safety_level, SafetyLevel)
                            else entry.safety_level
                        ),
                        entry.safety_notes,
                        entry.source_file,
                        entry.source_page,
                        entry.source_url,
                        entry.license,
                        json.dumps(entry.tags),
                        json.dumps(entry.keywords),
                        entry.created_at,
                        entry.updated_at,
                    ),
                )
                added += 1
            except sqlite3.Error as e:
                logger.warning(f"Failed to insert entry {entry.id}: {e}")
                continue

        self._conn.commit()

        # Get rowids for vector index mapping
        entry_ids = [e.id for e in entries]
        placeholders = ",".join("?" * len(entry_ids))
        cursor = self._conn.execute(
            f"SELECT rowid, id FROM entries WHERE id IN ({placeholders})",
            entry_ids,
        )
        id_to_rowid = {row["id"]: row["rowid"] for row in cursor}

        # Add to vector index
        embeddings = []
        labels = []
        for entry in entries:
            if entry.embedding and entry.id in id_to_rowid:
                embeddings.append(entry.embedding)
                labels.append(id_to_rowid[entry.id])

        if embeddings and self._index is not None:
            self._index.add_items(embeddings, labels)

        logger.info(f"Added {added} entries to store ({len(embeddings)} with embeddings)")
        return added

    def search(
        self,
        query: str,
        query_embedding: list[float] | None = None,
        category: str | None = None,
        safety_max: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Search using hybrid FTS + vector similarity.

        Args:
            query: Text query for keyword search.
            query_embedding: Query embedding for semantic search.
            category: Filter by category (optional).
            safety_max: Maximum safety level to include (optional).
            limit: Maximum number of results.

        Returns:
            List of result dictionaries.
        """
        # FTS5 keyword search
        fts_results = self._fts_search(query, category, limit * 2)

        # Vector search (if embedding provided)
        vector_results: list[dict[str, Any]] = []
        if query_embedding and self._index is not None:
            try:
                vector_results = self._vector_search(query_embedding, category, limit * 2)
            except Exception as e:
                logger.warning(f"Vector search failed: {e}")

        # Combine with Reciprocal Rank Fusion
        if vector_results:
            combined = self._reciprocal_rank_fusion(fts_results, vector_results, limit * 2)
        else:
            combined = fts_results

        # Filter by safety level if specified
        if safety_max:
            safety_order = ["safe", "caution", "warning", "danger", "lethal"]
            try:
                max_idx = safety_order.index(safety_max.lower())
                combined = [
                    r
                    for r in combined
                    if safety_order.index(r.get("safety_level", "safe")) <= max_idx
                ]
            except ValueError:
                pass  # Invalid safety level, don't filter

        return combined[:limit]

    def _fts_search(
        self,
        query: str,
        category: str | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Full-text search using FTS5.

        Args:
            query: Search query.
            category: Optional category filter.
            limit: Maximum results.

        Returns:
            List of result dictionaries with BM25 scores.
        """
        if self._conn is None:
            return []

        # Clean query for FTS5
        fts_query = self._sanitize_fts_query(query)
        if not fts_query:
            return []

        sql = """
            SELECT e.*, bm25(entries_fts) as score
            FROM entries_fts
            JOIN entries e ON entries_fts.rowid = e.rowid
            WHERE entries_fts MATCH ?
        """
        params: list[Any] = [fts_query]

        if category:
            sql += " AND e.category = ?"
            params.append(category)

        sql += " ORDER BY score LIMIT ?"
        params.append(limit)

        try:
            cursor = self._conn.execute(sql, params)
            results = [dict(row) for row in cursor.fetchall()]

            # Parse JSON fields
            for r in results:
                r["tags"] = json.loads(r.get("tags") or "[]")
                r["keywords"] = json.loads(r.get("keywords") or "[]")

            return results
        except sqlite3.Error as e:
            logger.warning(f"FTS search failed: {e}")
            return []

    def _sanitize_fts_query(self, query: str) -> str:
        """Sanitize query for FTS5.

        Args:
            query: Raw query string.

        Returns:
            Sanitized query safe for FTS5.
        """
        # Remove special FTS5 characters that could cause syntax errors
        special_chars = '"()-*:^'
        for char in special_chars:
            query = query.replace(char, " ")

        # Split into words and filter empty
        words = [w.strip() for w in query.split() if w.strip()]

        if not words:
            return ""

        # Join words with OR for broader matching
        return " OR ".join(words)

    def _vector_search(
        self,
        embedding: list[float],
        category: str | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Semantic search using Hnswlib.

        Args:
            embedding: Query embedding vector.
            category: Optional category filter.
            limit: Maximum results.

        Returns:
            List of result dictionaries with similarity scores.
        """
        if self._index is None or self._conn is None:
            return []

        k = min(limit, self._index.get_current_count())
        labels, distances = self._index.knn_query([embedding], k=k)

        results: list[dict[str, Any]] = []
        for label, dist in zip(labels[0], distances[0]):
            cursor = self._conn.execute(
                "SELECT * FROM entries WHERE rowid = ?",
                (int(label),),
            )
            row = cursor.fetchone()
            if row:
                entry = dict(row)
                if category and entry.get("category") != category:
                    continue
                entry["vector_score"] = float(1 - dist)  # Convert distance to similarity
                entry["tags"] = json.loads(entry.get("tags") or "[]")
                entry["keywords"] = json.loads(entry.get("keywords") or "[]")
                results.append(entry)

        return results

    def _reciprocal_rank_fusion(
        self,
        fts_results: list[dict[str, Any]],
        vector_results: list[dict[str, Any]],
        limit: int,
        k: int = 60,
    ) -> list[dict[str, Any]]:
        """Combine FTS and vector results using RRF algorithm.

        Args:
            fts_results: Results from FTS search.
            vector_results: Results from vector search.
            limit: Maximum combined results.
            k: RRF constant (default 60).

        Returns:
            Combined and re-ranked results.
        """
        scores: dict[str, float] = {}
        entries: dict[str, dict[str, Any]] = {}

        for rank, entry in enumerate(fts_results):
            entry_id = entry["id"]
            scores[entry_id] = scores.get(entry_id, 0) + 1 / (k + rank + 1)
            entries[entry_id] = entry

        for rank, entry in enumerate(vector_results):
            entry_id = entry["id"]
            scores[entry_id] = scores.get(entry_id, 0) + 1 / (k + rank + 1)
            entries[entry_id] = entry

        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        return [entries[eid] for eid in sorted_ids[:limit]]

    def save_index(self) -> None:
        """Save vector index to disk."""
        if self._index is not None:
            self._index.save_index(str(self.index_path))
            logger.info(f"Saved vector index to {self.index_path}")

    def load_index(self) -> bool:
        """Load vector index from disk.

        Returns:
            True if index was loaded successfully.
        """
        try:
            import hnswlib
        except ImportError:
            logger.warning("hnswlib not available")
            return False

        if not self.index_path.exists():
            logger.info("No vector index found")
            return False

        try:
            self._index = hnswlib.Index(space="cosine", dim=self.EMBEDDING_DIM)
            self._index.load_index(str(self.index_path))
            self._index.set_ef(50)
            logger.info(f"Loaded vector index from {self.index_path}")
            return True
        except Exception as e:
            logger.warning(f"Failed to load vector index: {e}")
            self._index = None
            return False

    def get_stats(self) -> dict[str, Any]:
        """Get index statistics.

        Returns:
            Dictionary with count and size information.
        """
        stats: dict[str, Any] = {
            "total_entries": 0,
            "by_category": {},
            "by_safety": {},
            "db_size_mb": 0,
            "index_size_mb": 0,
        }

        if self._conn is None:
            return stats

        try:
            cursor = self._conn.execute("SELECT COUNT(*) FROM entries")
            stats["total_entries"] = cursor.fetchone()[0]

            cursor = self._conn.execute("SELECT category, COUNT(*) FROM entries GROUP BY category")
            stats["by_category"] = dict(cursor.fetchall())

            cursor = self._conn.execute(
                "SELECT safety_level, COUNT(*) FROM entries GROUP BY safety_level"
            )
            stats["by_safety"] = dict(cursor.fetchall())

            if self.db_path.exists():
                stats["db_size_mb"] = round(self.db_path.stat().st_size / (1024 * 1024), 2)

            if self.index_path.exists():
                stats["index_size_mb"] = round(self.index_path.stat().st_size / (1024 * 1024), 2)

        except sqlite3.Error as e:
            logger.warning(f"Failed to get stats: {e}")

        return stats

    def clear(self) -> None:
        """Clear all data from the store."""
        if self._conn is not None:
            self._conn.execute("DELETE FROM entries")
            self._conn.commit()

        self._index = None
        if self.index_path.exists():
            self.index_path.unlink()

        logger.info("Cleared knowledge store")

    def close(self) -> None:
        """Close database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> HybridKnowledgeStore:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()
