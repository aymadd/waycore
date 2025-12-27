#!/bin/bash
# Download AI models for Waycore
# Usage: ./scripts/download-models.sh [--all|--language|--vision|--profile PROFILE]
#
# This script downloads AI models using either direct URLs or HuggingFace Hub.
# The model configuration is defined in config/models.yaml.

set -e

# Default model directory
MODEL_DIR="${WAYCORE_MODEL_PATH:-./models}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Model URLs (fallback if not using profile-based download)
PHI3_URL="https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf"
PHI3_FILENAME="phi-3-mini-4k-instruct.Q4_K_M.gguf"

# MobileNetV3 from TensorFlow Hub (converted to TFLite)
MOBILENET_URL="https://storage.googleapis.com/tfhub-lite-models/google/lite-model/imagenet/mobilenet_v3_small_100_224/classification/5/default/1.tflite"
MOBILENET_FILENAME="mobilenet_v3_small.tflite"

# ImageNet labels
LABELS_URL="https://storage.googleapis.com/download.tensorflow.org/data/ImageNetLabels.txt"
LABELS_FILENAME="imagenet_labels.txt"

print_usage() {
    echo "Usage: $0 [--all|--language|--vision|--labels|--profile PROFILE]"
    echo ""
    echo "Options:"
    echo "  --all       Download all models (language + vision + labels)"
    echo "  --language  Download Phi-3 Mini language model (~2.3GB)"
    echo "  --vision    Download MobileNetV3 vision model (~5MB)"
    echo "  --labels    Download ImageNet labels (~10KB)"
    echo "  --profile   Download models from a profile (basic, nature, full)"
    echo "  --list      List available profiles and models"
    echo "  --dir DIR   Set model directory (default: $MODEL_DIR)"
    echo ""
    echo "Environment:"
    echo "  WAYCORE_MODEL_PATH  Model directory path"
    echo ""
    echo "Profiles (via config/models.yaml):"
    echo "  basic   - General classification only (MobileNetV3)"
    echo "  nature  - Outdoor/nature focus (+ iNaturalist model)"
    echo "  full    - All available models"
}

download_file() {
    local url="$1"
    local output="$2"
    local name="$3"

    if [ -f "$output" ]; then
        echo "✓ $name already exists: $output"
        return 0
    fi

    echo "⬇ Downloading $name..."
    echo "  URL: $url"
    echo "  To: $output"

    # Create directory if needed
    mkdir -p "$(dirname "$output")"

    # Download with progress
    if command -v wget &> /dev/null; then
        wget --progress=bar:force -O "$output" "$url" || {
            rm -f "$output"
            echo "✗ Failed to download $name"
            return 1
        }
    elif command -v curl &> /dev/null; then
        curl -# -L -o "$output" "$url" || {
            rm -f "$output"
            echo "✗ Failed to download $name"
            return 1
        }
    else
        echo "✗ Neither wget nor curl found. Please install one."
        return 1
    fi

    echo "✓ Downloaded $name"
}

download_language() {
    echo ""
    echo "=== Language Model: Phi-3 Mini 4K (Q4) ==="
    echo "Size: ~2.3 GB"
    echo ""
    download_file "$PHI3_URL" "$MODEL_DIR/language/$PHI3_FILENAME" "Phi-3 Mini"
}

download_vision() {
    echo ""
    echo "=== Vision Model: MobileNetV3 Small ==="
    echo "Size: ~5 MB"
    echo ""
    download_file "$MOBILENET_URL" "$MODEL_DIR/vision/$MOBILENET_FILENAME" "MobileNetV3"
}

download_labels() {
    echo ""
    echo "=== ImageNet Labels ==="
    echo ""
    download_file "$LABELS_URL" "$MODEL_DIR/labels/$LABELS_FILENAME" "ImageNet Labels"
}

# Profile-based download using Python model loader
download_profile() {
    local profile="$1"
    echo ""
    echo -e "${BLUE}=== Downloading Profile: $profile ===${NC}"
    echo ""

    poetry run python -c "
import os
os.environ['WAYCORE_MODEL_PATH'] = '$MODEL_DIR'

from device.services.ai_service.vision.model_loader import VisionModelLoader
loader = VisionModelLoader(model_dir=__import__('pathlib').Path('$MODEL_DIR'))

try:
    paths = loader.download_profile('$profile')
    for model_id, path in paths.items():
        print(f'✓ {model_id}: {path}')
except Exception as e:
    print(f'Error: {e}')
    exit(1)
"
}

# List available profiles and models
list_models() {
    echo -e "${BLUE}=== Available Profiles ===${NC}"
    echo ""

    poetry run python -c "
import os
os.environ['WAYCORE_MODEL_PATH'] = '$MODEL_DIR'

from device.services.ai_service.vision.model_loader import VisionModelLoader
loader = VisionModelLoader(model_dir=__import__('pathlib').Path('$MODEL_DIR'))

profiles = loader.list_profiles()
for name, info in profiles.items():
    status = '✓' if info['all_available'] else '○'
    print(f'{status} {name}: {info[\"description\"]} ({info[\"model_count\"]} models)')

print()
print('=== Available Models ===')
print()

models = loader.list_models()
for model_id, info in models.items():
    status = '✓' if info['available'] else '○'
    print(f'{status} {model_id}: {info[\"name\"]} ({info[\"size_mb\"]}MB) - {info[\"use_case\"]}')
"
}

# Parse arguments
DOWNLOAD_ALL=false
DOWNLOAD_LANGUAGE=false
DOWNLOAD_VISION=false
DOWNLOAD_LABELS=false
DOWNLOAD_PROFILE=""
LIST_MODELS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --all)
            DOWNLOAD_ALL=true
            shift
            ;;
        --language)
            DOWNLOAD_LANGUAGE=true
            shift
            ;;
        --vision)
            DOWNLOAD_VISION=true
            shift
            ;;
        --labels)
            DOWNLOAD_LABELS=true
            shift
            ;;
        --profile)
            DOWNLOAD_PROFILE="$2"
            shift 2
            ;;
        --list)
            LIST_MODELS=true
            shift
            ;;
        --dir)
            MODEL_DIR="$2"
            shift 2
            ;;
        -h|--help)
            print_usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            print_usage
            exit 1
            ;;
    esac
done

# Handle --list
if $LIST_MODELS; then
    list_models
    exit 0
fi

# Handle --profile
if [[ -n "$DOWNLOAD_PROFILE" ]]; then
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  Waycore AI Model Downloader${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo "Model directory: $MODEL_DIR"

    mkdir -p "$MODEL_DIR/language" "$MODEL_DIR/vision" "$MODEL_DIR/labels"

    download_profile "$DOWNLOAD_PROFILE"

    echo ""
    echo -e "${GREEN}Download Complete${NC}"
    exit 0
fi

# Default to --all if nothing specified
if ! $DOWNLOAD_ALL && ! $DOWNLOAD_LANGUAGE && ! $DOWNLOAD_VISION && ! $DOWNLOAD_LABELS; then
    DOWNLOAD_ALL=true
fi

echo "========================================"
echo "  Waycore AI Model Downloader"
echo "========================================"
echo ""
echo "Model directory: $MODEL_DIR"

# Create directories
mkdir -p "$MODEL_DIR/language" "$MODEL_DIR/vision" "$MODEL_DIR/labels"

# Download requested models
if $DOWNLOAD_ALL || $DOWNLOAD_LANGUAGE; then
    download_language
fi

if $DOWNLOAD_ALL || $DOWNLOAD_VISION; then
    download_vision
fi

if $DOWNLOAD_ALL || $DOWNLOAD_LABELS; then
    download_labels
fi

echo ""
echo "========================================"
echo "  Download Complete"
echo "========================================"
echo ""
echo "Models are stored in: $MODEL_DIR"
echo ""
ls -lh "$MODEL_DIR"/*/ 2>/dev/null || true
