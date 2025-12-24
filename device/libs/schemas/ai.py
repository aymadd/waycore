from __future__ import annotations

from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, ValidationInfo, field_validator

from .base import BaseMessage


class InferenceType(str, Enum):
    image_classification = "image_classification"
    object_detection = "object_detection"
    qa = "qa"


class InferenceResult(BaseModel):
    label: str = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AIInferenceRequest(BaseMessage):
    """
    Request AI inference.
    Topic: ai/inference/request
    """

    inference_type: InferenceType = Field(..., description="Type of inference")
    model_id: str = Field(..., min_length=1, description="Which model to use")
    input_data: dict[str, Any] = Field(..., description="Input-specific data")
    options: dict[str, Any] = Field(default_factory=dict, description="Inference options")


class AIInferenceResponse(BaseMessage):
    """
    AI inference result.
    Topic: ai/inference/response
    """

    request_id: UUID = Field(..., description="Matches request msg_id")
    inference_type: InferenceType = Field(..., description="Type of inference")
    model_id: str = Field(..., min_length=1)
    results: list[InferenceResult] = Field(default_factory=list)
    processing_time_ms: int = Field(..., ge=0)
    success: bool = Field(..., description="Whether inference succeeded")
    error_message: str | None = Field(default=None, description="Error if any")

    @field_validator("error_message")
    @classmethod
    def _error_message_present_when_failed(
        cls, value: str | None, info: ValidationInfo
    ) -> str | None:
        success: bool = info.data.get("success", True)
        if not success and (value is None or value.strip() == ""):
            msg = "error_message must be provided when success is False"
            raise ValueError(msg)
        return value
