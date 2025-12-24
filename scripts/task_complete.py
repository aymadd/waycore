#!/usr/bin/env python3
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROGRESS = ROOT / "progress"


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: task-complete.sh PHASE.TASK_ID (e.g., 0.1)")
        sys.exit(1)
    task_id = sys.argv[1]
    task_file = next((PROGRESS / "IN_PROGRESS").glob(f"{task_id}-*.md"), None)
    if not task_file:
        print(f"Task not in progress: {task_id}")
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
