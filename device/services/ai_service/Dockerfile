# AI Service Dockerfile
# Supports both ARM (Raspberry Pi 5) and x86_64 development

FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

# Install build dependencies for llama-cpp-python
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==2.2.1

# Copy and install Python dependencies
COPY pyproject.toml poetry.lock /app/
RUN poetry config virtualenvs.create false && \
    poetry install --only main --no-interaction --no-ansi --no-root

# Install ML dependencies
# llama-cpp-python: For GGUF language models (Phi-3, TinyLlama, etc.)
# Note: Building from source for CPU-only support on any architecture
# IMPORTANT: Pin numpy<2.0 for tflite-runtime compatibility (numpy 2.x has breaking changes)
RUN pip install --no-cache-dir \
    "numpy>=1.24.0,<2.0" \
    llama-cpp-python==0.2.90

# tflite-runtime: For TensorFlow Lite vision models (MobileNetV3)
# Using official Google package that works on both ARM and x86
# Note: tflite-runtime 2.14.0 requires numpy<2.0
RUN pip install --no-cache-dir \
    tflite-runtime==2.14.0 || \
    pip install --no-cache-dir tensorflow-cpu==2.14.0

# Pillow for image preprocessing
RUN pip install --no-cache-dir Pillow>=10.0.0

# Copy application code
COPY device /app/device

# Create model directory
RUN mkdir -p /opt/waycore/models/language \
             /opt/waycore/models/vision \
             /opt/waycore/models/labels

# Set model path environment variable
ENV WAYCORE_MODEL_PATH=/opt/waycore/models
ENV LLAMA_CPP_LIB_PATH=/usr/local/lib

EXPOSE 8010
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD wget -qO- http://localhost:8010/health || exit 1

CMD ["python", "-m", "device.services.ai_service.main"]
