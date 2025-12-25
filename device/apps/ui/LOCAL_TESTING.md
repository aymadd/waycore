# Local Testing Guide for Waycore UI

This guide provides step-by-step instructions for setting up and testing the Waycore UI application on your local machine (macOS).

## Prerequisites

- Python 3.11 or higher
- Poetry (for dependency management)
- macOS (this guide is tailored for macOS, but similar steps apply to Linux)

## Step 1: Install Qt6 and PySide6 Dependencies

### Option A: Using Homebrew (Recommended for macOS)

1. **Install Homebrew** (if not already installed):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install Qt6**:
   ```bash
   brew install qt@6
   ```

3. **Add Qt to your PATH**:
   ```bash
   echo 'export PATH="/opt/homebrew/opt/qt@6/bin:$PATH"' >> ~/.zshrc
   source ~/.zshrc
   ```

   **Note**: If you're on an Intel Mac, the path will be `/usr/local/opt/qt@6/bin` instead.

4. **Verify Qt installation**:
   ```bash
   qmake6 --version
   # Should show Qt version 6.x.x
   ```

### Option B: Using Qt Installer (Alternative)

1. **Download Qt6**:
   - Visit https://www.qt.io/download-qt-installer
   - Download the Qt Online Installer for macOS

2. **Install Qt6**:
   - Run the installer
   - Select "Qt 6.x.x" (latest stable version)
   - Select components: Qt 6.x.x for macOS
   - Complete the installation

3. **Add Qt to PATH**:
   ```bash
   # Find your Qt installation path (usually ~/Qt/6.x.x/macos/bin)
   echo 'export PATH="$HOME/Qt/6.x.x/macos/bin:$PATH"' >> ~/.zshrc
   source ~/.zshrc
   ```

### Option C: Using Conda (If you use Conda)

```bash
conda install -c conda-forge qt-main pyqt
```

## Step 2: Install Python Dependencies

1. **Navigate to the project root**:
   ```bash
   cd /path/to/waycore/pyb
   ```

2. **Install dependencies with Poetry**:
   ```bash
   poetry install
   ```

   This will install:
   - PySide6 (Qt6 Python bindings)
   - All other project dependencies

3. **Verify PySide6 installation**:
   ```bash
   poetry run python -c "from PySide6.QtCore import __version__; print(__version__)"
   ```

   Should output the Qt version (e.g., `6.10.1`).

## Step 3: Test the UI Application

### Quick Test

Run the UI application directly:

```bash
poetry run python -m device.apps.ui.main
```

Or use the script entry point:

```bash
poetry run waycore-ui
```

### Expected Behavior

- A window should open with the Waycore UI
- You should see:
  - Status bar at the top
  - Navigation buttons (Home, Settings, Back)
  - Home screen with app tiles (AI, Map, Settings)

### Troubleshooting

#### Issue: "Cannot find Qt platform plugin"

**Solution**: Set the Qt plugin path explicitly:

```bash
export QT_PLUGIN_PATH="/opt/homebrew/opt/qt@6/plugins"
poetry run waycore-ui
```

Or for Intel Macs:
```bash
export QT_PLUGIN_PATH="/usr/local/opt/qt@6/plugins"
poetry run waycore-ui
```

#### Issue: "ModuleNotFoundError: No module named 'PySide6'"

**Solution**: Make sure you're using Poetry's virtual environment:

```bash
poetry install  # Reinstall dependencies
poetry shell     # Activate the virtual environment
python -m device.apps.ui.main
```

#### Issue: Window appears but is blank/white

**Solution**: Check QML file paths. The application looks for QML files relative to the `qml/` directory. Make sure you're running from the project root.

#### Issue: "QML module not found"

**Solution**: Verify QML import paths. The application should automatically add the correct import paths, but you can debug by checking:

```bash
poetry run python -c "
from pathlib import Path
qml_dir = Path('device/apps/ui/qml')
print(f'QML directory exists: {qml_dir.exists()}')
print(f'Main.qml exists: {(qml_dir / \"Main.qml\").exists()}')
"
```

## Step 4: Development Workflow

### Running with Auto-Reload (Recommended for Development)

For faster development iteration, you can use a file watcher. However, Qt/QML doesn't have built-in hot-reload. You'll need to:

1. **Make changes to QML files**
2. **Restart the application** to see changes

### Testing Different Screen Sizes

The UI is designed for 480×800 (portrait). To test different sizes, you can modify `Main.qml` temporarily:

```qml
Window {
    id: root
    width: 800   // Change for testing
    height: 600  // Change for testing
    // ...
}
```

### Debugging QML

Enable QML debugging by setting environment variables:

```bash
export QML_IMPORT_TRACE=1
export QT_LOGGING_RULES="*.debug=true"
poetry run waycore-ui
```

This will show:
- QML import traces
- Debug messages from QML

## Step 5: Testing with Backend Services (Optional)

To test the full integration with backend services:

1. **Start the backend services** (in separate terminals):
   ```bash
   # Terminal 1: Start MQTT
   docker compose -f docker/compose/dev.yml up -d mqtt

   # Terminal 2: Start core services
   docker compose -f docker/compose/dev.yml up -d --build core-daemon module-manager comms-bridge
   ```

2. **Verify services are running**:
   ```bash
   curl http://localhost:8000/health  # core-daemon
   curl http://localhost:8001/health  # module-manager
   ```

3. **Run the UI** (it will connect via Unix domain sockets when services are available):
   ```bash
   poetry run waycore-ui
   ```

## Common Commands Reference

```bash
# Install dependencies
poetry install

# Run UI application
poetry run waycore-ui

# Run with Python module syntax
poetry run python -m device.apps.ui.main

# Check Qt version
poetry run python -c "from PySide6.QtCore import __version__; print(__version__)"

# Verify QML files exist
ls -la device/apps/ui/qml/

# Activate Poetry shell (for interactive development)
poetry shell
```

## Next Steps

- Modify QML files in `device/apps/ui/qml/` to customize the UI
- Add new screens by creating QML files and updating navigation
- Connect to backend services using the `api_client.py` module
- See `device/apps/ui/README.md` for UI architecture details

## Platform-Specific Notes

### macOS

- Qt6 via Homebrew is the recommended approach
- If you encounter permission issues, you may need to allow the app in System Preferences > Security & Privacy
- On Apple Silicon (M1/M2), use `/opt/homebrew/opt/qt@6`
- On Intel Macs, use `/usr/local/opt/qt@6`

### Linux

- Install Qt6 via your package manager:
  ```bash
  # Ubuntu/Debian
  sudo apt-get install qt6-base-dev qt6-declarative-dev

  # Fedora
  sudo dnf install qt6-qtbase-devel qt6-qtdeclarative-devel
  ```

### Windows

- Download and install Qt6 from https://www.qt.io/download
- Add Qt bin directory to PATH
- Use PowerShell or Command Prompt (not WSL for Qt applications)

## Troubleshooting Summary

| Issue | Solution |
|-------|----------|
| Qt not found | Install Qt6 via Homebrew or Qt Installer |
| PySide6 not found | Run `poetry install` |
| Blank window | Check QML file paths, verify imports |
| Import errors | Ensure you're running from project root |
| Permission denied | Check macOS Security & Privacy settings |

## Getting Help

- Check Qt documentation: https://doc.qt.io/qt-6/
- PySide6 documentation: https://doc.qt.io/qtforpython/
- QML documentation: https://doc.qt.io/qt-6/qtqml-index.html
