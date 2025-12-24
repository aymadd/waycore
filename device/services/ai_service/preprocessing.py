from __future__ import annotations

from typing import Any, Literal, TypedDict, Union

from ...libs.schemas.ai import AIInferenceRequest, InferenceType


class PreprocessingError(ValueError):
    """
    Raised when an inference request's input_data cannot be validated
    or normalized into a model-ready structure.
    """


class ImagePreprocessed(TypedDict):
    type: Literal["image"]
    source: Literal["bytes", "b64"]
    data: bytes | str
    options: dict[str, Any]


class QAPreprocessed(TypedDict):
    type: Literal["qa"]
    question: str
    context: list[str]
    options: dict[str, Any]


PreprocessedInput = Union[ImagePreprocessed, QAPreprocessed]


def preprocess_for_inference(request: AIInferenceRequest) -> PreprocessedInput:
    """
    Validate and normalize AI input_data into a model-ready payload without
    bringing heavy external dependencies. This function performs strict
    structural checks and returns a typed, normalized representation
    that downstream inference code can consume.
    """
    if request.inference_type == InferenceType.image_classification:
        return _preprocess_image_like(request.input_data)
    if request.inference_type == InferenceType.object_detection:
        return _preprocess_image_like(request.input_data)
    if request.inference_type == InferenceType.qa:
        return _preprocess_qa(request.input_data)

    msg = f"Unsupported inference_type: {request.inference_type}"
    raise PreprocessingError(msg)


def _preprocess_image_like(input_data: dict[str, Any]) -> ImagePreprocessed:
    """
    Accepts either:
      - image_bytes: bytes
      - image_b64: str (base64-encoded)
    Returns a normalized dict indicating which source is provided.
    """
    if not isinstance(input_data, dict):
        raise PreprocessingError("input_data must be a dictionary for image tasks")

    image_bytes = input_data.get("image_bytes")
    image_b64 = input_data.get("image_b64")
    options = input_data.get("options") or {}

    if image_bytes is None and image_b64 is None:
        raise PreprocessingError("Provide either 'image_bytes' or 'image_b64'")

    if image_bytes is not None:
        if not isinstance(image_bytes, (bytes, bytearray)):
            raise PreprocessingError("'image_bytes' must be bytes or bytearray")
        data: bytes | str = bytes(image_bytes)
        source: Literal["bytes", "b64"] = "bytes"
    else:
        if not isinstance(image_b64, str) or len(image_b64.strip()) == 0:
            raise PreprocessingError("'image_b64' must be a non-empty string")
        data = image_b64
        source = "b64"

    if not isinstance(options, dict):
        raise PreprocessingError("'options' must be a dictionary if provided")

    return ImagePreprocessed(type="image", source=source, data=data, options=options)


def _preprocess_qa(input_data: dict[str, Any]) -> QAPreprocessed:
    """
    Normalize QA inputs:
      - question: str (required, non-empty)
      - context: str | list[str] (required, non-empty after normalization)
    """
    if not isinstance(input_data, dict):
        raise PreprocessingError("input_data must be a dictionary for QA tasks")

    question = input_data.get("question")
    context = input_data.get("context")
    options = input_data.get("options") or {}

    if not isinstance(question, str) or len(question.strip()) == 0:
        raise PreprocessingError("'question' must be a non-empty string")

    normalized_context: list[str]
    if isinstance(context, str):
        if len(context.strip()) == 0:
            raise PreprocessingError("'context' must not be an empty string")
        normalized_context = [context]
    elif isinstance(context, list):
        if not all(isinstance(c, str) and len(c.strip()) > 0 for c in context):
            raise PreprocessingError("'context' list must contain non-empty strings")
        normalized_context = context
    else:
        raise PreprocessingError("'context' must be a string or a list of strings")

    if len(normalized_context) == 0:
        raise PreprocessingError("'context' must not be empty")

    if not isinstance(options, dict):
        raise PreprocessingError("'options' must be a dictionary if provided")

    return QAPreprocessed(
        type="qa",
        question=question.strip(),
        context=normalized_context,
        options=options,
    )
