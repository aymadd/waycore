from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

import pytest

from device.libs.schemas.base import BaseMessage


def test_base_message_defaults_and_types() -> None:
    msg = BaseMessage(source="core-daemon")
    assert isinstance(msg.msg_id, UUID)
    assert isinstance(msg.timestamp, datetime)
    assert msg.timestamp.tzinfo is not None
    assert msg.timestamp.tzinfo == timezone.utc
    assert msg.source == "core-daemon"
    assert msg.version == "1.0.0"


def test_base_message_invalid_version_rejected() -> None:
    with pytest.raises(ValueError):
        BaseMessage(source="core-daemon", version="v1")


def test_base_message_serialization_roundtrip() -> None:
    orig = BaseMessage(source="core-daemon", version="1.2.3")
    json_str = orig.model_dump_json()
    loaded = BaseMessage.model_validate_json(json_str)
    # msg_id and timestamp are preserved
    assert loaded.msg_id == orig.msg_id
    assert loaded.timestamp == orig.timestamp
    assert loaded.source == "core-daemon"
    assert loaded.version == "1.2.3"
