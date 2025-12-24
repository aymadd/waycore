from __future__ import annotations

from device.libs.schemas.sensor import FixQuality, GPSPosition
from device.services.comms_bridge.tak_gateway import TAKGateway


def test_tak_gateway_build_and_send() -> None:
    gps = GPSPosition(
        source="core",
        latitude=30.0,
        longitude=-97.7,
        satellites=7,
        fix_quality=FixQuality.gps,
    )
    gw = TAKGateway(enabled=True)
    cot = gw.build_cot(gps, call_sign="alpha")
    ok = gw.send(cot)
    assert ok is True
    assert gw.last_xml() is not None
