"""Bridge for AI service between backend and QML UI."""

from __future__ import annotations

import base64
import logging
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PySide6.QtCore import Property, QObject, QRunnable, QThreadPool, Signal, Slot

from .api_client import AIServiceClient

logger = logging.getLogger(__name__)


class ChatWorker(QRunnable):
    """
    Worker for running AI chat inference in background thread.

    Uses a signaler object to communicate results back to the main thread.
    """

    class Signals(QObject):
        """Signals for worker communication."""

        finished = Signal(dict)  # Result dict
        error = Signal(str)  # Error message

    def __init__(
        self,
        client: AIServiceClient | None,
        question: str,
        model_id: str,
        backend_available: bool,
    ) -> None:
        super().__init__()
        self.signals = self.Signals()
        self._client = client
        self._question = question
        self._model_id = model_id
        self._backend_available = backend_available
        self.setAutoDelete(True)

    def run(self) -> None:
        """Execute chat inference in background thread."""
        try:
            if not self._backend_available or not self._client:
                # Mock response
                result = self._get_mock_response(self._question)
            else:
                api_result = self._client.chat(
                    question=self._question,
                    model_id=self._model_id,
                )

                if api_result.get("success", True):
                    results = api_result.get("results", [])
                    if results:
                        answer = results[0].get("label", "No response generated.")
                    else:
                        answer = "No response generated."
                    result = {"success": True, "answer": answer}
                else:
                    error_msg = api_result.get("error_message", "Unknown error")
                    result = {"success": False, "error": error_msg}

            self.signals.finished.emit(result)

        except Exception as e:
            logger.error(f"Chat worker error: {e}")
            self.signals.error.emit(str(e))

    def _get_mock_response(self, question: str) -> dict[str, Any]:
        """Generate a mock response when backend is unavailable."""
        import time

        # Simulate processing time
        time.sleep(0.5)

        question_lower = question.lower()

        if "hello" in question_lower or "hi" in question_lower:
            answer = "Hello! I'm your AI assistant. How can I help you today?"
        elif "weather" in question_lower:
            answer = (
                "I don't have access to real-time weather data, but I can help you "
                "with other questions about your surroundings or equipment."
            )
        elif "help" in question_lower:
            answer = (
                "I can help you with:\n"
                "• Answering questions about outdoor activities\n"
                "• Providing survival tips\n"
                "• Identifying plants and animals (with images)\n"
                "• Navigation guidance\n\n"
                "Just ask me anything!"
            )
        elif "name" in question_lower:
            answer = (
                "I'm Waycore AI, your intelligent outdoor companion. "
                "I run locally on your device for privacy and offline use."
            )
        else:
            answer = (
                f"You asked: '{question}'\n\n"
                "This is a mock response. When connected to the AI service, "
                "I'll provide helpful answers based on your questions."
            )

        return {"success": True, "answer": answer}


class ImageClassifyWorker(QRunnable):
    """
    Worker for running image classification in background thread.
    """

    class Signals(QObject):
        """Signals for worker communication."""

        finished = Signal(dict)  # Result dict
        error = Signal(str)  # Error message

    def __init__(
        self,
        client: AIServiceClient | None,
        image_b64: str,
        model_id: str,
        backend_available: bool,
    ) -> None:
        super().__init__()
        self.signals = self.Signals()
        self._client = client
        self._image_b64 = image_b64
        self._model_id = model_id
        self._backend_available = backend_available
        self.setAutoDelete(True)

    def run(self) -> None:
        """Execute image classification in background thread."""
        try:
            if not self._backend_available or not self._client:
                result = self._get_mock_classification()
            else:
                api_result = self._client.classify_image(
                    image_b64=self._image_b64,
                    model_id=self._model_id,
                )

                if api_result.get("success", True):
                    results = api_result.get("results", [])
                    result = {"success": True, "results": results}
                else:
                    error_msg = api_result.get("error_message", "Unknown error")
                    result = {"success": False, "error": error_msg}

            self.signals.finished.emit(result)

        except Exception as e:
            logger.error(f"Image classify worker error: {e}")
            self.signals.error.emit(str(e))

    def _get_mock_classification(self) -> dict[str, Any]:
        """Generate mock image classification results."""
        import random
        import time

        time.sleep(0.5)

        mock_labels = [
            ("Mountain", 0.85),
            ("Tree", 0.78),
            ("Bird", 0.72),
            ("Flower", 0.68),
            ("Rock", 0.65),
            ("Lake", 0.62),
        ]

        count = random.randint(3, 5)
        selected = random.sample(mock_labels, count)
        selected.sort(key=lambda x: x[1], reverse=True)

        results = [{"label": label, "confidence": conf, "metadata": {}} for label, conf in selected]
        return {"success": True, "results": results}


# Database path for local storage
AI_DB_PATH = os.getenv("AI_DB_PATH", str(Path.home() / ".waycore" / "ai.sqlite3"))


class AILocalDatabase:
    """
    Local SQLite database for AI chat history.

    Uses synchronous SQLite for UI thread compatibility.
    """

    def __init__(self, db_path: str = AI_DB_PATH) -> None:
        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None
        self._ensure_initialized()

    def _ensure_initialized(self) -> None:
        """Ensure database exists and schema is created."""
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.executescript(
            """
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
            """
        )
        conn.commit()
        conn.close()

    def _get_conn(self) -> sqlite3.Connection:
        """Get database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(self._db_path)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys=ON;")
        return self._conn

    def close(self) -> None:
        """Close database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    # Conversation methods

    def create_conversation(self, title: str | None = None, model_id: str = "phi3-mini") -> int:
        """Create a new conversation. Returns conversation ID."""
        conn = self._get_conn()
        cursor = conn.execute(
            "INSERT INTO ai_conversations (title, model_id) VALUES (?, ?)",
            (title, model_id),
        )
        conn.commit()
        return cursor.lastrowid if cursor.lastrowid else 0

    def get_conversation(self, conversation_id: int) -> dict[str, Any] | None:
        """Get a conversation by ID."""
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT * FROM ai_conversations WHERE id = ?",
            (conversation_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_all_conversations(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get all conversations, most recent first."""
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT * FROM ai_conversations ORDER BY updated_at DESC LIMIT ?",
            (limit,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def update_conversation(
        self,
        conversation_id: int,
        title: str | None = None,
        model_id: str | None = None,
    ) -> None:
        """Update conversation metadata."""
        conn = self._get_conn()
        updates = ["updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now')"]
        params: list[Any] = []

        if title is not None:
            updates.append("title = ?")
            params.append(title)
        if model_id is not None:
            updates.append("model_id = ?")
            params.append(model_id)

        params.append(conversation_id)
        conn.execute(
            f"UPDATE ai_conversations SET {', '.join(updates)} WHERE id = ?",
            tuple(params),
        )
        conn.commit()

    def delete_conversation(self, conversation_id: int) -> None:
        """Delete a conversation and all its messages."""
        conn = self._get_conn()
        conn.execute(
            "DELETE FROM ai_conversations WHERE id = ?",
            (conversation_id,),
        )
        conn.commit()

    def delete_all_conversations(self) -> int:
        """Delete all conversations and messages. Returns count deleted."""
        conn = self._get_conn()
        cursor = conn.execute("DELETE FROM ai_conversations")
        conn.commit()
        return cursor.rowcount if cursor.rowcount else 0

    # Message methods

    def add_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
    ) -> int:
        """Add a message to a conversation. Returns message ID."""
        conn = self._get_conn()
        cursor = conn.execute(
            "INSERT INTO ai_messages (conversation_id, role, content) VALUES (?, ?, ?)",
            (conversation_id, role, content),
        )
        # Update conversation's updated_at timestamp
        conn.execute(
            "UPDATE ai_conversations SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') "
            "WHERE id = ?",
            (conversation_id,),
        )
        conn.commit()
        return cursor.lastrowid if cursor.lastrowid else 0

    def get_messages(self, conversation_id: int, limit: int = 100) -> list[dict[str, Any]]:
        """Get messages for a conversation, oldest first."""
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT * FROM ai_messages WHERE conversation_id = ? "
            "ORDER BY created_at ASC LIMIT ?",
            (conversation_id, limit),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_message_count(self, conversation_id: int) -> int:
        """Get number of messages in a conversation."""
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT COUNT(*) as count FROM ai_messages WHERE conversation_id = ?",
            (conversation_id,),
        )
        row = cursor.fetchone()
        return int(row["count"]) if row else 0

    def clear_messages(self, conversation_id: int) -> int:
        """Clear all messages from a conversation. Returns count deleted."""
        conn = self._get_conn()
        cursor = conn.execute(
            "DELETE FROM ai_messages WHERE conversation_id = ?",
            (conversation_id,),
        )
        conn.commit()
        return cursor.rowcount if cursor.rowcount else 0

    def get_first_user_message(self, conversation_id: int) -> dict[str, Any] | None:
        """Get the first user message in a conversation (for auto-title)."""
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT * FROM ai_messages WHERE conversation_id = ? AND role = 'user' "
            "ORDER BY created_at ASC LIMIT 1",
            (conversation_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def factory_reset(self) -> dict[str, int]:
        """
        Delete all AI chat data for factory reset.

        Returns counts of deleted items.
        """
        conn = self._get_conn()
        messages = conn.execute("DELETE FROM ai_messages")
        conversations = conn.execute("DELETE FROM ai_conversations")
        conn.commit()
        return {
            "messages": messages.rowcount if messages.rowcount else 0,
            "conversations": conversations.rowcount if conversations.rowcount else 0,
        }


class AIBridge(QObject):
    """
    Bridge between QML UI and AI Service backend.

    Provides methods for chat Q&A, conversation management, and image classification.
    Uses background threads to keep UI responsive during inference.
    """

    # Signals
    loadingChanged = Signal()
    errorChanged = Signal()
    messagesChanged = Signal()
    conversationsChanged = Signal()
    currentConversationChanged = Signal()
    chatCompleted = Signal(dict)  # Emitted when async chat completes
    imageClassifyCompleted = Signal(dict)  # Emitted when async image classify completes

    # MCP Tool signals
    toolConfirmationRequired = Signal(dict)  # Emitted when tool needs user confirmation
    toolExecutionCompleted = Signal(dict)  # Emitted when tool execution finishes
    toolProgressUpdate = Signal(dict)  # Emitted for streaming tool progress

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._client: AIServiceClient | None = None
        self._backend_available = False
        self._is_loading = False
        self._error: str = ""
        self._model_id: str = "phi3-mini"
        self._messages: list[dict[str, Any]] = []
        self._current_conversation_id: int | None = None
        self._db = AILocalDatabase()
        self._thread_pool = QThreadPool.globalInstance()

        # MCP/Agent state
        self._pending_tool_confirmations: dict[str, dict[str, Any]] = {}

        self._init_client()

    def _init_client(self) -> None:
        """Initialize the AI service client and test connection."""
        try:
            self._client = AIServiceClient()
            # Test if backend is available with a health check
            self._client.get("/health")
            self._backend_available = True
            logger.info("AIBridge connected to AI Service backend")
        except Exception as e:
            logger.info(f"AI Service backend not available, using mock data: {e}")
            self._backend_available = False

    # Properties

    @Property(bool, notify=loadingChanged)  # type: ignore[arg-type]
    def isLoading(self) -> bool:
        """Whether a request is currently in progress."""
        return self._is_loading

    @Property(str, notify=errorChanged)  # type: ignore[arg-type]
    def error(self) -> str:
        """Current error message, if any."""
        return self._error

    @Property(str)  # type: ignore[arg-type]
    def modelId(self) -> str:
        """Current model ID."""
        return self._model_id

    @modelId.setter  # type: ignore[no-redef]
    def modelId(self, value: str) -> None:
        """Set current model ID."""
        self._model_id = value

    @Property("QVariantList", notify=messagesChanged)  # type: ignore[arg-type]
    def messages(self) -> list[dict[str, Any]]:
        """Current chat messages."""
        return self._messages

    @Property(int, notify=currentConversationChanged)  # type: ignore[arg-type]
    def currentConversationId(self) -> int:
        """Current conversation ID (0 if none)."""
        return self._current_conversation_id or 0

    # Slots - Model Management

    @Slot(str)  # type: ignore[arg-type]
    def setModelId(self, model_id: str) -> None:
        """Set the model ID to use for inference."""
        self._model_id = model_id
        # Update current conversation if exists
        if self._current_conversation_id:
            self._db.update_conversation(self._current_conversation_id, model_id=model_id)

    @Slot(result=str)  # type: ignore[arg-type]
    def getModelId(self) -> str:
        """Get the current model ID."""
        return self._model_id

    @Slot(result="QVariant")  # type: ignore[arg-type]
    def getAvailableModels(self) -> list[dict[str, str]]:
        """Get list of available models."""
        # For MVP, return hardcoded list
        return [
            {"id": "phi3-mini", "name": "Phi-3 Mini", "description": "Fast local LLM"},
            {"id": "llama2-7b", "name": "Llama 2 7B", "description": "Larger model"},
        ]

    # Slots - Chat

    def _create_conversation_with_sync(self, title: str | None = None) -> int:
        """Create a conversation locally and sync to backend."""
        # Create locally
        conv_id = self._db.create_conversation(title=title, model_id=self._model_id)

        # Sync to backend (non-blocking, best effort)
        if self._backend_available and self._client:
            try:
                result = self._client.create_conversation(title=title, model_id=self._model_id)
                # Optionally store the backend ID mapping
                logger.debug(f"Synced conversation to backend: {result}")
            except Exception as e:
                logger.debug(f"Failed to sync conversation to backend: {e}")

        return conv_id

    def _add_message_with_sync(self, conversation_id: int, role: str, content: str) -> int:
        """Add a message locally and sync to backend."""
        # Add locally
        msg_id = self._db.add_message(conversation_id, role, content)

        # Sync to backend (non-blocking, best effort)
        if self._backend_available and self._client:
            try:
                self._client.add_message(conversation_id, role, content)
            except Exception as e:
                logger.debug(f"Failed to sync message to backend: {e}")

        return msg_id

    @Slot(str)  # type: ignore[arg-type]
    def sendChat(self, question: str) -> None:
        """
        Send a chat message asynchronously.

        Creates a new conversation if none exists.
        Runs inference in background thread to keep UI responsive.
        Emits chatCompleted signal when done.
        """
        if not question.strip():
            self.chatCompleted.emit({"success": False, "error": "Empty question"})
            return

        self._set_loading(True)
        self._clear_error()

        # Ensure we have a conversation
        if not self._current_conversation_id:
            self._current_conversation_id = self._create_conversation_with_sync()
            self.currentConversationChanged.emit()
            self.conversationsChanged.emit()

        # Add user message immediately
        timestamp = self._get_timestamp()
        user_msg = {
            "role": "user",
            "content": question,
            "timestamp": timestamp,
        }
        self._messages.append(user_msg)
        self.messagesChanged.emit()

        # Persist user message (locally and to backend)
        self._add_message_with_sync(self._current_conversation_id, "user", question)

        # Auto-title conversation from first message
        if self._db.get_message_count(self._current_conversation_id) == 1:
            title = question[:50] + ("..." if len(question) > 50 else "")
            self._db.update_conversation(self._current_conversation_id, title=title)
            # Sync title to backend
            if self._backend_available and self._client:
                try:
                    self._client.update_conversation(self._current_conversation_id, title=title)
                except Exception as e:
                    logger.debug(f"Failed to sync conversation title: {e}")
            self.conversationsChanged.emit()

        # Run inference in background thread
        worker = ChatWorker(
            client=self._client,
            question=question,
            model_id=self._model_id,
            backend_available=self._backend_available,
        )
        worker.signals.finished.connect(self._on_chat_completed)
        worker.signals.error.connect(self._on_chat_error)
        self._thread_pool.start(worker)

    def _on_chat_completed(self, result: dict[str, Any]) -> None:
        """Handle completed chat inference (called on main thread)."""
        self._set_loading(False)

        if result.get("success"):
            # Add assistant message
            answer = result.get("answer", "")
            assistant_msg = {
                "role": "assistant",
                "content": answer,
                "timestamp": self._get_timestamp(),
            }
            self._messages.append(assistant_msg)
            self.messagesChanged.emit()

            # Persist assistant message (locally and to backend)
            if self._current_conversation_id:
                self._add_message_with_sync(self._current_conversation_id, "assistant", answer)
        else:
            self._set_error(result.get("error", "Unknown error"))

        self.chatCompleted.emit(result)

    def _on_chat_error(self, error_msg: str) -> None:
        """Handle chat error (called on main thread)."""
        self._set_loading(False)
        self._set_error(error_msg)
        self.chatCompleted.emit({"success": False, "error": error_msg})

    @Slot()  # type: ignore[arg-type]
    def clearMessages(self) -> None:
        """Clear messages from current conversation (keeps conversation)."""
        self._messages = []
        self.messagesChanged.emit()

        if self._current_conversation_id:
            self._db.clear_messages(self._current_conversation_id)

    @Slot(result="QVariant")  # type: ignore[arg-type]
    def getMessages(self) -> list[dict[str, Any]]:
        """Get all messages for current conversation."""
        return self._messages

    # Slots - Conversation Management

    @Slot(result="QVariant")  # type: ignore[arg-type]
    def getConversations(self) -> list[dict[str, Any]]:
        """Get all conversations, most recent first."""
        conversations = self._db.get_all_conversations()
        # Add message count to each conversation
        for conv in conversations:
            conv["message_count"] = self._db.get_message_count(conv["id"])
        return conversations

    @Slot(result=int)  # type: ignore[arg-type]
    def newConversation(self) -> int:
        """Create a new conversation and switch to it. Returns conversation ID."""
        self._current_conversation_id = self._db.create_conversation(model_id=self._model_id)
        self._messages = []
        self.messagesChanged.emit()
        self.currentConversationChanged.emit()
        self.conversationsChanged.emit()
        return self._current_conversation_id

    @Slot(int, result=bool)  # type: ignore[arg-type]
    def loadConversation(self, conversation_id: int) -> bool:
        """Load a conversation and its messages. Returns success."""
        conversation = self._db.get_conversation(conversation_id)
        if not conversation:
            return False

        self._current_conversation_id = conversation_id
        self._model_id = conversation.get("model_id", "phi3-mini")

        # Load messages
        db_messages = self._db.get_messages(conversation_id)
        self._messages = [
            {
                "role": msg["role"],
                "content": msg["content"],
                "timestamp": msg["created_at"],
            }
            for msg in db_messages
        ]

        self.messagesChanged.emit()
        self.currentConversationChanged.emit()
        return True

    @Slot(int, result=bool)  # type: ignore[arg-type]
    def deleteConversation(self, conversation_id: int) -> bool:
        """Delete a conversation. Returns success."""
        self._db.delete_conversation(conversation_id)

        # If we deleted the current conversation, clear state
        if self._current_conversation_id == conversation_id:
            self._current_conversation_id = None
            self._messages = []
            self.messagesChanged.emit()
            self.currentConversationChanged.emit()

        self.conversationsChanged.emit()
        return True

    @Slot(result=int)  # type: ignore[arg-type]
    def deleteAllConversations(self) -> int:
        """Delete all conversations. Returns count deleted."""
        count = self._db.delete_all_conversations()
        self._current_conversation_id = None
        self._messages = []
        self.messagesChanged.emit()
        self.currentConversationChanged.emit()
        self.conversationsChanged.emit()
        return count

    @Slot(int, result="QVariant")  # type: ignore[arg-type]
    def getConversation(self, conversation_id: int) -> dict[str, Any] | None:
        """Get a specific conversation by ID."""
        return self._db.get_conversation(conversation_id)

    @Slot(result="QVariant")  # type: ignore[arg-type]
    def factoryReset(self) -> dict[str, Any]:
        """
        Factory reset: Clear all AI data from both local and backend databases.

        This clears:
        - All local conversations and messages
        - Backend conversations, messages, and model registry

        Returns dict with deleted counts.
        """
        result: dict[str, Any] = {"success": True, "local": {}, "backend": {}}

        # Clear local database
        local_result = self._db.factory_reset()
        result["local"] = local_result

        # Clear UI state
        self._current_conversation_id = None
        self._messages = []
        self.messagesChanged.emit()
        self.currentConversationChanged.emit()
        self.conversationsChanged.emit()

        # Clear backend database (if available)
        if self._backend_available and self._client:
            try:
                backend_result = self._client.factory_reset()
                result["backend"] = backend_result.get("deleted", {})
            except Exception as e:
                logger.warning(f"Failed to reset backend: {e}")
                result["backend_error"] = str(e)

        logger.info(f"Factory reset completed: {result}")
        return result

    # Slots - Image Classification

    @Slot(str, result="QVariant")  # type: ignore[arg-type]
    def classifyImage(self, image_b64: str) -> dict[str, Any]:
        """
        Classify an image and return the results.

        Args:
            image_b64: Base64-encoded image data

        Returns:
            Dictionary with success, results (label, confidence), or error
        """
        if not image_b64.strip():
            return {"success": False, "error": "Empty image data"}

        self._set_loading(True)
        self._clear_error()

        if not self._backend_available or not self._client:
            # Mock response
            response = self._get_mock_image_classification()
        else:
            try:
                result = self._client.classify_image(
                    image_b64=image_b64,
                    model_id="mobilenetv3",
                )

                if result.get("success", True):
                    results = result.get("results", [])
                    response = {"success": True, "results": results}
                else:
                    error_msg = result.get("error_message", "Unknown error")
                    response = {"success": False, "error": error_msg}
            except Exception as e:
                logger.error(f"Failed to classify image: {e}")
                response = {"success": False, "error": str(e)}

        self._set_loading(False)

        if not response.get("success"):
            self._set_error(response.get("error", "Unknown error"))

        return response

    @Slot(str)  # type: ignore[arg-type]
    def classifyImageAndChat(self, image_b64: str) -> None:
        """
        Classify an image asynchronously and add the result as a chat message.

        Args:
            image_b64: Base64-encoded image data

        Emits imageClassifyCompleted signal when done.
        """
        if not image_b64.strip():
            self.imageClassifyCompleted.emit({"success": False, "error": "Empty image data"})
            return

        self._set_loading(True)
        self._clear_error()

        # Ensure we have a conversation
        if not self._current_conversation_id:
            self._current_conversation_id = self._create_conversation_with_sync(
                title="🖼️ Image Classification"
            )
            self.currentConversationChanged.emit()
            self.conversationsChanged.emit()

        # Add user message with image indicator
        timestamp = self._get_timestamp()
        user_msg = {
            "role": "user",
            "content": "📷 [Image for classification]",
            "timestamp": timestamp,
            "has_image": True,
            "image_b64": image_b64[:100] + "...",  # Truncated preview
        }
        self._messages.append(user_msg)
        self.messagesChanged.emit()

        # Persist user message (locally and to backend)
        self._add_message_with_sync(
            self._current_conversation_id, "user", "📷 [Image for classification]"
        )

        # Auto-title conversation if first message
        if self._db.get_message_count(self._current_conversation_id) == 1:
            title = "🖼️ Image Classification"
            self._db.update_conversation(self._current_conversation_id, title=title)
            if self._backend_available and self._client:
                try:
                    self._client.update_conversation(self._current_conversation_id, title=title)
                except Exception as e:
                    logger.debug(f"Failed to sync conversation title: {e}")
            self.conversationsChanged.emit()

        # Run classification in background thread
        worker = ImageClassifyWorker(
            client=self._client,
            image_b64=image_b64,
            model_id="mobilenetv3",
            backend_available=self._backend_available,
        )
        worker.signals.finished.connect(self._on_image_classify_completed)
        worker.signals.error.connect(self._on_image_classify_error)
        self._thread_pool.start(worker)

    def _on_image_classify_completed(self, result: dict[str, Any]) -> None:
        """Handle completed image classification (called on main thread)."""
        self._set_loading(False)

        if result.get("success"):
            # Format classification results as assistant message
            results = result.get("results", [])
            if results:
                lines = ["**Image Classification Results:**\n"]
                for r in results[:5]:  # Top 5 results
                    label = r.get("label", "Unknown")
                    confidence = r.get("confidence", 0)
                    pct = f"{confidence * 100:.1f}%"
                    lines.append(f"• **{label}**: {pct}")
                answer = "\n".join(lines)
            else:
                answer = "Could not classify the image. Please try a clearer photo."

            assistant_msg = {
                "role": "assistant",
                "content": answer,
                "timestamp": self._get_timestamp(),
            }
            self._messages.append(assistant_msg)
            self.messagesChanged.emit()

            # Persist assistant message (locally and to backend)
            if self._current_conversation_id:
                self._add_message_with_sync(self._current_conversation_id, "assistant", answer)
        else:
            self._set_error(result.get("error", "Unknown error"))

        self.imageClassifyCompleted.emit(result)

    def _on_image_classify_error(self, error_msg: str) -> None:
        """Handle image classification error (called on main thread)."""
        self._set_loading(False)
        self._set_error(error_msg)
        self.imageClassifyCompleted.emit({"success": False, "error": error_msg})

    @Slot(str)  # type: ignore[arg-type]
    def classifyImageFromPath(self, file_path: str) -> None:
        """
        Load an image from file path and classify it.

        Supports local file paths or file:// URLs.

        Args:
            file_path: Path to image file (can be file:// URL)

        Emits imageClassifyCompleted signal when done.
        """
        # Handle file:// URLs (from Qt FileDialog)
        if file_path.startswith("file://"):
            file_path = file_path[7:]  # Remove file:// prefix

        try:
            path = Path(file_path)
            if not path.exists():
                self._set_error(f"File not found: {file_path}")
                self.imageClassifyCompleted.emit({"success": False, "error": "File not found"})
                return

            # Check file size (limit to 10MB)
            file_size = path.stat().st_size
            if file_size > 10 * 1024 * 1024:
                self._set_error("Image file too large (max 10MB)")
                self.imageClassifyCompleted.emit(
                    {"success": False, "error": "Image file too large (max 10MB)"}
                )
                return

            # Read and encode image
            with open(path, "rb") as f:
                image_data = f.read()
            image_b64 = base64.b64encode(image_data).decode("utf-8")

            # Call the async classifier
            self.classifyImageAndChat(image_b64)

        except Exception as e:
            logger.error(f"Failed to load image from {file_path}: {e}")
            self._set_error(f"Failed to load image: {e}")
            self.imageClassifyCompleted.emit({"success": False, "error": str(e)})

    # Private helpers

    def _set_loading(self, loading: bool) -> None:
        """Set loading state."""
        if self._is_loading != loading:
            self._is_loading = loading
            self.loadingChanged.emit()

    def _set_error(self, error: str) -> None:
        """Set error message."""
        if self._error != error:
            self._error = error
            self.errorChanged.emit()

    def _clear_error(self) -> None:
        """Clear error message."""
        self._set_error("")

    def _get_timestamp(self) -> str:
        """Get current ISO timestamp."""
        return datetime.now(timezone.utc).isoformat()

    # MCP Tool Confirmation Methods

    @Slot(str, "QVariant", str, str)  # type: ignore[arg-type]
    def requestToolConfirmation(
        self,
        tool_name: str,
        params: dict[str, Any],
        warning: str = "",
        description: str = "",
    ) -> None:
        """
        Request user confirmation for a tool execution.

        This is called by the AI service when a tool requires confirmation.

        Args:
            tool_name: Name of the tool to execute.
            params: Tool parameters.
            warning: Optional warning message.
            description: Optional description of what the tool does.
        """
        confirmation_data = {
            "tool_name": tool_name,
            "params": params,
            "warning": warning,
            "description": description,
        }
        self._pending_tool_confirmations[tool_name] = confirmation_data
        self.toolConfirmationRequired.emit(confirmation_data)

    @Slot(str)  # type: ignore[arg-type]
    def confirmTool(self, tool_name: str) -> None:
        """
        Confirm and execute a pending tool.

        Args:
            tool_name: Name of the tool to confirm.
        """
        if tool_name not in self._pending_tool_confirmations:
            logger.warning(f"No pending confirmation for tool: {tool_name}")
            self.toolExecutionCompleted.emit(
                {"success": False, "tool": tool_name, "error": "No pending confirmation"}
            )
            return

        confirmation_data = self._pending_tool_confirmations.pop(tool_name)
        params = confirmation_data.get("params", {})

        # Execute the tool via backend API
        if self._backend_available and self._client:
            try:
                # Call the tool execution endpoint
                result = self._client.post(
                    "/api/tools/execute",
                    json={"tool_name": tool_name, "arguments": params},
                )
                self.toolExecutionCompleted.emit(
                    {"success": True, "tool": tool_name, "result": result}
                )
            except Exception as e:
                logger.error(f"Tool execution failed: {e}")
                self.toolExecutionCompleted.emit(
                    {"success": False, "tool": tool_name, "error": str(e)}
                )
        else:
            # Mock execution for development
            logger.info(f"Mock tool execution: {tool_name} with params {params}")
            self.toolExecutionCompleted.emit(
                {"success": True, "tool": tool_name, "result": f"Executed {tool_name} (mock)"}
            )

    @Slot(str)  # type: ignore[arg-type]
    def cancelTool(self, tool_name: str) -> None:
        """
        Cancel a pending tool confirmation.

        Args:
            tool_name: Name of the tool to cancel.
        """
        if tool_name in self._pending_tool_confirmations:
            self._pending_tool_confirmations.pop(tool_name)
            logger.info(f"Tool confirmation cancelled: {tool_name}")
            self.toolExecutionCompleted.emit(
                {"success": False, "tool": tool_name, "cancelled": True}
            )

    @Slot(result="QVariant")  # type: ignore[arg-type]
    def getPendingToolConfirmations(self) -> list[dict[str, Any]]:
        """
        Get list of tools waiting for confirmation.

        Returns:
            List of pending confirmation data.
        """
        return list(self._pending_tool_confirmations.values())

    @Slot(result="QVariant")  # type: ignore[arg-type]
    def getAvailableTools(self) -> list[dict[str, Any]]:
        """
        Get list of available MCP tools.

        Returns:
            List of tool definitions.
        """
        if self._backend_available and self._client:
            try:
                result = self._client.get("/api/tools")
                return result.get("tools", [])
            except Exception as e:
                logger.warning(f"Failed to get tools: {e}")
                return []
        else:
            # Return mock tools for development
            return [
                {
                    "name": "get_temperature",
                    "description": "Get current temperature reading",
                    "requires_confirmation": False,
                },
                {
                    "name": "get_gps_location",
                    "description": "Get current GPS coordinates",
                    "requires_confirmation": False,
                },
                {
                    "name": "send_mesh_message",
                    "description": "Send a message over mesh network",
                    "requires_confirmation": True,
                },
            ]
