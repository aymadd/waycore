"""Local embeddings generation for RAG.

This module provides vector embeddings for text using a local
sentence-transformers model. The model is suitable for running
on resource-constrained devices like Raspberry Pi.
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Default model - small and efficient, good for semantic similarity
DEFAULT_MODEL = "all-MiniLM-L6-v2"


class LocalEmbeddings:
    """Generate embeddings using a local sentence-transformers model.

    This class provides a lazy-loading interface to sentence-transformers,
    only loading the model when embeddings are actually needed.

    Args:
        model_name: Name of the sentence-transformers model to use.
            Defaults to 'all-MiniLM-L6-v2' which is small (~22MB) and
            runs well on CPU.
    """

    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or os.getenv("RAG_EMBEDDING_MODEL", DEFAULT_MODEL)
        self._model: SentenceTransformer | None = None
        self._dimension: int | None = None

    def _load_model(self) -> SentenceTransformer:
        """Load the embedding model (lazy loading).

        Returns:
            The loaded SentenceTransformer model.
        """
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                logger.info(f"Loading embedding model: {self.model_name}")
                self._model = SentenceTransformer(self.model_name)
                self._dimension = self._model.get_sentence_embedding_dimension()
                logger.info(f"Model loaded, dimension: {self._dimension}")
            except ImportError as e:
                raise ImportError(
                    "sentence-transformers is required for RAG. "
                    "Install with: poetry add sentence-transformers"
                ) from e

        return self._model

    @property
    def dimension(self) -> int:
        """Get the embedding dimension.

        Returns:
            The dimension of the embedding vectors.
        """
        if self._dimension is None:
            self._load_model()
        return self._dimension or 384  # Default for MiniLM

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors (each is a list of floats).
        """
        if not texts:
            return []

        model = self._load_model()

        # Encode texts to embeddings
        embeddings: Any = model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False,
            normalize_embeddings=True,  # Normalize for cosine similarity
        )

        result: list[list[float]] = embeddings.tolist()
        return result

    def embed_query(self, query: str) -> list[float]:
        """Generate embedding for a single query.

        Args:
            query: Query text to embed.

        Returns:
            Embedding vector as list of floats.
        """
        return self.embed([query])[0]

    def embed_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """Generate embeddings in batches for large collections.

        Args:
            texts: List of text strings to embed.
            batch_size: Number of texts per batch.

        Returns:
            List of embedding vectors.
        """
        if not texts:
            return []

        all_embeddings: list[list[float]] = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            batch_embeddings = self.embed(batch)
            all_embeddings.extend(batch_embeddings)

        return all_embeddings


class MockEmbeddings:
    """Mock embeddings for testing without loading the actual model.

    Generates random vectors of the specified dimension.
    """

    def __init__(self, dimension: int = 384) -> None:
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate mock embeddings.

        Uses hash of text to generate deterministic but "random" vectors.
        """
        import hashlib

        embeddings = []
        for text in texts:
            # Use hash to generate deterministic "random" values
            hash_bytes = hashlib.sha256(text.encode()).digest()
            # Convert bytes to floats in [-1, 1] range
            vector = [(b / 128.0) - 1.0 for b in hash_bytes[: self._dimension]]
            # Pad if needed
            while len(vector) < self._dimension:
                vector.extend(vector)
            vector = vector[: self._dimension]
            # Normalize
            norm = sum(v * v for v in vector) ** 0.5
            vector = [v / norm for v in vector] if norm > 0 else vector
            embeddings.append(vector)

        return embeddings

    def embed_query(self, query: str) -> list[float]:
        return self.embed([query])[0]
