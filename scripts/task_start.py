#!/usr/bin/env python3
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROGRESS = ROOT / "progress"


def find_task_file(task_id: str) -> Path | None:
    """Find task file in TODO directory based on task ID format."""
    todo_dir = PROGRESS / "TODO"

    # Handle phase tasks: "12.1" -> phase-12/12.1-*.md
    if "." in task_id and task_id.split(".")[0].isdigit():
        phase = int(task_id.split(".")[0])
        phase_dir = todo_dir / f"phase-{phase:02d}"
        if phase_dir.exists():
            task_file = next(phase_dir.glob(f"{task_id}-*.md"), None)
            if task_file:
                return task_file

    # Handle improvements: "imp-1" or "IMP-1" -> improvements/imp-1-*.md
    if task_id.lower().startswith("imp-"):
        imp_dir = todo_dir / "improvements"
        if imp_dir.exists():
            task_file = next(imp_dir.glob(f"{task_id.lower()}-*.md"), None)
            if task_file:
                return task_file

    # Handle ideas: "idea-1" or "IDEA-1" -> ideas/idea-1-*.md
    if task_id.lower().startswith("idea-"):
        ideas_dir = todo_dir / "ideas"
        if ideas_dir.exists():
            task_file = next(ideas_dir.glob(f"{task_id.lower()}-*.md"), None)
            if task_file:
                return task_file

    # Handle prod-phase tasks: "P-0.1" -> prod-phase-00/P-0.1-*.md
    if task_id.upper().startswith("P-"):
        parts = task_id.split(".")
        if len(parts) == 2:
            phase_num = parts[0].replace("P-", "").replace("p-", "")
            if phase_num.isdigit():
                prod_dir = todo_dir / f"prod-phase-{int(phase_num):02d}"
                if prod_dir.exists():
                    task_file = next(prod_dir.glob(f"{task_id.upper()}-*.md"), None)
                    if task_file:
                        return task_file

    return None


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: task-start.sh TASK_ID")
        print("  Examples:")
        print("    task-start.sh 12.1      (phase task)")
        print("    task-start.sh imp-1     (improvement)")
        print("    task-start.sh idea-1    (idea)")
        print("    task-start.sh P-0.1     (prod-phase task)")
        sys.exit(1)

    task_id = sys.argv[1]
    task_file = find_task_file(task_id)

    if not task_file:
        print(f"Task not found: {task_id}")
        print("Searched in: phase-XX/, improvements/, ideas/, prod-phase-XX/")
        sys.exit(1)

    dest = PROGRESS / "IN_PROGRESS" / task_file.name
    shutil.move(str(task_file), str(dest))
    content = dest.read_text(encoding="utf-8")
    content = content.replace("**Status**: TODO", "**Status**: IN_PROGRESS")
    content = content.replace("**Started**: Not started", f"**Started**: {datetime.now().date()}")
    dest.write_text(content, encoding="utf-8")
    print(f"Started task: {task_id}\nFile: {dest}")


if __name__ == "__main__":
    main()
