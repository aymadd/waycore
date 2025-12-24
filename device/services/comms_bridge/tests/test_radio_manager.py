from __future__ import annotations

import asyncio

import pytest
from device.services.comms_bridge.radio_manager import RadioManager


@pytest.mark.asyncio
async def test_radio_manager_init_status_and_send() -> None:
    rm = RadioManager(
        {
            "radios": [
                {"name": "lora1", "driver": "mock_lora", "config": {"node_id": "!dev"}},
            ]
        }
    )
    msgs: list = []
    rm.set_message_callback(lambda m: msgs.append(m))
    await rm.initialize()
    status = await rm.get_status()
    assert "lora1" in status
    ok = await rm.send(b"hi", transport_hint=None, to_node=None, channel="primary", want_ack=False)
    assert isinstance(ok, bool)
    await asyncio.sleep(0.05)
    await rm.shutdown()
