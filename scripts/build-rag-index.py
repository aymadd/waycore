#!/usr/bin/env python3
"""Build RAG index from documentation.

This script indexes all markdown files in the docs/ directory
into the vector store for RAG search.

Usage:
    python scripts/build-rag-index.py [--docs-dir DOCS_DIR] [--clear]
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from device.services.ai_service.rag import MarkdownChunker, VectorStore

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def main() -> int:
    """Build the RAG index."""
    parser = argparse.ArgumentParser(description="Build RAG index from documentation")
    parser.add_argument(
        "--docs-dir",
        default="docs",
        help="Path to documentation directory (default: docs)",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing index before building",
    )
    parser.add_argument(
        "--persist-dir",
        default="/app/data/rag",
        help="Directory to persist the index (default: /app/data/rag)",
    )
    args = parser.parse_args()

    docs_path = Path(args.docs_dir)
    if not docs_path.exists():
        logger.error(f"Documentation directory not found: {docs_path}")
        return 1

    logger.info("Building RAG index for documentation...")
    logger.info(f"  Source: {docs_path}")
    logger.info(f"  Persist: {args.persist_dir}")

    # Initialize store
    store = VectorStore(persist_dir=args.persist_dir)

    if args.clear:
        logger.info("Clearing existing index...")
        store.clear()

    # Check current count
    current = store.count()
    if current > 0:
        logger.info(f"  Current index size: {current} chunks")

    # Chunk documents
    chunker = MarkdownChunker(chunk_size=400, overlap=50)
    all_chunks = []

    md_files = list(docs_path.rglob("*.md"))
    logger.info(f"Found {len(md_files)} markdown files")

    for md_file in md_files:
        relative = md_file.relative_to(docs_path)
        chunks = chunker.chunk_file(md_file)

        if chunks:
            logger.info(f"  {relative}: {len(chunks)} chunks")
            all_chunks.extend(chunks)

    if not all_chunks:
        logger.warning("No chunks created. Check if docs directory has markdown files.")
        return 1

    # Add to store
    logger.info(f"\nAdding {len(all_chunks)} chunks to vector store...")
    store.add_chunks(all_chunks)

    final_count = store.count()
    logger.info("\nIndex build complete!")
    logger.info(f"  Total chunks: {final_count}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
