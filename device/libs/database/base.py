"""Base async SQLite database class."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import aiosqlite


class DatabaseError(RuntimeError):
    """Database operation error."""

    pass


class BaseAsyncDatabase:
    """
    Base class for async SQLite database wrappers.

    Provides common functionality for opening, closing, and querying.
    Subclasses should implement _get_schema() for their specific tables.
    """

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = str(db_path)
        self._conn: aiosqlite.Connection | None = None

    @property
    def is_open(self) -> bool:
        """Check if database connection is open."""
        return self._conn is not None

    async def open(self) -> None:
        """Open database connection and initialize schema."""
        try:
            Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
            self._conn = await aiosqlite.connect(self._db_path)
            await self._conn.execute("PRAGMA journal_mode=WAL;")
            await self._initialize_schema()
        except Exception as exc:  # noqa: BLE001
            raise DatabaseError(str(exc)) from exc

    async def close(self) -> None:
        """Close database connection."""
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    async def _initialize_schema(self) -> None:
        """Initialize database schema. Override in subclasses."""
        assert self._conn is not None
        schema = self._get_schema()
        if schema:
            await self._conn.executescript(schema)
            await self._conn.commit()

    def _get_schema(self) -> str:
        """Return SQL schema for this database. Override in subclasses."""
        return ""

    async def execute(self, sql: str, params: tuple[Any, ...] = ()) -> aiosqlite.Cursor:
        """Execute SQL statement."""
        assert self._conn is not None
        return await self._conn.execute(sql, params)

    async def executemany(self, sql: str, params_list: list[tuple[Any, ...]]) -> None:
        """Execute SQL statement with multiple parameter sets."""
        assert self._conn is not None
        await self._conn.executemany(sql, params_list)

    async def commit(self) -> None:
        """Commit current transaction."""
        assert self._conn is not None
        await self._conn.commit()

    async def fetchone(self, sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        """Execute query and return single row as dict."""
        assert self._conn is not None
        cursor = await self._conn.execute(sql, params)
        row = await cursor.fetchone()
        await cursor.close()
        if row is None:
            return None
        assert cursor.description is not None
        cols = [c[0] for c in cursor.description]
        return dict(zip(cols, row))

    async def fetchall(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        """Execute query and return all rows as list of dicts."""
        assert self._conn is not None
        cursor = await self._conn.execute(sql, params)
        rows = await cursor.fetchall()
        assert cursor.description is not None
        cols = [c[0] for c in cursor.description]
        await cursor.close()
        return [dict(zip(cols, row)) for row in rows]
