"""Structured data parsers for JSON and CSV formats.

Generic parsers for structured data that doesn't need specialized handling.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Callable

from ..models import Category, KnowledgeEntry, SafetyLevel


class JSONParser:
    """Parse JSON data files into knowledge entries.

    Supports various JSON structures with customizable field mapping.
    """

    def __init__(
        self,
        id_field: str = "id",
        title_field: str = "title",
        content_field: str = "content",
        category_field: str | None = None,
    ) -> None:
        """Initialize the JSON parser.

        Args:
            id_field: Field name for entry ID.
            title_field: Field name for title.
            content_field: Field name for main content.
            category_field: Field name for category (optional).
        """
        self.id_field = id_field
        self.title_field = title_field
        self.content_field = content_field
        self.category_field = category_field

    def parse_file(
        self,
        json_path: Path,
        default_category: Category,
        default_safety: SafetyLevel = SafetyLevel.SAFE,
        content_builder: Callable[[dict[str, Any]], str] | None = None,
    ) -> list[KnowledgeEntry]:
        """Parse a JSON file into knowledge entries.

        Args:
            json_path: Path to JSON file.
            default_category: Default category for entries.
            default_safety: Default safety level.
            content_builder: Optional function to build content from record.

        Returns:
            List of KnowledgeEntry objects.
        """
        entries: list[KnowledgeEntry] = []

        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        # Handle various JSON structures
        if isinstance(data, list):
            records = data
        elif isinstance(data, dict):
            # Look for common array keys
            for key in ["data", "items", "records", "entries", "results"]:
                if key in data and isinstance(data[key], list):
                    records = data[key]
                    break
            else:
                # Single object - wrap in list
                records = [data]
        else:
            return entries

        for i, record in enumerate(records):
            if not isinstance(record, dict):
                continue

            # Get or generate ID
            entry_id = str(record.get(self.id_field, f"json_{json_path.stem}_{i}"))

            # Get title
            title = str(record.get(self.title_field, f"Entry {i + 1}"))

            # Build content
            if content_builder:
                content = content_builder(record)
            else:
                content = str(record.get(self.content_field, ""))
                if not content:
                    # Fall back to JSON representation of the record
                    content = json.dumps(record, indent=2)

            # Get category
            if self.category_field and self.category_field in record:
                try:
                    category = Category(record[self.category_field])
                except ValueError:
                    category = default_category
            else:
                category = default_category

            entries.append(
                KnowledgeEntry(
                    id=entry_id,
                    title=title,
                    content=content,
                    category=category,
                    safety_level=default_safety,
                    source_file=json_path.name,
                    license="unknown",
                )
            )

        return entries


class CSVParser:
    """Parse CSV data files into knowledge entries.

    Supports CSV files with customizable column mapping.
    """

    def __init__(
        self,
        id_column: str | None = None,
        title_column: str | None = None,
        content_columns: list[str] | None = None,
    ) -> None:
        """Initialize the CSV parser.

        Args:
            id_column: Column name for entry ID.
            title_column: Column name for title.
            content_columns: List of columns to include in content.
        """
        self.id_column = id_column
        self.title_column = title_column
        self.content_columns = content_columns

    def parse_file(
        self,
        csv_path: Path,
        default_category: Category,
        default_safety: SafetyLevel = SafetyLevel.SAFE,
        content_builder: Callable[[dict[str, Any]], str] | None = None,
    ) -> list[KnowledgeEntry]:
        """Parse a CSV file into knowledge entries.

        Args:
            csv_path: Path to CSV file.
            default_category: Default category for entries.
            default_safety: Default safety level.
            content_builder: Optional function to build content from row.

        Returns:
            List of KnowledgeEntry objects.
        """
        entries: list[KnowledgeEntry] = []

        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for i, row in enumerate(reader):
                # Get or generate ID
                if self.id_column and self.id_column in row:
                    entry_id = f"csv_{row[self.id_column]}"
                else:
                    entry_id = f"csv_{csv_path.stem}_{i}"

                # Get title
                if self.title_column and self.title_column in row:
                    title = row[self.title_column]
                else:
                    # Use first non-empty column as title
                    title = next((v for v in row.values() if v), f"Row {i + 1}")

                # Build content
                if content_builder:
                    content = content_builder(row)
                elif self.content_columns:
                    parts = []
                    for col in self.content_columns:
                        if col in row and row[col]:
                            parts.append(f"{col}: {row[col]}")
                    content = "\n".join(parts)
                else:
                    # Include all columns
                    parts = [f"{k}: {v}" for k, v in row.items() if v]
                    content = "\n".join(parts)

                entries.append(
                    KnowledgeEntry(
                        id=entry_id,
                        title=title,
                        content=content,
                        category=default_category,
                        safety_level=default_safety,
                        source_file=csv_path.name,
                        license="unknown",
                    )
                )

        return entries
