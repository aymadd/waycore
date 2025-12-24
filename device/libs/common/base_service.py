from __future__ import annotations

import asyncio
import contextlib
from abc import ABC, abstractmethod
from typing import Any

from device.libs.messaging.bus import MessageBus


class BaseService(ABC):
    def __init__(self, config: dict[str, Any], bus: MessageBus | None = None) -> None:
        self._config = config
        self._bus = bus
        self._task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()
        self._started = False

    @property
    def config(self) -> dict[str, Any]:
        return self._config

    @property
    def bus(self) -> MessageBus | None:
        return self._bus

    @bus.setter
    def bus(self, value: MessageBus | None) -> None:
        self._bus = value

    async def start(self) -> None:
        if self._started:
            return
        await self._setup()
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run_wrapper())
        self._started = True

    async def stop(self) -> None:
        if not self._started:
            return
        self._stop_event.set()
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=5.0)
            except asyncio.TimeoutError:
                self._task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await self._task
            finally:
                self._task = None
        await self._cleanup()
        self._started = False

    async def _run_wrapper(self) -> None:
        try:
            await self._run()
        finally:
            # Ensure cleanup happens in case of unexpected exit
            pass

    def should_stop(self) -> bool:
        return self._stop_event.is_set()

    @abstractmethod
    async def _setup(self) -> None: ...

    @abstractmethod
    async def _run(self) -> None: ...

    @abstractmethod
    async def _cleanup(self) -> None: ...
