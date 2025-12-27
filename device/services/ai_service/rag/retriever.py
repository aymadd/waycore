"""Vector store and retrieval for RAG.

This module provides vector storage and similarity search capabilities
using ChromaDB for efficient document retrieval.
"""

# mypy: disable-error-code="arg-type,list-item"
# ChromaDB's type stubs have compatibility issues with list types

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from chromadb import Collection

from .chunker import DocChunk

logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_PERSIST_DIR = "/app/data/rag"
DEFAULT_COLLECTION_NAME = "waycore_docs"


class EmbeddingsProtocol(Protocol):
    """Protocol for embeddings providers."""

    @property
    def dimension(self) -> int: ...

    def embed(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, query: str) -> list[float]: ...


class VectorStore:
    """Vector database for document storage and retrieval.

    Uses ChromaDB for persistent vector storage with cosine similarity search.

    Args:
        persist_dir: Directory to persist the vector database.
        collection_name: Name of the ChromaDB collection.
        embeddings: Optional embeddings provider. Defaults to LocalEmbeddings.
        use_mock: If True, use MockEmbeddings for testing.
    """

    def __init__(
        self,
        persist_dir: str | None = None,
        collection_name: str | None = None,
        embeddings: EmbeddingsProtocol | None = None,
        use_mock: bool = False,
    ) -> None:
        self.persist_dir: str = persist_dir or os.getenv("RAG_PERSIST_DIR") or DEFAULT_PERSIST_DIR
        self.collection_name = collection_name or DEFAULT_COLLECTION_NAME

        # Ensure persist directory exists
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)

        # Initialize embeddings
        if embeddings is not None:
            self._embeddings = embeddings
        elif use_mock:
            from .embeddings import MockEmbeddings

            self._embeddings = MockEmbeddings()
        else:
            from .embeddings import LocalEmbeddings

            self._embeddings = LocalEmbeddings()

        # Initialize ChromaDB
        self._client: Any = None
        self._collection: Collection | None = None

    def _get_client(self) -> Any:
        """Get or create the ChromaDB client."""
        if self._client is None:
            try:
                import chromadb
                from chromadb.config import Settings

                logger.info(f"Initializing ChromaDB at {self.persist_dir}")
                self._client = chromadb.PersistentClient(
                    path=self.persist_dir,
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True,
                    ),
                )
            except ImportError as e:
                raise ImportError(
                    "chromadb is required for RAG. Install with: poetry add chromadb"
                ) from e

        return self._client

    def _get_collection(self) -> Collection:
        """Get or create the ChromaDB collection."""
        if self._collection is None:
            client = self._get_client()
            self._collection = client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            count = self._collection.count()
            logger.info(f"Collection '{self.collection_name}' has {count} documents")

        return self._collection

    def add_chunks(self, chunks: list[DocChunk]) -> int:
        """Add document chunks to the vector store.

        Args:
            chunks: List of DocChunk objects to add.

        Returns:
            Number of chunks added.
        """
        if not chunks:
            return 0

        collection = self._get_collection()

        # Extract text for embedding
        texts = [c.content for c in chunks]
        ids = [c.chunk_id for c in chunks]
        metadatas = [{"source": c.source, "section": c.section} for c in chunks]

        # Generate embeddings
        logger.info(f"Generating embeddings for {len(texts)} chunks...")
        embeddings = self._embeddings.embed(texts)

        # Add to collection
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )

        logger.info(f"Added {len(chunks)} chunks to vector store")
        return len(chunks)

    def search(
        self,
        query: str,
        n_results: int = 5,
        min_score: float = -1.0,
    ) -> list[dict[str, Any]]:
        """Search for relevant document chunks.

        Args:
            query: Search query text.
            n_results: Maximum number of results to return.
            min_score: Minimum similarity score (-1 to 1) to include.
                       Default is -1.0 (no filtering).

        Returns:
            List of result dictionaries with content, source, section, and score.
        """
        collection = self._get_collection()

        if collection.count() == 0:
            logger.warning("Vector store is empty")
            return []

        # Generate query embedding
        query_embedding = self._embeddings.embed_query(query)

        # Search
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )

        # Format results
        formatted: list[dict[str, Any]] = []

        docs = results.get("documents")
        metas = results.get("metadatas")
        dists = results.get("distances")

        if not docs or not docs[0] or not metas or not dists:
            return formatted

        for doc, meta, dist in zip(
            docs[0],
            metas[0],
            dists[0],
        ):
            # Convert distance to similarity score (cosine distance to similarity)
            score = 1 - dist

            if score >= min_score:
                formatted.append(
                    {
                        "content": doc,
                        "source": meta["source"],
                        "section": meta["section"],
                        "score": score,
                    }
                )

        return formatted

    def count(self) -> int:
        """Get the number of documents in the store.

        Returns:
            Number of documents.
        """
        count: int = self._get_collection().count()
        return count

    def clear(self) -> None:
        """Clear all documents from the store."""
        client = self._get_client()
        try:
            client.delete_collection(self.collection_name)
            self._collection = None
            logger.info(f"Cleared collection '{self.collection_name}'")
        except Exception as e:
            logger.warning(f"Failed to clear collection: {e}")

    def is_indexed(self) -> bool:
        """Check if the store has any indexed documents.

        Returns:
            True if there are indexed documents.
        """
        return self.count() > 0
