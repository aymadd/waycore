"""Knowledge base manager for waycore-knowledge releases.

This module provides infrastructure for downloading, verifying, and managing
the RAG knowledge base from GitHub releases.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Default paths
DEFAULT_DATA_DIR = Path(os.getenv("RAG_DATA_DIR", "data/outdoor"))
DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.parent.parent / "config" / "knowledge.yaml"

# GitHub API
REPO_OWNER = "dmitry-grechko"
REPO_NAME = "waycore-knowledge"
GITHUB_API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases"


@dataclass
class KnowledgeVersion:
    """Information about an installed knowledge base version."""

    version: str
    installed_at: str
    entry_count: int = 0
    db_size_mb: float = 0
    idx_size_mb: float = 0
    sha256_db: str | None = None
    sha256_idx: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "version": self.version,
            "installed_at": self.installed_at,
            "entry_count": self.entry_count,
            "db_size_mb": self.db_size_mb,
            "idx_size_mb": self.idx_size_mb,
            "sha256_db": self.sha256_db,
            "sha256_idx": self.sha256_idx,
        }


@dataclass
class KnowledgeBaseStatus:
    """Current status of the knowledge base."""

    installed: bool = False
    version: str | None = None
    db_exists: bool = False
    idx_exists: bool = False
    db_size_mb: float = 0
    idx_size_mb: float = 0
    entry_count: int = 0
    integrity_valid: bool = False
    update_available: str | None = None
    errors: list[str] = field(default_factory=list)


class KnowledgeBaseManager:
    """Manages the RAG knowledge base from waycore-knowledge releases.

    Features:
    - Download from GitHub releases
    - Version tracking with lock file
    - SHA256 checksum verification
    - Update checking
    - Graceful error handling

    Example:
        >>> manager = KnowledgeBaseManager()
        >>> manager.download()  # Download latest version
        True
        >>> manager.get_installed_version()
        'v1.0.1'
        >>> manager.verify_integrity()
        True
    """

    def __init__(
        self,
        data_dir: Path | None = None,
        config_path: Path | None = None,
    ) -> None:
        """Initialize the knowledge base manager.

        Args:
            data_dir: Directory containing knowledge base files.
            config_path: Path to knowledge.yaml configuration.
        """
        self.data_dir = data_dir or DEFAULT_DATA_DIR
        self.config_path = config_path or DEFAULT_CONFIG_PATH

        # Ensure directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # File paths
        self.db_path = self.data_dir / "knowledge.db"
        self.idx_path = self.data_dir / "knowledge.idx"
        self.manifest_path = self.data_dir / "manifest.json"
        self.version_file = self.data_dir / ".version"
        self.lock_file = self.data_dir.parent / "knowledge.lock"

    def get_installed_version(self) -> str | None:
        """Get the currently installed version.

        Returns:
            Version string (e.g., 'v1.0.1') or None if not installed.
        """
        # Check .version file first
        if self.version_file.exists():
            return self.version_file.read_text().strip()

        # Fall back to manifest
        if self.manifest_path.exists():
            try:
                manifest = json.loads(self.manifest_path.read_text())
                version: str | None = manifest.get("version")
                return version
            except (json.JSONDecodeError, OSError):
                pass

        # Check lock file
        if self.lock_file.exists():
            try:
                lock = json.loads(self.lock_file.read_text())
                lock_version: str | None = lock.get("version")
                return lock_version
            except (json.JSONDecodeError, OSError):
                pass

        return None

    def check_for_updates(self) -> str | None:
        """Check if a newer version is available.

        Returns:
            Latest version tag if update available, None if up-to-date.
        """
        installed = self.get_installed_version()
        try:
            latest = self._fetch_latest_version()
        except Exception as e:
            logger.warning(f"Failed to check for updates: {e}")
            return None

        if installed != latest:
            return latest
        return None

    def download(
        self,
        version: str = "latest",
        force: bool = False,
    ) -> bool:
        """Download knowledge base from GitHub releases.

        Args:
            version: Version tag or 'latest'.
            force: Re-download even if already installed.

        Returns:
            True if download succeeded.
        """
        if not force and self._is_current(version):
            logger.info(f"Knowledge base v{self.get_installed_version()} already installed")
            return True

        try:
            # Get release info
            release = self._get_release(version)
            if not release:
                logger.error(f"Release {version} not found")
                return False

            tag_name: str = release.get("tag_name", version)
            logger.info(f"Downloading knowledge base {tag_name}...")

            # Download assets
            assets = release.get("assets", [])
            success = self._download_assets(assets)

            if success:
                # Save version
                self.version_file.write_text(tag_name)
                self._update_lock(release)
                logger.info(f"Knowledge base {tag_name} installed successfully")
                return True
            else:
                logger.error("Failed to download required assets")
                return False

        except Exception as e:
            logger.error(f"Failed to download knowledge base: {e}")
            return False

    def verify_integrity(self) -> bool:
        """Verify integrity of installed knowledge base.

        Checks:
        - Required files exist
        - SHA256 checksums match manifest (if available)

        Returns:
            True if integrity check passes.
        """
        # Check required files exist
        if not self.db_path.exists():
            logger.warning("knowledge.db not found")
            return False

        if not self.idx_path.exists():
            logger.warning("knowledge.idx not found")
            return False

        # Verify checksums if manifest exists
        if self.manifest_path.exists():
            try:
                manifest = json.loads(self.manifest_path.read_text())
                checksums = manifest.get("checksums", {})

                # Check database
                expected_db = checksums.get("knowledge_db")
                if expected_db:
                    actual_db = self._compute_sha256(self.db_path)
                    if actual_db != expected_db:
                        logger.warning("knowledge.db checksum mismatch")
                        return False

                # Check index
                expected_idx = checksums.get("knowledge_idx")
                if expected_idx:
                    actual_idx = self._compute_sha256(self.idx_path)
                    if actual_idx != expected_idx:
                        logger.warning("knowledge.idx checksum mismatch")
                        return False

            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Failed to verify checksums: {e}")

        return True

    def get_status(self) -> KnowledgeBaseStatus:
        """Get current knowledge base status.

        Returns:
            KnowledgeBaseStatus object with current state.
        """
        status = KnowledgeBaseStatus()

        # Check file existence
        status.db_exists = self.db_path.exists()
        status.idx_exists = self.idx_path.exists()

        if status.db_exists:
            status.db_size_mb = round(self.db_path.stat().st_size / (1024 * 1024), 2)

        if status.idx_exists:
            status.idx_size_mb = round(self.idx_path.stat().st_size / (1024 * 1024), 2)

        # Check if installed
        status.installed = status.db_exists and status.idx_exists
        status.version = self.get_installed_version()

        # Get entry count from manifest
        if self.manifest_path.exists():
            try:
                manifest = json.loads(self.manifest_path.read_text())
                entry_count = manifest.get("entry_count")
                if isinstance(entry_count, int):
                    status.entry_count = entry_count
            except (json.JSONDecodeError, OSError):
                pass

        # Verify integrity
        if status.installed:
            status.integrity_valid = self.verify_integrity()

        # Check for updates
        try:
            status.update_available = self.check_for_updates()
        except Exception:
            pass  # Network error, not critical

        return status

    def get_stats(self) -> dict[str, Any]:
        """Get knowledge base statistics.

        Returns:
            Dictionary with statistics.
        """
        status = self.get_status()
        return {
            "version": status.version,
            "installed": status.installed,
            "db_exists": status.db_exists,
            "idx_exists": status.idx_exists,
            "db_size_mb": status.db_size_mb,
            "idx_size_mb": status.idx_size_mb,
            "entry_count": status.entry_count,
            "integrity": status.integrity_valid,
            "update_available": status.update_available,
        }

    def _is_current(self, version: str) -> bool:
        """Check if specified version is already installed."""
        installed = self.get_installed_version()
        if not installed:
            return False

        if version == "latest":
            try:
                latest = self._fetch_latest_version()
                return installed == latest
            except Exception:
                return True  # Assume current if can't check

        return installed == version

    def _fetch_latest_version(self) -> str:
        """Fetch latest release version from GitHub."""
        url = f"{GITHUB_API_URL}/latest"
        request = urllib.request.Request(
            url,
            headers={"Accept": "application/vnd.github.v3+json"},
        )

        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode())
            tag_name: str = data["tag_name"]
            return tag_name

    def _get_release(self, version: str) -> dict[str, Any] | None:
        """Get release information from GitHub."""
        if version == "latest":
            url = f"{GITHUB_API_URL}/latest"
        else:
            url = f"{GITHUB_API_URL}/tags/{version}"

        request = urllib.request.Request(
            url,
            headers={"Accept": "application/vnd.github.v3+json"},
        )

        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                result: dict[str, Any] = json.loads(response.read().decode())
                return result
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            raise

    def _download_assets(self, assets: list[dict[str, Any]]) -> bool:
        """Download release assets."""
        required = {"knowledge.db", "knowledge.idx"}
        downloaded: set[str] = set()

        for asset in assets:
            name = asset.get("name", "")
            url = asset.get("browser_download_url", "")

            if not url:
                continue

            if name == "knowledge.db":
                target = self.db_path
            elif name == "knowledge.idx":
                target = self.idx_path
            elif name == "manifest.json":
                target = self.manifest_path
            elif name == "species_safety.json":
                target = self.data_dir / "species_safety.json"
            else:
                continue

            try:
                logger.info(f"Downloading {name}...")
                urllib.request.urlretrieve(url, target)
                downloaded.add(name)
                logger.info(f"Downloaded {name}")
            except Exception as e:
                logger.warning(f"Failed to download {name}: {e}")

        # Check all required files were downloaded
        return required.issubset(downloaded)

    def _update_lock(self, release: dict[str, Any]) -> None:
        """Update lock file with installed version info."""
        lock = {
            "version": release.get("tag_name"),
            "installed_at": datetime.utcnow().isoformat() + "Z",
            "release_url": release.get("html_url"),
        }

        # Add checksums if available
        if self.db_path.exists():
            lock["sha256_db"] = self._compute_sha256(self.db_path)
        if self.idx_path.exists():
            lock["sha256_idx"] = self._compute_sha256(self.idx_path)

        self.lock_file.parent.mkdir(parents=True, exist_ok=True)
        self.lock_file.write_text(json.dumps(lock, indent=2))

    def _compute_sha256(self, path: Path) -> str:
        """Compute SHA256 hash of a file."""
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
