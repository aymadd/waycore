# Progress Tracking

This directory implements the file-based progress tracking system described in
`docs/ai_instructions/progress_tracking.md`.

## Structure

### TODO Categories

- `TODO/phase-XX/`: Sequential feature phases (e.g., `12.1-feature-name.md`)
- `TODO/prod-phase-XX/`: Production deployment phases (e.g., `P-0.1-task-name.md`)
- `TODO/improvements/`: Enhancements to existing features (e.g., `imp-1-description.md`)
- `TODO/ideas/`: Future feature concepts and proposals (e.g., `idea-1-description.md`)

### Workflow Directories

- `IN_PROGRESS/`: Tasks currently being worked on
- `COMPLETED/YYYY-MM/`: Completed tasks, archived monthly
- `BLOCKED/`: Tasks blocked by dependencies or issues

### Summary

- `SUMMARY.md`: High-level status across all categories

## Task ID Formats

| Category | Format | Example |
|----------|--------|---------|
| Phase | `PHASE.TASK` | `12.1`, `12.2` |
| Prod-Phase | `P-PHASE.TASK` | `P-0.1`, `P-1.2` |
| Improvement | `imp-N` | `imp-1`, `imp-2` |
| Idea | `idea-N` | `idea-1`, `idea-2` |

## Automation Scripts

Located in `scripts/`:

- `task-start.sh TASK_ID` - Move task from TODO to IN_PROGRESS
- `task-complete.sh TASK_ID` - Move task from IN_PROGRESS to COMPLETED
- `generate-tasks.py` - Generate phase tasks from `local_plan/08-implementation-phases.md`
- `generate-summary.py` - Create/update `SUMMARY.md`

### Examples

```bash
# Start a phase task
./scripts/task-start.sh 12.8

# Start an improvement
./scripts/task-start.sh imp-1

# Start an idea
./scripts/task-start.sh idea-1

# Complete any task
./scripts/task-complete.sh 12.8
```
