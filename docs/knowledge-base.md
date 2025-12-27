# Knowledge Base Management

The Waycore AI service uses a pre-built knowledge base for outdoor survival, navigation, first aid, and related topics. This guide covers how to download, verify, and manage the knowledge base.

## Overview

The knowledge base consists of:

| File | Description |
|------|-------------|
| `knowledge.db` | SQLite database with FTS5 full-text search index |
| `knowledge.idx` | Hnswlib vector index for semantic similarity search |
| `manifest.json` | Version, checksums, and metadata |
| `species_safety.json` | Optional species safety data (edibility, toxicity) |

Files are stored in `data/outdoor/` and are downloaded from the [waycore-knowledge](https://github.com/dmitry-grechko/waycore-knowledge) GitHub releases.

## Quick Start

### Automatic Download

The knowledge base is automatically downloaded when you start the development environment:

```bash
./scripts/dev-start.sh
```

### Manual Download

```bash
# Download latest version
./scripts/download-knowledge.sh

# Download specific version
./scripts/download-knowledge.sh --version v1.0.1

# Force re-download
./scripts/download-knowledge.sh --force
```

### Verify Installation

```bash
# Check current status
./scripts/knowledge-info.sh

# Full verification with checksums
./scripts/verify-knowledge.sh
```

## Scripts

### download-knowledge.sh

Downloads the knowledge base from GitHub releases.

```bash
./scripts/download-knowledge.sh [OPTIONS]

Options:
  --version VERSION  Specific version to download (default: latest)
  --dir DIR          Target directory (default: data/outdoor)
  --force            Re-download even if already present
  --verify           Only verify existing files
  --help             Show help message
```

Examples:

```bash
# Download latest
./scripts/download-knowledge.sh

# Download v1.0.1
./scripts/download-knowledge.sh --version v1.0.1

# Verify only
./scripts/download-knowledge.sh --verify
```

### verify-knowledge.sh

Verifies integrity of installed knowledge base.

```bash
./scripts/verify-knowledge.sh [OPTIONS]

Options:
  --dir DIR  Data directory (default: data/outdoor)
```

Checks:
- Required files exist (knowledge.db, knowledge.idx)
- Optional files present (manifest.json, species_safety.json)
- SHA256 checksums match manifest

### knowledge-info.sh

Displays current knowledge base version and status.

```bash
./scripts/knowledge-info.sh [OPTIONS]

Options:
  --dir DIR  Data directory (default: data/outdoor)
```

## Version Tracking

The installed version is tracked in:

1. `.version` file in the data directory
2. `manifest.json` with detailed metadata

Example manifest.json:

```json
{
  "version": "v1.0.1",
  "built_at": "2025-12-27T10:00:00Z",
  "entry_count": 1500,
  "categories": {
    "survival": 450,
    "navigation": 200,
    "first_aid": 350,
    "plants": 300,
    "weather": 200
  },
  "checksums": {
    "knowledge_db": "sha256:abc123...",
    "knowledge_idx": "sha256:def456..."
  }
}
```

## Docker Integration

In Docker, the knowledge base is mounted as a read-only volume:

```yaml
# docker/compose/dev.yml
ai-service:
  volumes:
    - ../../data/outdoor:/app/data/outdoor:ro
  environment:
    - RAG_DATA_DIR=/app/data/outdoor
```

The AI service checks for the knowledge base on startup and logs its version.

## Troubleshooting

### Knowledge base not found

```bash
./scripts/download-knowledge.sh --force
```

### Checksum mismatch

```bash
# Remove corrupted files and re-download
rm -rf data/outdoor/*
./scripts/download-knowledge.sh
```

### Network errors

The download script has built-in retry logic. If downloads continue to fail:

1. Check your internet connection
2. Verify the release exists at https://github.com/dmitry-grechko/waycore-knowledge/releases
3. Try downloading manually and placing files in `data/outdoor/`

### AI service not finding knowledge base

Ensure the Docker volume is mounted correctly:

```bash
docker compose -f docker/compose/dev.yml restart ai-service
```

Check service logs:

```bash
docker compose -f docker/compose/dev.yml logs ai-service | grep -i knowledge
```

## Building Locally (Development)

For contributors working on the knowledge base itself:

```bash
# Download source PDFs
./scripts/download-rag-sources.sh

# Build the knowledge base
poetry run python scripts/build-rag-index.py
```

This is only needed when modifying the knowledge base content. Regular users should download pre-built releases.

## Related Documentation

- [AI Model Management](models/README.md)
- [RAG Implementation](../device/services/ai_service/rag/README.md)
- [Local Development](local_dev_docker.md)
