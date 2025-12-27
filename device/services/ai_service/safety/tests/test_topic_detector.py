"""Tests for topic detector module."""

from __future__ import annotations

from device.services.ai_service.safety.topic_detector import (
    CRITICAL_TOPICS,
    add_safety_warning,
    detect_all_topics,
    detect_critical_topic,
    get_all_warnings,
    get_disclaimer_version,
)


class TestDetectCriticalTopic:
    """Tests for detect_critical_topic function."""

    def test_detects_plant_identification(self) -> None:
        """Test detection of plant identification queries."""
        queries = [
            "Can I eat this mushroom?",
            "Is this berry edible?",
            "What plant is this?",
            "Is it safe to eat these berries?",
            "How do I forage for food?",
        ]

        for query in queries:
            result = detect_critical_topic(query)
            assert result is not None, f"Should detect: {query}"
            assert "SAFETY WARNING" in result

    def test_detects_medical_topics(self) -> None:
        """Test detection of medical/first aid queries."""
        queries = [
            "How do I perform first aid?",
            "I have a bleeding wound",
            "What to do for snake bite?",
            "Signs of hypothermia",
            "How to treat frostbite?",
        ]

        for query in queries:
            result = detect_critical_topic(query)
            assert result is not None, f"Should detect: {query}"
            assert "MEDICAL" in result

    def test_detects_navigation_topics(self) -> None:
        """Test detection of navigation/lost queries."""
        queries = [
            "I'm lost in the woods",
            "How do I find my way back?",
            "Navigate to the trailhead",
        ]

        for query in queries:
            result = detect_critical_topic(query)
            assert result is not None, f"Should detect: {query}"
            assert "NAVIGATION" in result

    def test_detects_survival_topics(self) -> None:
        """Test detection of survival queries."""
        queries = [
            "How to survive in the wilderness",
            "How to find water in the desert",
            "How to build shelter",
            "How to start a fire without matches",
        ]

        for query in queries:
            result = detect_critical_topic(query)
            assert result is not None, f"Should detect: {query}"
            assert "SURVIVAL" in result or "SAFETY" in result

    def test_no_detection_for_safe_topics(self) -> None:
        """Test that safe topics don't trigger warnings."""
        queries = [
            "What is the weather like?",
            "Tell me a joke",
            "What time is it?",
            "How does GPS work?",
            "What's my battery level?",
        ]

        for query in queries:
            result = detect_critical_topic(query)
            assert result is None, f"Should not detect: {query}"

    def test_empty_input(self) -> None:
        """Test handling of empty input."""
        assert detect_critical_topic("") is None
        assert detect_critical_topic(None) is None  # type: ignore

    def test_case_insensitive(self) -> None:
        """Test that detection is case-insensitive."""
        assert detect_critical_topic("MUSHROOM") is not None
        assert detect_critical_topic("Mushroom") is not None
        assert detect_critical_topic("mushroom") is not None


class TestDetectAllTopics:
    """Tests for detect_all_topics function."""

    def test_detects_multiple_topics(self) -> None:
        """Test detection of multiple topics in one query."""
        query = "I'm lost and injured, need to find water and shelter"
        topics = detect_all_topics(query)

        assert len(topics) >= 2
        assert "navigation" in topics or "survival" in topics
        assert "medical" in topics

    def test_empty_input(self) -> None:
        """Test handling of empty input."""
        assert detect_all_topics("") == []

    def test_no_topics(self) -> None:
        """Test when no topics are detected."""
        result = detect_all_topics("What is the capital of France?")
        assert result == []


class TestAddSafetyWarning:
    """Tests for add_safety_warning function."""

    def test_adds_warning_for_query(self) -> None:
        """Test that warning is added for critical query."""
        query = "Is this mushroom edible?"
        response = "This appears to be a common mushroom..."

        result = add_safety_warning(response, query)

        assert "SAFETY WARNING" in result
        assert response in result
        assert result.index("SAFETY WARNING") < result.index(response)

    def test_adds_warning_for_response(self) -> None:
        """Test that warning is added for critical response content."""
        query = "Tell me about the forest"
        response = "In survival situations, finding water is critical..."

        result = add_safety_warning(response, query)

        assert "SURVIVAL" in result or "SAFETY" in result
        assert response in result

    def test_no_warning_for_safe_content(self) -> None:
        """Test that no warning is added for safe content."""
        query = "What time is it?"
        response = "The current time is 3:45 PM."

        result = add_safety_warning(response, query)

        assert result == response
        assert "WARNING" not in result

    def test_separator_included(self) -> None:
        """Test that warning is separated from response."""
        query = "Is this berry poisonous?"
        response = "Based on the description..."

        result = add_safety_warning(response, query)

        assert "---" in result  # Separator between warning and response


class TestGetAllWarnings:
    """Tests for get_all_warnings function."""

    def test_returns_all_topics(self) -> None:
        """Test that all topics have warnings."""
        warnings = get_all_warnings()

        assert len(warnings) == len(CRITICAL_TOPICS)
        for topic_name in CRITICAL_TOPICS:
            assert topic_name in warnings
            assert len(warnings[topic_name]) > 0

    def test_warnings_have_emoji(self) -> None:
        """Test that all warnings have warning emoji."""
        warnings = get_all_warnings()

        for warning in warnings.values():
            assert "⚠️" in warning


class TestGetDisclaimerVersion:
    """Tests for get_disclaimer_version function."""

    def test_returns_version_string(self) -> None:
        """Test that a version string is returned."""
        version = get_disclaimer_version()

        assert version is not None
        assert "." in version  # Should be semantic version format


class TestCriticalTopicsConfig:
    """Tests for CRITICAL_TOPICS configuration."""

    def test_all_topics_have_required_fields(self) -> None:
        """Test that all topics have required configuration."""
        for topic_name, config in CRITICAL_TOPICS.items():
            assert "keywords" in config, f"{topic_name} missing keywords"
            assert "warning" in config, f"{topic_name} missing warning"
            assert "severity" in config, f"{topic_name} missing severity"

            assert len(config["keywords"]) > 0, f"{topic_name} has no keywords"
            assert len(config["warning"]) > 50, f"{topic_name} warning too short"

    def test_severity_values_valid(self) -> None:
        """Test that severity values are valid."""
        valid_severities = {"warning", "danger", "info"}

        for topic_name, config in CRITICAL_TOPICS.items():
            assert (
                config["severity"] in valid_severities
            ), f"{topic_name} has invalid severity: {config['severity']}"
