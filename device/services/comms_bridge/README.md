# Comms Bridge Service

## Overview

The Comms Bridge connects the internal message bus to external communication
transports. It coordinates radio links and gateways (e.g., TAK) to exchange
typed messages with the outside world.

## Responsibilities

- Manage and abstract radio transports (`radio_manager.py`)
- Gateway integration for external systems (`tak_gateway.py`)
- Translate between internal schemas and external payload formats
- Service lifecycle and message bus integration (`service.py`, `main.py`)

## Directory layout

- `main.py`: service entrypoint.
- `service.py`: orchestration and bus I/O.
- `api.py`: optional control or health endpoints.
- `radio_manager.py`: radio transport coordination.
- `tak_gateway.py`: external gateway adapter.
- `config/`: runtime configuration in YAML.
- `tests/`: unit and integration tests for this service.
- `Dockerfile`: container build for this service.

## Configuration

- Place channel topics, endpoints, credentials, and rate limits in `config/`.
- Prefer environment variables for secrets.
- Use shared message types from `device/libs/schemas/` for internal exchange.

## Run locally (Poetry)

```bash
poetry install
poetry run python -m device.services.comms_bridge.main
```

## Run with Docker

```bash
docker build -t waycore/comms-bridge -f device/services/comms_bridge/Dockerfile .
docker run --rm -it waycore/comms-bridge
```

## Testing

```bash
poetry run pytest device/services/comms_bridge/tests -q
```

## Notes

- Keep wire-format conversions localized to adapters to avoid leaking external
  formats into core logic.
- Ensure backpressure and rate-limiting to protect the internal bus and radio
  links.
