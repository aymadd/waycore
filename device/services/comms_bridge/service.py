from __future__ import annotations

import asyncio
from typing import Any

from device.libs.common.base_service import BaseService
from device.libs.messaging.bus import MessageBus
from device.libs.schemas.comms import (
    CommsStatusChanged,
    MessageReceived,
    SendMessageRequest,
    Transport,
)
from device.libs.schemas.sensor import GPSPosition

from .radio_manager import RadioManager
from .tak_gateway import TAKGateway


class CommsBridgeService(BaseService):
    def __init__(self, config: dict[str, Any], bus: MessageBus | None = None) -> None:
        super().__init__(config, bus)
        self._manager = RadioManager(
            config.get(
                "radios_config",
                {"radios": [{"name": "lora1", "driver": "mock_lora", "config": {}}]},
            )
        )
        self._manager.set_message_callback(self._on_radio_message)
        self._tak = TAKGateway(enabled=bool(config.get("tak", {}).get("enabled", False)))
        self._healthy = False
        self._status_interval = float(config.get("status_interval_seconds", 1.0))

    async def _setup(self) -> None:
        await self._manager.initialize()
        self._healthy = True
        # subscribe to outgoing messages request
        if self.bus:
            self.bus.subscribe("comms/message/send", self._on_send_request)
            # GPS position to TAK
            self.bus.subscribe("sensor/gps/position", self._on_gps_position)

    async def _run(self) -> None:
        while not self.should_stop():
            # publish status periodically
            if self.bus:
                status = await self._manager.get_status()
                for name, st in status.items():
                    await self.bus.publish(
                        "comms/status/changed",
                        CommsStatusChanged(
                            source="comms-bridge",
                            transport=Transport.lora,  # mock transport
                            enabled=st.enabled,
                            connected=st.connected,
                            signal_strength=st.signal_strength,
                            error=st.error,
                            metadata={"name": name, "channel": st.channel},
                        ).model_dump_json(),
                    )
            await asyncio.sleep(self._status_interval)

    async def _cleanup(self) -> None:
        self._healthy = False
        await self._manager.shutdown()

    def is_healthy(self) -> bool:
        return self._healthy

    def _on_radio_message(self, msg) -> None:  # type: ignore[no-untyped-def]
        if not self.bus:
            return
        m = MessageReceived(
            source="comms-bridge",
            transport=Transport.lora,
            from_node=msg.from_node,
            to_node=msg.to_node,
            content=msg.content.decode("utf-8", errors="ignore"),
            channel="primary",
            rssi=msg.rssi,
            snr=msg.snr,
            hop_limit=3,
        )
        asyncio.create_task(self.bus.publish("comms/message/received", m.model_dump_json()))

    def _on_send_request(self, topic: str, payload: bytes) -> None:
        try:
            req = SendMessageRequest.model_validate_json(payload.decode("utf-8"))
        except Exception:
            return
        asyncio.create_task(
            self._manager.send(
                content=req.content.encode("utf-8"),
                transport_hint=req.transport.value,
                to_node=req.to_node,
                channel=req.channel,
                want_ack=req.want_ack,
            )
        )

    def _on_gps_position(self, topic: str, payload: bytes) -> None:
        try:
            pos = GPSPosition.model_validate_json(payload.decode("utf-8"))
        except Exception:
            return
        cot = self._tak.build_cot(pos)
        self._tak.send(cot)
