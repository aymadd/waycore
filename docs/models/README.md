# AI Model Management Guide

Waycore runs AI models locally on-device for offline-first operation. This guide
covers model management, uploading custom models, and troubleshooting.

## Table of Contents

- [Hardware Constraints](#hardware-constraints)
- [Default Models](#default-models)
- [Downloading Models](#downloading-models)
- [System Prompt Configuration](#system-prompt-configuration)
- [Uploading Custom Models](#uploading-custom-models)
- [Managing Models](#managing-models)
- [Supported Formats](#supported-formats)
- [Model Sources](#model-sources)
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)

---

## Hardware Constraints

| Resource    | Limit          | Notes                              |
| ----------- | -------------- | ---------------------------------- |
| **RAM**     | 4GB total      | ~2.5GB available for AI inference  |
| **Storage** | 64-128GB       | Typical SD card size               |
| **CPU**     | ARM Cortex-A76 | Raspberry Pi 5, CPU-only inference |
| **Power**   | Battery        | Model loading is energy-expensive  |

### One Model Per Category Rule

Due to RAM constraints, only **one model per category** can be active at a time:

- ✅ One **language model** (e.g., Phi-3 OR TinyLlama, not both)
- ✅ One **vision model** (e.g., MobileNetV3 OR custom classifier)

You can store multiple models on the device, but only one per category is loaded
into memory. Switching models requires an unload/load cycle.

---

## Default Models

Waycore ships with these models pre-configured (download required):

| Model         | Type     | Size   | Format | Description                            |
| ------------- | -------- | ------ | ------ | -------------------------------------- |
| Phi-3 Mini 4K | Language | 2.3 GB | GGUF   | Chat/Q&A, 4-bit quantized (Q4_K_M)     |
| MobileNetV3   | Vision   | 5 MB   | TFLite | ImageNet classification (1000 classes) |

---

## Downloading Models

### Using the Download Script (Recommended)

The easiest way to get started is using the provided download script:

```bash
# Download all default models
./scripts/download-models.sh --all

# Download only the language model
./scripts/download-models.sh --language

# Download only the vision model
./scripts/download-models.sh --vision

# Download ImageNet labels
./scripts/download-models.sh --labels

# Specify custom model directory
./scripts/download-models.sh --all --dir /path/to/models
```

### Manual Download

If you prefer to download manually:

**Phi-3 Mini 4K (Q4_K_M)**

```bash
mkdir -p /opt/waycore/models/language
wget -O /opt/waycore/models/language/phi-3-mini-4k-instruct.Q4_K_M.gguf \
  "https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf"
```

**MobileNetV3 Small**

```bash
mkdir -p /opt/waycore/models/vision
wget -O /opt/waycore/models/vision/mobilenet_v3_small.tflite \
  "https://storage.googleapis.com/tfhub-lite-models/google/lite-model/imagenet/mobilenet_v3_small_100_224/classification/5/default/1.tflite"
```

**ImageNet Labels**

```bash
mkdir -p /opt/waycore/models/labels
wget -O /opt/waycore/models/labels/imagenet_labels.txt \
  "https://storage.googleapis.com/download.tensorflow.org/data/ImageNetLabels.txt"
```

---

## System Prompt Configuration

The AI system prompt defines Waycore AI's personality, behavior, and response
style.

### Location

```
device/services/ai_service/config/system_prompt.txt
```

### Editing the Prompt

1. Open the config file:
   ```bash
   nano device/services/ai_service/config/system_prompt.txt
   ```

2. Edit the prompt content. The prompt is plain text with markdown formatting.

3. Restart the AI service:
   ```bash
   docker compose -f docker/compose/dev.yml restart ai-service
   ```

### Prompt Guidelines

- **Be concise**: Users have limited screen space and battery
- **Safety-first**: Prioritize user safety in outdoor/survival contexts
- **Practical focus**: Assume no internet and limited resources
- **Clear formatting**: Use markdown for structure (bullets, bold for warnings)

### Default Prompt

The default prompt configures Waycore AI for:

- Outdoor, survival, and tactical operations
- Plant/wildlife identification with safety warnings
- Navigation and location guidance
- Equipment and technical troubleshooting

See the full default prompt in the
[config file](../../device/services/ai_service/config/system_prompt.txt).

---

## Uploading Custom Models

### Via Script

The `upload-model.sh` script provides a convenient way to upload models:

```bash
# Upload a language model
./scripts/upload-model.sh path/to/model.gguf --id my-llm --type language

# Upload a vision model
./scripts/upload-model.sh path/to/model.tflite --id my-classifier --type vision

# Upload and immediately activate
./scripts/upload-model.sh model.gguf --id my-llm --type language --activate
```

### Via API

Upload directly to the AI service:

```bash
# Upload a language model
curl -X POST http://localhost:8010/api/models/upload \
  -F "file=@model.gguf" \
  -F "id=my-llm" \
  -F "type=language" \
  -F "name=My Custom LLM"

# Upload a vision model
curl -X POST http://localhost:8010/api/models/upload \
  -F "file=@classifier.tflite" \
  -F "id=plant-id" \
  -F "type=vision" \
  -F "name=Plant Identifier"
```

### Via Docker Volume

For very large models, copy directly to the Docker volume:

```bash
# Find the volume path
docker volume inspect waycore-models

# Copy model file
sudo cp model.gguf /var/lib/docker/volumes/waycore-models/_data/language/

# Restart AI service to detect new model
docker restart waycore-ai-service
```

---

## Managing Models

### List Installed Models

```bash
# Via API
curl http://localhost:8010/api/models

# Response
{
  "models": [
    {
      "id": "phi3-mini",
      "type": "language",
      "name": "Phi-3 Mini 4K",
      "format": "gguf",
      "size_mb": 2300,
      "active": true
    },
    {
      "id": "mobilenetv3",
      "type": "vision",
      "name": "MobileNetV3 Small",
      "format": "tflite",
      "size_mb": 5,
      "active": true
    }
  ],
  "active": {
    "language": "phi3-mini",
    "vision": "mobilenetv3"
  }
}
```

### Switch Active Model

```bash
# Activate a different language model
curl -X POST http://localhost:8010/api/models/tinyllama/activate

# Response
{
  "success": true,
  "message": "Model 'tinyllama' is now active for language tasks.",
  "previous": "phi3-mini"
}
```

### Delete a Model

```bash
# Remove an inactive model
curl -X DELETE http://localhost:8010/api/models/my-old-model

# Response
{
  "success": true,
  "message": "Model 'my-old-model' deleted.",
  "freed_mb": 800
}
```

> ⚠️ You cannot delete an active model. Activate a different model first.

---

## Supported Formats

### Language Models (GGUF)

**Format**: [GGUF](https://github.com/ggerganov/ggml/blob/master/docs/gguf.md)
(GPT-Generated Unified Format)

**Compatibility**: Any model compatible with
[llama.cpp](https://github.com/ggerganov/llama.cpp)

**Recommended Models**:

| Model          | Params | Quant  | Size   | Speed     | Quality    |
| -------------- | ------ | ------ | ------ | --------- | ---------- |
| Phi-3 Mini 4K  | 3.8B   | Q4_K_M | 2.3 GB | ~5 tok/s  | ⭐⭐⭐⭐⭐ |
| TinyLlama 1.1B | 1.1B   | Q4_K_M | 0.8 GB | ~15 tok/s | ⭐⭐⭐     |
| Gemma 2B       | 2B     | Q4_K_M | 1.5 GB | ~8 tok/s  | ⭐⭐⭐⭐   |

**Quantization Guide**:

- `Q4_K_M` - Best balance of size/quality (recommended)
- `Q4_K_S` - Slightly smaller, slightly lower quality
- `Q8_0` - Higher quality, but larger (may not fit in RAM)

### Vision Models (TensorFlow Lite)

**Format**: TensorFlow Lite (`.tflite`)

**Recommended Models**:

| Model              | Input Size | Classes | Size  | Speed  |
| ------------------ | ---------- | ------- | ----- | ------ |
| MobileNetV3 Small  | 224x224    | 1000    | 5 MB  | ~50ms  |
| MobileNetV3 Large  | 224x224    | 1000    | 22 MB | ~100ms |
| EfficientNet-Lite0 | 224x224    | 1000    | 12 MB | ~80ms  |

**Labels File**: Vision models require a labels file (one label per line).
Default: `imagenet_labels.txt` (1000 ImageNet classes)

---

## Model Sources

### Language Models

| Model          | Source                                                                       |
| -------------- | ---------------------------------------------------------------------------- |
| Phi-3 Mini 4K  | [HuggingFace](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf)  |
| TinyLlama 1.1B | [HuggingFace](https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF) |
| Gemma 2B       | [HuggingFace](https://huggingface.co/google/gemma-2b-it-GGUF)                |

### Vision Models

| Model        | Source                                                                                          |
| ------------ | ----------------------------------------------------------------------------------------------- |
| MobileNetV3  | [TensorFlow Hub](https://tfhub.dev/google/imagenet/mobilenet_v3_small_100_224/classification/5) |
| EfficientNet | [TensorFlow Hub](https://tfhub.dev/tensorflow/efficientnet/lite0/classification/2)              |

### Custom/Specialty Models

| Use Case | Model       | Source                                              |
| -------- | ----------- | --------------------------------------------------- |
| Plant ID | PlantNet    | [PlantNet API](https://plantnet.org/)               |
| Bird ID  | BirdNET     | [GitHub](https://github.com/kahst/BirdNET-Analyzer) |
| Wildlife | iNaturalist | Custom TFLite export                                |

---

## API Reference

### GET /api/models

List all installed models.

**Response**:

```json
{
  "models": [
    {
      "id": "phi3-mini",
      "type": "language",
      "name": "Phi-3 Mini 4K",
      "format": "gguf",
      "size_mb": 2300,
      "active": true,
      "path": "/opt/waycore/models/language/phi-3-mini-4k-instruct.Q4_K_M.gguf"
    }
  ],
  "active": {
    "language": "phi3-mini",
    "vision": "mobilenetv3"
  },
  "limits": {
    "max_language": 1,
    "max_vision": 1,
    "storage_used_mb": 2305,
    "storage_available_mb": 10000
  }
}
```

### POST /api/models/upload

Upload a new model.

**Request** (multipart/form-data):

- `file` (required): Model file
- `id` (required): Unique model ID
- `type` (required): "language" or "vision"
- `name` (optional): Display name
- `activate` (optional): "true" to activate immediately

**Response**:

```json
{
  "success": true,
  "model_id": "my-model",
  "size_mb": 800,
  "message": "Model uploaded successfully."
}
```

### POST /api/models/{model_id}/activate

Activate a model (deactivates current model of same type).

**Response**:

```json
{
  "success": true,
  "model_id": "tinyllama",
  "previous": "phi3-mini",
  "message": "Model 'tinyllama' is now active for language tasks."
}
```

### DELETE /api/models/{model_id}

Delete a model from the device.

**Response**:

```json
{
  "success": true,
  "model_id": "old-model",
  "freed_mb": 800
}
```

### GET /api/models/{model_id}/info

Get detailed model information.

**Response**:

```json
{
  "id": "phi3-mini",
  "type": "language",
  "name": "Phi-3 Mini 4K",
  "format": "gguf",
  "size_mb": 2300,
  "active": true,
  "path": "/opt/waycore/models/language/phi-3-mini-4k-instruct.Q4_K_M.gguf",
  "metadata": {
    "context_length": 4096,
    "quantization": "Q4_K_M",
    "source_url": "https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf"
  }
}
```

---

## Troubleshooting

### Model Won't Load

1. **Check format**: Language models must be GGUF, vision models must be TFLite
2. **Verify file integrity**: Re-download if corrupted
3. **Check storage space**: `df -h /opt/waycore/models`
4. **Check logs**: `docker logs waycore-ai-service`

### Out of Memory Errors

- Only one model per type can be active at a time
- Consider using a smaller model (e.g., TinyLlama instead of Phi-3)
- Restart the AI service to clear memory: `docker restart waycore-ai-service`
- Check memory usage: `docker stats waycore-ai-service`

### Slow Inference

| Model Type | Expected Speed | Notes                 |
| ---------- | -------------- | --------------------- |
| Language   | ~5-15 tok/s    | Depends on model size |
| Vision     | ~50-100ms      | Per image             |

**Tips**:

- Use 4-bit quantization (Q4_K_M) for language models
- Smaller models are faster (TinyLlama > Phi-3)
- Check CPU usage: `htop` or `docker stats`

### Upload Fails

1. **Check file size**: Large files may timeout
2. **Check disk space**: Need 2x model size during upload
3. **Check permissions**: AI service needs write access to model directory
4. **Try direct copy**: Use Docker volume mount for very large files

### Model Not Detected

After manually copying a model file:

```bash
# Restart AI service to rescan models
docker restart waycore-ai-service

# Or trigger a rescan via API
curl -X POST http://localhost:8010/api/models/rescan
```

---

## Storage Structure

```
/opt/waycore/models/
├── language/
│   ├── phi-3-mini-4k-instruct.Q4_K_M.gguf  # Active
│   └── tinyllama-1.1b.Q4_K_M.gguf          # Inactive
├── vision/
│   ├── mobilenet_v3_small.tflite           # Active
│   └── plant_classifier.tflite             # Inactive
├── labels/
│   └── imagenet_labels.txt
└── registry.json                           # Model metadata and active status
```

---

## See Also

- [AI Model Strategy](../../local_plan/11-ai-model-strategy.md) - Technical
  architecture
- [AI Service API](../api/ai-service.openapi.json) - Full OpenAPI specification
- [Local Development](../local_dev_docker.md) - Docker setup guide
