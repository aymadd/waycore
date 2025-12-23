# Waycore

Modular, communications-first field computer designed for outdoors, EDC, survival, and trades/handyman use. The system separates a Linux SBC “main brain” (UI, AI, storage, networking) from a low-power ESP32-S3 sidecar (radios, GPS, SOS, power policy) to ensure reliability even when the UI is busy or rebooting.

For the high-level vision and scope, see: `docs/overview.md`

## Highlights
- Communications-first and modular by design
- On-device intelligence without cloud dependency
- Reliable low-power controller for critical functions (e.g., SOS)
- Developer-friendly with clear interfaces and mockable hardware

## Repository Structure (MVP)
The repo is organized for a simulation-first workflow on a developer laptop using Docker Compose and mocked hardware.

```
device/
  apps/ui/                      # Qt/QML frontend (PySide6 backend)
  services/
    core_daemon/                # state machine, modes, policies
    module_manager/             # module discovery and lifecycle
    ai_service/                 # inference endpoints (ONNX/TFLite/OpenCV)
    comms_bridge/               # Meshtastic + TAK integration
  drivers/
    mock/                       # mocked drivers for laptop development
    real/                       # real hardware drivers (added later)
  proto/                        # JSON schemas and message contracts
  docker/                       # compose + container notes (simulation-first)
docs/
LICENSE
```

## Development Strategy (Simulation-First)
Build Phase 1 targets a full software MVP without hardware:
- UI skeleton at fixed target resolution (e.g. 480×800)
- Mock ESP32 + sensors
- AI inference pipeline (on-demand)
- Module protocol and discovery

Later phases add bench hardware (Raspberry Pi 5, Meshtastic, camera/display), then custom PCB, and finally field testing.

## Getting Started
1) Read the architecture and scope in `docs/overview.md`.
2) Explore the directory layout under `device/`.
3) Review `CONTRIBUTING.md` for conventions and commit style.
4) (Optional) Copy `device/docker/compose.sample.yml` to a local compose, and iterate on service stubs as code is added.

## Contributing
- Follow Conventional Commits and small, focused PRs.
- Open issues with the provided templates (bug, feature, tech debt, docs).
- See `CONTRIBUTING.md` and `CODE_OF_CONDUCT.md`.

## Security
Security disclosures are welcome. See `SECURITY.md` for details.


