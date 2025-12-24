from __future__ import annotations

from dataclasses import dataclass

from device.libs.schemas.system import SystemMode


@dataclass(frozen=True)
class PowerPolicy:
    wifi_enabled: bool
    lte_enabled: bool
    lora_enabled: bool
    gps_update_rate_hz: float
    screen_brightness_pct: int


def compute_power_policy(mode: SystemMode, battery_percent: int) -> PowerPolicy:
    # Defaults for normal/active
    wifi = True
    lte = True
    lora = True
    gps_rate = 1.0
    brightness = 80

    if mode == SystemMode.low_power:
        wifi = False
        lte = False
        gps_rate = 0.2
        brightness = 40
    elif mode == SystemMode.sos:
        # SOS: keep LoRa only, minimal GPS
        wifi = False
        lte = False
        lora = True
        gps_rate = 0.1
        brightness = 30
    elif mode == SystemMode.charging:
        # Allow more aggressive rates when charging
        wifi = True
        lte = True
        gps_rate = 2.0
        brightness = 90

    return PowerPolicy(
        wifi_enabled=wifi,
        lte_enabled=lte,
        lora_enabled=lora,
        gps_update_rate_hz=gps_rate,
        screen_brightness_pct=brightness,
    )
