from __future__ import annotations

import base64
from typing import Any

import pytest

from ....libs.schemas.ai import AIInferenceRequest, InferenceType
from ..preprocessing import (
    PreprocessingError,
    preprocess_for_inference,
)


def _mk_req(inference_type: InferenceType, input_data: dict[str, Any]) -> AIInferenceRequest:
    return AIInferenceRequest(
        source="test-suite",
        inference_type=inference_type,
        model_id="test-model",
        input_data=input_data,
        options={},
    )


def test_image_preprocess_with_b64_ok() -> None:
    raw = b"\x89PNG\r\n"  # just some bytes
    b64 = base64.b64encode(raw).decode("ascii")
    req = _mk_req(
        InferenceType.image_classification,
        {"image_b64": b64, "options": {"resize": [224, 224]}},
    )
    out = preprocess_for_inference(req)
    assert out["type"] == "image"
    assert out["source"] == "b64"
    assert out["data"] == b64
    assert out["options"]["resize"] == [224, 224]


def test_image_preprocess_with_bytes_ok() -> None:
    raw = b"\xff\xd8\xff"  # some bytes
    req = _mk_req(
        InferenceType.object_detection, {"image_bytes": raw, "options": {"normalize": True}}
    )
    out = preprocess_for_inference(req)
    assert out["type"] == "image"
    assert out["source"] == "bytes"
    assert out["data"] == raw
    assert out["options"]["normalize"] is True


def test_image_preprocess_missing_raises() -> None:
    req = _mk_req(InferenceType.image_classification, {})
    with pytest.raises(PreprocessingError):
        preprocess_for_inference(req)


def test_qa_preprocess_ok_with_string_context() -> None:
    req = _mk_req(
        InferenceType.qa, {"question": "What is Waycore?", "context": "Waycore is a system."}
    )
    out = preprocess_for_inference(req)
    assert out["type"] == "qa"
    assert out["question"] == "What is Waycore?"
    assert out["context"] == ["Waycore is a system."]


def test_qa_preprocess_ok_with_list_context() -> None:
    req = _mk_req(
        InferenceType.qa,
        {
            "question": "What is Waycore?",
            "context": ["Waycore is a system.", "It runs on devices."],
        },
    )
    out = preprocess_for_inference(req)
    assert out["type"] == "qa"
    assert len(out["context"]) == 2


def test_qa_preprocess_missing_question_raises() -> None:
    req = _mk_req(InferenceType.qa, {"context": "hello"})
    with pytest.raises(PreprocessingError):
        preprocess_for_inference(req)
