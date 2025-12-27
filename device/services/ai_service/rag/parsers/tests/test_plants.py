"""Tests for plant data parser."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from device.services.ai_service.rag.models import Category, SafetyLevel
from device.services.ai_service.rag.parsers.plants import PlantDataParser


class TestPlantDataParser:
    """Tests for PlantDataParser class."""

    def test_determine_safety_with_hazards(self) -> None:
        """Test safety determination with known hazards."""
        parser = PlantDataParser()
        plant = {"known_hazards": "Contains toxic compounds that can cause death"}
        level = parser._determine_safety(plant)
        assert level == SafetyLevel.LETHAL

    def test_determine_safety_high_edibility(self) -> None:
        """Test safety determination with high edibility rating."""
        parser = PlantDataParser()
        plant = {"edibility_rating": 5}
        level = parser._determine_safety(plant)
        assert level == SafetyLevel.CAUTION

    def test_determine_safety_low_edibility(self) -> None:
        """Test safety determination with low edibility rating."""
        parser = PlantDataParser()
        plant = {"edibility_rating": 1}
        level = parser._determine_safety(plant)
        assert level == SafetyLevel.LETHAL

    def test_determine_safety_unknown(self) -> None:
        """Test safety determination with no data defaults to lethal."""
        parser = PlantDataParser()
        plant = {}
        level = parser._determine_safety(plant)
        assert level == SafetyLevel.LETHAL

    def test_build_plant_content(self) -> None:
        """Test building content string from plant data."""
        parser = PlantDataParser()
        plant = {
            "latin_name": "Taraxacum officinale",
            "common_name": "Dandelion",
            "family": "Asteraceae",
            "edible_parts": "Leaves, roots, flowers",
            "medicinal_uses": "Digestive aid, diuretic",
            "habitat": "Lawns, meadows, roadsides",
        }
        content = parser._build_plant_content(plant)

        assert "Taraxacum officinale" in content
        assert "Dandelion" in content
        assert "Asteraceae" in content
        assert "Leaves, roots, flowers" in content
        assert "Digestive aid" in content

    def test_build_safety_notes_with_hazards(self) -> None:
        """Test safety notes include hazards."""
        parser = PlantDataParser()
        plant = {"known_hazards": "Causes skin irritation"}
        notes = parser._build_safety_notes(plant)

        assert "HAZARDS" in notes
        assert "skin irritation" in notes
        assert "verify identification" in notes.lower()

    def test_build_plant_tags_edible(self) -> None:
        """Test tag generation for edible plant."""
        parser = PlantDataParser()
        plant = {"edibility_rating": 4, "medicinal_rating": 3}
        tags = parser._build_plant_tags(plant)

        assert "plant" in tags
        assert "edible" in tags
        assert "commonly_eaten" in tags
        assert "medicinal" in tags

    def test_build_plant_tags_hazardous(self) -> None:
        """Test tag generation for hazardous plant."""
        parser = PlantDataParser()
        plant = {"known_hazards": "Toxic"}
        tags = parser._build_plant_tags(plant)

        assert "hazardous" in tags
        assert "toxic" in tags

    def test_extract_plant_keywords(self) -> None:
        """Test keyword extraction from plant data."""
        parser = PlantDataParser()
        plant = {
            "common_name": "Common Dandelion",
            "latin_name": "Taraxacum officinale",
            "family": "Asteraceae",
        }
        keywords = parser._extract_plant_keywords(plant)

        assert "common" in keywords
        assert "dandelion" in keywords
        assert "taraxacum" in keywords
        assert "asteraceae" in keywords

    def test_parse_pfaf_json_list_format(self) -> None:
        """Test parsing PFAF JSON in list format."""
        parser = PlantDataParser()

        test_data = [
            {
                "latin_name": "Taraxacum officinale",
                "common_name": "Dandelion",
                "family": "Asteraceae",
                "edibility_rating": 4,
            },
            {
                "latin_name": "Urtica dioica",
                "common_name": "Stinging Nettle",
                "family": "Urticaceae",
                "edibility_rating": 3,
            },
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            temp_path = Path(f.name)

        try:
            entries = parser.parse_pfaf_json(temp_path)

            assert len(entries) == 2
            assert entries[0].title == "Dandelion"
            assert entries[0].category == Category.PLANTS
            assert entries[1].title == "Stinging Nettle"
        finally:
            temp_path.unlink()

    def test_parse_pfaf_json_dict_format(self) -> None:
        """Test parsing PFAF JSON in dict format."""
        parser = PlantDataParser()

        test_data = {
            "plants": [
                {
                    "latin_name": "Allium ursinum",
                    "common_name": "Wild Garlic",
                    "edibility_rating": 5,
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            temp_path = Path(f.name)

        try:
            entries = parser.parse_pfaf_json(temp_path)

            assert len(entries) == 1
            assert entries[0].title == "Wild Garlic"
        finally:
            temp_path.unlink()

    def test_parse_usda_csv(self) -> None:
        """Test parsing USDA Plants CSV."""
        parser = PlantDataParser()

        csv_content = """Symbol,Scientific Name,Common Name,Family
TAROF,Taraxacum officinale,Dandelion,Asteraceae
URTDI,Urtica dioica,Stinging Nettle,Urticaceae
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            temp_path = Path(f.name)

        try:
            entries = parser.parse_usda_csv(temp_path)

            assert len(entries) == 2
            assert entries[0].title == "Dandelion"
            assert entries[0].id == "usda_tarof"
            assert entries[0].category == Category.PLANTS
            assert entries[0].safety_level == SafetyLevel.DANGER
            assert entries[1].title == "Stinging Nettle"
        finally:
            temp_path.unlink()

    def test_plant_entries_have_required_fields(self) -> None:
        """Test that plant entries have all required fields."""
        parser = PlantDataParser()

        test_data = [
            {
                "latin_name": "Test Plant",
                "common_name": "Test Common Name",
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            temp_path = Path(f.name)

        try:
            entries = parser.parse_pfaf_json(temp_path)

            entry = entries[0]
            assert entry.id
            assert entry.title
            assert entry.content
            assert entry.category == Category.PLANTS
            assert entry.safety_level in SafetyLevel
            assert entry.safety_notes
            assert entry.source_url == "https://pfaf.org/"
            assert entry.license == "cc_by_nc_sa"
        finally:
            temp_path.unlink()
