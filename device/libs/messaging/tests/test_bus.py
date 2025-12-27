from __future__ import annotations

import inspect

import pytest

from device.libs.messaging.bus import MessageBus


def test_message_bus_is_abstract() -> None:
    with pytest.raises(TypeError):
        MessageBus()  # type: ignore[abstract]

    # Ensure required methods exist
    assert hasattr(MessageBus, "connect")
    assert hasattr(MessageBus, "disconnect")
    assert hasattr(MessageBus, "publish")
    assert hasattr(MessageBus, "subscribe")
    assert inspect.iscoroutinefunction(MessageBus.connect)  # type: ignore[arg-type]
    assert inspect.iscoroutinefunction(MessageBus.disconnect)  # type: ignore[arg-type]
    assert inspect.iscoroutinefunction(MessageBus.publish)  # type: ignore[arg-type]
