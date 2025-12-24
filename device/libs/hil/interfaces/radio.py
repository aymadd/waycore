from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Callable


class RadioType(str, Enum):
    lora = "lora"
    wifi = "wifi"
    lte = "lte"
    bluetooth = "bluetooth"


@dataclass(frozen=True)
class RadioStatus:
    enabled: bool
    connected: bool
    signal_strength: int | None = None
    tx_power_dbm: int | None = None
    channel: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class ReceivedMessage:
    timestamp: datetime
    from_node: str
    to_node: str | None
    content: bytes
    rssi: int | None = None
    snr: float | None = None


class IRadio(ABC):
    @abstractmethod
    async def start(self) -> None: ...

    @abstractmethod
    async def stop(self) -> None: ...

    @abstractmethod
    async def send_message(
        self, content: bytes, to_node: str | None, channel: str | None, want_ack: bool
    ) -> bool: ...

    @abstractmethod
    def subscribe_messages(self, callback: Callable[[ReceivedMessage], None]) -> None: ...

    @abstractmethod
    async def get_status(self) -> RadioStatus: ...

    @abstractmethod
    async def set_power(self, enabled: bool) -> None: ...

    @property
    @abstractmethod
    def radio_type(self) -> RadioType: ...
