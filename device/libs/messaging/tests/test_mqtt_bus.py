from __future__ import annotations

from typing import Any

import pytest

from device.libs.messaging.mqtt_bus import MQTTBus


class _FakeClient:
    def __init__(self) -> None:
        self.on_connect = None
        self.on_disconnect = None
        self.on_message = None
        self._connected = False
        self._subs: list[tuple[str, int]] = []

    def loop_start(self) -> None: ...

    def loop_stop(self) -> None: ...

    def connect(self, host: str, port: int, keepalive: int) -> int:
        # Simulate async connect success by immediately invoking on_connect
        self._connected = True
        if self.on_connect:
            self.on_connect(self, None, None, 0)  # type: ignore[misc,call-arg]
        return 0

    def disconnect(self) -> None:
        self._connected = False
        if self.on_disconnect:
            self.on_disconnect(self, None, 0)  # type: ignore[misc,call-arg]

    def publish(self, topic: str, payload: Any, qos: int, retain: bool):
        class _Info:
            def wait_for_publish(self_inner) -> None: ...

        return _Info()

    def subscribe(self, topic: str, qos: int):
        self._subs.append((topic, qos))
        return 0, len(self._subs)  # rc, mid

    def unsubscribe(self, topic: str):
        self._subs = [(t, q) for (t, q) in self._subs if t != topic]


def test_mqtt_bus_connect_publish_subscribe(monkeypatch: pytest.MonkeyPatch) -> None:
    import device.libs.messaging.mqtt_bus as mqtt_bus_mod

    monkeypatch.setattr(mqtt_bus_mod, "Client", _FakeClient)  # type: ignore[arg-type]

    bus = MQTTBus()
    # Should connect without raising
    import asyncio

    asyncio.run(bus.connect("mqtt://localhost:1883"))

    # Subscribe and simulate a message
    got: dict[str, bytes] = {}

    def handler(topic: str, payload: bytes) -> None:
        got[topic] = payload

    unsub = bus.subscribe("test/topic", handler, qos=0)

    # Trigger on_message manually via fake client
    assert isinstance(bus._client, _FakeClient)  # type: ignore[attr-defined]
    fake = bus._client  # type: ignore[assignment]
    if fake.on_message:

        class _Msg:
            topic = "test/topic"
            payload = b"hello"

        fake.on_message(fake, None, _Msg())  # type: ignore[misc]

    assert got.get("test/topic") == b"hello"

    # Publish should not raise
    asyncio.run(bus.publish("test/topic", b"hi"))

    # Unsubscribe
    unsub()
    asyncio.run(bus.disconnect())
