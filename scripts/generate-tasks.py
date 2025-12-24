#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "local_plan" / "08-implementation-phases.md"
PROGRESS = ROOT / "progress"

TEMPLATE = """# Task: {title}

**Phase**: Phase {phase_num} - {phase_name}
**Task ID**: {task_id}
**Status**: TODO
**Started**: Not started
**Completed**: Not completed

## Description

{desc}

## Dependencies

- [ ] (Add if any)

## Acceptance Criteria

- [ ] Implemented per spec
- [ ] Tests added and passing
- [ ] Lint and type checks passing

## Files to Create/Modify

(Fill during implementation)

## Tests Required

- [ ] (Add test paths)
- [ ] Coverage target: 90%

## Implementation Notes

(Notes during implementation)

## Validation Commands

```bash
pytest -q
ruff check device/
black --check device/
mypy device/ --strict
```

## Completion Checklist

- [ ] Code implemented
- [ ] Tests written
- [ ] Tests passing
- [ ] Coverage target met
- [ ] Linting passing
- [ ] Documentation updated
- [ ] Files committed

## Time Tracking

- Estimated effort: 1-4 hours
- Actual effort:

## Blockers

None

## Related Tasks

(add links)
"""


def main() -> None:
    if not PLAN.exists():
        print(f"Plan file not found: {PLAN}")
        return
    text = PLAN.read_text(encoding="utf-8")
    # Very simple extraction: find headings like "## Phase X: NAME" and "#### N. Task Name"
    phase_matches = list(re.finditer(r"## Phase\s+(\d+):\s*(.+)", text))
    for i, pm in enumerate(phase_matches):
        phase_num = int(pm.group(1))
        phase_name = pm.group(2).strip()
        start = pm.end()
        end = phase_matches[i + 1].start() if i + 1 < len(phase_matches) else len(text)
        section = text[start:end]
        tasks = re.findall(r"####\s+(\d+)\.\s+([^\n]+)", section)
        out_dir = PROGRESS / "TODO" / f"phase-{phase_num:02d}"
        out_dir.mkdir(parents=True, exist_ok=True)
        for task_num, title in tasks:
            task_id = f"{phase_num}.{task_num}"
            filename = f"{task_id}-{re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')}.md"
            dest = out_dir / filename
            if dest.exists():
                continue
            dest.write_text(
                TEMPLATE.format(
                    title=title.strip(),
                    phase_num=phase_num,
                    phase_name=phase_name,
                    task_id=task_id,
                    desc=(
                        "Task generated from local_plan/08-implementation-phases.md "
                        f"under Phase {phase_num}."
                    ),
                ),
                encoding="utf-8",
            )
            print(f"Created: {dest}")


if __name__ == "__main__":
    main()
