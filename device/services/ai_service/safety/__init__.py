"""
Safety module for AI service.

Provides topic detection and safety warnings for critical topics
like plant identification, medical advice, navigation, and survival.
"""

from __future__ import annotations

from .topic_detector import (
    CRITICAL_TOPICS,
    add_safety_warning,
    detect_all_topics,
    detect_critical_topic,
    get_all_warnings,
    get_disclaimer_version,
)

__all__ = [
    "CRITICAL_TOPICS",
    "add_safety_warning",
    "detect_all_topics",
    "detect_critical_topic",
    "get_all_warnings",
    "get_disclaimer_version",
]
