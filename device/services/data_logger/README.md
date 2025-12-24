Data Logger Service
===================

Overview
--------
The Data Logger persists selected messages from the internal bus for offline analysis and debugging. It focuses on reliable, append-only storage with bounded retention.

Status
------
This service is a scaffold and may be expanded in future phases.

Planned responsibilities
------------------------
- Subscribe to configured topics and persist payloads
- Support rotating files and bounded retention
- Optional compression and indexing for fast retrieval

Directory layout
----------------
- `__init__.py`: package marker; service implementation to be added.

Configuration (planned)
-----------------------
- YAML in `config/` for topics, retention, and output paths.
- Environment variables for paths and storage tuning.

Run locally (Poetry)
--------------------
```bash
poetry install
USE_UNIX_SOCKET=true poetry run python -m device.services.data_logger.main
```

Testing
-------
```bash
poetry run pytest device/services/data_logger/tests -q
```
Note: test suite will be introduced with the implementation.

IPC
---
- API over Unix domain socket when `USE_UNIX_SOCKET=true` (default):
  - Socket: `/tmp/waycore/data-logger.sock`
  - Example: `curl --unix-socket /tmp/waycore/data-logger.sock http://localhost/health`
- Fallback TCP port when `USE_UNIX_SOCKET=false`:
  - Port from config (default 8002)
