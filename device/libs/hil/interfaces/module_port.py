from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ModuleInfo:
    module_id: str
    module_type: str
    hardware_version: str
    firmware_version: str
    capabilities: list[str]
    power_draw_ma: int
    metadata: dict[str, Any]


class IModulePort(ABC):
    @abstractmethod
    async def scan_ports(self) -> list[int]: ...

    @abstractmethod
    async def identify_module(self, port: int) -> ModuleInfo | None: ...

    @abstractmethod
    async def enable_module(self, port: int) -> bool: ...

    @abstractmethod
    async def disable_module(self, port: int) -> bool: ...

    @abstractmethod
    async def read_data(self, port: int) -> bytes | None: ...

    @abstractmethod
    async def write_data(self, port: int, data: bytes) -> bool: ...

    @abstractmethod
    async def get_power_draw(self, port: int) -> int | None: ...
