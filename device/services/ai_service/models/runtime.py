from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

from device.libs.schemas.ai import InferenceResult, InferenceType

from ..preprocessing import ImagePreprocessed, QAPreprocessed


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
                label=f"mobilenetv3:{source}:class0", confidence=0.0, metadata={"topk": []}
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
        return [InferenceResult(label=f"phi3-mini:{answer}", confidence=0.0, metadata={})]


class _Registry:
    def __init__(self) -> None:
        self._factories: dict[str, Callable[[], ModelRunner]] = {}
        self._instances: dict[str, ModelRunner] = {}

    def register(self, model_id: str, factory: Callable[[], ModelRunner]) -> None:
        self._factories[model_id] = factory

    def get(self, model_id: str) -> ModelRunner | None:
        if model_id in self._instances:
            return self._instances[model_id]
        factory = self._factories.get(model_id)
        if not factory:
            return None
        inst = factory()
        self._instances[model_id] = inst
        return inst

    def unload(self, model_id: str) -> None:
        self._instances.pop(model_id, None)

    def unload_all(self) -> None:
        self._instances.clear()


registry = _Registry()

# Default registrations
registry.register("mobilenetv3", MobileNetV3Stub)
registry.register("phi3-mini", Phi3MiniStub)


class VisionToLLMStub(ModelRunner):
    """
    Two-stage pipeline: image -> MobileNetV3Stub -> Phi3MiniStub
    Returns a textual description derived from the vision label.
    """

    def supports(self, inference_type: InferenceType) -> bool:
        return inference_type in (
            InferenceType.image_classification,
            InferenceType.object_detection,
        )

    def infer_image(self, pre: ImagePreprocessed) -> list[InferenceResult]:
        # Stage 1: vision
        vision = MobileNetV3Stub().infer_image(pre)
        label = vision[0].label if vision else "unknown"
        # Stage 2: LLM over derived prompt/context
        qa_input: QAPreprocessed = {
            "type": "qa",
            "question": "Describe image",
            "context": [label],
            "options": {},
        }
        return Phi3MiniStub().infer_qa(qa_input)

    def infer_qa(self, pre: QAPreprocessed) -> list[InferenceResult]:
        raise NotImplementedError("VisionToLLMStub expects image input")


registry.register("vision-llm", VisionToLLMStub)
