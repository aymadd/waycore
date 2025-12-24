from __future__ import annotations

import asyncio

import pytest
from device.drivers.mock.radio import MockLoRaRadio
from device.libs.hil.interfaces.radio import RadioType


@pytest.mark.asyncio
async def test_mock_lora_radio_send_and_receive() -> None:
    radio = MockLoRaRadio({"auto_generate_messages": True})
    acc: list = []
    radio.subscribe_messages(lambda msg: acc.append(msg))
    await radio.start()
    ok = await radio.send_message(b"hello", to_node=None, channel="primary", want_ack=False)
    assert isinstance(ok, bool)
    await asyncio.sleep(0.3)
    await radio.stop()
    assert len(acc) >= 1
    assert radio.radio_type is RadioType.lora
