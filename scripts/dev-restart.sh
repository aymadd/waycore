#!/bin/bash
# Restart Waycore development environment
# Usage: ./scripts/dev-restart.sh [--service SERVICE] [--rebuild]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_ROOT/docker/compose/dev.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  Restarting Waycore Development${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_step() {
    echo -e "${YELLOW}➤ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Restart the Waycore development environment."
    echo ""
    echo "Options:"
    echo "  --service SERVICE  Restart only a specific service"
    echo "  --rebuild          Rebuild images before restarting"
    echo "  -h, --help         Show this help message"
    echo ""
    echo "Services:"
    echo "  mqtt, comms-bridge, sensor-hub, data-logger, ai-service, db-viewer"
    echo ""
    echo "Examples:"
    echo "  $0                          Restart all services"
    echo "  $0 --service ai-service     Restart only AI service"
    echo "  $0 --rebuild                Rebuild and restart all"
}

# Parse arguments
SERVICE=""
REBUILD=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --service)
            SERVICE="$2"
            shift 2
            ;;
        --rebuild)
            REBUILD=true
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

print_header
cd "$PROJECT_ROOT"

if [ -n "$SERVICE" ]; then
    # Restart specific service
    print_step "Restarting $SERVICE..."

    if [ "$REBUILD" = true ]; then
        docker compose -f "$COMPOSE_FILE" up -d --build --force-recreate "$SERVICE"
    else
        docker compose -f "$COMPOSE_FILE" restart "$SERVICE"
    fi

    print_success "$SERVICE restarted"
else
    # Restart all services
    print_step "Restarting all services..."

    if [ "$REBUILD" = true ]; then
        docker compose -f "$COMPOSE_FILE" up -d --build --force-recreate
    else
        docker compose -f "$COMPOSE_FILE" restart
    fi

    print_success "All services restarted"
fi

# Show status
echo ""
print_step "Current status:"
docker compose -f "$COMPOSE_FILE" ps

echo ""
print_success "Restart complete"
