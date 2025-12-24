Module Manager Service
======================

Overview
--------
The Module Manager discovers, identifies, and supervises pluggable hardware modules connected to the system. It handles link protocol, hot-plug events, metadata, and health reporting for modules.

Responsibilities
----------------
- Discovery and enumeration of modules (`discovery.py`)
- Link- and framing-level protocol handling (`protocol.py`)
- Service lifecycle, health checks, and bus integration (`service.py`)
- Entrypoint and startup (`main.py`)

Directory layout
----------------
- `main.py`: service entrypoint.
- `service.py`: orchestration and messaging.
- `discovery.py`: bus/port probing and module discovery.
- `protocol.py`: on-wire protocol and framing.
- `api.py`: optional control/diagnostics endpoints.
- `config/`: configuration in YAML.
- `tests/`: unit and integration tests.
- `Dockerfile`: container build.

Configuration
-------------
- Keep port names, baud rates, timing windows, and protocol toggles in `config/`.
- Use environment variables for deployment-specific overrides.
- Use shared schemas in `device/libs/schemas/` for module descriptions and events.

Run locally (Poetry)
--------------------
```bash
poetry install
poetry run python -m device.services.module_manager.main
```

Run with Docker
---------------
```bash
docker build -t waycore/module-manager -f device/services/module_manager/Dockerfile .
docker run --rm -it --device /dev/ttyUSB0 waycore/module-manager
```

Testing
-------
```bash
poetry run pytest device/services/module_manager/tests -q
```

Notes
-----
- Keep protocol logic self-contained in `protocol.py`; publish only typed events to the bus.
- Discovery should be idempotent and resilient to transient link errors.
