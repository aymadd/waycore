"""AI database for inference logs, chat conversations, and model data."""

from __future__ import annotations

from typing import Any

from device.libs.schemas.ai import AIInferenceResponse

from .base import BaseAsyncDatabase


class AIDatabase(BaseAsyncDatabase):
    """
    Database for AI/ML related data.

    Tables:
    - ai_inferences: Inference request/response logs
    - ai_conversations: Chat conversation metadata
    - ai_messages: Chat messages within conversations
    - ai_models: Model registry (installed models and active status)
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

            CREATE TABLE IF NOT EXISTS ai_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                model_id TEXT NOT NULL DEFAULT 'phi3-mini',
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
            );

            CREATE INDEX IF NOT EXISTS idx_ai_conversations_updated
                ON ai_conversations(updated_at);

            CREATE TABLE IF NOT EXISTS ai_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                FOREIGN KEY (conversation_id) REFERENCES ai_conversations(id)
                    ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_ai_messages_conversation
                ON ai_messages(conversation_id);

            CREATE TABLE IF NOT EXISTS ai_models (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                name TEXT NOT NULL,
                format TEXT NOT NULL,
                path TEXT NOT NULL,
                size_mb REAL NOT NULL DEFAULT 0,
                is_active INTEGER NOT NULL DEFAULT 0,
                source_url TEXT,
                metadata TEXT,
                uploaded_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                last_used_at TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_ai_models_type ON ai_models(type);
            CREATE INDEX IF NOT EXISTS idx_ai_models_active ON ai_models(is_active);
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

    # --- Conversation Methods ---

    async def create_conversation(
        self, title: str | None = None, model_id: str = "phi3-mini"
    ) -> int:
        """Create a new conversation. Returns conversation ID."""
        cursor = await self.execute(
            "INSERT INTO ai_conversations (title, model_id) VALUES (?, ?)",
            (title, model_id),
        )
        await self.commit()
        return cursor.lastrowid if cursor.lastrowid else 0

    async def get_conversation(self, conversation_id: int) -> dict[str, Any] | None:
        """Get a conversation by ID."""
        return await self.fetchone(
            "SELECT * FROM ai_conversations WHERE id = ?",
            (conversation_id,),
        )

    async def get_all_conversations(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get all conversations, most recent first."""
        return await self.fetchall(
            "SELECT * FROM ai_conversations ORDER BY updated_at DESC LIMIT ?",
            (limit,),
        )

    async def update_conversation(
        self,
        conversation_id: int,
        title: str | None = None,
        model_id: str | None = None,
    ) -> None:
        """Update conversation metadata."""
        updates = ["updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now')"]
        params: list[Any] = []

        if title is not None:
            updates.append("title = ?")
            params.append(title)
        if model_id is not None:
            updates.append("model_id = ?")
            params.append(model_id)

        params.append(conversation_id)
        await self.execute(
            f"UPDATE ai_conversations SET {', '.join(updates)} WHERE id = ?",
            tuple(params),
        )
        await self.commit()

    async def delete_conversation(self, conversation_id: int) -> None:
        """Delete a conversation and all its messages."""
        await self.execute(
            "DELETE FROM ai_conversations WHERE id = ?",
            (conversation_id,),
        )
        await self.commit()

    async def delete_all_conversations(self) -> int:
        """Delete all conversations and messages. Returns count deleted."""
        cursor = await self.execute("DELETE FROM ai_conversations")
        await self.commit()
        return int(cursor.rowcount) if cursor.rowcount else 0

    # --- Message Methods ---

    async def add_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
    ) -> int:
        """Add a message to a conversation. Returns message ID."""
        cursor = await self.execute(
            "INSERT INTO ai_messages (conversation_id, role, content) VALUES (?, ?, ?)",
            (conversation_id, role, content),
        )
        # Update conversation's updated_at timestamp
        await self.execute(
            "UPDATE ai_conversations SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') "
            "WHERE id = ?",
            (conversation_id,),
        )
        await self.commit()
        return cursor.lastrowid if cursor.lastrowid else 0

    async def get_messages(self, conversation_id: int, limit: int = 100) -> list[dict[str, Any]]:
        """Get messages for a conversation, oldest first."""
        return await self.fetchall(
            "SELECT * FROM ai_messages WHERE conversation_id = ? "
            "ORDER BY created_at ASC LIMIT ?",
            (conversation_id, limit),
        )

    async def get_message_count(self, conversation_id: int) -> int:
        """Get number of messages in a conversation."""
        result = await self.fetchone(
            "SELECT COUNT(*) as count FROM ai_messages WHERE conversation_id = ?",
            (conversation_id,),
        )
        return int(result["count"]) if result else 0

    async def clear_messages(self, conversation_id: int) -> int:
        """Clear all messages from a conversation. Returns count deleted."""
        cursor = await self.execute(
            "DELETE FROM ai_messages WHERE conversation_id = ?",
            (conversation_id,),
        )
        await self.commit()
        return int(cursor.rowcount) if cursor.rowcount else 0

    async def get_first_user_message(self, conversation_id: int) -> dict[str, Any] | None:
        """Get the first user message in a conversation (for auto-title)."""
        return await self.fetchone(
            "SELECT * FROM ai_messages WHERE conversation_id = ? AND role = 'user' "
            "ORDER BY created_at ASC LIMIT 1",
            (conversation_id,),
        )

    # --- Model Methods ---

    async def add_model(
        self,
        model_id: str,
        model_type: str,
        name: str,
        fmt: str,
        path: str,
        size_mb: float = 0,
        source_url: str | None = None,
        metadata: str | None = None,
    ) -> None:
        """Add or update a model in the registry."""
        await self.execute(
            """
            INSERT INTO ai_models (id, type, name, format, path, size_mb, source_url, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                type = excluded.type,
                name = excluded.name,
                format = excluded.format,
                path = excluded.path,
                size_mb = excluded.size_mb,
                source_url = excluded.source_url,
                metadata = excluded.metadata
            """,
            (model_id, model_type, name, fmt, path, size_mb, source_url, metadata),
        )
        await self.commit()

    async def get_model(self, model_id: str) -> dict[str, Any] | None:
        """Get a model by ID."""
        return await self.fetchone(
            "SELECT * FROM ai_models WHERE id = ?",
            (model_id,),
        )

    async def get_all_models(self) -> list[dict[str, Any]]:
        """Get all registered models."""
        return await self.fetchall("SELECT * FROM ai_models ORDER BY type, name")

    async def get_models_by_type(self, model_type: str) -> list[dict[str, Any]]:
        """Get all models of a specific type."""
        return await self.fetchall(
            "SELECT * FROM ai_models WHERE type = ? ORDER BY name",
            (model_type,),
        )

    async def get_active_models(self) -> list[dict[str, Any]]:
        """Get all active models."""
        return await self.fetchall("SELECT * FROM ai_models WHERE is_active = 1")

    async def set_model_active(self, model_id: str, model_type: str) -> None:
        """Set a model as active, deactivating others of the same type."""
        # Deactivate other models of the same type
        await self.execute(
            "UPDATE ai_models SET is_active = 0 WHERE type = ?",
            (model_type,),
        )
        # Activate the specified model
        await self.execute(
            "UPDATE ai_models SET is_active = 1, "
            "last_used_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = ?",
            (model_id,),
        )
        await self.commit()

    async def update_model_last_used(self, model_id: str) -> None:
        """Update the last_used_at timestamp for a model."""
        await self.execute(
            "UPDATE ai_models SET last_used_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = ?",
            (model_id,),
        )
        await self.commit()

    async def delete_model(self, model_id: str) -> bool:
        """Delete a model from the registry. Returns True if deleted."""
        cursor = await self.execute(
            "DELETE FROM ai_models WHERE id = ?",
            (model_id,),
        )
        await self.commit()
        return bool(cursor.rowcount)

    async def delete_all_models(self) -> int:
        """Delete all models from the registry. Returns count deleted."""
        cursor = await self.execute("DELETE FROM ai_models")
        await self.commit()
        return int(cursor.rowcount) if cursor.rowcount else 0

    # --- Factory Reset ---

    async def factory_reset(self) -> dict[str, int]:
        """
        Delete all AI data for factory reset.

        Returns counts of deleted items by category.
        """
        # Delete in order to respect foreign keys
        messages = await self.execute("DELETE FROM ai_messages")
        conversations = await self.execute("DELETE FROM ai_conversations")
        inferences = await self.execute("DELETE FROM ai_inferences")
        models = await self.execute("DELETE FROM ai_models")
        await self.commit()

        return {
            "messages": int(messages.rowcount) if messages.rowcount else 0,
            "conversations": int(conversations.rowcount) if conversations.rowcount else 0,
            "inferences": int(inferences.rowcount) if inferences.rowcount else 0,
            "models": int(models.rowcount) if models.rowcount else 0,
        }
