#!/bin/bash
# Verify integrity of downloaded RAG sources.
#
# Usage: ./scripts/verify-rag-sources.sh [data_dir]
#
# Checks that downloaded files exist and are valid (non-empty PDFs, valid JSON).

set -e

DATA_DIR="${1:-data/raw}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Verifying RAG Sources ===${NC}"
echo "Directory: $DATA_DIR"
echo ""

if [[ ! -d "$DATA_DIR" ]]; then
    echo -e "${RED}Error: Directory $DATA_DIR does not exist${NC}"
    echo "Run ./scripts/download-rag-sources.sh first"
    exit 1
fi

VALID=0
INVALID=0
MISSING=0

# Verify PDF files
verify_pdf() {
    local file="$1"
    local name="$2"

    if [[ ! -f "$file" ]]; then
        echo -e "  ${RED}✗${NC} Missing: $name"
        MISSING=$((MISSING + 1))
        return 1
    fi

    # Check file is not empty
    if [[ ! -s "$file" ]]; then
        echo -e "  ${RED}✗${NC} Empty: $name"
        INVALID=$((INVALID + 1))
        return 1
    fi

    # Check PDF header
    if head -c 4 "$file" | grep -q "%PDF"; then
        local size=$(du -h "$file" | cut -f1)
        echo -e "  ${GREEN}✓${NC} Valid PDF ($size): $name"
        VALID=$((VALID + 1))
        return 0
    else
        echo -e "  ${RED}✗${NC} Invalid PDF: $name"
        INVALID=$((INVALID + 1))
        return 1
    fi
}

# Verify JSON files
verify_json() {
    local file="$1"
    local name="$2"

    if [[ ! -f "$file" ]]; then
        echo -e "  ${YELLOW}○${NC} Optional (not present): $name"
        return 0
    fi

    if python3 -c "import json; json.load(open('$file'))" 2>/dev/null; then
        local size=$(du -h "$file" | cut -f1)
        echo -e "  ${GREEN}✓${NC} Valid JSON ($size): $name"
        VALID=$((VALID + 1))
        return 0
    else
        echo -e "  ${RED}✗${NC} Invalid JSON: $name"
        INVALID=$((INVALID + 1))
        return 1
    fi
}

# ============================================================================
# Verify all expected files
# ============================================================================

echo -e "${BLUE}Survival Manuals:${NC}"
verify_pdf "$DATA_DIR/survival/FM21-76_Survival.pdf" "FM 21-76 Survival Manual"
verify_pdf "$DATA_DIR/survival/FM21-76-1_Evasion.pdf" "FM 21-76-1 Evasion"
verify_pdf "$DATA_DIR/survival/RangerHandbook.pdf" "Ranger Handbook"

echo -e "\n${BLUE}Navigation:${NC}"
verify_pdf "$DATA_DIR/navigation/FM3-25.26_MapReading.pdf" "FM 3-25.26 Map Reading"
verify_pdf "$DATA_DIR/navigation/USGS_TopoSymbols.pdf" "USGS Topo Symbols"

echo -e "\n${BLUE}First Aid:${NC}"
verify_pdf "$DATA_DIR/first_aid/FM4-25.11_FirstAid.pdf" "FM 4-25.11 First Aid"
verify_pdf "$DATA_DIR/first_aid/BSA_WildernessFirstAid.pdf" "BSA Wilderness First Aid"

echo -e "\n${BLUE}Knots:${NC}"
verify_pdf "$DATA_DIR/knots/FM5-125_Rigging.pdf" "FM 5-125 Rigging"
verify_pdf "$DATA_DIR/knots/Army_MountainWarfare_Knots.pdf" "Army Mountain Warfare Knots"

echo -e "\n${BLUE}Weather:${NC}"
verify_pdf "$DATA_DIR/weather/NOAA_CloudChart.pdf" "NOAA Cloud Chart"
verify_pdf "$DATA_DIR/weather/NWS_SpotterGuide.pdf" "NWS Weather Spotter Guide"

echo -e "\n${BLUE}Plants (Optional):${NC}"
verify_json "$DATA_DIR/plants/pfaf_database.json" "PFAF Database"
verify_json "$DATA_DIR/plants/usda_plants.json" "USDA Plants"

# ============================================================================
# Summary
# ============================================================================
echo -e "\n${BLUE}=== Verification Summary ===${NC}"
echo -e "${GREEN}Valid: $VALID${NC}"
if [[ $INVALID -gt 0 ]]; then
    echo -e "${RED}Invalid: $INVALID${NC}"
fi
if [[ $MISSING -gt 0 ]]; then
    echo -e "${RED}Missing: $MISSING${NC}"
fi

TOTAL_SIZE=$(du -sh "$DATA_DIR" 2>/dev/null | cut -f1)
echo -e "\nTotal size: $TOTAL_SIZE"

if [[ $INVALID -eq 0 ]] && [[ $MISSING -eq 0 ]]; then
    echo -e "\n${GREEN}✅ All sources verified!${NC}"
    exit 0
else
    echo -e "\n${YELLOW}⚠️ Some sources are missing or invalid.${NC}"
    echo "Re-run ./scripts/download-rag-sources.sh to download missing files."
    exit 1
fi
