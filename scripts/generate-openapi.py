#!/usr/bin/env python3
"""Generate OpenAPI specifications for all Waycore API services.

This script creates OpenAPI JSON specs for each service and saves them to docs/api/.
It also generates a combined index and updates the README.

Usage:
    python scripts/generate-openapi.py

The script is designed to be run as a pre-commit hook or manually.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def create_mock_core_daemon_service() -> Any:
    """Create a mock CoreDaemonService for API generation."""
    from unittest.mock import MagicMock

    service = MagicMock()
    service.is_healthy.return_value = True
    service.get_status.return_value = {"state": "running"}
    return service


def create_mock_comms_bridge_service() -> Any:
    """Create a mock CommsBridgeService for API generation."""
    from unittest.mock import MagicMock

    service = MagicMock()
    service.is_healthy.return_value = True
    return service


def create_mock_data_logger_service() -> Any:
    """Create a mock DataLoggerService for API generation."""
    from unittest.mock import MagicMock

    service = MagicMock()
    service.is_healthy.return_value = True
    return service


def create_mock_ai_service() -> Any:
    """Create a mock AIService for API generation."""
    from unittest.mock import MagicMock

    service = MagicMock()
    service.is_healthy.return_value = True
    service.response_source = "ai-service"
    return service


def create_mock_module_manager_service() -> Any:
    """Create a mock ModuleManagerService for API generation."""
    from unittest.mock import MagicMock

    service = MagicMock()
    service.is_healthy.return_value = True
    service.list_modules.return_value = []
    return service


def create_mock_camera_service() -> Any:
    """Create a mock CameraService for API generation."""
    from unittest.mock import MagicMock

    service = MagicMock()
    service.is_healthy.return_value = True
    service.get_camera_status.return_value = {"state": "ready", "is_ready": True}
    service.get_camera_settings.return_value = {
        "resolution_width": 1280,
        "resolution_height": 720,
        "is_front_camera": False,
        "available_resolutions": [(640, 480), (1280, 720), (1920, 1080)],
    }
    service.list_photos.return_value = []
    service.get_photo_filepath.return_value = None
    return service


# Service configuration: (module_path, create_app_function, mock_factory, output_name, port)
SERVICES = [
    (
        "device.services.core_daemon.api",
        "create_app",
        create_mock_core_daemon_service,
        "core-daemon",
        8001,
    ),
    (
        "device.services.comms_bridge.api",
        "create_app",
        create_mock_comms_bridge_service,
        "comms-bridge",
        8003,
    ),
    (
        "device.services.data_logger.api",
        "create_app",
        create_mock_data_logger_service,
        "data-logger",
        8002,
    ),
    (
        "device.services.ai_service.api",
        "create_app",
        create_mock_ai_service,
        "ai-service",
        8004,
    ),
    (
        "device.services.module_manager.api",
        "create_app",
        create_mock_module_manager_service,
        "module-manager",
        8005,
    ),
    (
        "device.services.camera_service.api",
        "create_app",
        create_mock_camera_service,
        "camera-service",
        8006,
    ),
]


def generate_openapi_spec(
    module_path: str,
    create_app_fn: str,
    mock_factory: Any,
    service_name: str,
    port: int,
) -> dict[str, Any] | None:
    """Generate OpenAPI spec for a single service."""
    try:
        import importlib

        module = importlib.import_module(module_path)
        create_app = getattr(module, create_app_fn)

        # Create mock service and app
        mock_service = mock_factory()
        app = create_app(mock_service)

        # Get OpenAPI schema
        openapi_schema = app.openapi()

        # Add server information
        openapi_schema["servers"] = [
            {"url": f"http://localhost:{port}", "description": "Local development"},
            {"url": f"http://{service_name}:{port}", "description": "Docker network"},
        ]

        # Add metadata
        openapi_schema["info"]["version"] = "0.1.0"
        desc = f"API specification for the Waycore {service_name} service."
        openapi_schema["info"]["description"] = desc

        return openapi_schema

    except Exception as e:
        print(f"  ⚠️  Error generating spec for {service_name}: {e}")
        return None


def save_spec(spec: dict[str, Any], output_path: Path) -> None:
    """Save OpenAPI spec to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")  # Trailing newline


def generate_readme(services: list[tuple[str, int, Path]], docs_dir: Path) -> None:
    """Generate README with links to all API specs."""
    # Note: Removed dynamic timestamp to avoid pre-commit loop
    # The git commit history shows when this was last updated

    readme_content = """# Waycore API Documentation

Auto-generated OpenAPI specifications for all Waycore services.

## Services

| Service | Port | OpenAPI Spec |
|---------|------|--------------|
"""

    for service_name, port, spec_path in services:
        rel_path = spec_path.name
        readme_content += f"| {service_name} | {port} | [{rel_path}](./{rel_path}) |\n"

    readme_content += """
## Usage

### View in Swagger UI

You can view any of these specs using Swagger UI:

1. **Online viewer**: Go to [Swagger Editor](https://editor.swagger.io/) and paste the JSON
2. **Local viewer**: Run a service and visit `http://localhost:<port>/docs`

### Import into Postman

1. Open Postman
2. Click "Import" → "File"
3. Select the JSON spec file

### Generate Client SDKs

Use [OpenAPI Generator](https://openapi-generator.tech/) to generate client code:

```bash
# Install OpenAPI Generator
npm install @openapitools/openapi-generator-cli -g

# Generate Python client
openapi-generator-cli generate -i docs/api/core-daemon.openapi.json \
  -g python -o generated/python-client/

# Generate TypeScript client
openapi-generator-cli generate -i docs/api/core-daemon.openapi.json \
  -g typescript-axios -o generated/ts-client/
```

## Regenerating Specs

Specs are automatically regenerated on commit via pre-commit hook.

To manually regenerate:

```bash
python scripts/generate-openapi.py
```
"""

    readme_path = docs_dir / "README.md"
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)


def generate_combined_spec(
    individual_specs: list[tuple[str, dict[str, Any]]], docs_dir: Path
) -> None:
    """Generate a combined OpenAPI spec with all services."""
    combined: dict[str, Any] = {
        "openapi": "3.1.0",
        "info": {
            "title": "Waycore API (Combined)",
            "version": "0.1.0",
            "description": "Combined API specification for all Waycore services.",
        },
        "servers": [
            {"url": "http://localhost", "description": "Local development (use service ports)"},
        ],
        "paths": {},
        "components": {"schemas": {}},
    }

    for service_name, spec in individual_specs:
        # Prefix paths with service name for clarity
        for path, path_item in spec.get("paths", {}).items():
            # Add tag to all operations
            for method in ["get", "post", "put", "delete", "patch"]:
                if method in path_item:
                    if "tags" not in path_item[method]:
                        path_item[method]["tags"] = []
                    path_item[method]["tags"].insert(0, service_name)

            combined["paths"][path] = path_item

        # Merge schemas (with service prefix to avoid conflicts)
        for schema_name, schema in spec.get("components", {}).get("schemas", {}).items():
            prefixed_name = f"{service_name.replace('-', '_')}_{schema_name}"
            combined["components"]["schemas"][prefixed_name] = schema

    save_spec(combined, docs_dir / "combined.openapi.json")


def main() -> int:
    """Generate OpenAPI specs for all services."""
    docs_dir = PROJECT_ROOT / "docs" / "api"
    docs_dir.mkdir(parents=True, exist_ok=True)

    print("🔧 Generating OpenAPI specifications...\n")

    generated_services: list[tuple[str, int, Path]] = []
    individual_specs: list[tuple[str, dict[str, Any]]] = []
    errors = 0

    for module_path, create_app_fn, mock_factory, service_name, port in SERVICES:
        output_path = docs_dir / f"{service_name}.openapi.json"
        print(f"  📄 {service_name}...", end=" ")

        spec = generate_openapi_spec(module_path, create_app_fn, mock_factory, service_name, port)

        if spec:
            save_spec(spec, output_path)
            generated_services.append((service_name, port, output_path))
            individual_specs.append((service_name, spec))
            print("✅")
        else:
            errors += 1
            print("❌")

    # Generate combined spec
    if individual_specs:
        print("\n  📦 Generating combined spec...", end=" ")
        generate_combined_spec(individual_specs, docs_dir)
        print("✅")

    # Generate README
    print("  📝 Updating README...", end=" ")
    generate_readme(generated_services, docs_dir)
    print("✅")

    print(f"\n✨ Generated {len(generated_services)} OpenAPI specs in docs/api/")

    if errors > 0:
        print(f"⚠️  {errors} service(s) had errors")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
