# UI App

This directory contains the Qt/QML application per:
- `local_plan/07-ui-implementation-plan.md`
- `local_plan/09-app-development-guide.md`
- `local_plan/10-design-system.md`

## Structure

- `main.py` - Application entry point
- `api_client.py` - Client for communicating with backend services via Unix domain sockets
- `qml/` - QML UI files
  - `Main.qml` - Main application window
  - `Theme.qml` - Design system singleton (colors/spacing/typography)
  - `components/` - Reusable QML components

## Running the Application

### Quick Start

```bash
# Using Poetry (recommended)
poetry run waycore-ui

# Or using Python module syntax
poetry run python -m device.apps.ui.main
```

### Local Testing

For detailed instructions on setting up Qt6, installing dependencies, and testing locally, see:
- **[LOCAL_TESTING.md](LOCAL_TESTING.md)** - Complete local testing guide

## Architecture

The UI communicates with backend services via Unix domain sockets (UDS) located at `/tmp/waycore/*.sock`. The `api_client.py module provides a client for making HTTP requests over UDS.

Apps should follow the template under `device/apps/ui/apps/{app_name}` as described in the App Development Guide.
