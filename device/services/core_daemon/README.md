Core Daemon Service
===================

Overview
--------
The Core Daemon is the system orchestrator. It runs the main state machine, enforces power policy, and coordinates startup/shutdown and inter-service readiness.

Responsibilities
----------------
- System state machine (`state_machine.py`)
- Power policy and duty cycling (`power_policy.py`)
- Service lifecycle and bus-level coordination (`service.py`)
- Entrypoint and boot sequence (`main.py`)

Directory layout
----------------
- `main.py`: entrypoint.
- `service.py`: orchestration and messaging.
- `state_machine.py`: system states and transitions.
- `power_policy.py`: power-saving rules and timing.
- `api.py`: optional control/health endpoints.
- `config/`: configuration in YAML.
- `tests/`: unit and integration tests.
- `Dockerfile`: container build.

Configuration
-------------
- Place state thresholds, timing constants, and feature flags in `config/`.
- Prefer environment variables for secrets and deployment-specific overrides.
- All inter-service communication uses shared schemas in `device/libs/schemas/`.

Run locally (Poetry)
--------------------
```bash
poetry install
poetry run python -m device.services.core_daemon.main
```

Run with Docker
---------------
```bash
docker build -t waycore/core-daemon -f device/services/core_daemon/Dockerfile .
docker run --rm -it waycore/core-daemon
```

Testing
-------
```bash
poetry run pytest device/services/core_daemon/tests -q
```

Notes
-----
- Keep transition logic pure and testable; avoid side-effects inside state evaluation where possible.
- Power policy must be conservative by default and opt-in for higher draw operations.
