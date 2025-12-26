#!/bin/bash
# Stop Waycore development environment
# Usage: ./scripts/dev-stop.sh [--volumes]

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
    echo -e "${BLUE}  Stopping Waycore Development${NC}"
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
    echo "Stop the Waycore development environment."
    echo ""
    echo "Options:"
    echo "  --volumes    Also remove Docker volumes (WARNING: deletes data)"
    echo "  -h, --help   Show this help message"
}

# Parse arguments
REMOVE_VOLUMES=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --volumes)
            REMOVE_VOLUMES=true
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

# Stop UI process if running
print_step "Stopping UI application (if running)..."
pkill -f "python.*main.py" 2>/dev/null && print_success "UI stopped" || echo "  (UI was not running)"

# Stop Docker containers
print_step "Stopping Docker containers..."
cd "$PROJECT_ROOT"

if [ "$REMOVE_VOLUMES" = true ]; then
    echo -e "${RED}⚠ WARNING: Removing volumes will delete all data!${NC}"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker compose -f "$COMPOSE_FILE" down -v
        print_success "Containers and volumes removed"
    else
        echo "Cancelled. Stopping containers only..."
        docker compose -f "$COMPOSE_FILE" down
        print_success "Containers stopped"
    fi
else
    docker compose -f "$COMPOSE_FILE" down
    print_success "Containers stopped"
fi

echo ""
print_success "Development environment stopped"
echo ""
echo "To start again, run:"
echo "  ./scripts/dev-start.sh"
