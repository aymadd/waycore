"""Response formatters for outdoor knowledge tools.

These formatters ensure consistent output with proper safety warnings
and source attribution.
"""

from __future__ import annotations

from typing import Any

# Safety level icons
SAFETY_ICONS = {
    "safe": "✅",
    "caution": "⚠️",
    "warning": "⚠️",
    "danger": "🚫",
    "lethal": "☠️",
}


def format_search_results(results: list[dict[str, Any]]) -> str:
    """Format general search results.

    Args:
        results: List of search result dictionaries.

    Returns:
        Formatted string with results and safety warnings.
    """
    lines = [f"📚 Found {len(results)} relevant knowledge entries:\n"]

    for i, r in enumerate(results, 1):
        title = r.get("title", "Unknown")
        category = r.get("category", "")
        content = r.get("content", "")[:500]
        safety = r.get("safety_level", "safe")
        safety_notes = r.get("safety_notes", "")
        source = r.get("source_file", "")
        page = r.get("source_page", "")

        lines.append(f"\n--- {i}. {title} ({category}) ---")
        lines.append(content)

        # Add safety warning if not "safe"
        if safety and safety != "safe":
            icon = SAFETY_ICONS.get(safety, "⚠️")
            lines.append(f"\n{icon} SAFETY ({safety.upper()})")
            if safety_notes:
                lines.append(safety_notes)

        # Add source
        if source:
            source_line = f"\nSource: {source}"
            if page:
                source_line += f" p.{page}"
            lines.append(source_line)

    return "\n".join(lines)


def format_plant_results(results: list[dict[str, Any]]) -> str:
    """Format plant identification results with strong safety warnings.

    Args:
        results: List of plant search results.

    Returns:
        Formatted string with plant info and critical safety warnings.
    """
    if not results:
        return "No plant information found."

    # Use the first (best) result
    plant = results[0]

    title = plant.get("title", "Unknown Plant")
    subcategory = plant.get("subcategory", "")
    content = plant.get("content", "")
    safety = plant.get("safety_level", "danger")
    safety_notes = plant.get("safety_notes", "")
    source = plant.get("source_url", plant.get("source_file", "Knowledge base"))

    icon = SAFETY_ICONS.get(safety, "⚠️")

    lines = [
        f"🌿 {title}",
    ]

    if subcategory:
        lines.append(f"Family: {subcategory}")

    lines.append("")
    lines.append(content)
    lines.append("")
    lines.append("=" * 50)
    lines.append(f"{icon} SAFETY LEVEL: {safety.upper()}")

    if safety_notes:
        lines.append(safety_notes)

    # Always add critical warning for plants
    lines.extend(
        [
            "",
            "⚠️ CRITICAL WARNING:",
            "• Many plants have DEADLY look-alikes",
            "• NEVER consume without expert verification",
            "• When in doubt, DO NOT EAT",
            "• This is for educational purposes ONLY",
            "",
            f"Source: {source}",
        ]
    )

    return "\n".join(lines)


def format_first_aid_results(results: list[dict[str, Any]]) -> str:
    """Format first aid guidance with medical disclaimer.

    Args:
        results: List of first aid search results.

    Returns:
        Formatted string with guidance and disclaimers.
    """
    lines = ["🏥 Wilderness First Aid Guidance\n"]

    for r in results:
        title = r.get("title", "First Aid")
        content = r.get("content", "")[:600]
        source = r.get("source_file", "")
        page = r.get("source_page", "")

        lines.append(f"\n**{title}**")
        lines.append("-" * 40)
        lines.append(content)

        if source:
            source_line = f"\nSource: {source}"
            if page:
                source_line += f" p.{page}"
            lines.append(source_line)

    # Always add medical disclaimer
    lines.extend(
        [
            "",
            "=" * 50,
            "⚠️ IMPORTANT MEDICAL DISCLAIMER:",
            "• This is EDUCATIONAL information only",
            "• NOT a substitute for professional medical care",
            "• Call emergency services when possible",
            "• Activate SOS beacon in wilderness emergencies",
            "• Do not delay seeking professional help",
        ]
    )

    return "\n".join(lines)


def format_knot_results(results: list[dict[str, Any]]) -> str:
    """Format knot lookup results.

    Args:
        results: List of knot search results.

    Returns:
        Formatted string with knot instructions.
    """
    if not results:
        return "No knot information found."

    result = results[0]
    title = result.get("title", "Knot")
    content = result.get("content", "")
    source = result.get("source_file", "")
    page = result.get("source_page", "")

    lines = [
        f"🪢 {title}",
        "",
        content,
    ]

    if source:
        source_line = f"\nSource: {source}"
        if page:
            source_line += f" p.{page}"
        lines.append(source_line)

    return "\n".join(lines)


def format_weather_results(results: list[dict[str, Any]]) -> str:
    """Format weather signs results.

    Args:
        results: List of weather search results.

    Returns:
        Formatted string with weather information.
    """
    lines = ["🌦️ Weather Signs\n"]

    for r in results:
        title = r.get("title", "Weather Info")
        content = r.get("content", "")[:400]

        lines.append(f"\n**{title}**")
        lines.append(content)

    return "\n".join(lines)
