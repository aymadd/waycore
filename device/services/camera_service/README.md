# Camera Service

Camera control and photo management service for Waycore.

## Overview

The camera service provides:
- Camera hardware abstraction via mock/real drivers
- Photo capture with automatic file storage
- Photo management (list, view, delete)
- Camera settings configuration

## API Endpoints

### Camera Control

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/camera/status` | Get camera state (ready, capturing, error) |
| GET | `/api/camera/settings` | Get current camera settings |
| PUT | `/api/camera/settings` | Update camera settings |
| POST | `/api/camera/capture` | Take a photo, return photo info |

### Photo Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/photos` | List all photos with metadata |
| GET | `/api/photos/{id}` | Get single photo details |
| GET | `/api/photos/{id}/file` | Get photo file (binary) |
| DELETE | `/api/photos/{id}` | Delete a photo |

## Configuration

```yaml
# config/default.yaml
mqtt_broker_url: "mqtt://mqtt:1883"
port: 8006

camera:
  driver: mock  # or "real" for hardware
  photos_dir: /app/data/photos
  default_resolution:
    width: 1280
    height: 720
  watermark: true
```

## Usage

### Local Development

```bash
# Run service
cd device/services/camera_service
USE_UNIX_SOCKET=false python main.py

# Test endpoints
curl http://localhost:8006/api/camera/status
curl -X POST http://localhost:8006/api/camera/capture
curl http://localhost:8006/api/photos
```

### Docker

```bash
docker-compose -f docker/compose/dev.yml up camera-service
```

## Testing

```bash
poetry run pytest device/services/camera_service/tests/ -v
```
