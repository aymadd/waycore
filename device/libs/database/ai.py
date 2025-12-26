"""AI database for inference logs and model data."""

from __future__ import annotations

from typing import Any

from device.libs.schemas.ai import AIInferenceResponse

from .base import BaseAsyncDatabase


class AIDatabase(BaseAsyncDatabase):
    """
    Database for AI/ML related data.

    Tables:
    - ai_inferences: Inference request/response logs
    - ai_models: Model registry (future)
    - ai_conversations: Chat history (future)
    """

    def _get_schema(self) -> str:
        return """
            CREATE TABLE IF NOT EXISTS ai_inferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                request_id TEXT NOT NULL,
                model_id TEXT NOT NULL,
                inference_type TEXT NOT NULL,
                success INTEGER NOT NULL,
                results TEXT NOT NULL,
                error_message TEXT,
                latency_ms REAL,
                tokens_used INTEGER
            );

            CREATE INDEX IF NOT EXISTS idx_ai_inferences_ts ON ai_inferences(ts);
            CREATE INDEX IF NOT EXISTS idx_ai_inferences_model ON ai_inferences(model_id);
        """

    async def log_inference(self, resp: AIInferenceResponse) -> None:
        """Log an AI inference response."""
        await self.execute(
            """
            INSERT INTO ai_inferences
            (request_id, model_id, inference_type, success, results, error_message)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(resp.request_id),
                resp.model_id,
                (
                    str(resp.inference_type.value)
                    if hasattr(resp.inference_type, "value")
                    else str(resp.inference_type)
                ),
                1 if resp.success else 0,
                str(resp.results),
                resp.error_message,
            ),
        )
        await self.commit()

    async def get_latest_inferences(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get most recent inference logs."""
        return await self.fetchall(
            "SELECT * FROM ai_inferences ORDER BY id DESC LIMIT ?",
            (limit,),
        )

    async def get_inferences_by_model(self, model_id: str, limit: int = 50) -> list[dict[str, Any]]:
        """Get inferences for a specific model."""
        return await self.fetchall(
            "SELECT * FROM ai_inferences WHERE model_id = ? ORDER BY id DESC LIMIT ?",
            (model_id, limit),
        )

    async def get_inference_stats(self) -> dict[str, Any]:
        """Get inference statistics."""
        total = await self.fetchone("SELECT COUNT(*) as count FROM ai_inferences")
        success = await self.fetchone(
            "SELECT COUNT(*) as count FROM ai_inferences WHERE success = 1"
        )
        by_model = await self.fetchall(
            """
            SELECT model_id, COUNT(*) as count, SUM(success) as successes
            FROM ai_inferences
            GROUP BY model_id
            """
        )

        return {
            "total": total["count"] if total else 0,
            "successful": success["count"] if success else 0,
            "by_model": by_model,
        }

    async def delete_all_inferences(self) -> int:
        """Delete all inference logs. Returns count deleted."""
        cursor = await self.execute("DELETE FROM ai_inferences")
        await self.commit()
        return int(cursor.rowcount) if cursor.rowcount else 0
