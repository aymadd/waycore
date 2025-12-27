#!/bin/bash
# Download all public domain resources for Waycore RAG knowledge base.
#
# DEPRECATED: This script is for development of the waycore-knowledge repository.
# For normal use, download the pre-built knowledge base instead:
#   ./scripts/download-knowledge.sh
#
# Usage: ./scripts/download-rag-sources.sh [data_dir]
#
# This script downloads survival manuals, first aid guides, navigation resources,
# and other public domain content for the offline RAG knowledge base.
#
# All resources are either public domain (US Government publications) or
# Creative Commons licensed.

set -e

# Configuration
DATA_DIR="${1:-data/raw}"
TIMEOUT=60  # seconds per download
MAX_RETRIES=2

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create directory structure
echo -e "${BLUE}=== Waycore RAG Knowledge Base Download ===${NC}"
echo "Target directory: $DATA_DIR"
echo ""

mkdir -p "$DATA_DIR"/{survival,navigation,first_aid,plants,weather,knots,comms}

# Download function with retry logic
download_file() {
    local url="$1"
    local output="$2"
    local description="$3"
    local retries=0

    # Skip if file already exists and is non-empty
    if [[ -f "$output" ]] && [[ -s "$output" ]]; then
        echo -e "  ${GREEN}✓${NC} Already exists: $(basename "$output")"
        return 0
    fi

    while [[ $retries -lt $MAX_RETRIES ]]; do
        if wget --timeout="$TIMEOUT" -q --show-progress -O "$output" "$url" 2>/dev/null; then
            if [[ -s "$output" ]]; then
                echo -e "  ${GREEN}✓${NC} Downloaded: $(basename "$output")"
                return 0
            fi
        fi
        retries=$((retries + 1))
        if [[ $retries -lt $MAX_RETRIES ]]; then
            echo -e "  ${YELLOW}⟳${NC} Retrying: $(basename "$output")"
        fi
    done

    echo -e "  ${RED}✗${NC} Failed: $description"
    rm -f "$output"  # Remove partial download
    return 1
}

# Track statistics
TOTAL=0
SUCCESS=0
FAILED=0

# ============================================================================
# SURVIVAL MANUALS (Public Domain - US Government)
# ============================================================================
echo -e "\n${BLUE}📚 Survival Manuals${NC}"

download_file \
    "https://archive.org/download/Fm21-76SurvivalManual/FM21-76_SurvivalManual.pdf" \
    "$DATA_DIR/survival/FM21-76_Survival.pdf" \
    "FM 21-76 Survival Manual" && SUCCESS=$((SUCCESS + 1)) || FAILED=$((FAILED + 1))
TOTAL=$((TOTAL + 1))

download_file \
    "https://irp.fas.org/doddir/army/fm21-76-1.pdf" \
    "$DATA_DIR/survival/FM21-76-1_Evasion.pdf" \
    "FM 21-76-1 Survival, Evasion & Recovery" && SUCCESS=$((SUCCESS + 1)) || FAILED=$((FAILED + 1))
TOTAL=$((TOTAL + 1))

download_file \
    "https://archive.org/download/ranger-handbook-sh-21-76/ranger-handbook-sh-21-76.pdf" \
    "$DATA_DIR/survival/RangerHandbook.pdf" \
    "Army Ranger Handbook" && SUCCESS=$((SUCCESS + 1)) || FAILED=$((FAILED + 1))
TOTAL=$((TOTAL + 1))

# ============================================================================
# NAVIGATION RESOURCES (Public Domain)
# ============================================================================
echo -e "\n${BLUE}🧭 Navigation Resources${NC}"

download_file \
    "https://irp.fas.org/doddir/army/fm3-25-26.pdf" \
    "$DATA_DIR/navigation/FM3-25.26_MapReading.pdf" \
    "FM 3-25.26 Map Reading & Land Navigation" && SUCCESS=$((SUCCESS + 1)) || FAILED=$((FAILED + 1))
TOTAL=$((TOTAL + 1))

download_file \
    "https://pubs.usgs.gov/gip/TopographicMapSymbols/topomapsymbols.pdf" \
    "$DATA_DIR/navigation/USGS_TopoSymbols.pdf" \
    "USGS Topographic Map Symbols" && SUCCESS=$((SUCCESS + 1)) || FAILED=$((FAILED + 1))
TOTAL=$((TOTAL + 1))

# ============================================================================
# FIRST AID GUIDES (Public Domain / Educational)
# ============================================================================
echo -e "\n${BLUE}🏥 First Aid Guides${NC}"

download_file \
    "https://irp.fas.org/doddir/army/fm4-25-11.pdf" \
    "$DATA_DIR/first_aid/FM4-25.11_FirstAid.pdf" \
    "FM 4-25.11 First Aid" && SUCCESS=$((SUCCESS + 1)) || FAILED=$((FAILED + 1))
TOTAL=$((TOTAL + 1))

download_file \
    "https://filestore.scouting.org/filestore/pdf/680-008.pdf" \
    "$DATA_DIR/first_aid/BSA_WildernessFirstAid.pdf" \
    "BSA Wilderness First Aid" && SUCCESS=$((SUCCESS + 1)) || FAILED=$((FAILED + 1))
TOTAL=$((TOTAL + 1))

# ============================================================================
# KNOTS & RIGGING (Public Domain)
# ============================================================================
echo -e "\n${BLUE}🪢 Knots & Rigging${NC}"

download_file \
    "https://www.globalsecurity.org/military/library/policy/army/fm/5-125/fm5-125.pdf" \
    "$DATA_DIR/knots/FM5-125_Rigging.pdf" \
    "FM 5-125 Rigging" && SUCCESS=$((SUCCESS + 1)) || FAILED=$((FAILED + 1))
TOTAL=$((TOTAL + 1))

download_file \
    "https://www.benning.army.mil/infantry/amws/content/pdf/Knot%20Guide.pdf" \
    "$DATA_DIR/knots/Army_MountainWarfare_Knots.pdf" \
    "Army Mountain Warfare Knot Guide" && SUCCESS=$((SUCCESS + 1)) || FAILED=$((FAILED + 1))
TOTAL=$((TOTAL + 1))

# ============================================================================
# WEATHER (Public Domain - NOAA/NWS)
# ============================================================================
echo -e "\n${BLUE}🌦️ Weather Resources${NC}"

download_file \
    "https://www.weather.gov/media/owlie/cloud_chart.pdf" \
    "$DATA_DIR/weather/NOAA_CloudChart.pdf" \
    "NOAA Cloud Chart" && SUCCESS=$((SUCCESS + 1)) || FAILED=$((FAILED + 1))
TOTAL=$((TOTAL + 1))

download_file \
    "https://www.weather.gov/media/bis/Spotter_Guide.pdf" \
    "$DATA_DIR/weather/NWS_SpotterGuide.pdf" \
    "NWS Weather Spotter Guide" && SUCCESS=$((SUCCESS + 1)) || FAILED=$((FAILED + 1))
TOTAL=$((TOTAL + 1))

# ============================================================================
# SUMMARY
# ============================================================================
echo -e "\n${BLUE}=== Download Summary ===${NC}"
echo -e "Total attempted: ${TOTAL}"
echo -e "${GREEN}Successful: ${SUCCESS}${NC}"
if [[ $FAILED -gt 0 ]]; then
    echo -e "${RED}Failed: ${FAILED}${NC}"
fi

# Count files
PDF_COUNT=$(find "$DATA_DIR" -type f -name "*.pdf" 2>/dev/null | wc -l | tr -d ' ')
JSON_COUNT=$(find "$DATA_DIR" -type f -name "*.json" 2>/dev/null | wc -l | tr -d ' ')
TOTAL_SIZE=$(du -sh "$DATA_DIR" 2>/dev/null | cut -f1)

echo ""
echo "Files downloaded:"
echo "  PDFs: $PDF_COUNT"
echo "  JSON: $JSON_COUNT"
echo "  Total size: $TOTAL_SIZE"

echo ""
if [[ $FAILED -eq 0 ]]; then
    echo -e "${GREEN}✅ Download complete!${NC}"
    echo "Next step: Run the parsing script to build the knowledge index."
else
    echo -e "${YELLOW}⚠️ Some downloads failed.${NC}"
    echo "Re-run the script to retry failed downloads."
    echo "Some resources may be temporarily unavailable."
fi
