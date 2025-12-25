"""
Notes Bridge - Manages notes data and syncs with backend.
"""

from __future__ import annotations

import logging
from typing import Any

from PySide6.QtCore import Property, QObject, Signal, Slot

from .api_client import DataLoggerClient

logger = logging.getLogger(__name__)


class NotesBridge(QObject):
    """
    Bridge between Notes UI and backend API.
    """

    notesChanged = Signal()
    currentNoteChanged = Signal()
    errorOccurred = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)

        self._client: DataLoggerClient | None = None
        self._connected = False
        self._notes: list[dict[str, Any]] = []
        self._current_note: dict[str, Any] | None = None

        self._try_connect()

    def _try_connect(self) -> None:
        """Attempt to connect to the backend."""
        try:
            self._client = DataLoggerClient()
            # Test connection
            self._client.get_all_notes()
            self._connected = True
            logger.info("NotesBridge connected to Data Logger")
        except Exception as e:
            logger.debug(f"Data Logger not available: {e}")
            self._client = None
            self._connected = False

    @Property(bool, constant=True)  # type: ignore[arg-type]
    def connected(self) -> bool:
        return self._connected

    @Property("QVariantList", notify=notesChanged)  # type: ignore[arg-type]
    def notes(self) -> list[dict[str, Any]]:
        return self._notes

    @Property("QVariant", notify=currentNoteChanged)  # type: ignore[arg-type]
    def currentNote(self) -> dict[str, Any] | None:
        return self._current_note

    @Slot()  # type: ignore[arg-type]
    def loadNotes(self) -> None:
        """Load all notes from backend."""
        if not self._client:
            self._try_connect()

        if self._client:
            try:
                self._notes = self._client.get_all_notes()
                self.notesChanged.emit()
                logger.debug(f"Loaded {len(self._notes)} notes")
            except Exception as e:
                logger.error(f"Failed to load notes: {e}")
                self.errorOccurred.emit(str(e))
        else:
            # Mock data for offline mode
            self._notes = []
            self.notesChanged.emit()

    @Slot(int)  # type: ignore[arg-type]
    def loadNote(self, note_id: int) -> None:
        """Load a single note by ID."""
        if note_id < 0:
            # New note
            self._current_note = {"id": -1, "title": "", "content": ""}
            self.currentNoteChanged.emit()
            return

        if self._client:
            try:
                self._current_note = self._client.get_note(note_id)
                self.currentNoteChanged.emit()
            except Exception as e:
                logger.error(f"Failed to load note {note_id}: {e}")
                self.errorOccurred.emit(str(e))

    @Slot(str, str, result=int)  # type: ignore[arg-type]
    def createNote(self, title: str, content: str) -> int:
        """Create a new note. Returns the note ID or -1 on failure."""
        if self._client:
            try:
                result = self._client.create_note(title, content)
                note_id = result.get("note", {}).get("id", -1)
                self.loadNotes()  # Refresh list
                return note_id
            except Exception as e:
                logger.error(f"Failed to create note: {e}")
                self.errorOccurred.emit(str(e))
        return -1

    @Slot(int, str, str, result=bool)  # type: ignore[arg-type]
    def updateNote(self, note_id: int, title: str, content: str) -> bool:
        """Update an existing note."""
        if self._client and note_id >= 0:
            try:
                self._client.update_note(note_id, title, content)
                self.loadNotes()  # Refresh list
                return True
            except Exception as e:
                logger.error(f"Failed to update note {note_id}: {e}")
                self.errorOccurred.emit(str(e))
        return False

    @Slot(int, result=bool)  # type: ignore[arg-type]
    def deleteNote(self, note_id: int) -> bool:
        """Delete a note."""
        if self._client and note_id >= 0:
            try:
                self._client.delete_note(note_id)
                self.loadNotes()  # Refresh list
                return True
            except Exception as e:
                logger.error(f"Failed to delete note {note_id}: {e}")
                self.errorOccurred.emit(str(e))
        return False

    @Slot(int, str, str, result=int)  # type: ignore[arg-type]
    def saveNote(self, note_id: int, title: str, content: str) -> int:
        """Save a note (create if new, update if existing). Returns note ID."""
        if note_id < 0:
            return self.createNote(title, content)
        else:
            if self.updateNote(note_id, title, content):
                return note_id
            return -1
