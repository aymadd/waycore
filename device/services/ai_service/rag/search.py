"""High-level search interface for the RAG knowledge base.

This module provides a unified search interface that combines the
embedding generator with the hybrid knowledge store.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from .embeddings import LocalEmbeddings
from .store import HybridKnowledgeStore

logger = logging.getLogger(__name__)


class OutdoorKnowledgeSearch:
    """High-level search interface for outdoor knowledge.

    Combines embedding generation with hybrid search for
    simple query-to-results workflow.
    """

    def __init__(
        self,
        data_dir: str | Path | None = None,
        use_vectors: bool = True,
    ) -> None:
        """Initialize the search interface.

        Args:
            data_dir: Base directory for data files.
            use_vectors: Whether to use vector search (requires embeddings).
        """
        self.store = HybridKnowledgeStore(data_dir=data_dir)
        self.use_vectors = use_vectors
        self._embeddings: LocalEmbeddings | None = None

        # Try to load existing vector index
        if use_vectors:
            self.store.load_index()

    def _get_embeddings(self) -> LocalEmbeddings:
        """Get or create embeddings instance."""
        if self._embeddings is None:
            self._embeddings = LocalEmbeddings()
        return self._embeddings

    def search(
        self,
        query: str,
        category: str | None = None,
        limit: int = 5,
        include_embeddings: bool = True,
    ) -> list[dict[str, Any]]:
        """Search the outdoor knowledge base.

        Args:
            query: Natural language query.
            category: Optional category filter.
            limit: Maximum number of results.
            include_embeddings: Whether to use semantic search.

        Returns:
            List of matching entries with scores.
        """
        query_embedding = None

        if include_embeddings and self.use_vectors:
            try:
                embeddings = self._get_embeddings()
                query_embedding = embeddings.embed_query(query)
            except Exception as e:
                logger.warning(f"Failed to generate query embedding: {e}")

        return self.store.search(
            query=query,
            query_embedding=query_embedding,
            category=category,
            limit=limit,
        )

    def search_plants(
        self,
        plant_name: str,
        limit: int = 3,
    ) -> list[dict[str, Any]]:
        """Search specifically for plant information.

        Args:
            plant_name: Common or scientific plant name.
            limit: Maximum results.

        Returns:
            Plant entries with safety warnings.
        """
        return self.search(
            query=plant_name,
            category="plants",
            limit=limit,
        )

    def search_first_aid(
        self,
        condition: str,
        limit: int = 3,
    ) -> list[dict[str, Any]]:
        """Search for first aid guidance.

        Args:
            condition: Injury or condition description.
            limit: Maximum results.

        Returns:
            First aid entries with medical disclaimers.
        """
        # Expand query for better results
        expanded_query = f"first aid treatment {condition}"
        return self.search(
            query=expanded_query,
            category="first_aid",
            limit=limit,
        )

    def search_survival(
        self,
        topic: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Search for survival/bushcraft information.

        Args:
            topic: Survival topic (fire, shelter, water, etc.).
            limit: Maximum results.

        Returns:
            Survival knowledge entries.
        """
        return self.search(
            query=topic,
            category="survival",
            limit=limit,
        )

    def get_stats(self) -> dict[str, Any]:
        """Get search index statistics."""
        return self.store.get_stats()

    def close(self) -> None:
        """Close resources."""
        self.store.close()
