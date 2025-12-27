"""Tests for document chunker."""

from __future__ import annotations

import tempfile
from pathlib import Path

from device.services.ai_service.rag.chunker import DocChunk, MarkdownChunker


class TestDocChunk:
    """Tests for DocChunk dataclass."""

    def test_create_chunk(self) -> None:
        """Test creating a DocChunk."""
        chunk = DocChunk(
            content="Test content",
            source="test.md",
            section="Test Section",
            chunk_id="test_0",
        )

        assert chunk.content == "Test content"
        assert chunk.source == "test.md"
        assert chunk.section == "Test Section"
        assert chunk.chunk_id == "test_0"

    def test_repr(self) -> None:
        """Test DocChunk repr."""
        chunk = DocChunk(
            content="Short content",
            source="test.md",
            section="Section",
            chunk_id="id",
        )

        repr_str = repr(chunk)
        assert "source=" in repr_str
        assert "section=" in repr_str


class TestMarkdownChunker:
    """Tests for MarkdownChunker."""

    def test_chunk_simple_file(self) -> None:
        """Test chunking a simple markdown file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Header\n\nThis is content.\n\n## Subheader\n\nMore content.")
            f.flush()

            chunker = MarkdownChunker()
            chunks = chunker.chunk_file(Path(f.name))

            assert len(chunks) >= 1
            assert all(isinstance(c, DocChunk) for c in chunks)

    def test_chunk_with_sections(self) -> None:
        """Test that sections are properly extracted."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Main\n\nIntro\n\n## Section A\n\nContent A\n\n## Section B\n\nContent B")
            f.flush()

            chunker = MarkdownChunker()
            chunks = chunker.chunk_file(Path(f.name))

            sections = [c.section for c in chunks]
            assert "Main" in sections or "Section A" in sections

    def test_chunk_size_limit(self) -> None:
        """Test that chunks respect size limits."""
        # Create content with many words
        words = " ".join(["word"] * 1000)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(f"# Header\n\n{words}")
            f.flush()

            chunker = MarkdownChunker(chunk_size=100, overlap=10)
            chunks = chunker.chunk_file(Path(f.name))

            # Should be multiple chunks
            assert len(chunks) > 1

    def test_chunk_empty_file(self) -> None:
        """Test chunking an empty file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("")
            f.flush()

            chunker = MarkdownChunker()
            chunks = chunker.chunk_file(Path(f.name))

            assert len(chunks) == 0

    def test_chunk_nonexistent_file(self) -> None:
        """Test chunking a nonexistent file."""
        chunker = MarkdownChunker()
        chunks = chunker.chunk_file(Path("/nonexistent/file.md"))

        assert len(chunks) == 0

    def test_chunk_directory(self) -> None:
        """Test chunking a directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            (Path(tmpdir) / "file1.md").write_text("# File 1\n\nContent 1")
            (Path(tmpdir) / "file2.md").write_text("# File 2\n\nContent 2")
            (Path(tmpdir) / "file.txt").write_text("Not markdown")

            chunker = MarkdownChunker()
            chunks = chunker.chunk_directory(Path(tmpdir))

            # Should have chunks from both .md files
            sources = {c.source for c in chunks}
            assert len(sources) == 2

    def test_make_safe_id(self) -> None:
        """Test safe ID generation."""
        chunker = MarkdownChunker()

        assert chunker._make_safe_id("Simple") == "simple"
        assert chunker._make_safe_id("With Spaces") == "with_spaces"
        assert chunker._make_safe_id("Special!@#$Chars") == "special_chars"
        assert chunker._make_safe_id("___Leading") == "leading"


class TestChunkerOverlap:
    """Tests for chunk overlap behavior."""

    def test_overlap_content(self) -> None:
        """Test that chunks have overlapping content."""
        # Create content with distinct numbered words
        words = " ".join([f"word{i}" for i in range(200)])

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(f"# Header\n\n{words}")
            f.flush()

            chunker = MarkdownChunker(chunk_size=50, overlap=10)
            chunks = chunker.chunk_file(Path(f.name))

            # Check that there are multiple chunks
            assert len(chunks) >= 2

            # The end of first chunk should overlap with start of second
            if len(chunks) >= 2:
                first_words = set(chunks[0].content.split()[-15:])
                second_words = set(chunks[1].content.split()[:15])
                overlap = first_words & second_words
                assert len(overlap) > 0, "Chunks should have overlapping content"
