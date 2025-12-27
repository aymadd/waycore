"""Real MobileNetV3 model runner using TensorFlow Lite."""

from __future__ import annotations

import base64
import io
import logging
import os
from pathlib import Path
from typing import Any

from device.libs.schemas.ai import InferenceResult, InferenceType

from ..preprocessing import ImagePreprocessed, QAPreprocessed
from .runtime import ModelRunner

logger = logging.getLogger(__name__)

# Default paths
MODEL_DIR = Path(os.getenv("WAYCORE_MODEL_PATH", "/opt/waycore/models"))
DEFAULT_MODEL_PATH = MODEL_DIR / "vision" / "mobilenet_v3_small.tflite"
DEFAULT_LABELS_PATH = MODEL_DIR / "labels" / "imagenet_labels.txt"

# ImageNet labels fallback (top 10 common outdoor labels)
FALLBACK_LABELS = [
    "background",
    "bird",
    "tree",
    "mountain",
    "rock",
    "flower",
    "animal",
    "water",
    "sky",
    "grass",
]


class MobileNetV3Runner(ModelRunner):
    """
    Real MobileNetV3 model runner using TensorFlow Lite.

    Supports image classification with lazy model loading.
    Uses MobileNetV3-Small for fast inference on Pi 5.
    """

    def __init__(
        self,
        model_path: str | Path | None = None,
        labels_path: str | Path | None = None,
    ) -> None:
        self._model_path = Path(model_path) if model_path else DEFAULT_MODEL_PATH
        self._labels_path = Path(labels_path) if labels_path else DEFAULT_LABELS_PATH
        self._interpreter: Any = None  # Lazy loaded
        self._labels: list[str] = []
        self._available: bool | None = None
        self._input_details: list[dict[str, Any]] = []
        self._output_details: list[dict[str, Any]] = []

    def _ensure_loaded(self) -> bool:
        """Ensure model is loaded. Returns True if available."""
        if self._available is not None:
            return self._available

        if not self._model_path.exists():
            logger.warning(f"MobileNetV3 model not found at {self._model_path}")
            self._available = False
            return False

        try:
            # Try tflite_runtime first (smaller package)
            try:
                import tflite_runtime.interpreter as tflite

                logger.info("Using tflite_runtime")
            except ImportError:
                # Fall back to full TensorFlow
                import tensorflow.lite as tflite

                logger.info("Using tensorflow.lite")

            logger.info(f"Loading MobileNetV3 model from {self._model_path}")
            self._interpreter = tflite.Interpreter(model_path=str(self._model_path))
            self._interpreter.allocate_tensors()

            self._input_details = self._interpreter.get_input_details()
            self._output_details = self._interpreter.get_output_details()

            # Load labels
            self._labels = self._load_labels()

            self._available = True
            logger.info(f"MobileNetV3 model loaded successfully ({len(self._labels)} labels)")
            return True
        except ImportError:
            logger.warning("TFLite runtime not installed, using stub")
            self._available = False
            return False
        except Exception as e:
            logger.error(f"Failed to load MobileNetV3 model: {e}")
            self._available = False
            return False

    def _load_labels(self) -> list[str]:
        """Load classification labels from file."""
        if self._labels_path.exists():
            with open(self._labels_path) as f:
                return [line.strip() for line in f.readlines()]
        logger.warning(f"Labels file not found at {self._labels_path}, using fallback")
        return FALLBACK_LABELS

    def supports(self, inference_type: InferenceType) -> bool:
        return inference_type in (
            InferenceType.image_classification,
            InferenceType.object_detection,
        )

    def infer_image(self, pre: ImagePreprocessed) -> list[InferenceResult]:
        """Run image classification with MobileNetV3."""
        if not self._ensure_loaded():
            return self._stub_response(pre)

        try:
            # Get image data from preprocessed input
            # ImagePreprocessed has: type, source ("bytes" or "b64"), data, options
            image_data: bytes | None = None
            source = pre.get("source", "")
            data = pre.get("data")

            if source == "bytes" and isinstance(data, bytes):
                image_data = data
            elif source == "b64" and isinstance(data, str) and data:
                image_data = base64.b64decode(data)

            if not image_data:
                return [
                    InferenceResult(
                        label="Error: No image data provided",
                        confidence=0.0,
                        metadata={"error": "no_image"},
                    )
                ]

            # Preprocess image
            input_tensor = self._preprocess_image(image_data)

            # Run inference
            self._interpreter.set_tensor(self._input_details[0]["index"], input_tensor)
            self._interpreter.invoke()

            # Get output logits
            output_data = self._interpreter.get_tensor(self._output_details[0]["index"])
            logits = output_data[0]

            # Apply softmax to convert logits to probabilities
            import numpy as np

            exp_logits = np.exp(logits - np.max(logits))  # Subtract max for numerical stability
            probabilities = exp_logits / np.sum(exp_logits)

            # Get top-5 predictions
            top_k = 5
            top_indices = probabilities.argsort()[-top_k:][::-1]

            results = []
            for idx in top_indices:
                label = self._labels[idx] if idx < len(self._labels) else f"class_{idx}"
                confidence = float(probabilities[idx])
                if confidence > 0.01:  # Filter very low confidence
                    results.append(
                        InferenceResult(
                            label=label,
                            confidence=confidence,
                            metadata={"class_index": int(idx)},
                        )
                    )

            return (
                results
                if results
                else [
                    InferenceResult(
                        label="Unknown",
                        confidence=0.0,
                        metadata={"note": "No confident predictions"},
                    )
                ]
            )

        except Exception as e:
            logger.error(f"MobileNetV3 inference error: {e}")
            return [
                InferenceResult(
                    label=f"Error: {e}",
                    confidence=0.0,
                    metadata={"error": str(e)},
                )
            ]

    def _preprocess_image(self, image_data: bytes) -> Any:
        """Preprocess image for MobileNetV3 input."""
        try:
            import numpy as np
            from PIL import Image

            # Load image from bytes
            loaded_img = Image.open(io.BytesIO(image_data))

            # Convert to RGB if needed
            rgb_img = loaded_img.convert("RGB") if loaded_img.mode != "RGB" else loaded_img

            # Get expected input size from model
            input_shape = self._input_details[0]["shape"]
            height, width = input_shape[1], input_shape[2]

            # Resize image
            resized_img = rgb_img.resize((width, height), Image.Resampling.BILINEAR)

            # Convert to numpy array and normalize
            img_array = np.array(resized_img, dtype=np.float32)

            # Normalize to [-1, 1] range (MobileNetV3 preprocessing)
            img_array = (img_array / 127.5) - 1.0

            # Add batch dimension
            img_array = np.expand_dims(img_array, axis=0)

            return img_array

        except ImportError as e:
            raise RuntimeError(f"PIL/numpy not available: {e}") from e

    def _stub_response(self, pre: ImagePreprocessed) -> list[InferenceResult]:
        """Fallback stub response when model not available."""
        source = pre.get("source", "unknown")
        return [
            InferenceResult(
                label=f"[Model not loaded] image:{source}",
                confidence=0.0,
                metadata={"stub": True, "source": source},
            )
        ]

    def infer_qa(self, pre: QAPreprocessed) -> list[InferenceResult]:
        raise NotImplementedError("MobileNetV3 does not support Q&A tasks")

    def unload(self) -> None:
        """Unload the model to free memory."""
        if self._interpreter is not None:
            del self._interpreter
            self._interpreter = None
            self._available = None
            self._labels = []
            logger.info("MobileNetV3 model unloaded")

    @property
    def is_loaded(self) -> bool:
        """Check if model is currently loaded."""
        return self._interpreter is not None
