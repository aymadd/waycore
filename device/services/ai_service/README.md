# AI Service

## Overview

The AI Service performs on-device inference. It consumes normalized inputs from
the system (e.g., sensors, modules, or pre-aggregated messages), applies
deterministic preprocessing, runs the model via the local inference engine, and
publishes typed outputs back onto the message bus.

## Responsibilities

- Input normalization and validation (`preprocessing.py`)
- Model runtime abstraction and inference (`engine.py`)
- Service lifecycle and message bus integration (`service.py`)
- Thin API surface for local RPC or debug hooks (`api.py`)

## Directory layout

- `main.py`: entrypoint for running the service.
- `service.py`: service orchestration, messaging, and lifecycle.
- `api.py`: optional API endpoints/hooks for local control.
- `preprocessing.py`: feature extraction and input transforms.
- `engine.py`: model loading and inference execution.
- `config/`: service configuration in YAML.
- `models/`: model runners and model mapping config (`models/config/models.yaml`).
- `tests/`: unit and integration tests for this service.

## Configuration

- Primary config: `config/` (YAML). Keep runtime-tunable values (thresholds,
  topic names, batching) here.
- Environment variables can be used to override sensitive or deployment-specific
  values.
- Message schemas: see the shared schemas under `device/libs/schemas/`.

## Run locally (Poetry)

```bash
poetry install
poetry run python -m device.services.ai_service.main
```

## Testing

```bash
poetry run pytest device/services/ai_service/tests -q
```

## Notes

- Favor pure, deterministic preprocessing to ease testing.
- Inference code in `engine.py` should be isolated behind a clean interface to
  allow swapping backends.
- All bus I/O must use the shared schema types to ensure interop with other
  services.
