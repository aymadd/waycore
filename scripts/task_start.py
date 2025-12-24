#!/usr/bin/env python3
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROGRESS = ROOT / "progress"


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: task-start.sh PHASE.TASK_ID (e.g., 0.1)")
        sys.exit(1)
    task_id = sys.argv[1]
    phase = int(task_id.split(".")[0])
    phase_dir = PROGRESS / "TODO" / f"phase-{phase:02d}"
    task_file = next(phase_dir.glob(f"{task_id}-*.md"), None)
    if not task_file:
        print(f"Task not found in {phase_dir}: {task_id}")
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
