#!/bin/bash
# Download pre-built knowledge base from waycore-knowledge GitHub releases.
#
# Usage: ./scripts/download-knowledge.sh [--version VERSION] [--dir DIR] [--force]
#
# This script downloads the pre-built SQLite database and Hnswlib vector index
# from the waycore-knowledge repository releases.
#
# Options:
#   --version VERSION  Specific version to download (default: latest)
#   --dir DIR          Target directory (default: data/outdoor)
#   --force            Re-download even if already present
#   --verify           Only verify existing files
#   --help             Show this help message

set -e

# Configuration
REPO="dmitry-grechko/waycore-knowledge"
DATA_DIR="data/outdoor"
VERSION="latest"
FORCE=false
VERIFY_ONLY=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

print_usage() {
    echo "Download pre-built knowledge base from waycore-knowledge releases."
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --version VERSION  Specific version to download (default: latest)"
    echo "  --dir DIR          Target directory (default: data/outdoor)"
    echo "  --force            Re-download even if already present"
    echo "  --verify           Only verify existing files (no download)"
    echo "  --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                        # Download latest version"
    echo "  $0 --version v1.0.1       # Download specific version"
    echo "  $0 --verify               # Verify existing files"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --version)
            VERSION="$2"
            shift 2
            ;;
        --dir)
            DATA_DIR="$2"
            shift 2
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --verify)
            VERIFY_ONLY=true
            shift
            ;;
        -h|--help)
            print_usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            print_usage
            exit 1
            ;;
    esac
done

echo -e "${BLUE}========================================"
echo -e "  Waycore Knowledge Base Downloader"
echo -e "========================================${NC}"
echo ""
echo -e "Repository: ${CYAN}$REPO${NC}"
echo -e "Target dir: ${CYAN}$DATA_DIR${NC}"
echo -e "Version:    ${CYAN}$VERSION${NC}"
echo ""

# Create target directory
mkdir -p "$DATA_DIR"

# Get release information
get_release_info() {
    local version="$1"
    local api_url

    if [[ "$version" == "latest" ]]; then
        api_url="https://api.github.com/repos/$REPO/releases/latest"
    else
        api_url="https://api.github.com/repos/$REPO/releases/tags/$version"
    fi

    curl -s "$api_url"
}

# Download a release asset
download_asset() {
    local url="$1"
    local output="$2"
    local name="$3"

    echo -e "  ⬇ Downloading ${CYAN}$name${NC}..."

    if curl -sL --fail -o "$output" "$url"; then
        echo -e "  ${GREEN}✓${NC} Downloaded: $name"
        return 0
    else
        echo -e "  ${RED}✗${NC} Failed to download: $name"
        rm -f "$output"
        return 1
    fi
}

# Compute SHA256 checksum
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

# Verify file checksums
verify_checksums() {
    local manifest="$DATA_DIR/manifest.json"

    if [[ ! -f "$manifest" ]]; then
        echo -e "${YELLOW}⚠ No manifest found, cannot verify checksums${NC}"
        return 1
    fi

    echo -e "${BLUE}Verifying checksums...${NC}"

    local all_ok=true

    # Check knowledge.db
    if [[ -f "$DATA_DIR/knowledge.db" ]]; then
        local expected_db=$(jq -r '.checksums.knowledge_db // empty' "$manifest" 2>/dev/null)
        if [[ -n "$expected_db" ]]; then
            local actual_db=$(compute_sha256 "$DATA_DIR/knowledge.db")
            if [[ "$actual_db" == "$expected_db" ]]; then
                echo -e "  ${GREEN}✓${NC} knowledge.db checksum verified"
            else
                echo -e "  ${RED}✗${NC} knowledge.db checksum mismatch"
                all_ok=false
            fi
        fi
    fi

    # Check knowledge.idx
    if [[ -f "$DATA_DIR/knowledge.idx" ]]; then
        local expected_idx=$(jq -r '.checksums.knowledge_idx // empty' "$manifest" 2>/dev/null)
        if [[ -n "$expected_idx" ]]; then
            local actual_idx=$(compute_sha256 "$DATA_DIR/knowledge.idx")
            if [[ "$actual_idx" == "$expected_idx" ]]; then
                echo -e "  ${GREEN}✓${NC} knowledge.idx checksum verified"
            else
                echo -e "  ${RED}✗${NC} knowledge.idx checksum mismatch"
                all_ok=false
            fi
        fi
    fi

    if $all_ok; then
        return 0
    else
        return 1
    fi
}

# Show current version info
show_info() {
    local version_file="$DATA_DIR/.version"
    local manifest="$DATA_DIR/manifest.json"

    echo -e "${BLUE}=== Current Knowledge Base ===${NC}"

    if [[ -f "$version_file" ]]; then
        echo -e "Version: ${GREEN}$(cat "$version_file")${NC}"
    elif [[ -f "$manifest" ]]; then
        local ver=$(jq -r '.version // "unknown"' "$manifest" 2>/dev/null)
        echo -e "Version: ${GREEN}$ver${NC}"
    else
        echo -e "Version: ${YELLOW}not installed${NC}"
    fi

    if [[ -f "$DATA_DIR/knowledge.db" ]]; then
        local db_size=$(du -h "$DATA_DIR/knowledge.db" | cut -f1)
        echo -e "Database: ${GREEN}✓${NC} ($db_size)"
    else
        echo -e "Database: ${RED}✗ missing${NC}"
    fi

    if [[ -f "$DATA_DIR/knowledge.idx" ]]; then
        local idx_size=$(du -h "$DATA_DIR/knowledge.idx" | cut -f1)
        echo -e "Index: ${GREEN}✓${NC} ($idx_size)"
    else
        echo -e "Index: ${RED}✗ missing${NC}"
    fi

    if [[ -f "$manifest" ]]; then
        local entries=$(jq -r '.entry_count // "unknown"' "$manifest" 2>/dev/null)
        echo -e "Entries: $entries"
    fi

    echo ""
}

# Verify-only mode
if $VERIFY_ONLY; then
    show_info

    if verify_checksums; then
        echo -e "${GREEN}✅ Knowledge base is valid${NC}"
        exit 0
    else
        echo -e "${RED}✗ Verification failed${NC}"
        exit 1
    fi
fi

# Check if already installed
if [[ -f "$DATA_DIR/knowledge.db" ]] && [[ -f "$DATA_DIR/knowledge.idx" ]] && ! $FORCE; then
    show_info

    if verify_checksums 2>/dev/null; then
        echo -e "${GREEN}Knowledge base is already installed and verified.${NC}"
        echo "Use --force to re-download."
        exit 0
    else
        echo -e "${YELLOW}Existing files may be corrupted, re-downloading...${NC}"
    fi
fi

# Fetch release info
echo -e "${BLUE}Fetching release information...${NC}"
RELEASE_INFO=$(get_release_info "$VERSION")

if [[ -z "$RELEASE_INFO" ]] || echo "$RELEASE_INFO" | jq -e '.message' &>/dev/null; then
    error_msg=$(echo "$RELEASE_INFO" | jq -r '.message // "Unknown error"' 2>/dev/null)
    echo -e "${RED}✗ Failed to fetch release: $error_msg${NC}"
    echo ""
    echo "Make sure the release exists at:"
    echo "  https://github.com/$REPO/releases"
    exit 1
fi

TAG_NAME=$(echo "$RELEASE_INFO" | jq -r '.tag_name')
PUBLISHED=$(echo "$RELEASE_INFO" | jq -r '.published_at' | cut -d'T' -f1)
echo -e "Found release: ${GREEN}$TAG_NAME${NC} (published: $PUBLISHED)"
echo ""

# Download assets
echo -e "${BLUE}Downloading assets...${NC}"
SUCCESS=true

# Get asset URLs
DB_URL=$(echo "$RELEASE_INFO" | jq -r '.assets[] | select(.name == "knowledge.db") | .browser_download_url')
IDX_URL=$(echo "$RELEASE_INFO" | jq -r '.assets[] | select(.name == "knowledge.idx") | .browser_download_url')
MANIFEST_URL=$(echo "$RELEASE_INFO" | jq -r '.assets[] | select(.name == "manifest.json") | .browser_download_url')
SAFETY_URL=$(echo "$RELEASE_INFO" | jq -r '.assets[] | select(.name == "species_safety.json") | .browser_download_url')

# Download knowledge.db (required)
if [[ -n "$DB_URL" && "$DB_URL" != "null" ]]; then
    download_asset "$DB_URL" "$DATA_DIR/knowledge.db" "knowledge.db" || SUCCESS=false
else
    echo -e "${RED}✗ knowledge.db not found in release${NC}"
    SUCCESS=false
fi

# Download knowledge.idx (required)
if [[ -n "$IDX_URL" && "$IDX_URL" != "null" ]]; then
    download_asset "$IDX_URL" "$DATA_DIR/knowledge.idx" "knowledge.idx" || SUCCESS=false
else
    echo -e "${RED}✗ knowledge.idx not found in release${NC}"
    SUCCESS=false
fi

# Download manifest.json (optional but recommended)
if [[ -n "$MANIFEST_URL" && "$MANIFEST_URL" != "null" ]]; then
    download_asset "$MANIFEST_URL" "$DATA_DIR/manifest.json" "manifest.json" || true
fi

# Download species_safety.json (optional)
if [[ -n "$SAFETY_URL" && "$SAFETY_URL" != "null" ]]; then
    download_asset "$SAFETY_URL" "$DATA_DIR/species_safety.json" "species_safety.json" || true
fi

# Save version info
echo "$TAG_NAME" > "$DATA_DIR/.version"

echo ""

# Verify checksums
if [[ -f "$DATA_DIR/manifest.json" ]]; then
    verify_checksums || SUCCESS=false
fi

# Summary
echo ""
echo -e "${BLUE}========================================"
echo -e "  Download Complete"
echo -e "========================================${NC}"
echo ""

if $SUCCESS; then
    show_info
    echo -e "${GREEN}✅ Knowledge base installed successfully!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some downloads failed${NC}"
    echo "Re-run with --force to retry."
    exit 1
fi
