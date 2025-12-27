#!/usr/bin/env python3
"""Build the complete RAG knowledge base from downloaded sources.

DEPRECATED: This script is for development of the waycore-knowledge repository.
For normal use, download the pre-built knowledge base instead:
    ./scripts/download-knowledge.sh

This script:
1. Parses all downloaded PDFs and data files
2. Generates embeddings for each entry
3. Builds the hybrid SQLite + Hnswlib index

Usage:
    python scripts/build-rag-index.py
    python scripts/build-rag-index.py --rebuild  # Clear and rebuild
    python scripts/build-rag-index.py --raw-dir data/raw --output-dir data/outdoor
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from device.services.ai_service.rag.embeddings import LocalEmbeddings  # noqa: E402
from device.services.ai_service.rag.models import Category, KnowledgeEntry  # noqa: E402
from device.services.ai_service.rag.parsers.pdf import PDFParser  # noqa: E402
from device.services.ai_service.rag.parsers.plants import PlantDataParser  # noqa: E402
from device.services.ai_service.rag.store import HybridKnowledgeStore  # noqa: E402


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Build RAG knowledge base from downloaded sources")
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=Path("data/raw"),
        help="Directory containing downloaded source files",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/outdoor"),
        help="Directory for processed knowledge base",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Clear existing index and rebuild from scratch",
    )
    parser.add_argument(
        "--skip-embeddings",
        action="store_true",
        help="Skip embedding generation (faster, keyword-only search)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size for embedding generation",
    )
    return parser.parse_args()


def parse_survival_pdfs(raw_dir: Path, pdf_parser: PDFParser) -> list[KnowledgeEntry]:
    """Parse survival manual PDFs."""
    entries: list[KnowledgeEntry] = []
    survival_dir = raw_dir / "survival"

    if not survival_dir.exists():
        print("  ⚠️  No survival directory found")
        return entries

    for pdf_file in survival_dir.glob("*.pdf"):
        try:
            parsed = pdf_parser.parse_file(pdf_file, Category.SURVIVAL)
            entries.extend(parsed)
            print(f"  ✓ {pdf_file.name}: {len(parsed)} entries")
        except Exception as e:
            print(f"  ✗ {pdf_file.name}: {e}")

    return entries


def parse_navigation_pdfs(raw_dir: Path, pdf_parser: PDFParser) -> list[KnowledgeEntry]:
    """Parse navigation PDFs."""
    entries: list[KnowledgeEntry] = []
    nav_dir = raw_dir / "navigation"

    if not nav_dir.exists():
        print("  ⚠️  No navigation directory found")
        return entries

    for pdf_file in nav_dir.glob("*.pdf"):
        try:
            parsed = pdf_parser.parse_file(pdf_file, Category.NAVIGATION)
            entries.extend(parsed)
            print(f"  ✓ {pdf_file.name}: {len(parsed)} entries")
        except Exception as e:
            print(f"  ✗ {pdf_file.name}: {e}")

    return entries


def parse_first_aid_pdfs(raw_dir: Path, pdf_parser: PDFParser) -> list[KnowledgeEntry]:
    """Parse first aid PDFs."""
    entries: list[KnowledgeEntry] = []
    fa_dir = raw_dir / "first_aid"

    if not fa_dir.exists():
        print("  ⚠️  No first_aid directory found")
        return entries

    for pdf_file in fa_dir.glob("*.pdf"):
        try:
            parsed = pdf_parser.parse_file(pdf_file, Category.FIRST_AID)
            entries.extend(parsed)
            print(f"  ✓ {pdf_file.name}: {len(parsed)} entries")
        except Exception as e:
            print(f"  ✗ {pdf_file.name}: {e}")

    return entries


def parse_knots_pdfs(raw_dir: Path, pdf_parser: PDFParser) -> list[KnowledgeEntry]:
    """Parse knots/rigging PDFs."""
    entries: list[KnowledgeEntry] = []
    knots_dir = raw_dir / "knots"

    if not knots_dir.exists():
        print("  ⚠️  No knots directory found")
        return entries

    for pdf_file in knots_dir.glob("*.pdf"):
        try:
            parsed = pdf_parser.parse_file(pdf_file, Category.KNOTS)
            entries.extend(parsed)
            print(f"  ✓ {pdf_file.name}: {len(parsed)} entries")
        except Exception as e:
            print(f"  ✗ {pdf_file.name}: {e}")

    return entries


def parse_weather_pdfs(raw_dir: Path, pdf_parser: PDFParser) -> list[KnowledgeEntry]:
    """Parse weather PDFs."""
    entries: list[KnowledgeEntry] = []
    weather_dir = raw_dir / "weather"

    if not weather_dir.exists():
        print("  ⚠️  No weather directory found")
        return entries

    for pdf_file in weather_dir.glob("*.pdf"):
        try:
            parsed = pdf_parser.parse_file(pdf_file, Category.WEATHER)
            entries.extend(parsed)
            print(f"  ✓ {pdf_file.name}: {len(parsed)} entries")
        except Exception as e:
            print(f"  ✗ {pdf_file.name}: {e}")

    return entries


def parse_plant_data(raw_dir: Path, plant_parser: PlantDataParser) -> list[KnowledgeEntry]:
    """Parse plant database files."""
    entries: list[KnowledgeEntry] = []
    plants_dir = raw_dir / "plants"

    if not plants_dir.exists():
        print("  ⚠️  No plants directory found")
        return entries

    # Parse JSON files (PFAF format)
    for json_file in plants_dir.glob("*.json"):
        try:
            parsed = plant_parser.parse_pfaf_json(json_file)
            entries.extend(parsed)
            print(f"  ✓ {json_file.name}: {len(parsed)} entries")
        except Exception as e:
            print(f"  ✗ {json_file.name}: {e}")

    # Parse CSV files (USDA format)
    for csv_file in plants_dir.glob("*.csv"):
        try:
            parsed = plant_parser.parse_usda_csv(csv_file)
            entries.extend(parsed)
            print(f"  ✓ {csv_file.name}: {len(parsed)} entries")
        except Exception as e:
            print(f"  ✗ {csv_file.name}: {e}")

    return entries


def generate_embeddings(
    entries: list[KnowledgeEntry],
    batch_size: int = 32,
) -> list[KnowledgeEntry]:
    """Generate embeddings for all entries."""
    print(f"\n🔢 Generating embeddings for {len(entries)} entries...")
    print("   This may take several minutes on slower hardware...")

    embeddings = LocalEmbeddings()

    # Combine title and content for embedding
    texts = [f"{e.title} {e.content}" for e in entries]

    start_time = time.time()

    # Process in batches with progress
    all_embeddings: list[list[float]] = []
    total_batches = (len(texts) + batch_size - 1) // batch_size

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        batch_embeddings = embeddings.embed(batch)
        all_embeddings.extend(batch_embeddings)

        batch_num = (i // batch_size) + 1
        progress = (batch_num / total_batches) * 100
        print(f"\r   Progress: {progress:.1f}% ({batch_num}/{total_batches} batches)", end="")

    print()  # Newline after progress

    # Assign embeddings to entries
    for entry, embedding in zip(entries, all_embeddings):
        entry.embedding = embedding

    elapsed = time.time() - start_time
    print(f"   Completed in {elapsed:.1f} seconds")

    return entries


def main() -> int:
    """Main build function."""
    args = parse_args()

    print("=" * 60)
    print("   Waycore RAG Knowledge Base Builder")
    print("=" * 60)
    print(f"\nSource directory: {args.raw_dir}")
    print(f"Output directory: {args.output_dir}")

    # Check if source directory exists
    if not args.raw_dir.exists():
        print(f"\n❌ Error: Source directory not found: {args.raw_dir}")
        print("   Run ./scripts/download-rag-sources.sh first")
        return 1

    # Initialize parsers
    pdf_parser = PDFParser(chunk_size=500, chunk_overlap=50)
    plant_parser = PlantDataParser()

    # Initialize store
    args.output_dir.mkdir(parents=True, exist_ok=True)
    store = HybridKnowledgeStore(data_dir=args.output_dir)

    if args.rebuild:
        print("\n🗑️  Clearing existing index...")
        store.clear()

    # Parse all sources
    all_entries: list[KnowledgeEntry] = []

    print("\n📚 Parsing survival manuals...")
    all_entries.extend(parse_survival_pdfs(args.raw_dir, pdf_parser))

    print("\n🧭 Parsing navigation resources...")
    all_entries.extend(parse_navigation_pdfs(args.raw_dir, pdf_parser))

    print("\n🏥 Parsing first aid guides...")
    all_entries.extend(parse_first_aid_pdfs(args.raw_dir, pdf_parser))

    print("\n🪢 Parsing knots resources...")
    all_entries.extend(parse_knots_pdfs(args.raw_dir, pdf_parser))

    print("\n🌦️ Parsing weather resources...")
    all_entries.extend(parse_weather_pdfs(args.raw_dir, pdf_parser))

    print("\n🌿 Parsing plant databases...")
    all_entries.extend(parse_plant_data(args.raw_dir, plant_parser))

    print(f"\n📊 Total entries parsed: {len(all_entries)}")

    if len(all_entries) == 0:
        print("\n⚠️  No entries found. Make sure source files are downloaded.")
        return 1

    # Generate embeddings (unless skipped)
    if not args.skip_embeddings:
        try:
            all_entries = generate_embeddings(all_entries, args.batch_size)
        except ImportError as e:
            print(f"\n⚠️  Embedding generation skipped: {e}")
            print("   Install sentence-transformers for semantic search")
    else:
        print("\n⏭️  Skipping embedding generation (--skip-embeddings)")

    # Add entries to store
    print("\n💾 Building hybrid index...")
    start_time = time.time()
    added = store.add_entries(all_entries)
    store.save_index()

    elapsed = time.time() - start_time
    print(f"   Added {added} entries in {elapsed:.1f} seconds")

    # Print stats
    stats = store.get_stats()
    print("\n" + "=" * 60)
    print("   Build Summary")
    print("=" * 60)
    print(f"\nTotal entries: {stats['total_entries']}")
    print(f"Database size: {stats['db_size_mb']:.1f} MB")
    print(f"Vector index size: {stats['index_size_mb']:.1f} MB")

    print("\nBy category:")
    for cat, count in sorted(stats.get("by_category", {}).items()):
        print(f"  • {cat}: {count}")

    print("\nBy safety level:")
    for level, count in sorted(stats.get("by_safety", {}).items()):
        print(f"  • {level}: {count}")

    print("\n✅ RAG knowledge base built successfully!")
    print(f"   Location: {args.output_dir}")

    store.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
