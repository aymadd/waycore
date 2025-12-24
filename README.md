# Waycore

<img src="assets/logo/waycore_logo_wbg.svg" alt="Waycore logo" width="200">

Modular, communications-first field computer designed for outdoors, EDC,
survival, and trades/handyman use. The system separates a Linux SBC “main brain”
(UI, AI, storage, networking) from a low-power ESP32-S3 sidecar (radios, GPS,
SOS, power policy) to ensure reliability even when the UI is busy or rebooting.

For the high-level vision and scope, see: `docs/overview.md`

For a detailed software architecture overview, see:
`docs/architecture/architecture.md`

## Highlights

- Communications-first and modular by design
- On-device intelligence without cloud dependency
- Reliable low-power controller for critical functions (e.g., SOS)
- Developer-friendly with clear interfaces and mockable hardware

## Repository Structure (MVP)

The repo is organized for a simulation-first workflow on a developer laptop
using Docker Compose and mocked hardware. Key libraries and services delivered
in Phases 0–6 are included.

```
device/
  libs/
    schemas/                    # Pydantic message schemas (system, comms, sensor, module, ai)
    hil/                        # Hardware interfaces (IGPS, IRadio, ISensor, IModulePort, IPowerController) + factory
    messaging/                  # Message bus interface + MQTT implementation (paho-mqtt)
    common/                     # BaseService lifecycle
  apps/ui/                      # Qt/QML frontend (PySide6 backend) + Theme.qml design system
  services/
    core_daemon/                # State machine, power policy, service + FastAPI
    module_manager/             # Module discovery/lifecycle service + FastAPI
    ai_service/                 # On-device inference service (preproc, engine, REST, bus)
    comms_bridge/               # Radio manager, TAK gateway stub, service + FastAPI
    data_logger/                # Async SQLite logger + REST for latest records
  drivers/
    mock/                       # Mock GPS, LoRa radio, sensor, module_port, power (registered in factory)
    real/                       # Real drivers (stubs added in later phases)
  docker/
    compose/dev.yml             # Development Docker Compose (mqtt, core-daemon, module-manager, comms-bridge)
    mosquitto.conf              # MQTT broker dev config
docs/
progress/                       # File-based task tracking (TODO/IN_PROGRESS/COMPLETED/BLOCKED)
LICENSE
```

## Development Strategy (Simulation-First)

Build Phase 1 targets a full software MVP without hardware:

- UI skeleton at fixed target resolution (e.g. 480×800)
- Mock ESP32 + sensors
- AI inference pipeline (on-demand)
- Module protocol and discovery

Later phases add bench hardware (Raspberry Pi 5, Meshtastic, camera/display),
then custom PCB, and finally field testing.

## Getting Started

1. Read the architecture and scope in `docs/overview.md`.
2. Explore the directory layout under `device/`.
3. Review `CONTRIBUTING.md` for conventions and commit style.
4. (Optional) Copy `device/docker/compose.sample.yml` to a local compose, and
   iterate on service stubs as code is added.

## Current Status (Phases 0–8)

- **Phase 0 (Foundation)**: Poetry, linters (ruff/black), type checking (mypy),
  CI workflows, repo structure, progress tracker.
- **Phase 1 (Schemas & HIL)**: All message schemas; HIL interfaces; driver
  factory; 100% tests for these layers.
- **Phase 2 (Messaging & Base Service)**: MessageBus interface; MQTT (paho-mqtt)
  implementation; BaseService; dev Docker Compose with Mosquitto.
- **Phase 3 (Mock Drivers)**: Mock GPS/Radio/Sensor/ModulePort/Power implemented
  with tests and factory registration.
- **Phase 4 (Core Daemon)**: State machine, power policy, service loop, FastAPI
  (`/health`, `/api/status`, `/api/command`), Dockerfile, compose integration.
- **Phase 5 (Module Manager)**: Protocol helpers, discovery manager, service,
  FastAPI (`/health`, `/api/modules`), Dockerfile, compose integration.
- **Phase 6 (Comms Bridge)**: Radio manager, TAK gateway stub, service, FastAPI
  (`/health`, `/api/radios`, `/api/send`), Dockerfile, compose integration.
- **Phase 7 (AI Service)**: Preprocessing, inference engine with model runners
  (MobileNetV3 stub, Phi3-mini stub), REST endpoints (`/api/inference`,
  `/api/image/classify`, `/api/chat`), two-stage vision→LLM pipeline stub, model
  registry/config, lazy loading, perf sanity tests; Dockerfile and compose
  integration.
- **Phase 8 (Data Logger)**: Async SQLite DB, logger service consuming bus
  topics (comms, AI, system), REST endpoints for latest records, Dockerfile and
  compose integration.

## How to Run (Dev)

- Prereqs: Docker, Docker Compose, Python 3.11, Poetry.

For a complete Docker quickstart and common workflows, see
[Local run with Docker](docs/local_dev_docker.md).

Run tests and quality checks:

```bash
poetry install --no-interaction --no-ansi

# Unit tests (examples)
poetry run pytest device/libs/{schemas,hil,messaging,common}/tests -q
poetry run pytest device/services/{core_daemon,module_manager,comms_bridge}/tests -q

# Lint / format / types
poetry run ruff check device/
poetry run black --check device/
poetry run mypy device/ --strict
```

Start infrastructure and services:

```bash
docker-compose -f docker/compose/dev.yml up -d mqtt
docker-compose -f docker/compose/dev.yml up -d --build core-daemon module-manager comms-bridge ai-service data-logger
```

Health checks and basic API calls:

```bash
curl http://localhost:8000/health          # core-daemon
curl http://localhost:8001/health          # module-manager
curl http://localhost:8003/health          # comms-bridge
curl http://localhost:8010/health          # ai-service
curl http://localhost:8002/health          # data-logger
```

## Service APIs (Dev)

- **Core Daemon (8000)**:
  - `GET /health`
  - `GET /api/status`
  - `POST /api/command` (body: SystemCommand)
- **Module Manager (8001)**:
  - `GET /health`
  - `GET /api/modules`
- **Comms Bridge (8003)**:
  - `GET /health`
  - `GET /api/radios`
  - `POST /api/send` (body: SendMessageRequest)
- **AI Service (8010)**:
  - `GET /health`
  - `POST /api/inference` (body: AIInferenceRequest)
  - `POST /api/image/classify` (body: {model_id?, input_data})
  - `POST /api/chat` (body: {model_id?, question, context})
- **Data Logger (8002)**:
  - `GET /health`
  - `GET /api/ai/latest?n=50`
  - `GET /api/comms/latest?n=50`
  - `GET /api/events/latest?n=50`

## Progress Tracking

- We use a file-based task tracker under `progress/`, aligned with
  `docs/ai_instructions/progress_tracking.md`.
- New tasks live in `progress/TODO/phase-XX/`, current work in
  `progress/IN_PROGRESS/`, and completed tasks are archived monthly in
  `progress/COMPLETED/YYYY-MM/`.
- Automation:
  - `scripts/generate-tasks.py` – generate task files from
    `local_plan/08-implementation-phases.md`
  - `scripts/task-start.sh PHASE.TASK` – move a task to IN_PROGRESS and stamp
    start date
  - `scripts/task-complete.sh PHASE.TASK` – mark as COMPLETED and archive
  - `scripts/generate-summary.py` – refresh `progress/SUMMARY.md`

Example:

```bash
python scripts/generate-tasks.py
./scripts/task-start.sh 4.1
./scripts/task-complete.sh 4.1
python scripts/generate-summary.py
```

## Contributing

- Follow Conventional Commits and small, focused PRs.
- Open issues with the provided templates (bug, feature, tech debt, docs).
- See `CONTRIBUTING.md` and `CODE_OF_CONDUCT.md`.

## Security

Security disclosures are welcome. See `SECURITY.md` for details.
