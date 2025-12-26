"""Database module with specialized databases for different domains."""

# New domain-specific databases
from .ai import AIDatabase
from .base import BaseAsyncDatabase, DatabaseError
from .general import GeneralDatabase
from .mesh import MeshDatabase

# Legacy - keep for backwards compatibility
from .sqlite import AsyncSQLite

__all__ = [
    # Domain databases
    "MeshDatabase",
    "AIDatabase",
    "GeneralDatabase",
    # Base
    "BaseAsyncDatabase",
    "DatabaseError",
    # Legacy
    "AsyncSQLite",
]
