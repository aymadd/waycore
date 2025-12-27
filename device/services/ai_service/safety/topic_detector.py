"""
Topic detector for critical safety topics in AI responses.

This module detects when AI queries or responses touch on sensitive topics
that require safety warnings, such as plant identification, medical advice,
navigation, and survival situations.
"""

from __future__ import annotations

DISCLAIMER_VERSION = "1.0.0"

CRITICAL_TOPICS: dict[str, dict[str, str | list[str]]] = {
    "plant_identification": {
        "keywords": [
            "edible",
            "eat this",
            "mushroom",
            "berry",
            "berries",
            "forage",
            "foraging",
            "poisonous plant",
            "toxic plant",
            "wild plant",
            "identify this plant",
            "safe to eat",
            "what plant",
            "this plant",
        ],
        "warning": (
            "⚠️ **SAFETY WARNING: PLANT IDENTIFICATION**\n\n"
            "AI plant identification can be INCORRECT and potentially FATAL. "
            "Many poisonous species closely resemble edible ones. "
            "NEVER consume any plant, mushroom, or berry based solely on AI identification. "
            "Always consult multiple expert field guides and local experts before consuming "
            "any wild food."
        ),
        "severity": "danger",
    },
    "medical": {
        "keywords": [
            "first aid",
            "injury",
            "injured",
            "bleeding",
            "broken bone",
            "fracture",
            "bite",
            "sting",
            "hypothermia",
            "frostbite",
            "heat stroke",
            "dehydration",
            "allergic reaction",
            "poison",
            "wound",
            "burn",
            "concussion",
            "pain",
            "symptoms",
            "treat",
            "treatment",
        ],
        "warning": (
            "⚠️ **MEDICAL DISCLAIMER**\n\n"
            "This is general information only and NOT medical advice. "
            "The AI cannot diagnose conditions, assess injury severity, or prescribe treatment. "
            "Seek professional medical help immediately for serious injuries or illness. "
            "Call emergency services (911) for life-threatening situations."
        ),
        "severity": "warning",
    },
    "navigation": {
        "keywords": [
            "lost",
            "find my way",
            "navigate",
            "direction",
            "trail",
            "route",
            "rescue",
            "which way",
            "how to get",
            "path",
        ],
        "warning": (
            "⚠️ **NAVIGATION WARNING**\n\n"
            "AI navigation suggestions should be verified with proper navigation tools. "
            "Use maps, compass, and GPS devices for critical navigation decisions. "
            "Stay on marked trails when possible. If lost, stay put and signal for help "
            "using the SOS feature rather than moving based on AI suggestions."
        ),
        "severity": "warning",
    },
    "survival": {
        "keywords": [
            "survive",
            "survival",
            "emergency",
            "stranded",
            "water source",
            "find water",
            "shelter",
            "build fire",
            "start fire",
            "start a fire",
            "make fire",
            "signal for help",
            "rescue",
            "stuck",
        ],
        "warning": (
            "⚠️ **SURVIVAL SITUATION WARNING**\n\n"
            "In genuine emergencies, prioritize established survival protocols over AI advice. "
            "Use the SOS feature to contact emergency services. "
            "The AI cannot assess your actual situation or environment. "
            "Follow the survival priority order: Shelter, Water, Fire, Food."
        ),
        "severity": "danger",
    },
}


def detect_critical_topic(text: str | None) -> str | None:
    """
    Detect if text contains critical topics requiring warnings.

    Args:
        text: The text to analyze (query or response)

    Returns:
        Warning message if a critical topic is detected, None otherwise
    """
    if not text:
        return None

    text_lower = text.lower()

    for config in CRITICAL_TOPICS.values():
        keywords = config.get("keywords", [])
        if isinstance(keywords, list):
            for keyword in keywords:
                if keyword in text_lower:
                    warning = config.get("warning")
                    return warning if isinstance(warning, str) else None

    return None


def detect_all_topics(text: str | None) -> list[str]:
    """
    Detect all critical topics present in text.

    Args:
        text: The text to analyze

    Returns:
        List of topic names found in the text
    """
    if not text:
        return []

    text_lower = text.lower()
    detected: list[str] = []

    for topic_name, config in CRITICAL_TOPICS.items():
        keywords = config.get("keywords", [])
        if isinstance(keywords, list):
            for keyword in keywords:
                if keyword in text_lower:
                    detected.append(topic_name)
                    break  # Only add topic once

    return detected


def add_safety_warning(response: str, query: str) -> str:
    """
    Add safety warning to response if critical topic detected.

    Checks both the user's query and the AI's response for critical topics.
    If found, prepends an appropriate warning to the response.

    Args:
        response: The AI response text
        query: The user's original query

    Returns:
        Response with safety warning prepended if applicable
    """
    warning = detect_critical_topic(query) or detect_critical_topic(response)

    if warning:
        return f"{warning}\n\n---\n\n{response}"

    return response


def get_all_warnings() -> dict[str, str]:
    """
    Get all topic warnings as a dictionary.

    Returns:
        Dictionary mapping topic names to their warning messages
    """
    warnings: dict[str, str] = {}

    for topic_name, config in CRITICAL_TOPICS.items():
        warning = config.get("warning")
        if isinstance(warning, str):
            warnings[topic_name] = warning

    return warnings


def get_disclaimer_version() -> str:
    """
    Get the current version of the disclaimer system.

    Returns:
        Semantic version string
    """
    return DISCLAIMER_VERSION
