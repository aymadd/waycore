# Progress Tracking System

## Purpose

This document defines how Cursor AI should track and manage implementation progress using a file-based task management system.

---

## Directory Structure

```
progress/
├── TODO/                    # Tasks not yet started
│   ├── phase-00/            # Sequential feature phases
│   │   ├── 0.1-repository-structure.md
│   │   ├── 0.2-poetry-setup.md
│   │   └── ...
│   ├── phase-01/
│   ├── phase-02/
│   ├── ...
│   ├── prod-phase-00/       # Production deployment phases
│   │   ├── P-0.1-production-compose.md
│   │   └── ...
│   ├── improvements/        # Enhancements to existing features
│   │   ├── imp-1-notes-rich-text.md
│   │   └── ...
│   └── ideas/               # Future feature concepts
│       ├── idea-1-save-coordinates.md
│       └── ...
├── IN_PROGRESS/            # Tasks currently being worked on
│   ├── current-task.md
│   └── ...
├── COMPLETED/              # Finished tasks
│   ├── 2024-12/
│   │   ├── 0.1-repository-structure.md
│   │   └── ...
│   └── ...
├── BLOCKED/                # Tasks that are blocked
│   ├── task-with-blocker.md
│   └── ...
└── README.md              # This file - instructions for Cursor
```

---

## Task Categories

| Category | Directory | Purpose | Priority |
|----------|-----------|---------|----------|
| Phase | `phase-XX/` | Sequential feature implementation | High - core roadmap |
| Prod-Phase | `prod-phase-XX/` | Production deployment tasks | High - release blockers |
| Improvements | `improvements/` | Enhancements to existing features | Medium - polish |
| Ideas | `ideas/` | Future concepts and proposals | Low - backlog |

---

## Task File Format

### File Naming Convention

| Category | Format | Examples |
|----------|--------|----------|
| Phase | `{phase}.{task}-{description}.md` | `0.1-repository-structure.md`, `12.8-settings-submenu.md` |
| Prod-Phase | `P-{phase}.{task}-{description}.md` | `P-0.1-production-compose.md` |
| Improvement | `imp-{n}-{description}.md` | `imp-1-notes-rich-text.md` |
| Idea | `idea-{n}-{description}.md` | `idea-1-save-coordinates.md` |

### Task File Template

Every task file must follow this structure:

```markdown
# Task: {Task Title}

**Phase**: {Phase Number and Name}
**Task ID**: {Phase.Task}
**Status**: {TODO | IN_PROGRESS | COMPLETED | BLOCKED}
**Started**: {Date or "Not started"}
**Completed**: {Date or "Not completed"}

## Description

{Detailed description of what needs to be done}

## Dependencies

- [ ] Task {X.Y} - {Description}
- [ ] Task {X.Z} - {Description}

## Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Files to Create/Modify

- `path/to/file1.py`
- `path/to/file2.qml`

## Tests Required

- [ ] Test file 1: `path/to/test_file1.py`
- [ ] Coverage target: {percentage}%

## Implementation Notes

{Cursor adds notes here during implementation}

## Validation Commands

```bash
# Commands to verify task completion
pytest path/to/tests/
ruff check path/to/code/
```

## Completion Checklist

- [ ] Code implemented
- [ ] Tests written
- [ ] Tests passing
- [ ] Coverage target met
- [ ] Linting passing
- [ ] Documentation updated
- [ ] Files committed

## Blockers

{None or describe blockers}

## Related Tasks

- Related to: Task {X.Y}
- Blocks: Task {X.Z}
```

---

## Cursor Workflow

### Starting Work

**Step 1: Select Next Task**

```bash
# List available tasks
ls progress/TODO/phase-00/

# Choose highest priority task
# Move to IN_PROGRESS
mv progress/TODO/phase-00/0.1-repository-structure.md progress/IN_PROGRESS/
```

**Step 2: Update Task File**

```markdown
**Status**: IN_PROGRESS
**Started**: 2024-12-23
```

**Step 3: Add Initial Notes**

Add any initial observations or approach notes to the "Implementation Notes" section.

---

### During Work

**Update Progress**

As you work, update the task file:

1. Check off acceptance criteria as met
2. Check off files as created/modified
3. Check off tests as written
4. Add implementation notes
5. Document any issues or decisions

**Example Updates**:

```markdown
## Implementation Notes

2024-12-23 10:00 - Started repository structure
- Created all directories as specified
- Used mkdir -p for nested directories

2024-12-23 10:15 - Issue: .gitkeep files
- Decision: Added .gitkeep to empty directories
- Rationale: Ensures directories are tracked in git

2024-12-23 10:30 - Progress update
- All directories created
- Moving to validation
```

---

### Completing Task

**Step 1: Complete Checklist**

Ensure all items in "Completion Checklist" are checked:

```markdown
## Completion Checklist

- [x] Code implemented
- [x] Tests written
- [x] Tests passing
- [x] Coverage target met
- [x] Linting passing
- [x] Documentation updated
- [x] Files committed
```

**Step 2: Run Validation**

Execute all validation commands and document results:

```markdown
## Validation Results

```bash
$ pytest device/libs/schemas/tests/ -v --cov
======================== 15 passed in 2.3s ========================
Coverage: 100%
```

All validation passed ✓
```

**Step 3: Update Status**

```markdown
**Status**: COMPLETED
**Completed**: 2024-12-23
```

**Step 4: Move to COMPLETED**

```bash
# Move to COMPLETED with date folder
mkdir -p progress/COMPLETED/2024-12
mv progress/IN_PROGRESS/0.1-repository-structure.md progress/COMPLETED/2024-12/
```

**Step 5: Update Summary**

Update `progress/SUMMARY.md` (see below).

---

### Handling Blockers

**When Blocked**:

**Step 1: Update Task File**

```markdown
**Status**: BLOCKED

## Blockers

### Blocker 1: Dependency Not Ready
- **Description**: Task 1.2 must complete before this task
- **Impact**: Cannot proceed with implementation
- **Workaround**: None available
- **Expected Resolution**: When Task 1.2 completes
```

**Step 2: Move to BLOCKED**

```bash
mv progress/IN_PROGRESS/task.md progress/BLOCKED/
```

**Step 3: Select New Task**

Choose a different task from TODO that isn't blocked.

**When Blocker Resolved**:

```bash
# Move back to TODO or IN_PROGRESS
mv progress/BLOCKED/task.md progress/TODO/phase-XX/
# Or directly to IN_PROGRESS if ready to work
```

---

## Summary File

### Location

`progress/SUMMARY.md`

### Purpose

High-level overview of all phases and current progress.

### Format

```markdown
# Waycore Implementation Progress

**Last Updated**: 2024-12-23 10:45

---

## Overall Status

| Phase | Status | Progress | Tasks | Completed | In Progress | Blocked |
|-------|--------|----------|-------|-----------|-------------|---------|
| 0 | 🟡 | 20% | 7 | 1 | 1 | 0 |
| 1 | ⚪ | 0% | 8 | 0 | 0 | 0 |
| 2 | ⚪ | 0% | 5 | 0 | 0 | 0 |
| ... | ... | ... | ... | ... | ... | ... |

**Total Progress**: 2% (1/65 tasks complete)

---

## Current Focus

**Active Tasks** (IN_PROGRESS):
- [ ] 0.2 - Poetry Setup

**Recently Completed**:
- [x] 0.1 - Repository Structure (2024-12-23)

**Upcoming Next**:
- [ ] 0.3 - Configuration Files
- [ ] 0.4 - Pre-commit Hooks

---

## Phase Details

### Phase 0: Project Foundation (20% Complete)

**Status**: 🟡 In Progress
**Started**: 2024-12-23

**Tasks**:
- [x] 0.1 - Repository structure (COMPLETED)
- [🟡] 0.2 - Poetry setup (IN_PROGRESS)
- [ ] 0.3 - Configuration files
- [ ] 0.4 - Pre-commit hooks
- [ ] 0.5 - CI/CD pipeline
- [ ] 0.6 - Documentation structure
- [ ] 0.7 - Phase validation

### Phase 1: Message Schemas & HIL (0% Complete)

**Status**: ⚪ Not Started
**Dependencies**: Phase 0 complete

**Tasks**:
- [ ] 1.1 - Base message schema
- [ ] 1.2 - System schemas
- [ ] 1.3 - Communication schemas
- [ ] 1.4 - Sensor schemas
- [ ] 1.5 - Module schemas
- [ ] 1.6 - AI schemas
- [ ] 1.7 - HIL interfaces
- [ ] 1.8 - Driver factory

{Continue for all phases...}

---

## Metrics

**Code Statistics**:
- Total Lines of Code: 347
- Total Files: 23
- Python Files: 5
- QML Files: 0
- Test Files: 2

**Testing Metrics**:
- Total Tests: 15
- Passing Tests: 15
- Failing Tests: 0
- Coverage: 45%

**Quality Metrics**:
- Linting Issues: 0
- Type Errors: 0
- Security Issues: 0

---

## Recent Activity (Last 7 Days)

### 2024-12-23
- ✓ Completed 0.1 - Repository structure
- Started 0.2 - Poetry setup

---

## Blockers

None currently.

---

## Next Sprint Goals

1. Complete Phase 0 (Project Foundation)
2. Begin Phase 1 (Message Schemas)
3. Setup CI/CD pipeline
```

**Update Frequency**: After every task completion or status change.

---

## Task Generation

### Initial Task Creation

When starting the project, Cursor should:

1. **Create TODO Directory Structure**

```bash
mkdir -p progress/TODO/{phase-00,phase-01,phase-02,phase-03,phase-04,phase-05,phase-06,phase-07,phase-08,phase-09,phase-10,phase-11,phase-12}
mkdir -p progress/{IN_PROGRESS,COMPLETED,BLOCKED}
```

2. **Generate Task Files**

For each task in each phase (from `08-implementation-phases.md`), create a task file in the appropriate `progress/TODO/phase-XX/` directory.

Example script:

```bash
# For Phase 0, Task 1
cat > progress/TODO/phase-00/0.1-repository-structure.md << 'EOF'
# Task: Repository Structure

**Phase**: Phase 0 - Project Foundation
**Task ID**: 0.1
**Status**: TODO
**Started**: Not started
**Completed**: Not completed

## Description

Create the complete directory structure for the Waycore project as defined in the architecture overview.

## Dependencies

None - this is the first task.

## Acceptance Criteria

- [ ] All directories created as per architecture
- [ ] .gitkeep files in empty directories
- [ ] Directory structure matches documentation
- [ ] All paths accessible

## Files to Create/Modify

- `device/libs/hil/interfaces/`
- `device/libs/schemas/`
- `device/libs/messaging/`
- `device/libs/common/`
- `device/libs/database/`
- `device/services/core_daemon/`
- `device/services/module_manager/`
- `device/services/ai_service/`
- `device/services/comms_bridge/`
- `device/services/data_logger/`
- `device/apps/ui/`
- `device/drivers/mock/`
- `device/drivers/real/`
- `device/tests/integration/`
- `device/tests/e2e/`
- `device/tests/fixtures/`
- `docker/compose/`
- `config/`
- `scripts/`
- `progress/`
- `local_plan/` (for plan documents)

## Tests Required

- [ ] Manual verification: all directories exist
- [ ] Script test: `scripts/verify-structure.sh`

## Implementation Notes

{Add notes during implementation}

## Validation Commands

```bash
# Verify all directories exist
ls -R device/ docker/ config/ scripts/ progress/

# Verify directory tree matches architecture
tree -L 3 device/
```

## Completion Checklist

- [ ] Code implemented
- [ ] Tests written
- [ ] Tests passing
- [ ] Coverage target met (N/A for this task)
- [ ] Linting passing (N/A for this task)
- [ ] Documentation updated
- [ ] Files committed

## Blockers

None

## Related Tasks

- Blocks: All other tasks depend on this
EOF
```

3. **Create Verification Script**

Create `scripts/generate-tasks.py` to automate task file generation from phase specifications.

---

## Daily Workflow

### Morning Routine

1. **Review Status**

```bash
# Check current tasks
ls progress/IN_PROGRESS/

# Review SUMMARY.md
cat progress/SUMMARY.md
```

2. **Select Next Task**

```bash
# Find next available task
find progress/TODO/phase-00/ -name "*.md" | head -1
```

3. **Begin Work**

Move task to IN_PROGRESS and update status.

### Throughout Day

- Update task files with progress notes
- Check off criteria as completed
- Document any issues or decisions

### End of Day

1. **Update All Task Files**

Ensure all IN_PROGRESS tasks have current notes.

2. **Update SUMMARY.md**

Update metrics, recent activity, and status.

3. **Commit Progress**

```bash
git add progress/
git commit -m "chore: update progress tracking"
```

---

## Best Practices

### Task Granularity

- Tasks should be completable in 1-4 hours
- If task seems too large, split into subtasks
- Create new task files for subtasks

### Documentation

- Write notes as you go, not at the end
- Document decisions and rationale
- Include code snippets or examples when helpful

### File Organization

- Keep IN_PROGRESS lean (max 3 tasks at once)
- Archive COMPLETED tasks monthly
- Review BLOCKED tasks weekly

### Quality

- Never mark task complete without validation
- Always run test suite before completion
- Check off all acceptance criteria

---

## Automation

### Scripts to Create

**1. `scripts/task-start.sh`**

```bash
#!/bin/bash
# Move task from TODO to IN_PROGRESS
# Usage: ./scripts/task-start.sh 0.1

TASK_ID=$1
PHASE=$(echo $TASK_ID | cut -d. -f1)
PHASE_DIR=$(printf "phase-%02d" $PHASE)

# Find task file
TASK_FILE=$(find progress/TODO/$PHASE_DIR/ -name "${TASK_ID}-*.md" | head -1)

if [ -z "$TASK_FILE" ]; then
  echo "Task not found: $TASK_ID"
  exit 1
fi

# Move to IN_PROGRESS
mv "$TASK_FILE" progress/IN_PROGRESS/

# Update status and date
sed -i "s/Status: TODO/Status: IN_PROGRESS/" progress/IN_PROGRESS/$(basename $TASK_FILE)
sed -i "s/Started: Not started/Started: $(date +%Y-%m-%d)/" progress/IN_PROGRESS/$(basename $TASK_FILE)

echo "Started task: $TASK_ID"
echo "File: progress/IN_PROGRESS/$(basename $TASK_FILE)"
```

**2. `scripts/task-complete.sh`**

```bash
#!/bin/bash
# Move task from IN_PROGRESS to COMPLETED
# Usage: ./scripts/task-complete.sh 0.1

TASK_ID=$1
TASK_FILE=$(find progress/IN_PROGRESS/ -name "${TASK_ID}-*.md" | head -1)

if [ -z "$TASK_FILE" ]; then
  echo "Task not in progress: $TASK_ID"
  exit 1
fi

# Create monthly folder
MONTH=$(date +%Y-%m)
mkdir -p progress/COMPLETED/$MONTH

# Update status
sed -i "s/Status: IN_PROGRESS/Status: COMPLETED/" "$TASK_FILE"
sed -i "s/Completed: Not completed/Completed: $(date +%Y-%m-%d)/" "$TASK_FILE"

# Move to COMPLETED
mv "$TASK_FILE" progress/COMPLETED/$MONTH/

echo "Completed task: $TASK_ID"
echo "Archived to: progress/COMPLETED/$MONTH/"
```

**3. `scripts/generate-summary.py`**

Python script to generate SUMMARY.md from task files.

---

## Example Workflow

### Day 1: Starting Fresh

```bash
# 1. Create structure
mkdir -p progress/{TODO,IN_PROGRESS,COMPLETED,BLOCKED}

# 2. Generate all task files
python scripts/generate-tasks.py

# 3. Review tasks
ls progress/TODO/phase-00/

# 4. Start first task
./scripts/task-start.sh 0.1

# 5. Work on task...
# 6. Complete task
./scripts/task-complete.sh 0.1

# 7. Update summary
python scripts/generate-summary.py > progress/SUMMARY.md

# 8. Commit
git add progress/
git commit -m "chore: completed task 0.1"
```

---

## Cursor Instructions

### When Starting Implementation

1. Create progress tracking directories
2. Generate all task files from phase specifications
3. Create automation scripts
4. Initialize SUMMARY.md

### For Each Task

1. **Select**: Choose next task from TODO
2. **Start**: Move to IN_PROGRESS, update dates
3. **Work**: Implement, document, test
4. **Validate**: Run all validation commands
5. **Complete**: Check all criteria, move to COMPLETED
6. **Update**: Update SUMMARY.md

### Daily

1. Update task notes
2. Update SUMMARY.md
3. Commit progress
4. Review next day's tasks

### Never

- Skip validation before marking complete
- Leave tasks in IN_PROGRESS overnight without notes
- Mark task complete with failing tests
- Move tasks without updating status in file

---

## Questions or Issues

If unclear about a task:
1. Add question to task file in "Implementation Notes"
2. Mark as BLOCKED if cannot proceed
3. Document what information is needed
4. Continue with other tasks
