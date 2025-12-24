# Progress Tracking

This directory implements the file-based progress tracking system described in
`docs/ai_instructions/progress_tracking.md`.

Structure:

- `TODO/phase-XX/`: Not-yet-started tasks, organized by phase
- `IN_PROGRESS/`: Tasks currently being worked on
- `COMPLETED/YYYY-MM/`: Completed tasks, archived monthly
- `BLOCKED/`: Tasks blocked by dependencies or issues
- `SUMMARY.md`: High-level status across phases

Automation scripts (see `scripts/`):

- `task-start.sh` and `task-complete.sh`
- `generate-tasks.py` (optional generator from
  `local_plan/08-implementation-phases.md`)
- `generate-summary.py` (creates/updates `SUMMARY.md`)
