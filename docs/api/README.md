# Waycore API Documentation

Auto-generated OpenAPI specifications for all Waycore services.

**Last updated:** 2025-12-26 02:45:08 UTC

## Services

| Service | Port | OpenAPI Spec |
|---------|------|--------------|
| core-daemon | 8001 | [core-daemon.openapi.json](./core-daemon.openapi.json) |
| comms-bridge | 8003 | [comms-bridge.openapi.json](./comms-bridge.openapi.json) |
| data-logger | 8002 | [data-logger.openapi.json](./data-logger.openapi.json) |
| ai-service | 8004 | [ai-service.openapi.json](./ai-service.openapi.json) |
| module-manager | 8005 | [module-manager.openapi.json](./module-manager.openapi.json) |

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
openapi-generator-cli generate -i docs/api/core-daemon.openapi.json   -g python -o generated/python-client/

# Generate TypeScript client
openapi-generator-cli generate -i docs/api/core-daemon.openapi.json   -g typescript-axios -o generated/ts-client/
```

## Regenerating Specs

Specs are automatically regenerated on commit via pre-commit hook.

To manually regenerate:

```bash
python scripts/generate-openapi.py
```
