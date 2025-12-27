"""PDF parser for extracting knowledge from military manuals and guides.

Uses PyMuPDF (fitz) for text extraction - lightweight and works on ARM64.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from ..models import CATEGORY_DEFAULT_SAFETY, Category, KnowledgeEntry, SafetyLevel


class PDFParser:
    """Parse PDF documents into knowledge entries.

    Extracts text from PDFs, detects chapter/section structure,
    and chunks content into searchable entries.

    Args:
        chunk_size: Target number of words per chunk.
        chunk_overlap: Number of words to overlap between chunks.
    """

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def parse_file(
        self,
        pdf_path: Path,
        category: Category,
        default_safety: SafetyLevel | None = None,
        source_url: str = "",
        license_type: str = "public_domain",
    ) -> list[KnowledgeEntry]:
        """Parse a PDF file into knowledge entries.

        Args:
            pdf_path: Path to the PDF file.
            category: Category for all entries from this file.
            default_safety: Default safety level (uses category default if None).
            source_url: URL where the source was obtained.
            license_type: License type for the content.

        Returns:
            List of KnowledgeEntry objects.
        """
        try:
            import fitz  # PyMuPDF
        except ImportError as e:
            raise ImportError(
                "PyMuPDF required for PDF parsing. Install with: poetry add pymupdf"
            ) from e

        if default_safety is None:
            default_safety = CATEGORY_DEFAULT_SAFETY.get(category, SafetyLevel.SAFE)

        entries: list[KnowledgeEntry] = []
        doc = fitz.open(pdf_path)

        current_chapter = ""
        current_section = ""

        for page_num, page in enumerate(doc, start=1):
            text = page.get_text()

            if not text.strip():
                continue

            # Detect chapter headers (CHAPTER 1, Chapter 1: ..., etc.)
            chapter_match = re.search(r"CHAPTER\s+(\d+)[:\s-]*(.+?)(?:\n|$)", text, re.IGNORECASE)
            if chapter_match:
                current_chapter = chapter_match.group(2).strip()
                # Clean up chapter title
                current_chapter = re.sub(r"\s+", " ", current_chapter)
                current_chapter = current_chapter[:100]  # Limit length

            # Detect section headers (ALL CAPS lines at start)
            section_match = re.search(r"^([A-Z][A-Z\s]{5,50})$", text, re.MULTILINE)
            if section_match:
                current_section = section_match.group(1).strip().title()

            # Chunk the page content
            chunks = self._chunk_text(text)

            for i, chunk_text in enumerate(chunks):
                # Skip tiny or empty chunks
                if len(chunk_text.strip()) < 50:
                    continue

                entry_id = self._generate_id(pdf_path.stem, page_num, i)

                # Build title from chapter and section
                if current_chapter and current_section:
                    title = f"{current_chapter} - {current_section}"
                elif current_chapter:
                    title = current_chapter
                elif current_section:
                    title = current_section
                else:
                    title = f"{pdf_path.stem} - Page {page_num}"

                # Detect safety level from content
                detected_safety = self._detect_safety(chunk_text, default_safety)

                entries.append(
                    KnowledgeEntry(
                        id=entry_id,
                        title=title,
                        content=chunk_text,
                        category=category,
                        subcategory=current_section,
                        safety_level=detected_safety,
                        safety_notes=self._generate_safety_notes(detected_safety),
                        source_file=pdf_path.name,
                        source_page=page_num,
                        source_url=source_url,
                        license=license_type,
                        tags=self._extract_tags(chunk_text, category),
                        keywords=self._extract_keywords(chunk_text),
                    )
                )

        doc.close()
        return entries

    def _chunk_text(self, text: str) -> list[str]:
        """Split text into overlapping chunks by word count.

        Args:
            text: Text to chunk.

        Returns:
            List of text chunks.
        """
        # Clean up the text
        text = re.sub(r"\s+", " ", text)
        words = text.split()

        if not words:
            return []

        # If text is smaller than chunk size, return as single chunk
        if len(words) <= self.chunk_size:
            return [text.strip()]

        chunks = []
        step = max(1, self.chunk_size - self.chunk_overlap)

        for i in range(0, len(words), step):
            chunk = " ".join(words[i : i + self.chunk_size])
            if chunk.strip():
                chunks.append(chunk.strip())

            # Stop if we've covered all content
            if i + self.chunk_size >= len(words):
                break

        return chunks

    def _generate_id(self, source: str, page: int, chunk: int) -> str:
        """Generate unique ID for an entry.

        Args:
            source: Source file stem.
            page: Page number.
            chunk: Chunk index on the page.

        Returns:
            12-character hash-based ID.
        """
        raw = f"{source}:{page}:{chunk}"
        return hashlib.md5(raw.encode()).hexdigest()[:12]

    def _detect_safety(self, text: str, default: SafetyLevel) -> SafetyLevel:
        """Detect safety level from content keywords.

        Args:
            text: Text to analyze.
            default: Default safety level if no keywords found.

        Returns:
            Detected SafetyLevel.
        """
        text_lower = text.lower()

        # Lethal indicators
        lethal_words = ["poison", "poisonous", "toxic", "deadly", "fatal", "lethal", "death"]
        if any(w in text_lower for w in lethal_words):
            return SafetyLevel.LETHAL

        # Danger indicators
        danger_words = ["dangerous", "hazard", "hazardous", "venomous", "venom"]
        if any(w in text_lower for w in danger_words):
            return SafetyLevel.DANGER

        # Warning indicators
        warning_words = ["warning", "caution", "careful", "risk", "injury", "harm"]
        if any(w in text_lower for w in warning_words):
            return SafetyLevel.WARNING

        return default

    def _generate_safety_notes(self, level: SafetyLevel) -> str:
        """Generate safety notes based on level.

        Args:
            level: Safety level.

        Returns:
            Safety note string.
        """
        notes = {
            SafetyLevel.SAFE: "",
            SafetyLevel.CAUTION: "Practice in controlled conditions first.",
            SafetyLevel.WARNING: "Seek expert guidance when possible.",
            SafetyLevel.DANGER: "Expert verification required.",
            SafetyLevel.LETHAL: "NEVER proceed without expert verification.",
        }
        return notes.get(level, "")

    def _extract_tags(self, text: str, category: Category) -> list[str]:
        """Extract relevant tags from content.

        Args:
            text: Text to analyze.
            category: Category for context.

        Returns:
            List of relevant tags.
        """
        # Domain-specific terms to look for
        survival_terms = {
            "fire",
            "water",
            "shelter",
            "food",
            "signal",
            "navigate",
            "navigation",
            "compass",
            "map",
            "first aid",
            "snake",
            "plant",
            "edible",
            "poison",
            "trap",
            "knot",
            "rope",
            "weather",
            "storm",
            "cold",
            "heat",
            "hypothermia",
            "dehydration",
            "wound",
            "bleeding",
            "fracture",
            "splint",
        }

        text_lower = text.lower()
        found_tags = [term for term in survival_terms if term in text_lower]

        # Add category as a tag
        found_tags.append(category.value)

        return list(set(found_tags))[:10]  # Limit to 10 tags

    def _extract_keywords(self, text: str) -> list[str]:
        """Extract searchable keywords from text.

        Args:
            text: Text to analyze.

        Returns:
            List of keywords.
        """
        # Common stopwords to exclude
        stopwords = {
            "the",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "must",
            "shall",
            "can",
            "need",
            "to",
            "of",
            "and",
            "or",
            "in",
            "on",
            "at",
            "for",
            "with",
            "by",
            "from",
            "as",
            "into",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
            "between",
            "under",
            "again",
            "further",
            "then",
            "once",
            "here",
            "there",
            "when",
            "where",
            "why",
            "how",
            "all",
            "each",
            "few",
            "more",
            "most",
            "other",
            "some",
            "such",
            "no",
            "nor",
            "not",
            "only",
            "own",
            "same",
            "so",
            "than",
            "too",
            "very",
            "just",
            "but",
            "if",
            "this",
            "that",
            "these",
            "those",
            "which",
            "who",
            "whom",
            "what",
            "whose",
            "it",
            "its",
            "you",
            "your",
            "they",
            "them",
            "their",
            "we",
            "us",
            "our",
            "he",
            "him",
            "his",
            "she",
            "her",
        }

        # Extract words 4+ characters
        words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())

        # Filter and deduplicate
        keywords = list(set(w for w in words if w not in stopwords))

        return keywords[:20]  # Limit to 20 keywords
