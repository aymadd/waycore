# Docker (Simulation-First)

Use Docker Compose to develop on a laptop with mocked hardware. Start by copying the sample compose file to a local file and iterating as services are implemented.

## Quick Start
1) Copy the sample:
   - `cp compose.sample.yml compose.local.yml`
2) Edit `compose.local.yml` to point to real build contexts as code lands (e.g., `device/services/core_daemon/`).
3) Run services:
   - `docker compose -f compose.local.yml up --build`

Keep services small and focused. Prefer explicit network links and JSON schemas under `device/proto/`.
