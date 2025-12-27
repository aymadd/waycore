from __future__ import annotations

import pytest
from pydantic import ValidationError

from device.libs.schemas.comms import (
    CommsStatusChanged,
    MessageReceived,
    Priority,
    SendMessageRequest,
    Transport,
)


def test_message_received_valid_lora() -> None:
    msg = MessageReceived(
        source="comms-bridge",
        transport=Transport.lora,
        from_node="nodeA",
        to_node=None,
        content="hello",
        channel="primary",
        rssi=-70,
        snr=7.5,
        hop_limit=3,
    )
    assert msg.transport is Transport.lora
    assert msg.content == "hello"


def test_message_received_lora_length_enforced() -> None:
    long_content = "x" * 238
    with pytest.raises(ValidationError):
        MessageReceived(
            source="comms-bridge",
            transport=Transport.lora,
            from_node="nodeA",
            content=long_content,
        )


def test_send_message_request_defaults() -> None:
    req = SendMessageRequest(
        source="ui",
        transport=Transport.wifi,
        to_node="nodeB",
        content="hi",
    )
    assert req.priority is Priority.normal
    assert req.channel == "primary"
    assert req.want_ack is False


def test_comms_status_changed_valid() -> None:
    status = CommsStatusChanged(
        source="comms-bridge",
        transport=Transport.bluetooth,
        enabled=True,
        connected=False,
        signal_strength=None,
        metadata={"adapter": "hci0"},
    )
    assert status.enabled is True
    assert status.connected is False
    assert status.metadata["adapter"] == "hci0"
