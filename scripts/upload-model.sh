#!/bin/bash
# Upload an AI model to Waycore
# Usage: ./scripts/upload-model.sh <model_file> --id <id> --type <language|vision> [--name <name>] [--activate]

set -e

AI_SERVICE_URL="${AI_SERVICE_URL:-http://localhost:8010}"

print_usage() {
    echo "Upload an AI model to Waycore"
    echo ""
    echo "Usage: $0 <model_file> --id <id> --type <type> [options]"
    echo ""
    echo "Arguments:"
    echo "  <model_file>    Path to the model file (.gguf for language, .tflite for vision)"
    echo ""
    echo "Required Options:"
    echo "  --id <id>       Unique identifier for the model"
    echo "  --type <type>   Model type: 'language' or 'vision'"
    echo ""
    echo "Optional:"
    echo "  --name <name>   Display name for the model"
    echo "  --activate      Activate the model immediately after upload"
    echo "  --url <url>     AI service URL (default: $AI_SERVICE_URL)"
    echo ""
    echo "Examples:"
    echo "  $0 phi-3-mini.gguf --id phi3-mini --type language --activate"
    echo "  $0 plant-id.tflite --id plant-classifier --type vision --name 'Plant Identifier'"
    echo ""
    echo "Environment Variables:"
    echo "  AI_SERVICE_URL  AI service URL (default: http://localhost:8010)"
}

# Parse arguments
MODEL_FILE=""
MODEL_ID=""
MODEL_TYPE=""
MODEL_NAME=""
ACTIVATE="false"

if [[ $# -lt 1 ]]; then
    print_usage
    exit 1
fi

# First argument is the model file
MODEL_FILE="$1"
shift

# Parse remaining options
while [[ $# -gt 0 ]]; do
    case $1 in
        --id)
            MODEL_ID="$2"
            shift 2
            ;;
        --type)
            MODEL_TYPE="$2"
            shift 2
            ;;
        --name)
            MODEL_NAME="$2"
            shift 2
            ;;
        --activate)
            ACTIVATE="true"
            shift
            ;;
        --url)
            AI_SERVICE_URL="$2"
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

# Validate required arguments
if [[ -z "$MODEL_FILE" ]]; then
    echo "Error: Model file is required"
    print_usage
    exit 1
fi

if [[ ! -f "$MODEL_FILE" ]]; then
    echo "Error: Model file not found: $MODEL_FILE"
    exit 1
fi

if [[ -z "$MODEL_ID" ]]; then
    echo "Error: --id is required"
    print_usage
    exit 1
fi

if [[ -z "$MODEL_TYPE" ]]; then
    echo "Error: --type is required"
    print_usage
    exit 1
fi

if [[ "$MODEL_TYPE" != "language" && "$MODEL_TYPE" != "vision" ]]; then
    echo "Error: --type must be 'language' or 'vision'"
    exit 1
fi

# Validate file extension
case "$MODEL_TYPE" in
    language)
        if [[ ! "$MODEL_FILE" == *.gguf ]]; then
            echo "Error: Language models must have .gguf extension"
            exit 1
        fi
        ;;
    vision)
        if [[ ! "$MODEL_FILE" == *.tflite ]]; then
            echo "Error: Vision models must have .tflite extension"
            exit 1
        fi
        ;;
esac

# Get file size
FILE_SIZE=$(du -h "$MODEL_FILE" | cut -f1)

echo "========================================"
echo "  Waycore Model Upload"
echo "========================================"
echo ""
echo "File:     $MODEL_FILE ($FILE_SIZE)"
echo "ID:       $MODEL_ID"
echo "Type:     $MODEL_TYPE"
echo "Name:     ${MODEL_NAME:-$MODEL_ID}"
echo "Activate: $ACTIVATE"
echo "Service:  $AI_SERVICE_URL"
echo ""

# Check if service is available
echo "Checking AI service..."
if ! curl -s --connect-timeout 5 "$AI_SERVICE_URL/health" > /dev/null 2>&1; then
    echo "Error: AI service is not available at $AI_SERVICE_URL"
    echo "Make sure the service is running:"
    echo "  docker-compose -f docker/compose/dev.yml up -d ai-service"
    exit 1
fi
echo "✓ AI service is healthy"
echo ""

# Upload the model
echo "Uploading model..."

CURL_ARGS=(
    -X POST
    "$AI_SERVICE_URL/api/models/upload"
    -F "file=@$MODEL_FILE"
    -F "id=$MODEL_ID"
    -F "type=$MODEL_TYPE"
    -F "activate=$ACTIVATE"
)

if [[ -n "$MODEL_NAME" ]]; then
    CURL_ARGS+=(-F "name=$MODEL_NAME")
fi

# Show progress for large files
if command -v pv &> /dev/null; then
    # Use pv for progress if available
    RESPONSE=$(pv "$MODEL_FILE" | curl -s "${CURL_ARGS[@]}" --data-binary @-)
else
    # Fall back to curl with progress
    RESPONSE=$(curl -# "${CURL_ARGS[@]}")
fi

echo ""

# Check response
if echo "$RESPONSE" | grep -q '"success":true'; then
    echo "========================================"
    echo "  Upload Successful!"
    echo "========================================"
    echo ""
    echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"

    if [[ "$ACTIVATE" == "false" ]]; then
        echo ""
        echo "To activate this model, run:"
        echo "  curl -X POST $AI_SERVICE_URL/api/models/$MODEL_ID/activate"
    fi
else
    echo "========================================"
    echo "  Upload Failed"
    echo "========================================"
    echo ""
    echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
    exit 1
fi
