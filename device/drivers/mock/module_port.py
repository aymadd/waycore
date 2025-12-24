from __future__ import annotations

from typing import Any

from device.libs.hil.interfaces.module_port import IModulePort, ModuleInfo


class MockModulePort(IModulePort):
    def __init__(self, config: dict[str, Any]) -> None:
        self._num_ports: int = int(config.get("num_ports", 2))
        self._auto_connect: bool = bool(config.get("auto_connect_modules", True))
        self._enabled: set[int] = set()

    async def scan_ports(self) -> list[int]:
        if not self._auto_connect:
            return []
        return list(range(self._num_ports))

    async def identify_module(self, port: int) -> ModuleInfo | None:
        if port < 0 or port >= self._num_ports:
            return None
        return ModuleInfo(
            module_id=f"mod-{port}",
            module_type="mock",
            hardware_version="1.0",
            firmware_version="1.0.0",
            capabilities=["sensor"],
            power_draw_ma=150,
            metadata={"port": port},
        )

    async def enable_module(self, port: int) -> bool:
        self._enabled.add(port)
        return True

    async def disable_module(self, port: int) -> bool:
        self._enabled.discard(port)
        return True

    async def read_data(self, port: int) -> bytes | None:
        if port not in self._enabled:
            return None
        return None

    async def write_data(self, port: int, data: bytes) -> bool:
        return port in self._enabled

    async def get_power_draw(self, port: int) -> int | None:
        return 150 if port in self._enabled else 0


def register(_: object) -> None:
    from device.libs.hil.factory import DriverFactory

    DriverFactory.register_module_port("mock", lambda cfg: MockModulePort(dict(cfg)))
