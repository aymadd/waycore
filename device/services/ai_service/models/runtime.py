"""Model runner registry and base classes."""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable

from device.libs.schemas.ai import InferenceResult, InferenceType

from ..preprocessing import ImagePreprocessed, QAPreprocessed

logger = logging.getLogger(__name__)

# Model directory from environment
MODEL_DIR = Path(os.getenv("WAYCORE_MODEL_PATH", "/opt/waycore/models"))


class ModelRunner(ABC):
    """
    Abstract base for model runners.
    Implementations should be lightweight and dependency-free where possible.
    """

    @abstractmethod
    def supports(self, inference_type: InferenceType) -> bool: ...

    @abstractmethod
    def infer_image(self, pre: ImagePreprocessed) -> list[InferenceResult]: ...

    @abstractmethod
    def infer_qa(self, pre: QAPreprocessed) -> list[InferenceResult]: ...


class MobileNetV3Stub(ModelRunner):
    """
    Stubbed MobileNetV3 runner that returns deterministic placeholder predictions.
    """

    def supports(self, inference_type: InferenceType) -> bool:
        return inference_type in (
            InferenceType.image_classification,
            InferenceType.object_detection,
        )

    def infer_image(self, pre: ImagePreprocessed) -> list[InferenceResult]:
        source = pre.get("source", "unknown")
        # Deterministic placeholder label
        return [
            InferenceResult(
                label=f"mobilenetv3:{source}:class0",
                confidence=0.0,
                metadata={"topk": [], "stub": True},
            )
        ]

    def infer_qa(self, pre: QAPreprocessed) -> list[InferenceResult]:
        raise NotImplementedError("MobileNetV3 does not support QA")


class Phi3MiniStub(ModelRunner):
    """
    Stubbed Phi3-mini LLM runner supporting QA.
    """

    def supports(self, inference_type: InferenceType) -> bool:
        return inference_type is InferenceType.qa

    def infer_image(self, pre: ImagePreprocessed) -> list[InferenceResult]:
        raise NotImplementedError("Phi3-mini does not support image tasks")

    def infer_qa(self, pre: QAPreprocessed) -> list[InferenceResult]:
        # Deterministic answer: echo first context segment
        answer = pre["context"][0] if pre["context"] else "N/A"
        return [
            InferenceResult(
                label=f"phi3-mini:{answer}",
                confidence=0.0,
                metadata={"stub": True},
            )
        ]


class _Registry:
    """Registry for model runners with lazy loading."""

    def __init__(self) -> None:
        self._factories: dict[str, Callable[[], ModelRunner]] = {}
        self._instances: dict[str, ModelRunner] = {}

    def register(self, model_id: str, factory: Callable[[], ModelRunner]) -> None:
        """Register a model factory."""
        self._factories[model_id] = factory

    def get(self, model_id: str) -> ModelRunner | None:
        """Get or create a model runner by ID."""
        if model_id in self._instances:
            return self._instances[model_id]
        factory = self._factories.get(model_id)
        if not factory:
            return None
        inst = factory()
        self._instances[model_id] = inst
        return inst

    def unload(self, model_id: str) -> None:
        """Unload a specific model."""
        runner = self._instances.pop(model_id, None)
        if runner and hasattr(runner, "unload"):
            runner.unload()

    def unload_all(self) -> None:
        """Unload all models."""
        for model_id in list(self._instances.keys()):
            self.unload(model_id)

    def list_models(self) -> list[str]:
        """List all registered model IDs."""
        return list(self._factories.keys())

    def list_loaded(self) -> list[str]:
        """List currently loaded model IDs."""
        return list(self._instances.keys())


registry = _Registry()


# --- Model Registration ---


def _create_phi3_runner() -> ModelRunner:
    """Create Phi-3 runner, using real model if available, else stub."""
    try:
        from .phi3_runner import Phi3Runner

        runner = Phi3Runner()
        # Check if model file exists
        model_path = MODEL_DIR / "language" / "phi-3-mini-4k-instruct.Q4_K_M.gguf"
        if model_path.exists():
            logger.info(f"Using real Phi-3 model at {model_path}")
            return runner
        logger.info("Phi-3 model not found, using stub")
    except ImportError as e:
        logger.info(f"llama-cpp-python not available: {e}, using stub")
    return Phi3MiniStub()


def _create_mobilenet_runner() -> ModelRunner:
    """Create MobileNetV3 runner, using real model if available, else stub."""
    try:
        from .mobilenet_runner import MobileNetV3Runner

        runner = MobileNetV3Runner()
        # Check if model file exists
        model_path = MODEL_DIR / "vision" / "mobilenet_v3_small.tflite"
        if model_path.exists():
            logger.info(f"Using real MobileNetV3 model at {model_path}")
            return runner
        logger.info("MobileNetV3 model not found, using stub")
    except ImportError as e:
        logger.info(f"TFLite runtime not available: {e}, using stub")
    return MobileNetV3Stub()


# Register models with smart factory functions
registry.register("phi3-mini", _create_phi3_runner)
registry.register("mobilenetv3", _create_mobilenet_runner)


# --- Vision-LLM Pipeline ---


class VisionToLLMPipeline(ModelRunner):
    """
    Two-stage pipeline: image -> MobileNetV3 -> Phi3 LLM
    Returns a textual description derived from the vision classification.
    """

    def supports(self, inference_type: InferenceType) -> bool:
        return inference_type in (
            InferenceType.image_classification,
            InferenceType.object_detection,
        )

    def infer_image(self, pre: ImagePreprocessed) -> list[InferenceResult]:
        # Stage 1: Vision classification
        vision_runner = registry.get("mobilenetv3")
        if not vision_runner:
            return [
                InferenceResult(
                    label="Vision model not available",
                    confidence=0.0,
                    metadata={"error": "no_vision_model"},
                )
            ]

        vision_results = vision_runner.infer_image(pre)
        if not vision_results:
            return [
                InferenceResult(
                    label="No classification results",
                    confidence=0.0,
                    metadata={"error": "no_results"},
                )
            ]

        # Format classification results for LLM
        classifications = []
        for r in vision_results[:5]:  # Top 5
            pct = f"{r.confidence * 100:.1f}%"
            classifications.append(f"{r.label} ({pct})")

        context = "Image classification results:\n" + "\n".join(
            f"{i+1}. {c}" for i, c in enumerate(classifications)
        )

        # Stage 2: LLM description
        llm_runner = registry.get("phi3-mini")
        if not llm_runner:
            # Return vision results if no LLM
            return vision_results

        qa_input: QAPreprocessed = {
            "type": "qa",
            "question": (
                "Based on these classifications, provide a brief description "
                "of what's in the image and any relevant safety information."
            ),
            "context": [context],
            "options": {},
        }
        return llm_runner.infer_qa(qa_input)

    def infer_qa(self, pre: QAPreprocessed) -> list[InferenceResult]:
        raise NotImplementedError("VisionToLLMPipeline expects image input")


registry.register("vision-llm", VisionToLLMPipeline)
