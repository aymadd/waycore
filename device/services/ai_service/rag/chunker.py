"""Document chunker for RAG indexing.

This module provides utilities to split markdown documents into
searchable chunks while preserving section context.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DocChunk:
    """A chunk of documentation with metadata.

    Attributes:
        content: The text content of the chunk.
        source: Path to the source file.
        section: Section heading this chunk belongs to.
        chunk_id: Unique identifier for this chunk.
    """

    content: str
    source: str
    section: str
    chunk_id: str

    def __repr__(self) -> str:
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return (
            f"DocChunk(source={self.source!r}, section={self.section!r}, "
            f"content={content_preview!r})"
        )


class MarkdownChunker:
    """Chunk markdown documents by sections for RAG indexing.

    Splits markdown files by headers and creates overlapping chunks
    of configurable size for better retrieval.

    Args:
        chunk_size: Target number of words per chunk.
        overlap: Number of words to overlap between chunks.
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_file(self, path: Path) -> list[DocChunk]:
        """Chunk a markdown file into DocChunk objects.

        Args:
            path: Path to the markdown file.

        Returns:
            List of DocChunk objects.
        """
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            return []

        sections = self._split_by_headers(content)

        chunks = []
        for section_title, section_content in sections:
            # Clean up the section title for use in chunk_id
            safe_title = self._make_safe_id(section_title)
            section_chunks = self._chunk_text(section_content)

            for i, chunk_text in enumerate(section_chunks):
                if not chunk_text.strip():
                    continue

                chunks.append(
                    DocChunk(
                        content=chunk_text,
                        source=str(path),
                        section=section_title,
                        chunk_id=f"{path.stem}_{safe_title}_{i}",
                    )
                )

        return chunks

    def chunk_directory(
        self, directory: Path, extensions: tuple[str, ...] = (".md",)
    ) -> list[DocChunk]:
        """Chunk all matching files in a directory.

        Args:
            directory: Directory to scan.
            extensions: File extensions to include.

        Returns:
            List of DocChunk objects from all files.
        """
        chunks: list[DocChunk] = []

        if not directory.exists():
            return chunks

        for path in directory.rglob("*"):
            if path.is_file() and path.suffix in extensions:
                file_chunks = self.chunk_file(path)
                chunks.extend(file_chunks)

        return chunks

    def _split_by_headers(self, content: str) -> list[tuple[str, str]]:
        """Split content by markdown headers (h1-h3).

        Args:
            content: Markdown content.

        Returns:
            List of (section_title, section_content) tuples.
        """
        # Match h1, h2, h3 headers
        pattern = r"^(#{1,3})\s+(.+)$"
        sections: list[tuple[str, str]] = []
        current_title = "Introduction"
        current_content: list[str] = []

        for line in content.split("\n"):
            match = re.match(pattern, line)
            if match:
                # Save previous section if it has content
                if current_content:
                    section_text = "\n".join(current_content).strip()
                    if section_text:
                        sections.append((current_title, section_text))

                # Start new section
                current_title = match.group(2).strip()
                current_content = []
            else:
                current_content.append(line)

        # Don't forget the last section
        if current_content:
            section_text = "\n".join(current_content).strip()
            if section_text:
                sections.append((current_title, section_text))

        return sections

    def _chunk_text(self, text: str) -> list[str]:
        """Chunk text into overlapping pieces by word count.

        Args:
            text: Text to chunk.

        Returns:
            List of text chunks.
        """
        words = text.split()
        if not words:
            return []

        # If text is smaller than chunk size, return as single chunk
        if len(words) <= self.chunk_size:
            return [text]

        chunks = []
        step = max(1, self.chunk_size - self.overlap)

        for i in range(0, len(words), step):
            chunk = " ".join(words[i : i + self.chunk_size])
            if chunk.strip():
                chunks.append(chunk)

            # Stop if we've covered all content
            if i + self.chunk_size >= len(words):
                break

        return chunks

    def _make_safe_id(self, text: str) -> str:
        """Convert text to a safe identifier for chunk IDs.

        Args:
            text: Text to convert.

        Returns:
            Safe identifier string.
        """
        # Replace non-alphanumeric with underscores
        safe = re.sub(r"[^a-zA-Z0-9]+", "_", text.lower())
        # Remove leading/trailing underscores
        safe = safe.strip("_")
        # Limit length
        return safe[:50]
