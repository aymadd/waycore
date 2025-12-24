from __future__ import annotations

from datetime import datetime, timezone
from typing import ClassVar
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class BaseMessage(BaseModel):
    """
    Base schema for all messages exchanged over the message bus.
    """

    msg_id: UUID = Field(default_factory=uuid4, description="Unique message identifier (UUID4)")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp in UTC",
    )
    source: str = Field(..., description="Service name that created the message", min_length=1)
    version: str = Field("1.0.0", description="Schema version (semver)")

    # Semver pattern kept simple, validated lightly
    _SEMVER_PATTERN: ClassVar[str] = r"^\d+\.\d+\.\d+$"

    @field_validator("version")
    @classmethod
    def _validate_version(cls, value: str) -> str:
        import re

        if not re.match(cls._SEMVER_PATTERN, value):
            msg = "version must be semantic version (e.g., 1.0.0)"
            raise ValueError(msg)
        return value

    class Config:
        # Pydantic v2 config via model_config is optional here; using legacy-style for readability.
        # Keep datetime and UUID serialization as strings (default behavior).
        populate_by_name = True
        # Allow extra to be ignored by default to ease forward-compatible consumers
        extra = "ignore"
