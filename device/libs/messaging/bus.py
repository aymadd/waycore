from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable, Protocol


class MessageHandler(Protocol):
    def __call__(self, topic: str, payload: bytes) -> None: ...


class MessageBus(ABC):
    """
    Abstract message bus interface.
    Implementations provide MQTT or other transports.
    """

    @abstractmethod
    async def connect(self, broker_url: str) -> None: ...

    @abstractmethod
    async def disconnect(self) -> None: ...

    @abstractmethod
    async def publish(
        self, topic: str, payload: bytes | str, qos: int = 0, retain: bool = False
    ) -> None: ...

    @abstractmethod
    def subscribe(
        self, topic: str, handler: MessageHandler, qos: int = 0
    ) -> Callable[[], None]: ...
