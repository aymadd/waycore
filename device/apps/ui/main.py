"""
Waycore UI Application Entry Point

Launches the Qt/QML application for the Waycore device interface.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from .sensor_bridge import SensorBridge


def main() -> int:
    """
    Main entry point for the Waycore UI application.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    app = QGuiApplication(sys.argv)
    app.setApplicationName("Waycore")
    app.setOrganizationName("Waycore")

    engine = QQmlApplicationEngine()

    # Create and register the sensor bridge for backend communication
    sensor_bridge = SensorBridge()
    engine.rootContext().setContextProperty("SensorBridge", sensor_bridge)

    # Get the QML directory path
    qml_dir = Path(__file__).parent / "qml"
    qml_dir_absolute = qml_dir.resolve()

    # Add the QML directory as an import path so relative imports work
    # This allows imports like "Theme.qml" to be resolved relative to the qml directory
    engine.addImportPath(str(qml_dir_absolute))

    # Load the main QML file using QUrl for proper path resolution
    qml_file = qml_dir_absolute / "Main.qml"
    if not qml_file.exists():
        print(f"Error: QML file not found at {qml_file}", file=sys.stderr)
        return 1

    # Use QUrl.fromLocalFile to ensure proper path resolution
    # This sets the base URL correctly so relative imports in Main.qml work
    qml_url = QUrl.fromLocalFile(str(qml_file))
    engine.load(qml_url)

    if not engine.rootObjects():
        print("Error: Failed to load QML root object", file=sys.stderr)
        return -1

    return int(app.exec())


if __name__ == "__main__":
    sys.exit(main())
