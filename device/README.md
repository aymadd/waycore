# Device Workspace

Top-level workspace for the runtime device stack. This mirrors the architecture in `docs/overview.md`.

## Layout
- `apps/ui/`: Qt/QML frontend with a Python (PySide6) backend
- `services/`:
  - `core_daemon/`: state machine, modes, policies
  - `module_manager/`: module discovery and lifecycle
  - `ai_service/`: inference endpoints (ONNX Runtime / TFLite / OpenCV)
  - `comms_bridge/`: Meshtastic + TAK integration
- `drivers/`:
  - `mock/`: mock drivers for laptop development
  - `real/`: real hardware drivers added as hardware integrates
- `proto/`: JSON schemas and versioned message contracts
- `docker/`: compose files and container notes for simulation-first development

Start by building mocked flows and services locally. Hardware integration comes later phases.


