from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass

from device.libs.hil.interfaces.module_port import IModulePort, ModuleInfo


@dataclass
class DiscoveredModule:
    info: ModuleInfo
    enabled: bool = False


class DiscoveryManager:
    def __init__(self, port: IModulePort, scan_interval_seconds: float = 2.0) -> None:
        self._port = port
        self._scan_interval = scan_interval_seconds
        self._known: dict[str, DiscoveredModule] = {}
        self._task: asyncio.Task[None] | None = None
        self._running = False

    def list_modules(self) -> list[DiscoveredModule]:
        return list(self._known.values())

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def _loop(self) -> None:
        while self._running:
            await self.scan_once()
            await asyncio.sleep(self._scan_interval)

    async def scan_once(self) -> None:
        ports = await self._port.scan_ports()
        seen_ids: set[str] = set()
        for p in ports:
            info = await self._port.identify_module(p)
            if info is None:
                continue
            seen_ids.add(info.module_id)
            if info.module_id not in self._known:
                self._known[info.module_id] = DiscoveredModule(info=info, enabled=False)
                await self._port.enable_module(p)
                self._known[info.module_id].enabled = True
        # Remove modules not seen anymore
        for module_id in list(self._known.keys()):
            if module_id not in seen_ids:
                del self._known[module_id]
