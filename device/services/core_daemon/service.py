from __future__ import annotations

import asyncio
from typing import Any

from device.libs.common.base_service import BaseService
from device.libs.messaging.bus import MessageBus
from device.libs.schemas.system import (
    CommandType,
    SystemCommand,
    SystemStateChanged,
)

from .power_policy import compute_power_policy
from .state_machine import StateMachine


class CoreDaemonService(BaseService):
    def __init__(self, config: dict[str, Any], bus: MessageBus | None = None) -> None:
        super().__init__(config, bus)
        self._sm = StateMachine()
        self._healthy = False
        self._publish_interval = float(config.get("publish_interval_seconds", 1.0))
        self._low_power_threshold = int(config.get("low_battery_threshold_percent", 15))
        self._critical_threshold = int(config.get("critical_battery_threshold_percent", 5))

    async def _setup(self) -> None:
        self._sm.boot()
        self._healthy = True
        # Subscribe to system commands
        if self.bus:
            self.bus.subscribe("system/command/execute", self._on_command)

    async def _run(self) -> None:
        # Periodically publish state
        while not self.should_stop():
            self._sm.apply_battery_policy(self._low_power_threshold, self._critical_threshold)
            await self._publish_state()
            await asyncio.sleep(self._publish_interval)

    async def _cleanup(self) -> None:
        self._healthy = False

    def is_healthy(self) -> bool:
        return self._healthy

    def get_status(self) -> dict[str, Any]:
        s = self._sm.state
        policy = compute_power_policy(s.mode, s.battery_percent)
        return {
            "mode": s.mode.value,
            "battery_percent": s.battery_percent,
            "battery_voltage": s.battery_voltage,
            "charging": s.charging,
            "radios_enabled": s.radios_enabled,
            "gps_locked": s.gps_locked,
            "modules_connected": s.modules_connected,
            "uptime_seconds": s.uptime_seconds,
            "policy": {
                "wifi_enabled": policy.wifi_enabled,
                "lte_enabled": policy.lte_enabled,
                "lora_enabled": policy.lora_enabled,
                "gps_update_rate_hz": policy.gps_update_rate_hz,
                "screen_brightness_pct": policy.screen_brightness_pct,
            },
        }

    async def handle_command(
        self, command: CommandType, parameters: dict[str, Any] | None = None
    ) -> bool:
        return self._sm.handle_command(command)

    def _on_command(self, topic: str, payload: bytes) -> None:
        try:
            cmd = SystemCommand.model_validate_json(payload.decode("utf-8"))
            # Fire and forget; not awaited (subscriber context)
            asyncio.create_task(self.handle_command(cmd.command, cmd.parameters))
        except Exception:
            # Ignore malformed messages
            pass

    async def _publish_state(self) -> None:
        if not self.bus:
            return
        s = self._sm.state
        msg = SystemStateChanged(
            source="core-daemon",
            mode=s.mode,
            battery_percent=s.battery_percent,
            battery_voltage=s.battery_voltage,
            charging=s.charging,
            radios_enabled=s.radios_enabled,
            gps_locked=s.gps_locked,
            modules_connected=s.modules_connected,
            uptime_seconds=s.uptime_seconds,
            metadata={},
        )
        await self.bus.publish("system/state/changed", msg.model_dump_json())
