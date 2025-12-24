from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class IdentifyRequest:
    type: str = "identify_request"

    def to_json(self) -> dict[str, Any]:
        return {"type": self.type}


@dataclass(frozen=True)
class IdentifyResponse:
    type: str
    module_id: str
    module_type: str
    hardware_version: str
    firmware_version: str

    @staticmethod
    def from_json(data: dict[str, Any]) -> IdentifyResponse:
        return IdentifyResponse(
            type=str(data.get("type", "")),
            module_id=str(data["module_id"]),
            module_type=str(data["module_type"]),
            hardware_version=str(data["hardware_version"]),
            firmware_version=str(data["firmware_version"]),
        )
