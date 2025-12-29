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

    # Calculate Localization Progress
    # Convention: English files are *.md (excluding *_AR.md), Arabic files are *_AR.md
    docs_dir = ROOT / "docs"
    
    # Get all markdown files in docs/ recursively + root READMEs
    all_md_docs = list(docs_dir.rglob("*.md"))
    if (ROOT / "README.md").exists():
        all_md_docs.append(ROOT / "README.md")

    english_files = {f for f in all_md_docs if not f.name.endswith("_AR.md")}
    arabic_files = {f for f in all_md_docs if f.name.endswith("_AR.md") or (f.parent / f"{f.stem}_AR.md").exists()}
    
    # Check for root README specifically
    if (ROOT / "README_AR.md").exists():
        arabic_files.add(ROOT / "README.md") # Count the source as "covered"

    total_docs = len(english_files)
    total_translated = len(arabic_files.intersection(english_files)) # Files that have a corresponding translation
    
    ar_percent = (total_translated / total_docs * 100) if total_docs > 0 else 0

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
        f"## Localization Progress\n\n"
        f"| Language | Coverage | Files |\n"
        f"|----------|----------|-------|\n"
        f"| English  | 100%     | {total_docs} |\n"
        f"| Arabic   | {ar_percent:.1f}%    | {total_translated}/{total_docs} |\n\n"
        f"## Current Focus\n\n"
        f"See `progress/IN_PROGRESS/`\n",
        encoding="utf-8",
    )
    print(f"Updated {summary}")


if __name__ == "__main__":
    main()
