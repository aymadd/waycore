#!/bin/bash
# Display current knowledge base version and status.
#
# Usage: ./scripts/knowledge-info.sh [--dir DIR]

set -e

# Configuration
DATA_DIR="data/outdoor"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dir)
            DATA_DIR="$2"
            shift 2
            ;;
        -h|--help)
            echo "Display knowledge base information."
            echo ""
            echo "Usage: $0 [--dir DIR]"
            exit 0
            ;;
        *)
            shift
            ;;
    esac
done

echo -e "${BLUE}=== Knowledge Base Info ===${NC}"

# Version
if [[ -f "$DATA_DIR/.version" ]]; then
    VERSION=$(cat "$DATA_DIR/.version")
    echo -e "Version: ${GREEN}$VERSION${NC}"
elif [[ -f "$DATA_DIR/manifest.json" ]]; then
    VERSION=$(jq -r '.version // "unknown"' "$DATA_DIR/manifest.json" 2>/dev/null)
    echo -e "Version: ${GREEN}$VERSION${NC}"
else
    echo -e "Version: ${YELLOW}not installed${NC}"
fi

# Database
if [[ -f "$DATA_DIR/knowledge.db" ]]; then
    DB_SIZE=$(du -h "$DATA_DIR/knowledge.db" | cut -f1)
    echo -e "Database: ${GREEN}✓${NC} ($DB_SIZE)"
else
    echo -e "Database: ${YELLOW}✗ not found${NC}"
fi

# Index
if [[ -f "$DATA_DIR/knowledge.idx" ]]; then
    IDX_SIZE=$(du -h "$DATA_DIR/knowledge.idx" | cut -f1)
    echo -e "Index: ${GREEN}✓${NC} ($IDX_SIZE)"
else
    echo -e "Index: ${YELLOW}✗ not found${NC}"
fi

# Entry count from manifest
if [[ -f "$DATA_DIR/manifest.json" ]]; then
    ENTRIES=$(jq -r '.entry_count // "unknown"' "$DATA_DIR/manifest.json" 2>/dev/null)
    echo -e "Entries: ${CYAN}$ENTRIES${NC}"
fi

# Safety data
if [[ -f "$DATA_DIR/species_safety.json" ]]; then
    echo -e "Safety data: ${GREEN}✓${NC}"
fi
