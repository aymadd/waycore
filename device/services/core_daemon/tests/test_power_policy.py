from __future__ import annotations

from device.libs.schemas.system import SystemMode
from device.services.core_daemon.power_policy import compute_power_policy


def test_low_power_policy_disables_wifi_lte() -> None:
    p = compute_power_policy(SystemMode.low_power, 10)
    assert p.wifi_enabled is False
    assert p.lte_enabled is False
    assert p.lora_enabled is True
    assert p.gps_update_rate_hz <= 0.2


def test_sos_policy_keeps_lora_only() -> None:
    p = compute_power_policy(SystemMode.sos, 3)
    assert p.lora_enabled is True
    assert p.wifi_enabled is False
    assert p.lte_enabled is False
