from __future__ import annotations

import asyncio
from typing import Any

import device.drivers.mock as mockpkg  # noqa: F401 - trigger registrations
from device.libs.common.base_service import BaseService
from device.libs.hil.factory import DriverFactory
from device.libs.hil.interfaces.module_port import IModulePort
from device.libs.schemas.module import ModuleDiscovered as DiscoveredSchema
from device.libs.schemas.module import (
    ModuleStatus,
)
from device.services.module_manager.discovery import DiscoveryManager


class ModuleManagerService(BaseService):
    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        self._port: IModulePort | None = None
        self._discovery: DiscoveryManager | None = None
        self._healthy = False
        self._publish_interval = float(config.get("publish_interval_seconds", 1.0))

    async def _setup(self) -> None:
        driver_name = str(self.config.get("driver_name", "mock"))
        driver_cfg = dict(self.config.get("driver_config", {}))
        self._port = DriverFactory.create_module_port(driver_name, driver_cfg)
        self._discovery = DiscoveryManager(self._port, scan_interval_seconds=0.5)
        await self._discovery.start()
        self._healthy = True

    async def _run(self) -> None:
        assert self._discovery is not None
        while not self.should_stop():
            # Publish status for all known modules
            if self.bus:
                for dm in self._discovery.list_modules():
                    await self.bus.publish(
                        f"module/{dm.info.module_id}/status",
                        ModuleStatus(
                            source="module-manager",
                            module_id=dm.info.module_id,
                            connected=True,
                            healthy=True,
                            data={"type": dm.info.module_type},
                        ).model_dump_json(),
                    )
                    # Note: ideally publish 'discovered' once; for MVP we publish it periodically
                    await self.bus.publish(
                        f"module/{dm.info.module_id}/discovered",
                        DiscoveredSchema(
                            source="module-manager",
                            module_id=dm.info.module_id,
                            module_type=dm.info.module_type,
                            hardware_version=dm.info.hardware_version,
                            firmware_version=dm.info.firmware_version,
                            capabilities=[],
                            power_draw_ma=dm.info.power_draw_ma,
                            metadata=dm.info.metadata,
                        ).model_dump_json(),
                    )
            await asyncio.sleep(self._publish_interval)

    async def _cleanup(self) -> None:
        self._healthy = False
        if self._discovery:
            await self._discovery.stop()
            self._discovery = None

    def is_healthy(self) -> bool:
        return self._healthy

    def list_modules(self) -> list[dict[str, Any]]:
        if not self._discovery:
            return []
        return [
            {
                "module_id": dm.info.module_id,
                "type": dm.info.module_type,
                "power_draw_ma": dm.info.power_draw_ma,
                "enabled": dm.enabled,
            }
            for dm in self._discovery.list_modules()
        ]
