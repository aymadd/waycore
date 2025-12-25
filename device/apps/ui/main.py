"""
Waycore UI Application Entry Point

Launches the Qt/QML application for the Waycore device interface.
Supports QML hot reload in development mode.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import QFileSystemWatcher, QObject, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from .notes_bridge import NotesBridge
from .sensor_bridge import SensorBridge

# Development mode settings (disable QML caching for hot reload)
DEV_MODE = os.getenv("WAYCORE_DEV", "1") == "1"

if DEV_MODE:
    os.environ["QML_DISK_CACHE_DISABLE"] = "1"
    os.environ["QML_DISABLE_DISK_CACHE"] = "1"

# Enable Qt Virtual Keyboard for touchscreen input
os.environ["QT_IM_MODULE"] = "qtvirtualkeyboard"


class QmlReloader(QObject):
    """Watches QML files and triggers reload on changes."""

    reloadRequested = Signal()

    def __init__(self, qml_dir: Path, engine: QQmlApplicationEngine) -> None:
        super().__init__()
        self._engine = engine
        self._qml_dir = qml_dir
        self._main_qml = qml_dir / "Main.qml"

        # Set up file watcher
        self._watcher = QFileSystemWatcher(self)
        self._watch_qml_files()
        self._watcher.fileChanged.connect(self._on_file_changed)
        self._watcher.directoryChanged.connect(self._on_directory_changed)

        print(f"🔥 QML Hot Reload enabled - watching {qml_dir}")

    def _watch_qml_files(self) -> None:
        """Add all QML files to the watcher."""
        # Watch the directory for new files
        self._watcher.addPath(str(self._qml_dir))
        self._watcher.addPath(str(self._qml_dir / "components"))

        # Watch individual QML files
        for qml_file in self._qml_dir.rglob("*.qml"):
            self._watcher.addPath(str(qml_file))

    @Slot(str)  # type: ignore[arg-type]
    def _on_file_changed(self, path: str) -> None:
        """Handle file change - reload QML."""
        print(f"📝 File changed: {Path(path).name}")

        # Re-add the file to watcher (Qt removes it after change)
        if not self._watcher.files() or path not in self._watcher.files():
            self._watcher.addPath(path)

        self._reload()

    @Slot(str)  # type: ignore[arg-type]
    def _on_directory_changed(self, path: str) -> None:
        """Handle directory change - check for new files."""
        self._watch_qml_files()

    def _reload(self) -> None:
        """Reload the QML engine."""
        print("🔄 Reloading QML...")

        # Clear the QML cache
        self._engine.clearComponentCache()

        # Get the root object and reload
        root_objects = self._engine.rootObjects()
        if root_objects:
            root = root_objects[0]
            # Store window geometry
            geometry = (root.x(), root.y(), root.width(), root.height())

            # Destroy old root
            root.close()
            root.deleteLater()

        # Reload main QML
        qml_url = QUrl.fromLocalFile(str(self._main_qml))
        self._engine.load(qml_url)

        # Restore window geometry
        new_roots = self._engine.rootObjects()
        if new_roots and "geometry" in dir():
            new_root = new_roots[-1]  # Get the newly loaded root
            new_root.setX(geometry[0])
            new_root.setY(geometry[1])
            new_root.setWidth(geometry[2])
            new_root.setHeight(geometry[3])

        print("✅ QML reloaded!")


def main() -> int:
    """
    Main entry point for the Waycore UI application.

    Environment variables:
        WAYCORE_DEV: Set to "1" to enable QML hot reload (default: "1")
        CORE_DAEMON_URL: HTTP URL for Core Daemon (default: http://localhost:8000)
        DATA_LOGGER_URL: HTTP URL for Data Logger (default: http://localhost:8002)

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    app = QGuiApplication(sys.argv)
    app.setApplicationName("Waycore")
    app.setOrganizationName("Waycore")

    engine = QQmlApplicationEngine()

    # Create and register bridges for backend communication
    sensor_bridge = SensorBridge()
    notes_bridge = NotesBridge()
    engine.rootContext().setContextProperty("SensorBridge", sensor_bridge)
    engine.rootContext().setContextProperty("NotesBridge", notes_bridge)

    # Get the QML directory path
    qml_dir = Path(__file__).parent / "qml"
    qml_dir_absolute = qml_dir.resolve()

    # Add the QML directory as an import path
    engine.addImportPath(str(qml_dir_absolute))

    # Load the main QML file
    qml_file = qml_dir_absolute / "Main.qml"
    if not qml_file.exists():
        print(f"Error: QML file not found at {qml_file}", file=sys.stderr)
        return 1

    qml_url = QUrl.fromLocalFile(str(qml_file))
    engine.load(qml_url)

    if not engine.rootObjects():
        print("Error: Failed to load QML root object", file=sys.stderr)
        return -1

    # Set up QML hot reload in dev mode
    reloader = None
    if DEV_MODE:
        reloader = QmlReloader(qml_dir_absolute, engine)
        # Keep reference to prevent garbage collection
        engine.rootContext().setContextProperty("_reloader", reloader)

    return int(app.exec())


if __name__ == "__main__":
    sys.exit(main())
