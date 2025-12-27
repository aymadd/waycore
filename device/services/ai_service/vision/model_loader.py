"""Vision model loader with HuggingFace Hub integration.

This module provides unified model loading for vision models, supporting
both direct downloads (TensorFlow Hub, Google Storage) and HuggingFace Hub.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# Default paths
_config_path = Path(__file__).parent.parent.parent.parent.parent.parent
DEFAULT_CONFIG_PATH = _config_path / "config" / "models.yaml"
DEFAULT_MODEL_DIR = Path(os.getenv("WAYCORE_MODEL_PATH", "/opt/waycore/models"))
DEFAULT_CACHE_DIR = Path.home() / ".cache" / "waycore" / "models"


class VisionModelLoader:
    """Loads vision models from HuggingFace Hub or direct URLs.

    Supports:
    - HuggingFace Hub models via huggingface_hub library
    - Direct URL downloads with caching
    - Model profiles for different installation sizes
    - Context-aware model selection
    """

    def __init__(
        self,
        config_path: Path | None = None,
        model_dir: Path | None = None,
        cache_dir: Path | None = None,
    ) -> None:
        """Initialize the model loader.

        Args:
            config_path: Path to models.yaml configuration file.
            model_dir: Directory containing local model files.
            cache_dir: Cache directory for downloaded models.
        """
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self.model_dir = model_dir or DEFAULT_MODEL_DIR
        self.cache_dir = cache_dir or DEFAULT_CACHE_DIR
        self.config = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from YAML file."""
        if self.config_path.exists():
            with open(self.config_path) as f:
                return yaml.safe_load(f) or {}
        logger.warning(f"Config not found at {self.config_path}, using defaults")
        return {"models": {}, "profiles": {}, "language_models": {}}

    def get_model_config(self, model_id: str) -> dict[str, Any] | None:
        """Get configuration for a specific model.

        Args:
            model_id: Model identifier.

        Returns:
            Model configuration dict or None if not found.
        """
        # Check vision models
        models = self.config.get("models", {})
        if model_id in models:
            result: dict[str, Any] = models[model_id]
            return result

        # Check language models
        lang_models = self.config.get("language_models", {})
        if model_id in lang_models:
            lang_result: dict[str, Any] = lang_models[model_id]
            return lang_result

        return None

    def get_local_path(self, model_id: str) -> Path | None:
        """Get path to locally installed model file.

        Args:
            model_id: Model identifier.

        Returns:
            Path to model file or None if not found.
        """
        config = self.get_model_config(model_id)
        if not config:
            return None

        local_path_str: str | None = config.get("local_path")
        if local_path_str:
            full_path = self.model_dir / local_path_str
            if full_path.exists():
                return Path(full_path)

        return None

    def is_available(self, model_id: str) -> bool:
        """Check if a model is downloaded and available locally.

        Args:
            model_id: Model identifier.

        Returns:
            True if model file exists locally.
        """
        return self.get_local_path(model_id) is not None

    def download_model(self, model_id: str, force: bool = False) -> Path:
        """Download a model from its source.

        Args:
            model_id: Model identifier from config.
            force: Force re-download even if already exists.

        Returns:
            Path to downloaded model file.

        Raises:
            ValueError: If model not found in config.
            RuntimeError: If download fails.
        """
        config = self.get_model_config(model_id)
        if not config:
            raise ValueError(f"Unknown model: {model_id}")

        # Check if already available
        if not force:
            local_path = self.get_local_path(model_id)
            if local_path:
                logger.debug(f"Model {model_id} already available at {local_path}")
                return local_path

        source = config.get("source", "direct")

        if source == "huggingface":
            return self._download_from_huggingface(model_id, config)
        elif source == "direct":
            return self._download_direct(model_id, config)
        else:
            raise ValueError(f"Unsupported source: {source}")

    def _download_from_huggingface(self, model_id: str, config: dict[str, Any]) -> Path:
        """Download model from HuggingFace Hub.

        Args:
            model_id: Model identifier.
            config: Model configuration dict.

        Returns:
            Path to downloaded model file.
        """
        try:
            from huggingface_hub import hf_hub_download
        except ImportError as e:
            raise RuntimeError(
                "huggingface_hub required for HuggingFace downloads. "
                "Install with: poetry add huggingface-hub"
            ) from e

        repo_id: str | None = config.get("repo_id")
        filename: str | None = config.get("filename")

        if not repo_id:
            raise ValueError(f"No repo_id configured for model {model_id}")
        if not filename:
            raise ValueError(f"No filename configured for model {model_id}")

        model_name: str = config.get("name", model_id)
        logger.info(f"Downloading {model_name} from HuggingFace...")

        try:
            # Download to HuggingFace cache
            downloaded_path: str = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                cache_dir=str(self.cache_dir),
            )

            # If we have a local_path, copy to the expected location
            local_path_str: str | None = config.get("local_path")
            if local_path_str:
                target_path = self.model_dir / local_path_str
                target_path.parent.mkdir(parents=True, exist_ok=True)

                import shutil

                shutil.copy2(downloaded_path, target_path)
                logger.info(f"Installed {model_id} to {target_path}")
                return Path(target_path)

            return Path(downloaded_path)

        except Exception as e:
            raise RuntimeError(f"Failed to download {model_id} from HuggingFace: {e}") from e

    def _download_direct(self, model_id: str, config: dict[str, Any]) -> Path:
        """Download model from direct URL.

        Args:
            model_id: Model identifier.
            config: Model configuration dict.

        Returns:
            Path to downloaded model file.
        """
        import urllib.request

        url = config.get("download_url")
        if not url:
            raise ValueError(f"No download_url configured for model {model_id}")

        local_path = config.get("local_path")
        if not local_path:
            filename = config.get("filename", f"{model_id}.model")
            local_path = f"vision/{filename}"

        target_path = self.model_dir / local_path
        target_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Downloading {config.get('name', model_id)} from {url}...")

        try:
            urllib.request.urlretrieve(url, target_path)
            logger.info(f"Installed {model_id} to {target_path}")

            # Download labels if configured
            labels_url = config.get("labels_url")
            labels_path = config.get("local_labels")
            if labels_url and labels_path:
                labels_target = self.model_dir / labels_path
                labels_target.parent.mkdir(parents=True, exist_ok=True)
                urllib.request.urlretrieve(labels_url, labels_target)
                logger.info(f"Downloaded labels to {labels_target}")

            return target_path

        except Exception as e:
            raise RuntimeError(f"Failed to download {model_id}: {e}") from e

    def download_profile(self, profile: str = "basic") -> dict[str, Path]:
        """Download all models in a profile.

        Args:
            profile: Profile name (basic, nature, full).

        Returns:
            Dict mapping model_id to downloaded path.

        Raises:
            ValueError: If profile not found.
        """
        profiles = self.config.get("profiles", {})
        profile_config = profiles.get(profile)

        if not profile_config:
            available = list(profiles.keys())
            raise ValueError(f"Unknown profile: {profile}. Available: {available}")

        model_ids = profile_config.get("models", [])
        paths: dict[str, Path] = {}

        logger.info(f"Downloading profile '{profile}' ({len(model_ids)} models)...")

        for model_id in model_ids:
            try:
                paths[model_id] = self.download_model(model_id)
            except Exception as e:
                logger.warning(f"Failed to download {model_id}: {e}")

        return paths

    def get_model_for_context(self, context: str) -> str:
        """Select best available model for a use case.

        Args:
            context: Usage context (general, nature, outdoor, etc.)

        Returns:
            model_id of best available model for the context.
        """
        context_mapping: dict[str, str] = self.config.get("context_mapping", {})
        preferred: str | None = context_mapping.get(context.lower())

        if preferred and self.is_available(preferred):
            return str(preferred)

        # Fall back to default
        default: str = context_mapping.get("default", "mobilenet_v3")
        if self.is_available(default):
            return str(default)

        # Return first available model
        models: dict[str, Any] = self.config.get("models", {})
        for model_id in models:
            if self.is_available(model_id):
                return str(model_id)

        raise RuntimeError("No vision models available")

    def list_models(self) -> dict[str, dict[str, Any]]:
        """List all configured models with their status.

        Returns:
            Dict mapping model_id to info including availability.
        """
        result: dict[str, dict[str, Any]] = {}

        for model_id, config in self.config.get("models", {}).items():
            result[model_id] = {
                "name": config.get("name", model_id),
                "description": config.get("description", ""),
                "size_mb": config.get("size_mb", 0),
                "use_case": config.get("use_case", "general"),
                "available": self.is_available(model_id),
            }

        return result

    def list_profiles(self) -> dict[str, dict[str, Any]]:
        """List all configured profiles.

        Returns:
            Dict mapping profile name to info.
        """
        result: dict[str, dict[str, Any]] = {}

        for profile, config in self.config.get("profiles", {}).items():
            models = config.get("models", [])
            result[profile] = {
                "description": config.get("description", ""),
                "model_count": len(models),
                "models": models,
                "all_available": all(self.is_available(m) for m in models),
            }

        return result


# Singleton instance for convenience
_loader: VisionModelLoader | None = None


def get_loader() -> VisionModelLoader:
    """Get the global model loader instance."""
    global _loader
    if _loader is None:
        _loader = VisionModelLoader()
    return _loader
