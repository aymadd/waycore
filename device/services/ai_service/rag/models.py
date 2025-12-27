"""Data models for the RAG knowledge base.

This module defines the schema for knowledge entries that can be indexed
and searched. Entries include safety levels and source attribution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class SafetyLevel(str, Enum):
    """Safety classification for knowledge entries.

    Used to determine which warnings to display with results.
    """

    SAFE = "safe"  # General info, no special warnings needed
    CAUTION = "caution"  # Requires care (e.g., knife handling)
    WARNING = "warning"  # Significant risk (e.g., fire starting)
    DANGER = "danger"  # High risk (e.g., plant identification)
    LETHAL = "lethal"  # Life-threatening if wrong (e.g., mushrooms)


class Category(str, Enum):
    """Knowledge categories matching Waycore use cases."""

    SURVIVAL = "survival"
    NAVIGATION = "navigation"
    FIRST_AID = "first_aid"
    PLANTS = "plants"
    WEATHER = "weather"
    KNOTS = "knots"
    SHELTER = "shelter"
    WATER = "water"
    FIRE = "fire"
    SIGNALING = "signaling"
    WILDLIFE = "wildlife"
    EQUIPMENT = "equipment"
    COMMUNICATION = "communication"


# Default safety levels by category
CATEGORY_DEFAULT_SAFETY: dict[Category, SafetyLevel] = {
    Category.SURVIVAL: SafetyLevel.SAFE,
    Category.NAVIGATION: SafetyLevel.SAFE,
    Category.FIRST_AID: SafetyLevel.WARNING,
    Category.PLANTS: SafetyLevel.DANGER,
    Category.WEATHER: SafetyLevel.SAFE,
    Category.KNOTS: SafetyLevel.SAFE,
    Category.SHELTER: SafetyLevel.SAFE,
    Category.WATER: SafetyLevel.CAUTION,
    Category.FIRE: SafetyLevel.CAUTION,
    Category.SIGNALING: SafetyLevel.SAFE,
    Category.WILDLIFE: SafetyLevel.DANGER,
    Category.EQUIPMENT: SafetyLevel.SAFE,
    Category.COMMUNICATION: SafetyLevel.SAFE,
}


@dataclass
class KnowledgeEntry:
    """A single searchable knowledge entry.

    Attributes:
        id: Unique identifier for this entry.
        title: Title/heading for the entry.
        content: Main text content (searchable).
        category: Primary category for filtering.
        subcategory: More specific subcategory.
        safety_level: Risk level for this information.
        safety_notes: Specific safety warnings.
        source_file: Original source file name.
        source_page: Page number in source document.
        source_url: URL of the source (if applicable).
        license: License type (e.g., 'public_domain').
        tags: Tags for search and filtering.
        keywords: Extracted keywords for search.
        embedding: Vector embedding (populated during indexing).
        created_at: When this entry was created.
        updated_at: When this entry was last updated.
    """

    id: str
    title: str
    content: str
    category: Category
    subcategory: str = ""

    # Safety metadata
    safety_level: SafetyLevel = SafetyLevel.SAFE
    safety_notes: str = ""

    # Source tracking
    source_file: str = ""
    source_page: int = 0
    source_url: str = ""
    license: str = "public_domain"

    # Search optimization
    tags: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)

    # Embeddings (populated during indexing)
    embedding: list[float] = field(default_factory=list)

    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "category": (
                self.category.value if isinstance(self.category, Category) else self.category
            ),
            "subcategory": self.subcategory,
            "safety_level": (
                self.safety_level.value
                if isinstance(self.safety_level, SafetyLevel)
                else self.safety_level
            ),
            "safety_notes": self.safety_notes,
            "source_file": self.source_file,
            "source_page": self.source_page,
            "source_url": self.source_url,
            "license": self.license,
            "tags": self.tags,
            "keywords": self.keywords,
            "embedding": self.embedding,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> KnowledgeEntry:
        """Create from dictionary."""
        # Convert category string to enum
        category = data.get("category", "survival")
        if isinstance(category, str):
            try:
                category = Category(category)
            except ValueError:
                category = Category.SURVIVAL

        # Convert safety_level string to enum
        safety_level = data.get("safety_level", "safe")
        if isinstance(safety_level, str):
            try:
                safety_level = SafetyLevel(safety_level)
            except ValueError:
                safety_level = SafetyLevel.SAFE

        return cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            content=data.get("content", ""),
            category=category,
            subcategory=data.get("subcategory", ""),
            safety_level=safety_level,
            safety_notes=data.get("safety_notes", ""),
            source_file=data.get("source_file", ""),
            source_page=data.get("source_page", 0),
            source_url=data.get("source_url", ""),
            license=data.get("license", "public_domain"),
            tags=data.get("tags", []),
            keywords=data.get("keywords", []),
            embedding=data.get("embedding", []),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )


# Safety warning templates by level
SAFETY_WARNINGS: dict[SafetyLevel, str] = {
    SafetyLevel.SAFE: "",
    SafetyLevel.CAUTION: "⚠️ Exercise caution when applying this information.",
    SafetyLevel.WARNING: (
        "⚠️ WARNING: This information involves significant risk. "
        "Always prioritize safety and seek expert guidance when possible."
    ),
    SafetyLevel.DANGER: (
        "🚫 DANGER: This information carries high risk of harm. "
        "Expert verification is REQUIRED before acting on this information. "
        "Misidentification or misapplication can cause serious injury or death."
    ),
    SafetyLevel.LETHAL: (
        "☠️ LETHAL RISK: This information is LIFE-THREATENING if wrong. "
        "NEVER act on this without expert verification. "
        "Many similar-looking items are deadly. When in doubt, DO NOT PROCEED."
    ),
}
