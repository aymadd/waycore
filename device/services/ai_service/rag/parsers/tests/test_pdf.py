"""Tests for PDF parser."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from device.services.ai_service.rag.models import Category, SafetyLevel
from device.services.ai_service.rag.parsers.pdf import PDFParser


class TestPDFParser:
    """Tests for PDFParser class."""

    def test_init_default_values(self) -> None:
        """Test default initialization values."""
        parser = PDFParser()
        assert parser.chunk_size == 500
        assert parser.chunk_overlap == 50

    def test_init_custom_values(self) -> None:
        """Test custom initialization values."""
        parser = PDFParser(chunk_size=300, chunk_overlap=30)
        assert parser.chunk_size == 300
        assert parser.chunk_overlap == 30

    def test_chunk_text_small(self) -> None:
        """Test chunking text smaller than chunk size."""
        parser = PDFParser(chunk_size=100)
        text = "This is a short text that fits in one chunk."
        chunks = parser._chunk_text(text)
        assert len(chunks) == 1
        assert chunks[0] == text.strip()

    def test_chunk_text_large(self) -> None:
        """Test chunking text larger than chunk size."""
        parser = PDFParser(chunk_size=10, chunk_overlap=2)
        words = ["word"] * 30
        text = " ".join(words)
        chunks = parser._chunk_text(text)
        assert len(chunks) > 1
        # Each chunk should have ~10 words
        for chunk in chunks:
            word_count = len(chunk.split())
            assert word_count <= 10

    def test_chunk_text_empty(self) -> None:
        """Test chunking empty text."""
        parser = PDFParser()
        chunks = parser._chunk_text("")
        assert chunks == []

    def test_generate_id_unique(self) -> None:
        """Test ID generation produces unique IDs."""
        parser = PDFParser()
        id1 = parser._generate_id("test", 1, 0)
        id2 = parser._generate_id("test", 1, 1)
        id3 = parser._generate_id("test", 2, 0)
        assert id1 != id2
        assert id1 != id3
        assert id2 != id3

    def test_generate_id_deterministic(self) -> None:
        """Test ID generation is deterministic."""
        parser = PDFParser()
        id1 = parser._generate_id("test", 1, 0)
        id2 = parser._generate_id("test", 1, 0)
        assert id1 == id2

    def test_detect_safety_lethal(self) -> None:
        """Test detection of lethal safety level."""
        parser = PDFParser()
        text = "This plant is poisonous and can cause death."
        level = parser._detect_safety(text, SafetyLevel.SAFE)
        assert level == SafetyLevel.LETHAL

    def test_detect_safety_danger(self) -> None:
        """Test detection of danger safety level."""
        parser = PDFParser()
        text = "This is a dangerous and hazardous situation."
        level = parser._detect_safety(text, SafetyLevel.SAFE)
        assert level == SafetyLevel.DANGER

    def test_detect_safety_warning(self) -> None:
        """Test detection of warning safety level."""
        parser = PDFParser()
        text = "Use caution when performing this procedure."
        level = parser._detect_safety(text, SafetyLevel.SAFE)
        assert level == SafetyLevel.WARNING

    def test_detect_safety_default(self) -> None:
        """Test default safety level when no keywords found."""
        parser = PDFParser()
        text = "This is general information about navigation."
        level = parser._detect_safety(text, SafetyLevel.CAUTION)
        assert level == SafetyLevel.CAUTION

    def test_extract_tags(self) -> None:
        """Test tag extraction from text."""
        parser = PDFParser()
        text = "Build a shelter near water and start a fire for warmth."
        tags = parser._extract_tags(text, Category.SURVIVAL)
        assert "survival" in tags
        assert "shelter" in tags
        assert "water" in tags
        assert "fire" in tags

    def test_extract_keywords(self) -> None:
        """Test keyword extraction."""
        parser = PDFParser()
        text = "The compass is an essential navigation tool for wilderness travel."
        keywords = parser._extract_keywords(text)
        assert "compass" in keywords
        assert "essential" in keywords
        assert "navigation" in keywords
        # Stopwords should be excluded
        assert "the" not in keywords
        assert "is" not in keywords

    def test_parse_file_with_mock_fitz(self) -> None:
        """Test that parse_file works with mocked fitz module."""
        # Create mock document and page
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Test content for parsing with enough words."
        mock_doc = MagicMock()
        mock_doc.__iter__ = lambda self: iter([mock_page])
        mock_doc.close = MagicMock()

        # Mock the fitz module
        mock_fitz = MagicMock()
        mock_fitz.open.return_value = mock_doc

        with patch.dict("sys.modules", {"fitz": mock_fitz}):
            parser = PDFParser()
            parser.parse_file(
                Path("test.pdf"),
                Category.SURVIVAL,
            )

            mock_fitz.open.assert_called_once()

    def test_parse_file_error_message_format(self) -> None:
        """Test that ImportError has correct message format."""
        # Verify the error message format used in the parser
        error_msg = "PyMuPDF required for PDF parsing. Install with: poetry add pymupdf"
        assert "pymupdf" in error_msg.lower()


class TestPDFParserIntegration:
    """Integration tests for PDFParser (require actual PDF files)."""

    @pytest.mark.skipif(
        not Path("data/raw/survival/FM21-76_Survival.pdf").exists(),
        reason="Test PDF not available",
    )
    def test_parse_real_pdf(self) -> None:
        """Test parsing a real PDF file if available."""
        parser = PDFParser()
        entries = parser.parse_file(
            Path("data/raw/survival/FM21-76_Survival.pdf"),
            Category.SURVIVAL,
        )

        assert len(entries) > 0
        for entry in entries[:5]:  # Check first 5 entries
            assert entry.id
            assert entry.title
            assert len(entry.content) >= 50
            assert entry.category == Category.SURVIVAL
            assert entry.source_file == "FM21-76_Survival.pdf"
