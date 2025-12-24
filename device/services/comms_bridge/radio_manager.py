from __future__ import annotations

from typing import Any, Callable

import device.drivers.mock as mockpkg  # noqa: F401 - ensure mock radios register
from device.libs.hil.factory import DriverFactory
from device.libs.hil.interfaces.radio import IRadio, RadioStatus, ReceivedMessage


class RadioManager:
    def __init__(self, config: dict[str, Any]) -> None:
        """
        config example:
        {
                "radios": [
                        {"name": "lora1", "driver": "mock_lora", "config": {"node_id": "!dev_node"}}
                ]
        }
        """
        self._radios: dict[str, IRadio] = {}
        self._message_callback: Callable[[ReceivedMessage], None] | None = None
        self._config = config

    def set_message_callback(self, cb: Callable[[ReceivedMessage], None]) -> None:
        self._message_callback = cb

    async def initialize(self) -> None:
        for r in self._config.get("radios", []):
            name = str(r.get("name"))
            driver = str(r.get("driver"))
            rcfg = dict(r.get("config", {}))
            radio = DriverFactory.create_radio(driver, rcfg)
            radio.subscribe_messages(self._on_radio_message)
            self._radios[name] = radio
            await radio.start()

    async def shutdown(self) -> None:
        for radio in self._radios.values():
            await radio.stop()
        self._radios.clear()

    def list_radio_names(self) -> list[str]:
        return list(self._radios.keys())

    async def get_status(self) -> dict[str, RadioStatus]:
        result: dict[str, RadioStatus] = {}
        for name, radio in self._radios.items():
            result[name] = await radio.get_status()
        return result

    async def send(
        self,
        content: bytes,
        transport_hint: str | None = None,
        to_node: str | None = None,
        channel: str | None = None,
        want_ack: bool = False,
    ) -> bool:
        # simple routing: pick first radio if no hint
        if transport_hint is None:
            targets = list(self._radios.values())
        else:
            targets = []
            for name, radio in self._radios.items():
                t = getattr(radio, "radio_type", None)
                t_value = getattr(t, "value", None) if t is not None else None
                if transport_hint == name or transport_hint == t_value:
                    targets.append(radio)
        ok_any = False
        for r in targets:
            ok = await r.send_message(content, to_node, channel, want_ack)
            ok_any = ok_any or ok
        return ok_any

    def _on_radio_message(self, msg: ReceivedMessage) -> None:
        if self._message_callback:
            try:
                self._message_callback(msg)
            except Exception:
                pass
