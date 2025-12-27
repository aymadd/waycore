"""Plant data parser for extracting knowledge from plant databases.

Handles PFAF (Plants For A Future) JSON exports and USDA Plants CSV data.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from ..models import Category, KnowledgeEntry, SafetyLevel


class PlantDataParser:
    """Parse plant databases into knowledge entries.

    All plant entries default to DANGER safety level since
    misidentification can be life-threatening.
    """

    def parse_pfaf_json(self, json_path: Path) -> list[KnowledgeEntry]:
        """Parse Plants For A Future database export.

        Args:
            json_path: Path to PFAF JSON export file.

        Returns:
            List of KnowledgeEntry objects.
        """
        entries: list[KnowledgeEntry] = []

        with open(json_path, encoding="utf-8") as f:
            plants = json.load(f)

        # Handle both list and dict formats
        if isinstance(plants, dict):
            plants = plants.get("plants", [])

        for plant in plants:
            safety = self._determine_safety(plant)
            content = self._build_plant_content(plant)

            # Generate ID from latin name
            latin_name = plant.get("latin_name", plant.get("scientific_name", "unknown"))
            entry_id = f"plant_{latin_name.replace(' ', '_').replace('.', '').lower()}"

            entries.append(
                KnowledgeEntry(
                    id=entry_id,
                    title=plant.get("common_name", latin_name),
                    content=content,
                    category=Category.PLANTS,
                    subcategory=plant.get("family", ""),
                    safety_level=safety,
                    safety_notes=self._build_safety_notes(plant),
                    source_url="https://pfaf.org/",
                    license="cc_by_nc_sa",
                    tags=self._build_plant_tags(plant),
                    keywords=self._extract_plant_keywords(plant),
                )
            )

        return entries

    def parse_usda_csv(self, csv_path: Path) -> list[KnowledgeEntry]:
        """Parse USDA Plants Database CSV export.

        Args:
            csv_path: Path to USDA Plants CSV file.

        Returns:
            List of KnowledgeEntry objects.
        """
        entries: list[KnowledgeEntry] = []

        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                # Get identifiers
                symbol = row.get("Symbol", row.get("symbol", ""))
                scientific_name = row.get("Scientific Name", row.get("scientific_name", ""))
                common_name = row.get("Common Name", row.get("common_name", ""))

                if not symbol and not scientific_name:
                    continue

                entry_id = f"usda_{symbol.lower()}" if symbol else f"usda_{hash(scientific_name)}"

                entries.append(
                    KnowledgeEntry(
                        id=entry_id,
                        title=common_name or scientific_name,
                        content=self._build_usda_content(row),
                        category=Category.PLANTS,
                        subcategory=row.get("Family", row.get("family", "")),
                        safety_level=SafetyLevel.DANGER,  # Default cautious for plants
                        safety_notes=(
                            "Verify identification before any use. "
                            "Many plants have toxic look-alikes."
                        ),
                        source_url="https://plants.usda.gov/",
                        license="public_domain",
                        tags=["plant", "usda"],
                        keywords=[w.lower() for w in common_name.split() if len(w) > 3],
                    )
                )

        return entries

    def _determine_safety(self, plant: dict[str, Any]) -> SafetyLevel:
        """Determine safety level from plant data.

        Args:
            plant: Plant data dictionary.

        Returns:
            SafetyLevel for this plant.
        """
        # Check for known hazards
        hazards = plant.get("known_hazards", plant.get("hazards", ""))
        if hazards:
            hazards_lower = hazards.lower()
            if any(w in hazards_lower for w in ["fatal", "deadly", "lethal", "death"]):
                return SafetyLevel.LETHAL
            return SafetyLevel.LETHAL  # Any hazard = lethal for plants

        # Check edibility rating (PFAF uses 0-5 scale)
        edibility = plant.get("edibility_rating", plant.get("edibility", 0))
        try:
            edibility = int(edibility)
        except (ValueError, TypeError):
            edibility = 0

        if edibility >= 4:
            return SafetyLevel.CAUTION  # Well-known edible, still needs verification
        elif edibility >= 2:
            return SafetyLevel.DANGER
        else:
            return SafetyLevel.LETHAL  # Unknown or low edibility = assume dangerous

    def _build_plant_content(self, plant: dict[str, Any]) -> str:
        """Build searchable content string from plant data.

        Args:
            plant: Plant data dictionary.

        Returns:
            Formatted content string.
        """
        parts = []

        # Names
        latin = plant.get("latin_name", plant.get("scientific_name", "Unknown"))
        common = plant.get("common_name", "Unknown")
        parts.append(f"Scientific name: {latin}")
        parts.append(f"Common name: {common}")

        # Family
        family = plant.get("family", "")
        if family:
            parts.append(f"Family: {family}")

        # Edibility
        edible_parts = plant.get("edible_parts", plant.get("edible_uses", ""))
        if edible_parts:
            parts.append(f"Edible parts: {edible_parts}")

        # Medicinal uses
        medicinal = plant.get("medicinal_uses", plant.get("medicinal", ""))
        if medicinal:
            parts.append(f"Medicinal uses: {medicinal}")

        # Habitat
        habitat = plant.get("habitat", plant.get("habitats", ""))
        if habitat:
            parts.append(f"Habitat: {habitat}")

        # Physical description
        height = plant.get("height", "")
        if height:
            parts.append(f"Height: {height}")

        # Hazards (important!)
        hazards = plant.get("known_hazards", plant.get("hazards", ""))
        if hazards:
            parts.append(f"KNOWN HAZARDS: {hazards}")

        return "\n".join(parts)

    def _build_usda_content(self, row: dict[str, Any]) -> str:
        """Build content string from USDA CSV row.

        Args:
            row: CSV row dictionary.

        Returns:
            Formatted content string.
        """
        parts = []

        # Core fields
        for key in [
            "Scientific Name",
            "Common Name",
            "Family",
            "Duration",
            "Growth Habit",
            "Native Status",
            "State and Province",
        ]:
            value = row.get(key, row.get(key.lower().replace(" ", "_"), ""))
            if value:
                parts.append(f"{key}: {value}")

        return "\n".join(parts) if parts else "Plant data from USDA database."

    def _build_safety_notes(self, plant: dict[str, Any]) -> str:
        """Build safety warning string for a plant.

        Args:
            plant: Plant data dictionary.

        Returns:
            Safety notes string.
        """
        notes = []

        hazards = plant.get("known_hazards", plant.get("hazards", ""))
        if hazards:
            notes.append(f"HAZARDS: {hazards}")

        notes.append("Always verify identification with multiple authoritative sources.")
        notes.append("Many plants have DEADLY look-alikes.")
        notes.append("When in doubt, DO NOT consume.")

        return " ".join(notes)

    def _build_plant_tags(self, plant: dict[str, Any]) -> list[str]:
        """Build tags for a plant entry.

        Args:
            plant: Plant data dictionary.

        Returns:
            List of tags.
        """
        tags = ["plant"]

        # Edibility
        edibility = plant.get("edibility_rating", plant.get("edibility", 0))
        try:
            edibility = int(edibility)
        except (ValueError, TypeError):
            edibility = 0

        if edibility > 0:
            tags.append("edible")
        if edibility >= 4:
            tags.append("commonly_eaten")

        # Medicinal
        medicinal = plant.get("medicinal_rating", plant.get("medicinal", 0))
        try:
            medicinal = int(medicinal)
        except (ValueError, TypeError):
            medicinal = 0

        if medicinal > 0:
            tags.append("medicinal")

        # Hazards
        if plant.get("known_hazards"):
            tags.append("hazardous")
            tags.append("toxic")

        return tags

    def _extract_plant_keywords(self, plant: dict[str, Any]) -> list[str]:
        """Extract keywords from plant data.

        Args:
            plant: Plant data dictionary.

        Returns:
            List of keywords.
        """
        keywords: list[str] = []

        # Extract from common name
        common = plant.get("common_name", "")
        if common:
            keywords.extend(w.lower() for w in common.split() if len(w) > 3)

        # Extract from latin name
        latin = plant.get("latin_name", plant.get("scientific_name", ""))
        if latin:
            keywords.extend(w.lower() for w in latin.split() if len(w) > 3)

        # Family
        family = plant.get("family", "")
        if family:
            keywords.append(family.lower())

        return list(set(keywords))[:15]
