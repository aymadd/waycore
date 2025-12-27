"""Tests for KnowledgeBaseManager."""

from __future__ import annotations

import json
from pathlib import Path

from device.libs.knowledge.manager import KnowledgeBaseManager


class TestKnowledgeBaseManager:
    """Tests for KnowledgeBaseManager class."""

    def test_init_creates_directory(self, tmp_path: Path) -> None:
        """Test that init creates data directory."""
        data_dir = tmp_path / "knowledge"
        manager = KnowledgeBaseManager(data_dir=data_dir)

        assert data_dir.exists()
        assert manager.data_dir == data_dir

    def test_get_installed_version_none(self, tmp_path: Path) -> None:
        """Test get_installed_version returns None when not installed."""
        manager = KnowledgeBaseManager(data_dir=tmp_path)
        assert manager.get_installed_version() is None

    def test_get_installed_version_from_version_file(self, tmp_path: Path) -> None:
        """Test get_installed_version reads from .version file."""
        manager = KnowledgeBaseManager(data_dir=tmp_path)
        (tmp_path / ".version").write_text("v1.0.1")

        assert manager.get_installed_version() == "v1.0.1"

    def test_get_installed_version_from_manifest(self, tmp_path: Path) -> None:
        """Test get_installed_version reads from manifest.json."""
        manager = KnowledgeBaseManager(data_dir=tmp_path)
        manifest = {"version": "v2.0.0", "entry_count": 100}
        (tmp_path / "manifest.json").write_text(json.dumps(manifest))

        assert manager.get_installed_version() == "v2.0.0"

    def test_get_status_not_installed(self, tmp_path: Path) -> None:
        """Test get_status when not installed."""
        manager = KnowledgeBaseManager(data_dir=tmp_path)
        status = manager.get_status()

        assert status.installed is False
        assert status.db_exists is False
        assert status.idx_exists is False
        assert status.version is None

    def test_get_status_installed(self, tmp_path: Path) -> None:
        """Test get_status when installed."""
        manager = KnowledgeBaseManager(data_dir=tmp_path)

        # Create mock files
        (tmp_path / "knowledge.db").write_bytes(b"x" * 1024 * 1024)  # 1MB
        (tmp_path / "knowledge.idx").write_bytes(b"y" * 512 * 1024)  # 0.5MB
        (tmp_path / ".version").write_text("v1.0.0")
        (tmp_path / "manifest.json").write_text(json.dumps({"entry_count": 500}))

        status = manager.get_status()

        assert status.installed is True
        assert status.db_exists is True
        assert status.idx_exists is True
        assert status.version == "v1.0.0"
        assert status.db_size_mb == 1.0
        assert status.idx_size_mb == 0.5
        assert status.entry_count == 500

    def test_verify_integrity_no_files(self, tmp_path: Path) -> None:
        """Test verify_integrity returns False when files missing."""
        manager = KnowledgeBaseManager(data_dir=tmp_path)
        assert manager.verify_integrity() is False

    def test_verify_integrity_files_exist(self, tmp_path: Path) -> None:
        """Test verify_integrity returns True when files exist."""
        manager = KnowledgeBaseManager(data_dir=tmp_path)

        (tmp_path / "knowledge.db").write_bytes(b"test database")
        (tmp_path / "knowledge.idx").write_bytes(b"test index")

        assert manager.verify_integrity() is True

    def test_verify_integrity_checksum_match(self, tmp_path: Path) -> None:
        """Test verify_integrity with matching checksums."""
        manager = KnowledgeBaseManager(data_dir=tmp_path)

        # Create files
        db_content = b"test database content"
        idx_content = b"test index content"
        (tmp_path / "knowledge.db").write_bytes(db_content)
        (tmp_path / "knowledge.idx").write_bytes(idx_content)

        # Create manifest with correct checksums
        manifest = {
            "checksums": {
                "knowledge_db": manager._compute_sha256(tmp_path / "knowledge.db"),
                "knowledge_idx": manager._compute_sha256(tmp_path / "knowledge.idx"),
            }
        }
        (tmp_path / "manifest.json").write_text(json.dumps(manifest))

        assert manager.verify_integrity() is True

    def test_verify_integrity_checksum_mismatch(self, tmp_path: Path) -> None:
        """Test verify_integrity with mismatched checksums."""
        manager = KnowledgeBaseManager(data_dir=tmp_path)

        # Create files
        (tmp_path / "knowledge.db").write_bytes(b"test database")
        (tmp_path / "knowledge.idx").write_bytes(b"test index")

        # Create manifest with wrong checksums
        manifest = {
            "checksums": {
                "knowledge_db": "wrong_checksum",
                "knowledge_idx": "wrong_checksum",
            }
        }
        (tmp_path / "manifest.json").write_text(json.dumps(manifest))

        assert manager.verify_integrity() is False

    def test_get_stats(self, tmp_path: Path) -> None:
        """Test get_stats returns dictionary."""
        manager = KnowledgeBaseManager(data_dir=tmp_path)

        # Create mock files
        (tmp_path / "knowledge.db").write_bytes(b"x" * 1000)
        (tmp_path / "knowledge.idx").write_bytes(b"y" * 500)
        (tmp_path / ".version").write_text("v1.0.0")

        stats = manager.get_stats()

        assert isinstance(stats, dict)
        assert stats["version"] == "v1.0.0"
        assert stats["installed"] is True
        assert stats["db_exists"] is True
        assert stats["idx_exists"] is True
        assert stats["integrity"] is True

    def test_compute_sha256(self, tmp_path: Path) -> None:
        """Test _compute_sha256 computes correct hash."""
        manager = KnowledgeBaseManager(data_dir=tmp_path)

        # Known SHA256 for "hello world"
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")

        sha256 = manager._compute_sha256(test_file)

        # Verify format (64 hex characters)
        assert len(sha256) == 64
        assert all(c in "0123456789abcdef" for c in sha256)

    def test_is_current_not_installed(self, tmp_path: Path) -> None:
        """Test _is_current returns False when not installed."""
        manager = KnowledgeBaseManager(data_dir=tmp_path)
        assert manager._is_current("v1.0.0") is False

    def test_is_current_version_match(self, tmp_path: Path) -> None:
        """Test _is_current returns True when version matches."""
        manager = KnowledgeBaseManager(data_dir=tmp_path)
        (tmp_path / ".version").write_text("v1.0.0")

        assert manager._is_current("v1.0.0") is True
        assert manager._is_current("v2.0.0") is False
