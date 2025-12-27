#!/bin/bash
# Start Waycore development environment
# Usage: ./scripts/dev-start.sh [--ui] [--no-models]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_ROOT/docker/compose/dev.yml"
MODEL_DIR="${WAYCORE_MODEL_PATH:-./models}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  Waycore Development Environment${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_step() {
    echo -e "${YELLOW}➤ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running. Please start Docker first."
        exit 1
    fi
    print_success "Docker is available"
}

check_poetry() {
    if ! command -v poetry &> /dev/null; then
        print_error "Poetry is not installed. Please install Poetry first."
        exit 1
    fi
    print_success "Poetry is available"
}

wait_for_health() {
    local url="$1"
    local max_attempts="${2:-30}"
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
    done
    return 1
}

download_models_if_needed() {
    local lang_model="$MODEL_DIR/language/phi-3-mini-4k-instruct.Q4_K_M.gguf"
    local vision_model="$MODEL_DIR/vision/mobilenet_v3_small.tflite"

    if [ ! -f "$lang_model" ] || [ ! -f "$vision_model" ]; then
        print_step "Downloading AI models (first-time setup)..."
        "$SCRIPT_DIR/download-models.sh" --all --dir "$MODEL_DIR"
        print_success "Models downloaded"
    else
        print_success "AI models already present"
    fi
}

download_knowledge_if_needed() {
    local kb_db="$PROJECT_ROOT/data/outdoor/knowledge.db"
    local kb_idx="$PROJECT_ROOT/data/outdoor/knowledge.idx"

    if [ ! -f "$kb_db" ] || [ ! -f "$kb_idx" ]; then
        print_step "Downloading knowledge base (first-time setup)..."
        "$SCRIPT_DIR/download-knowledge.sh"
        print_success "Knowledge base downloaded"
    else
        print_success "Knowledge base already present"
    fi
}

start_services() {
    print_step "Starting Docker services..."

    cd "$PROJECT_ROOT"
    docker compose -f "$COMPOSE_FILE" up -d

    print_success "Services started"
}

wait_for_services() {
    print_step "Waiting for services to be healthy..."

    local services=("8000:comms-bridge" "8001:sensor-hub" "8010:ai-service")
    local all_healthy=true

    for service in "${services[@]}"; do
        local port="${service%%:*}"
        local name="${service##*:}"

        if wait_for_health "http://localhost:$port/health" 30; then
            print_success "$name is healthy (port $port)"
        else
            print_error "$name failed to start (port $port)"
            all_healthy=false
        fi
    done

    if [ "$all_healthy" = false ]; then
        echo ""
        print_error "Some services failed to start. Check logs with:"
        echo "  docker compose -f docker/compose/dev.yml logs -f"
        return 1
    fi
}

start_ui() {
    print_step "Starting UI application..."
    cd "$PROJECT_ROOT/device/apps/ui"
    poetry run python main.py
}

print_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Start the Waycore development environment."
    echo ""
    echo "Options:"
    echo "  --ui         Also start the UI application"
    echo "  --no-models  Skip model download check"
    echo "  -h, --help   Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0              Start backend services only"
    echo "  $0 --ui         Start backend and UI"
    echo "  $0 --no-models  Start without checking models"
}

# Parse arguments
START_UI=false
SKIP_MODELS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --ui)
            START_UI=true
            shift
            ;;
        --no-models)
            SKIP_MODELS=true
            shift
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

# Main execution
print_header

print_step "Checking prerequisites..."
check_docker
check_poetry

if [ "$SKIP_MODELS" = false ]; then
    download_models_if_needed
    download_knowledge_if_needed
fi

start_services
wait_for_services

echo ""
print_success "Development environment is ready!"
echo ""
echo "Services:"
echo "  • MQTT Broker:    localhost:1883"
echo "  • Comms Bridge:   localhost:8000"
echo "  • Sensor Hub:     localhost:8001"
echo "  • Data Logger:    localhost:8002"
echo "  • AI Service:     localhost:8010"
echo "  • DB Viewer:      http://localhost:8080"
echo ""

if [ "$START_UI" = true ]; then
    echo "Starting UI..."
    start_ui
else
    echo "To start the UI, run:"
    echo "  cd device/apps/ui && poetry run python main.py"
    echo ""
    echo "Or restart with:"
    echo "  ./scripts/dev-start.sh --ui"
fi
