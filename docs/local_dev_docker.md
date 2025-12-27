# Run Waycore Locally with Docker (Dev)

This guide covers running the development stack with Docker Compose, including
the MQTT broker and core services.

## Prerequisites

- Docker Desktop (or Docker Engine) with Docker Compose v2 (`docker compose`)
- ~4–8 GB free RAM and adequate disk space for images
- Python 3.11+ with Poetry
- Git checked out to the repository root

## Quickstart (Recommended)

Use the convenience scripts from the repository root:

```bash
# Start all services (downloads AI models on first run)
./scripts/dev-start.sh

# Start with UI
./scripts/dev-start.sh --ui

# Check status of all services
./scripts/dev-status.sh

# Restart all services
./scripts/dev-restart.sh

# Restart specific service with rebuild
./scripts/dev-restart.sh --service ai-service --rebuild

# Stop everything
./scripts/dev-stop.sh

# Stop and remove volumes (WARNING: deletes data)
./scripts/dev-stop.sh --volumes
```

## Manual Setup

If you prefer manual control:

### 1. Start the MQTT broker

```bash
docker compose -f docker/compose/dev.yml up -d mqtt
```

### 2. Build and start the core services

```bash
docker compose -f docker/compose/dev.yml up -d --build
```

### 3. Verify health endpoints

```bash
curl http://localhost:8000/health   # comms-bridge
curl http://localhost:8001/health   # sensor-hub
curl http://localhost:8002/health   # data-logger
curl http://localhost:8010/health   # ai-service
```

## What's Running

| Service       | Port | Description                        |
| ------------- | ---- | ---------------------------------- |
| mqtt          | 1883 | Eclipse Mosquitto message broker   |
| comms-bridge  | 8000 | Mesh networking and radio control  |
| sensor-hub    | 8001 | Sensor registry and readings       |
| data-logger   | 8002 | Persistence (notes, preferences)   |
| ai-service    | 8010 | AI inference (chat, classification)|
| db-viewer     | 8080 | Datasette database viewer          |

## Database Viewer

In development mode, you can browse all databases at:

- **http://localhost:8080/general** - Preferences, notes, sensors
- **http://localhost:8080/mesh** - Mesh contacts and messages
- **http://localhost:8080/ai** - AI conversations, messages, models

## Common Workflows

### View logs for a specific service

```bash
docker compose -f docker/compose/dev.yml logs -f ai-service
```

### Rebuild and restart a service

```bash
docker compose -f docker/compose/dev.yml up -d --build --force-recreate ai-service
```

Or use the convenience script:

```bash
./scripts/dev-restart.sh --service ai-service --rebuild
```

### Clean rebuild (no cache) of all services

```bash
docker compose -f docker/compose/dev.yml build --no-cache
docker compose -f docker/compose/dev.yml up -d
```

### Stop everything

```bash
docker compose -f docker/compose/dev.yml down
```

Or:

```bash
./scripts/dev-stop.sh
```

### Stop and remove volumes

```bash
docker compose -f docker/compose/dev.yml down -v
```

Or:

```bash
./scripts/dev-stop.sh --volumes
```

## AI Model Management

AI models are stored in a Docker volume and need to be downloaded on first run.

### Automatic Download

The `dev-start.sh` script automatically downloads models if not present.

### Manual Download

```bash
./scripts/download-models.sh --all
```

### Upload Custom Models

```bash
./scripts/upload-model.sh path/to/model.gguf --id my-model --type language
```

See `docs/models/README.md` for detailed model management.

## Knowledge Base Management

The AI service uses a pre-built knowledge base for outdoor survival, navigation, and first aid topics.

### Automatic Download

The `dev-start.sh` script automatically downloads the knowledge base if not present.

### Manual Download

```bash
# Download latest version
./scripts/download-knowledge.sh

# Download specific version
./scripts/download-knowledge.sh --version v1.0.1

# Verify installation
./scripts/verify-knowledge.sh
```

### Check Status

```bash
./scripts/knowledge-info.sh
```

See `docs/knowledge-base.md` for detailed knowledge base management.

## Running the UI

The Qt/QML frontend runs outside Docker:

```bash
cd device/apps/ui
poetry run python main.py
```

Or use:

```bash
./scripts/dev-start.sh --ui
```

## Configuration Notes

- Each service uses environment variables configured in the Compose file
- Service configs: `CORE_DAEMON_CONFIG`, `AI_SERVICE_CONFIG`, etc.
- Prefer environment variables for secrets; keep them out of the repo
- Internal message schemas: `device/libs/schemas/`

## Troubleshooting

### Port in use

Another process may be bound to ports. Stop conflicting processes or change
host ports in `docker/compose/dev.yml`.

Common ports: `1883` (MQTT), `8000-8002`, `8010`, `8080`

### Container not picking up code changes

```bash
docker compose -f docker/compose/dev.yml build --no-cache ai-service
docker compose -f docker/compose/dev.yml up -d --force-recreate ai-service
```

### Database tables missing

Restart the db-viewer to pick up schema changes:

```bash
docker compose -f docker/compose/dev.yml restart db-viewer
```

### AI service not responding

Check if models are downloaded:

```bash
./scripts/dev-status.sh
```

Download if missing:

```bash
./scripts/download-models.sh --all
```

## Next Steps

- Explore service READMEs under `device/services/*/README.md`
- See `docs/models/README.md` for AI model management
- See `docs/database-schema.md` for database structure
- See the top-level `README.md` for test and lint commands
