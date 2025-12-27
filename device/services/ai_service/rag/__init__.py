"""RAG (Retrieval-Augmented Generation) module for Waycore AI Service.

This module provides document indexing and retrieval capabilities for
the AI assistant, enabling it to answer questions about Waycore features
using actual documentation and outdoor knowledge.

Components:
- chunker: Split documents into searchable chunks
- embeddings: Generate vector embeddings for text
- retriever: Search and retrieve relevant documentation (ChromaDB)
- store: Hybrid SQLite+Hnswlib store for outdoor knowledge
- search: High-level search interface
- models: Data models for knowledge entries
- parsers: Extract knowledge from PDFs, JSON, CSV
"""

from __future__ import annotations

from .chunker import DocChunk, MarkdownChunker
from .embeddings import LocalEmbeddings
from .models import Category, KnowledgeEntry, SafetyLevel
from .retriever import VectorStore
from .search import OutdoorKnowledgeSearch
from .store import HybridKnowledgeStore

__all__ = [
    # Document chunking
    "DocChunk",
    "MarkdownChunker",
    # Embeddings
    "LocalEmbeddings",
    # Vector stores
    "VectorStore",  # ChromaDB (docs)
    "HybridKnowledgeStore",  # SQLite+Hnswlib (outdoor)
    # Models
    "Category",
    "KnowledgeEntry",
    "SafetyLevel",
    # Search
    "OutdoorKnowledgeSearch",
]
