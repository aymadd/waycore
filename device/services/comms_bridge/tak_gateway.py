from __future__ import annotations

from dataclasses import dataclass

from device.libs.schemas.sensor import GPSPosition


@dataclass
class CoTMessage:
    call_sign: str
    lat: float
    lon: float
    alt: float | None

    def to_xml(self) -> str:
        # Minimal CoT-like XML stub
        alt_str = "" if self.alt is None else f' alt="{self.alt:.1f}"'
        xml = (
            '<event type="a-f-G-U-C" how="m-g" >'
            f'<point lat="{self.lat:.6f}" lon="{self.lon:.6f}"{alt_str}/>'
            "</event>"
        )
        return xml


class TAKGateway:
    def __init__(self, enabled: bool = False) -> None:
        self.enabled = enabled
        self._last_xml: str | None = None

    def build_cot(self, gps: GPSPosition, call_sign: str = "waycore") -> CoTMessage:
        return CoTMessage(
            call_sign=call_sign, lat=gps.latitude, lon=gps.longitude, alt=gps.altitude_meters
        )

    def send(self, cot: CoTMessage) -> bool:
        if not self.enabled:
            return False
        self._last_xml = cot.to_xml()
        # In a real gateway, send over network; here we just store
        return True

    def last_xml(self) -> str | None:
        return self._last_xml
