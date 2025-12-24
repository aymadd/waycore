#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROGRESS = ROOT / "progress"


def count_tasks(base: Path) -> int:
    return len(list(base.glob("*.md")))


def main() -> None:
    todo = sum(count_tasks(p) for p in (PROGRESS / "TODO").glob("phase-*"))
    in_prog = count_tasks(PROGRESS / "IN_PROGRESS")
    completed = sum(count_tasks(p) for p in (PROGRESS / "COMPLETED").glob("*") if p.is_dir())
    blocked = count_tasks(PROGRESS / "BLOCKED")
    total = todo + in_prog + completed + blocked
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    summary = PROGRESS / "SUMMARY.md"
    summary.write_text(
        f"# Waycore Implementation Progress\n\n"
        f"Last Updated: {now}\n\n"
        f"Overall Status\n"
        f"- Total tasks: {total}\n"
        f"- TODO: {todo}\n"
        f"- IN_PROGRESS: {in_prog}\n"
        f"- COMPLETED: {completed}\n"
        f"- BLOCKED: {blocked}\n\n"
        f"Current Focus\n"
        f"- See `progress/IN_PROGRESS/`\n",
        encoding="utf-8",
    )
    print(f"Updated {summary}")


if __name__ == "__main__":
    main()
