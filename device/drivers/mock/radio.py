from __future__ import annotations

import asyncio
import contextlib
import random
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from device.libs.hil.interfaces.radio import IRadio, RadioStatus, RadioType, ReceivedMessage


class MockLoRaRadio(IRadio):
    def __init__(self, config: dict[str, Any]) -> None:
        self._enabled = True
        self._connected = False
        self._node_id: str = str(config.get("node_id", "!dev_node"))
        self._success_rate: float = float(config.get("success_rate", 0.98))
        self._latency_ms: int = int(config.get("latency_ms", 30))
        self._auto_generate: bool = bool(config.get("auto_generate_messages", False))
        self._channel: str | None = "primary"
        self._callbacks: list[Callable[[ReceivedMessage], None]] = []
        self._task: asyncio.Task[None] | None = None
        random.seed(1)

    async def start(self) -> None:
        self._connected = True
        if self._auto_generate and self._task is None:
            self._task = asyncio.create_task(self._generator_loop())

    async def stop(self) -> None:
        self._connected = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def send_message(
        self, content: bytes, to_node: str | None, channel: str | None, want_ack: bool
    ) -> bool:
        await asyncio.sleep(self._latency_ms / 1000.0)
        return random.random() < self._success_rate

    def subscribe_messages(self, callback: Callable[[ReceivedMessage], None]) -> None:
        self._callbacks.append(callback)

    async def get_status(self) -> RadioStatus:
        return RadioStatus(
            enabled=self._enabled,
            connected=self._connected,
            signal_strength=-60 if self._connected else None,
            tx_power_dbm=14,
            channel=self._channel,
            error=None,
        )

    async def set_power(self, enabled: bool) -> None:
        self._enabled = enabled
        if not enabled:
            self._connected = False

    @property
    def radio_type(self) -> RadioType:
        return RadioType.lora

    async def _generator_loop(self) -> None:
        while self._connected:
            await asyncio.sleep(0.2)
            msg = ReceivedMessage(
                timestamp=datetime.now(timezone.utc),
                from_node="node-sim",
                to_node=self._node_id,
                content=b"simulated",
                rssi=-70,
                snr=7.0,
            )
            for cb in list(self._callbacks):
                try:
                    cb(msg)
                except Exception:
                    pass


def register(_: object) -> None:
    from device.libs.hil.factory import DriverFactory

    DriverFactory.register_radio("mock_lora", lambda cfg: MockLoRaRadio(dict(cfg)))
