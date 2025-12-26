#!/usr/bin/env python3
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROGRESS = ROOT / "progress"


def find_in_progress_task(task_id: str) -> Path | None:
    """Find task file in IN_PROGRESS directory based on task ID."""
    in_progress = PROGRESS / "IN_PROGRESS"

    # Try exact match first (handles all formats)
    task_file = next(in_progress.glob(f"{task_id}-*.md"), None)
    if task_file:
        return task_file

    # Try case-insensitive for P- prefix
    if task_id.upper().startswith("P-"):
        task_file = next(in_progress.glob(f"{task_id.upper()}-*.md"), None)
        if task_file:
            return task_file

    # Try lowercase for imp- and idea- prefixes
    if task_id.lower().startswith(("imp-", "idea-")):
        task_file = next(in_progress.glob(f"{task_id.lower()}-*.md"), None)
        if task_file:
            return task_file

    return None


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: task-complete.sh TASK_ID")
        print("  Examples:")
        print("    task-complete.sh 12.1      (phase task)")
        print("    task-complete.sh imp-1     (improvement)")
        print("    task-complete.sh idea-1    (idea)")
        print("    task-complete.sh P-0.1     (prod-phase task)")
        sys.exit(1)

    task_id = sys.argv[1]
    task_file = find_in_progress_task(task_id)

    if not task_file:
        print(f"Task not in progress: {task_id}")
        print(f"Check: {PROGRESS / 'IN_PROGRESS'}")
        # List available tasks
        in_progress_files = list((PROGRESS / "IN_PROGRESS").glob("*.md"))
        if in_progress_files:
            print("Available tasks in IN_PROGRESS:")
            for f in in_progress_files:
                print(f"  - {f.name}")
        sys.exit(1)

    content = task_file.read_text(encoding="utf-8")
    content = content.replace("**Status**: IN_PROGRESS", "**Status**: COMPLETED")
    content = content.replace(
        "**Completed**: Not completed", f"**Completed**: {datetime.now().date()}"
    )
    task_file.write_text(content, encoding="utf-8")

    month_dir = PROGRESS / "COMPLETED" / datetime.now().strftime("%Y-%m")
    month_dir.mkdir(parents=True, exist_ok=True)
    shutil.move(str(task_file), str(month_dir / task_file.name))
    print(f"Completed task: {task_id}\nArchived to: {month_dir}")


if __name__ == "__main__":
    main()
