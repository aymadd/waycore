from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Callable
from urllib.parse import urlparse

from paho.mqtt.client import Client, MQTTMessage

from .bus import MessageBus, MessageHandler


@dataclass
class _Subscription:
    topic: str
    qos: int
    handler: MessageHandler


class MQTTBus(MessageBus):
    def __init__(self) -> None:
        self._client: Client | None = None
        self._connected: bool = False
        self._subs: dict[int, _Subscription] = {}
        self._lock = threading.Lock()

    async def connect(self, broker_url: str) -> None:
        parsed = urlparse(broker_url)
        host = parsed.hostname or "localhost"
        port = parsed.port or 1883

        client = Client()
        client.on_connect = self._on_connect
        client.on_disconnect = self._on_disconnect
        client.on_message = self._on_message

        # Keep references
        self._client = client

        # Start network loop in background thread
        client.loop_start()
        rc = client.connect(host, port, keepalive=60)
        if rc != 0:
            # paho returns 0 on successful start; actual connection result comes in on_connect
            # Non-zero here means immediate failure to initiate connection
            raise ConnectionError(f"Failed to initiate MQTT connect (rc={rc})")

    async def disconnect(self) -> None:
        if self._client is None:
            return
        self._client.disconnect()
        self._client.loop_stop()
        self._client = None
        self._connected = False
        self._subs.clear()

    async def publish(
        self, topic: str, payload: bytes | str, qos: int = 0, retain: bool = False
    ) -> None:
        if self._client is None or not self._connected:
            raise ConnectionError("MQTT not connected")
        self._client.publish(topic, payload=payload, qos=qos, retain=retain)
        # Optionally wait for publish to complete: info.wait_for_publish()

    def subscribe(self, topic: str, handler: MessageHandler, qos: int = 0) -> Callable[[], None]:
        if self._client is None:
            raise RuntimeError("MQTT client not initialized. Call connect() first.")
        result, mid = self._client.subscribe(topic, qos=qos)
        if result != 0:
            raise RuntimeError(f"Subscribe failed (rc={result})")
        with self._lock:
            self._subs[mid] = _Subscription(topic=topic, qos=qos, handler=handler)

        def _unsubscribe() -> None:
            if self._client is None:
                return
            self._client.unsubscribe(topic)
            with self._lock:
                # remove all entries matching topic
                for k in list(self._subs.keys()):
                    if self._subs[k].topic == topic:
                        del self._subs[k]

        return _unsubscribe

    # Callbacks (run in paho's background thread)
    def _on_connect(self, client: Client, userdata, flags, rc) -> None:  # type: ignore[no-untyped-def]
        self._connected = rc == 0

    def _on_disconnect(self, client: Client, userdata, rc) -> None:  # type: ignore[no-untyped-def]
        self._connected = False

    def _on_message(self, client: Client, userdata, message: MQTTMessage) -> None:  # type: ignore[no-untyped-def]
        payload: bytes = message.payload or b""
        topic: str = message.topic
        # Deliver to all handlers matching this topic filter.
        # Since we only store exact topics here, invoke all with same topic.
        with self._lock:
            for sub in self._subs.values():
                if sub.topic == topic:
                    try:
                        sub.handler(topic, payload)
                    except Exception:
                        # Swallow handler exceptions to avoid breaking network loop
                        pass
