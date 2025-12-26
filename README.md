# Waycore

<p align="center">
<img src="assets/logo/waycore_logo_wbg.svg" alt="Waycore logo" width="200">
</p>

<p align="center">
  <strong>Modular, communications-first field computer for the outdoors</strong>
</p>

<p align="center">
  <a href="docs/vision.md">Vision</a> •
  <a href="docs/overview.md">Overview</a> •
  <a href="docs/architecture/architecture.md">Architecture</a> •
  <a href="progress/SUMMARY.md">Progress</a> •
  <a href="docs/local_dev_docker.md">Development</a> •
  <a href="CONTRIBUTING.md">Contributing</a>
</p>

---

## What is Waycore?

Waycore is a **modular, rugged, handheld field computer** designed for outdoors,
EDC, survival, and trades/handyman use. The system uses a split-brain design: a
Linux SBC "main brain" (UI, AI, storage, networking) paired with a low-power
ESP32-S3 sidecar (radios, GPS, SOS, power policy) to ensure reliability even
when the UI is busy or rebooting.

### Key Principles

- **Communications-first** — Works when phones and networks fail
- **Modular by design** — Core device + expandable external modules
- **On-device intelligence** — AI without cloud dependency
- **Reliable & resilient** — SOS works even if the UI crashes
- **Developer-friendly** — Clear interfaces and mockable hardware

## Documentation

| Document                                                  | Description                                                   |
| --------------------------------------------------------- | ------------------------------------------------------------- |
| [Vision](docs/vision.md)                                  | Full aspirational scope and long-term direction               |
| [Overview](docs/overview.md)                              | Project scope, architecture decisions, and MVP definition     |
| [Architecture](docs/architecture/architecture.md)         | Detailed software architecture, services, APIs, and standards |
| [Progress](progress/SUMMARY.md)                           | Current implementation status and task tracking               |
| [Local Development](docs/local_dev_docker.md)             | Docker-based development setup and workflows                  |
| [IPC Guide](local_plan/12-ipc-implementation-guide.md.md) | Inter-process communication strategy                          |

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Poetry

### Run Services

```bash
# Start infrastructure and services
docker-compose -f docker/compose/dev.yml up -d mqtt
docker-compose -f docker/compose/dev.yml up -d --build core-daemon module-manager comms-bridge ai-service data-logger

# Verify services are running
curl http://localhost:8000/health   # core-daemon
curl http://localhost:8001/health   # module-manager
curl http://localhost:8002/health   # data-logger
curl http://localhost:8003/health   # comms-bridge
curl http://localhost:8010/health   # ai-service
```

### Run Tests

```bash
poetry install --no-interaction

# Unit tests
poetry run pytest device/libs/ -q
poetry run pytest device/services/ -q

# Quality checks
poetry run ruff check device/
poetry run black --check device/
poetry run mypy device/ --strict
```

## Repository Structure

```
device/
├── apps/ui/              # Qt/QML frontend with PySide6 backend
├── libs/
│   ├── schemas/          # Pydantic message schemas
│   ├── hil/              # Hardware abstraction interfaces
│   ├── messaging/        # MQTT message bus
│   ├── database/         # SQLite async wrapper
│   └── common/           # Shared utilities
├── services/
│   ├── core_daemon/      # System state, power policy
│   ├── module_manager/   # Module discovery & lifecycle
│   ├── comms_bridge/     # Radio management, TAK gateway
│   ├── ai_service/       # On-device inference
│   └── data_logger/      # Event persistence
└── drivers/
    ├── mock/             # Mock hardware for development
    └── real/             # Real hardware drivers
docs/                     # Documentation
progress/                 # Task tracking system
docker/                   # Docker Compose and configs
```

## Services

| Service        | Port | Description                                       |
| -------------- | ---- | ------------------------------------------------- |
| core-daemon    | 8000 | System state machine, power policy, orchestration |
| module-manager | 8001 | Module discovery and lifecycle management         |
| data-logger    | 8002 | Event persistence and retrieval                   |
| comms-bridge   | 8003 | Radio coordination and TAK gateway                |
| ai-service     | 8010 | Image classification and Q&A inference            |

All services support Unix domain sockets (preferred) and HTTP/JSON APIs.

## UI Application

The Qt/QML frontend provides:

- **Home grid** with app tiles (AI, Maps, Compass, Meshtastic, Camera, Notes,
  etc.)
- **Status bar** with time, battery, connectivity indicators
- **Theme system** with dark mode optimized for outdoor visibility
- **Settings** for units, display, developer options

Run the UI locally:

```bash
cd device/apps/ui && python main.py
```

## Contributing

We welcome contributions! Please read:

- [Contributing Guide](CONTRIBUTING.md) — Code style, commit conventions, PR
  process
- [Code of Conduct](CODE_OF_CONDUCT.md) — Community guidelines
- [Security Policy](SECURITY.md) — Reporting vulnerabilities

## Progress Tracking

We use a file-based task tracking system:

- **[Progress Summary](progress/SUMMARY.md)** — Current status overview
- **[Task System](progress/README.md)** — How tasks are organized
- **[Tracking Guide](docs/ai_instructions/progress_tracking.md)** — Detailed
  workflow

Task categories include sequential phases, production tasks, improvements, and
ideas.

## License

This project is licensed under the terms in [LICENSE](LICENSE).
