#!/bin/bash
# Verify integrity of installed knowledge base.
#
# Usage: ./scripts/verify-knowledge.sh [--dir DIR]
#
# This script verifies the knowledge base files:
# - Checks that required files exist
# - Verifies SHA256 checksums against manifest
# - Reports knowledge base statistics

set -e

# Configuration
DATA_DIR="data/outdoor"

# Colors
RED='\033[0;31m'
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
            echo "Verify knowledge base integrity."
            echo ""
            echo "Usage: $0 [--dir DIR]"
            echo ""
            echo "Options:"
            echo "  --dir DIR  Data directory (default: data/outdoor)"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}========================================"
echo -e "  Knowledge Base Verification"
echo -e "========================================${NC}"
echo ""
echo -e "Directory: ${CYAN}$DATA_DIR${NC}"
echo ""

ERRORS=0
WARNINGS=0

# Check directory exists
if [[ ! -d "$DATA_DIR" ]]; then
    echo -e "${RED}✗ Directory not found: $DATA_DIR${NC}"
    exit 1
fi

# Check required files
echo -e "${BLUE}Checking required files...${NC}"

if [[ -f "$DATA_DIR/knowledge.db" ]]; then
    DB_SIZE=$(du -h "$DATA_DIR/knowledge.db" | cut -f1)
    echo -e "  ${GREEN}✓${NC} knowledge.db ($DB_SIZE)"
else
    echo -e "  ${RED}✗${NC} knowledge.db missing"
    ERRORS=$((ERRORS + 1))
fi

if [[ -f "$DATA_DIR/knowledge.idx" ]]; then
    IDX_SIZE=$(du -h "$DATA_DIR/knowledge.idx" | cut -f1)
    echo -e "  ${GREEN}✓${NC} knowledge.idx ($IDX_SIZE)"
else
    echo -e "  ${RED}✗${NC} knowledge.idx missing"
    ERRORS=$((ERRORS + 1))
fi

# Check optional files
echo ""
echo -e "${BLUE}Checking optional files...${NC}"

if [[ -f "$DATA_DIR/manifest.json" ]]; then
    echo -e "  ${GREEN}✓${NC} manifest.json"
else
    echo -e "  ${YELLOW}○${NC} manifest.json (not present)"
    WARNINGS=$((WARNINGS + 1))
fi

if [[ -f "$DATA_DIR/species_safety.json" ]]; then
    echo -e "  ${GREEN}✓${NC} species_safety.json"
else
    echo -e "  ${YELLOW}○${NC} species_safety.json (not present)"
fi

if [[ -f "$DATA_DIR/.version" ]]; then
    VERSION=$(cat "$DATA_DIR/.version")
    echo -e "  ${GREEN}✓${NC} .version ($VERSION)"
else
    echo -e "  ${YELLOW}○${NC} .version (not present)"
fi

# Verify checksums if manifest exists
echo ""
if [[ -f "$DATA_DIR/manifest.json" ]]; then
    echo -e "${BLUE}Verifying checksums...${NC}"

    # Compute SHA256
    compute_sha256() {
        local file="$1"
        if command -v sha256sum &> /dev/null; then
            sha256sum "$file" | cut -d' ' -f1
        elif command -v shasum &> /dev/null; then
            shasum -a 256 "$file" | cut -d' ' -f1
        else
            echo "unknown"
        fi
    }

    # Check knowledge.db
    if [[ -f "$DATA_DIR/knowledge.db" ]]; then
        EXPECTED_DB=$(jq -r '.checksums.knowledge_db // empty' "$DATA_DIR/manifest.json" 2>/dev/null)
        if [[ -n "$EXPECTED_DB" ]]; then
            ACTUAL_DB=$(compute_sha256 "$DATA_DIR/knowledge.db")
            if [[ "$ACTUAL_DB" == "$EXPECTED_DB" ]]; then
                echo -e "  ${GREEN}✓${NC} knowledge.db checksum valid"
            else
                echo -e "  ${RED}✗${NC} knowledge.db checksum MISMATCH"
                echo -e "      Expected: $EXPECTED_DB"
                echo -e "      Actual:   $ACTUAL_DB"
                ERRORS=$((ERRORS + 1))
            fi
        else
            echo -e "  ${YELLOW}○${NC} knowledge.db checksum not in manifest"
        fi
    fi

    # Check knowledge.idx
    if [[ -f "$DATA_DIR/knowledge.idx" ]]; then
        EXPECTED_IDX=$(jq -r '.checksums.knowledge_idx // empty' "$DATA_DIR/manifest.json" 2>/dev/null)
        if [[ -n "$EXPECTED_IDX" ]]; then
            ACTUAL_IDX=$(compute_sha256 "$DATA_DIR/knowledge.idx")
            if [[ "$ACTUAL_IDX" == "$EXPECTED_IDX" ]]; then
                echo -e "  ${GREEN}✓${NC} knowledge.idx checksum valid"
            else
                echo -e "  ${RED}✗${NC} knowledge.idx checksum MISMATCH"
                echo -e "      Expected: $EXPECTED_IDX"
                echo -e "      Actual:   $ACTUAL_IDX"
                ERRORS=$((ERRORS + 1))
            fi
        else
            echo -e "  ${YELLOW}○${NC} knowledge.idx checksum not in manifest"
        fi
    fi
else
    echo -e "${YELLOW}⚠ No manifest.json, cannot verify checksums${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

# Show statistics from manifest
echo ""
if [[ -f "$DATA_DIR/manifest.json" ]]; then
    echo -e "${BLUE}Knowledge Base Statistics:${NC}"

    VERSION=$(jq -r '.version // "unknown"' "$DATA_DIR/manifest.json" 2>/dev/null)
    ENTRIES=$(jq -r '.entry_count // "unknown"' "$DATA_DIR/manifest.json" 2>/dev/null)
    BUILT=$(jq -r '.built_at // "unknown"' "$DATA_DIR/manifest.json" 2>/dev/null)

    echo -e "  Version:     ${CYAN}$VERSION${NC}"
    echo -e "  Entries:     ${CYAN}$ENTRIES${NC}"
    echo -e "  Built:       ${CYAN}$BUILT${NC}"

    # Show categories if available
    CATEGORIES=$(jq -r '.categories | keys[]' "$DATA_DIR/manifest.json" 2>/dev/null | tr '\n' ', ' | sed 's/,$//')
    if [[ -n "$CATEGORIES" ]]; then
        echo -e "  Categories:  ${CYAN}$CATEGORIES${NC}"
    fi
fi

# Summary
echo ""
echo -e "${BLUE}========================================"
echo -e "  Verification Summary"
echo -e "========================================${NC}"
echo ""

if [[ $ERRORS -eq 0 ]]; then
    if [[ $WARNINGS -eq 0 ]]; then
        echo -e "${GREEN}✅ Knowledge base is valid and complete${NC}"
        exit 0
    else
        echo -e "${YELLOW}⚠ Knowledge base is valid with $WARNINGS warning(s)${NC}"
        exit 0
    fi
else
    echo -e "${RED}✗ Verification failed with $ERRORS error(s)${NC}"
    echo ""
    echo "To fix, run:"
    echo "  ./scripts/download-knowledge.sh --force"
    exit 1
fi
