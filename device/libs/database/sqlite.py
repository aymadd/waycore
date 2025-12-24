from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import aiosqlite

from device.libs.schemas.ai import AIInferenceResponse
from device.libs.schemas.comms import MessageReceived


class DatabaseError(RuntimeError):
    pass


class AsyncSQLite:
    """
    Lightweight async SQLite wrapper for logging device data.
    """

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = str(db_path)
        self._conn: aiosqlite.Connection | None = None

    async def open(self) -> None:
        try:
            self._conn = await aiosqlite.connect(self._db_path)
            await self._conn.execute("PRAGMA journal_mode=WAL;")
            await self._initialize_schema()
        except Exception as exc:  # noqa: BLE001
            raise DatabaseError(str(exc)) from exc

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    async def _initialize_schema(self) -> None:
        assert self._conn is not None
        await self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                topic TEXT NOT NULL,
                payload TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS comms_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                transport TEXT NOT NULL,
                from_node TEXT,
                to_node TEXT,
                content TEXT NOT NULL,
                channel TEXT,
                rssi REAL,
                snr REAL,
                metadata TEXT
            );

            CREATE TABLE IF NOT EXISTS ai_inferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                request_id TEXT NOT NULL,
                model_id TEXT NOT NULL,
                inference_type TEXT NOT NULL,
                success INTEGER NOT NULL,
                results TEXT NOT NULL,
                error_message TEXT
            );
            """
        )
        await self._conn.commit()

    async def log_event(self, topic: str, payload: str) -> None:
        assert self._conn is not None
        await self._conn.execute(
            "INSERT INTO events (topic, payload) VALUES (?, ?)", (topic, payload)
        )
        await self._conn.commit()

    async def log_comms_message(self, msg: MessageReceived) -> None:
        assert self._conn is not None
        await self._conn.execute(
            """
            INSERT INTO comms_messages
            (transport, from_node, to_node, content, channel, rssi, snr, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                msg.transport.value,
                msg.from_node,
                msg.to_node,
                msg.content,
                msg.channel,
                msg.rssi,
                msg.snr,
                json.dumps(msg.model_dump(mode="json")),
            ),
        )
        await self._conn.commit()

    async def log_ai_inference(self, resp: AIInferenceResponse) -> None:
        assert self._conn is not None
        await self._conn.execute(
            """
            INSERT INTO ai_inferences
            (request_id, model_id, inference_type, success, results, error_message)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(resp.request_id),
                resp.model_id,
                resp.inference_type.value,
                1 if resp.success else 0,
                json.dumps([r.model_dump(mode="json") for r in resp.results]),
                resp.error_message,
            ),
        )
        await self._conn.commit()

    async def fetch_latest(self, table: str, limit: int = 50) -> list[dict[str, Any]]:
        """
        Fetch latest rows from a supported table.
        """
        assert self._conn is not None
        if table not in {"events", "comms_messages", "ai_inferences"}:
            raise DatabaseError(f"Unsupported table: {table}")
        cursor = await self._conn.execute(
            f"SELECT * FROM {table} ORDER BY id DESC LIMIT ?", (int(limit),)
        )
        assert cursor.description is not None
        cols = [c[0] for c in cursor.description]
        rows = await cursor.fetchall()
        await cursor.close()
        return [dict(zip(cols, row)) for row in rows]
