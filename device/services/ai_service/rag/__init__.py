"""RAG (Retrieval-Augmented Generation) module for Waycore AI Service.

This module provides document indexing and retrieval capabilities for
the AI assistant, enabling it to answer questions about Waycore features
using actual documentation.

Components:
- chunker: Split documents into searchable chunks
- embeddings: Generate vector embeddings for text
- retriever: Search and retrieve relevant documentation
"""

from __future__ import annotations

from .chunker import DocChunk, MarkdownChunker
from .embeddings import LocalEmbeddings
from .retriever import VectorStore

__all__ = [
    "DocChunk",
    "MarkdownChunker",
    "LocalEmbeddings",
    "VectorStore",
]
