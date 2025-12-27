#!/bin/bash
# Show status of Waycore development environment
# Usage: ./scripts/dev-status.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_ROOT/docker/compose/dev.yml"
MODEL_DIR="${WAYCORE_MODEL_PATH:-./models}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
GRAY='\033[0;90m'
NC='\033[0m' # No Color

print_section() {
    echo ""
    echo -e "${BLUE}═══ $1 ═══${NC}"
}

check_service() {
    local port="$1"
    local name="$2"

    if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
        echo -e "  ${GREEN}●${NC} $name ${GRAY}(port $port)${NC}"
    else
        echo -e "  ${RED}○${NC} $name ${GRAY}(port $port)${NC}"
    fi
}

check_file() {
    local path="$1"
    local name="$2"
    local size=""

    if [ -f "$path" ]; then
        size=$(du -h "$path" 2>/dev/null | cut -f1)
        echo -e "  ${GREEN}●${NC} $name ${GRAY}($size)${NC}"
    else
        echo -e "  ${RED}○${NC} $name ${GRAY}(not downloaded)${NC}"
    fi
}

echo ""
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "${BLUE}     Waycore Development Status${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}"

# Docker Status
print_section "Docker Services"
cd "$PROJECT_ROOT"
if docker info &> /dev/null; then
    docker compose -f "$COMPOSE_FILE" ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null | tail -n +2
    if [ ${PIPESTATUS[0]} -ne 0 ]; then
        echo -e "  ${GRAY}No containers running${NC}"
    fi
else
    echo -e "  ${RED}Docker is not running${NC}"
fi

# Service Health
print_section "Service Health"
check_service 8000 "Comms Bridge"
check_service 8001 "Sensor Hub"
check_service 8002 "Data Logger"
check_service 8010 "AI Service"
check_service 8080 "DB Viewer"

# MQTT
if nc -z localhost 1883 2>/dev/null; then
    echo -e "  ${GREEN}●${NC} MQTT Broker ${GRAY}(port 1883)${NC}"
else
    echo -e "  ${RED}○${NC} MQTT Broker ${GRAY}(port 1883)${NC}"
fi

# AI Models
print_section "AI Models"
check_file "$MODEL_DIR/language/phi-3-mini-4k-instruct.Q4_K_M.gguf" "Phi-3 Mini (Language)"
check_file "$MODEL_DIR/vision/mobilenet_v3_small.tflite" "MobileNetV3 (Vision)"
check_file "$MODEL_DIR/labels/imagenet_labels.txt" "ImageNet Labels"

# Knowledge Base
print_section "Knowledge Base"
KB_DIR="$PROJECT_ROOT/data/outdoor"
if [ -f "$KB_DIR/knowledge.db" ]; then
    db_size=$(du -h "$KB_DIR/knowledge.db" 2>/dev/null | cut -f1)
    echo -e "  ${GREEN}●${NC} Database ${GRAY}($db_size)${NC}"
else
    echo -e "  ${RED}○${NC} Database ${GRAY}(not downloaded)${NC}"
fi
if [ -f "$KB_DIR/knowledge.idx" ]; then
    idx_size=$(du -h "$KB_DIR/knowledge.idx" 2>/dev/null | cut -f1)
    echo -e "  ${GREEN}●${NC} Vector Index ${GRAY}($idx_size)${NC}"
else
    echo -e "  ${RED}○${NC} Vector Index ${GRAY}(not downloaded)${NC}"
fi
if [ -f "$KB_DIR/.version" ]; then
    version=$(cat "$KB_DIR/.version")
    echo -e "  ${GRAY}Version: $version${NC}"
fi

# UI Process
print_section "UI Application"
if pgrep -f "python.*main.py" > /dev/null 2>&1; then
    echo -e "  ${GREEN}●${NC} UI is running"
else
    echo -e "  ${GRAY}○${NC} UI is not running"
fi

# Volumes
print_section "Docker Volumes"
echo -e "  ${GRAY}waycore-data:${NC} $(docker volume inspect waycore-data --format '{{.Mountpoint}}' 2>/dev/null || echo 'not created')"
echo -e "  ${GRAY}waycore-models:${NC} $(docker volume inspect waycore-models --format '{{.Mountpoint}}' 2>/dev/null || echo 'not created')"

# Quick actions
echo ""
echo -e "${BLUE}═══ Quick Actions ═══${NC}"
echo ""
echo "  Start:    ./scripts/dev-start.sh"
echo "  Stop:     ./scripts/dev-stop.sh"
echo "  Restart:  ./scripts/dev-restart.sh"
echo "  Logs:     docker compose -f docker/compose/dev.yml logs -f"
echo "  UI:       cd device/apps/ui && poetry run python main.py"
echo ""
