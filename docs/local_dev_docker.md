# Run Waycore Locally with Docker (Dev)

This guide covers running the development stack with Docker Compose, including the MQTT broker and core services.

## Prerequisites

- Docker Desktop (or Docker Engine) with Docker Compose v2 (`docker compose`)
- ~4–8 GB free RAM and adequate disk space for images
- Git checked out to the repository root

## Quickstart

From the repository root:

1) Start the MQTT broker

```bash
docker compose -f docker/compose/dev.yml up -d mqtt
```

2) Build and start the core services

```bash
docker compose -f docker/compose/dev.yml up -d --build core-daemon module-manager comms-bridge ai-service
```

3) Verify health endpoints

```bash
curl http://localhost:8000/health   # core-daemon
curl http://localhost:8001/health   # module-manager
curl http://localhost:8003/health   # comms-bridge
curl http://localhost:8010/health   # ai-service (if enabled)
```

## What’s running

- `mqtt` (Eclipse Mosquitto) on port `1883`, configured by `docker/mosquitto.conf`
- `core-daemon` (port `8000`)
- `module-manager` (port `8001`)
- `comms-bridge` (port `8003`)
- `ai-service` (port `8010`)

The Compose file mounts:
- `docker/mosquitto.conf` into the Mosquitto container (read-only)
- The repository root at `/workspace` in the MQTT container (read-only)

## Common workflows

- View logs for a specific service:

```bash
docker compose -f docker/compose/dev.yml logs -f core-daemon
```

- Rebuild and restart a service:

```bash
docker compose -f docker/compose/dev.yml build core-daemon
docker compose -f docker/compose/dev.yml up -d core-daemon
```

- Clean rebuild (no cache) of all services:

```bash
docker compose -f docker/compose/dev.yml build --no-cache
docker compose -f docker/compose/dev.yml up -d
```

- Stop everything:

```bash
docker compose -f docker/compose/dev.yml down
```

- Stop and remove containers, networks, and named volumes created by this file:

```bash
docker compose -f docker/compose/dev.yml down -v
```

## Configuration notes

- Each service sets a default config file path via environment variables in the Compose file:
  - `CORE_DAEMON_CONFIG`, `MODULE_MANAGER_CONFIG`, `COMMS_BRIDGE_CONFIG`, `AI_SERVICE_CONFIG`
- Prefer environment variables for secrets; keep them out of the repo.
- Internal message schemas live under `device/libs/schemas/` and are used across services.

## Troubleshooting

- Port in use:
  - Another process may be bound to `1883`, `8000`, `8001`, `8003`, or `8010`. Stop conflicting processes or change host ports in `docker/compose/dev.yml`.
- Mosquitto config mount errors:
  - Ensure `docker/mosquitto.conf` exists and is readable. The mount is read-only by design.
- Rebuild not picking up code changes:
  - Use `--no-cache` during `docker compose build`, or bump the Dockerfile build context where necessary.

## Next steps

- Explore service READMEs under `device/services/*/README.md` for responsibilities and APIs.
- See the top-level `README.md` for test and lint commands using Poetry.
