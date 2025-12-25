#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROGRESS = ROOT / "progress"


def count_tasks(base: Path) -> int:
    if not base.exists():
        return 0
    return len(list(base.glob("*.md")))


def main() -> None:
    todo_dir = PROGRESS / "TODO"

    # Count phase tasks
    phase_todo = sum(count_tasks(p) for p in todo_dir.glob("phase-*"))
    prod_phase_todo = sum(count_tasks(p) for p in todo_dir.glob("prod-phase-*"))

    # Count improvements and ideas
    improvements_todo = count_tasks(todo_dir / "improvements")
    ideas_todo = count_tasks(todo_dir / "ideas")

    todo = phase_todo + prod_phase_todo + improvements_todo + ideas_todo
    in_prog = count_tasks(PROGRESS / "IN_PROGRESS")
    completed = sum(count_tasks(p) for p in (PROGRESS / "COMPLETED").glob("*") if p.is_dir())
    blocked = count_tasks(PROGRESS / "BLOCKED")
    total = todo + in_prog + completed + blocked
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    summary = PROGRESS / "SUMMARY.md"
    summary.write_text(
        f"# Waycore Implementation Progress\n\n"
        f"Last Updated: {now}\n\n"
        f"## Overall Status\n\n"
        f"| Category | Count |\n"
        f"|----------|-------|\n"
        f"| Total tasks | {total} |\n"
        f"| TODO | {todo} |\n"
        f"| IN_PROGRESS | {in_prog} |\n"
        f"| COMPLETED | {completed} |\n"
        f"| BLOCKED | {blocked} |\n\n"
        f"## TODO Breakdown\n\n"
        f"| Category | Count |\n"
        f"|----------|-------|\n"
        f"| Phase tasks | {phase_todo} |\n"
        f"| Prod-phase tasks | {prod_phase_todo} |\n"
        f"| Improvements | {improvements_todo} |\n"
        f"| Ideas | {ideas_todo} |\n\n"
        f"## Current Focus\n\n"
        f"See `progress/IN_PROGRESS/`\n",
        encoding="utf-8",
    )
    print(f"Updated {summary}")


if __name__ == "__main__":
    main()
