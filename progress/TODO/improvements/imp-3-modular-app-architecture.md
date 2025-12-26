# Improvement: Modular App Architecture

**Category**: Improvements
**Task ID**: IMP-3
**Status**: TODO
**Started**: Not started
**Completed**: Not completed
**Priority**: High

## Description

Refactor the application architecture so that each app (Compass, Notes, Camera, etc.) is a self-contained, modular unit that can be developed, tested, and potentially installed/uninstalled independently. Currently, apps are tightly coupled QML pages nested directly in the UI folder with backend logic scattered across services. This improvement establishes clear boundaries and a consistent structure for all apps.

### Current State (Problems)

1. **Frontend**: Apps are just `.qml` files in `device/apps/ui/qml/` with no clear separation
2. **Backend**: App-specific logic is mixed into core services or scattered
3. **Dependencies**: No clear declaration of what each app requires
4. **Testing**: Apps cannot be tested in isolation
5. **Installation**: All apps are always present, no add/remove capability

### Target State (Goals)

1. **Self-contained apps**: Each app lives in its own directory with all assets
2. **Clear manifest**: Each app declares its dependencies, permissions, entry points
3. **Isolated backend**: App-specific backend logic packaged with the app
4. **Independent testing**: Apps can be unit tested without loading entire UI
5. **Plugin architecture**: Apps loaded dynamically, can be enabled/disabled
6. **Consistent structure**: All apps follow the same template

## Proposed App Structure

### Directory Layout

```
device/apps/
├── core/                        # Core UI framework (shell, navigation, theme)
│   ├── qml/
│   │   ├── AppShell.qml
│   │   ├── Home.qml
│   │   ├── StatusBar.qml
│   │   └── Theme.qml
│   ├── components/              # Shared UI components
│   │   ├── Button.qml
│   │   ├── Card.qml
│   │   └── ...
│   └── main.py                  # Core UI entry point
│
├── compass/                     # Compass app (example)
│   ├── manifest.json            # App metadata and dependencies
│   ├── qml/
│   │   ├── CompassMain.qml      # App entry point
│   │   └── components/          # App-specific components
│   ├── backend/
│   │   ├── __init__.py
│   │   └── compass_service.py   # App-specific backend logic
│   ├── assets/
│   │   └── compass_rose.svg
│   └── tests/
│       ├── test_compass_ui.py
│       └── test_compass_backend.py
│
├── notes/                       # Notes app
│   ├── manifest.json
│   ├── qml/
│   │   ├── NotesMain.qml
│   │   ├── NotesList.qml
│   │   └── NoteEditor.qml
│   ├── backend/
│   │   └── notes_service.py
│   └── tests/
│
├── camera/                      # Camera app
│   ├── manifest.json
│   ├── qml/
│   ├── backend/
│   └── tests/
│
└── ...                          # Other apps
```

### App Manifest Format

```json
{
  "id": "com.waycore.compass",
  "name": "Compass",
  "version": "1.0.0",
  "icon": "🧭",
  "entry": "qml/CompassMain.qml",
  "backend": "backend/compass_service.py",
  "permissions": [
    "sensors.magnetometer",
    "sensors.gps",
    "sensors.barometer"
  ],
  "dependencies": {
    "core": ">=1.0.0"
  },
  "enabled": true
}
```

## Implementation Phases

### Phase 1: Core Framework Extraction
- Extract shared components to `apps/core/`
- Create app loader mechanism
- Define manifest schema
- Implement basic app registration

### Phase 2: App Migration
- Migrate existing apps to new structure one by one
- Start with simplest app (e.g., Flashlight or Calendar)
- Document migration process
- Update each app to use manifest

### Phase 3: Backend Isolation
- Move app-specific backend logic to app directories
- Create app backend loader
- Define API patterns for app backends
- Handle service dependencies

### Phase 4: Dynamic Loading
- Implement app discovery from directories
- Enable/disable apps from settings
- Hot-reload capability (optional)
- App installation from packages (future)

## Technical Considerations

### App Loader

```python
class AppLoader:
    def __init__(self, apps_dir: Path):
        self.apps_dir = apps_dir
        self.apps: dict[str, AppManifest] = {}

    def discover_apps(self) -> list[AppManifest]:
        """Scan apps directory and load manifests."""
        apps = []
        for app_dir in self.apps_dir.iterdir():
            manifest_path = app_dir / "manifest.json"
            if manifest_path.exists():
                manifest = self._load_manifest(manifest_path)
                if manifest.enabled:
                    apps.append(manifest)
        return apps

    def get_app_entry(self, app_id: str) -> str:
        """Get QML entry point for an app."""
        return self.apps[app_id].entry
```

### QML App Registration

```qml
// Core loader registers discovered apps
Repeater {
    model: AppLoader.apps

    Loader {
        id: appLoader
        source: modelData.entry
        active: currentApp === modelData.id
    }
}
```

### Backend Integration

Each app's backend module should:
- Register API endpoints under `/api/apps/{app_id}/`
- Subscribe to relevant MQTT topics
- Expose a `start()` and `stop()` lifecycle

## Dependencies

- [ ] Stable core UI components
- [ ] App manifest schema defined

## Acceptance Criteria

- [ ] Core UI framework extracted to `apps/core/`
- [ ] App manifest schema defined and documented
- [ ] App loader discovers and registers apps
- [ ] At least 3 apps migrated to new structure
- [ ] Apps can be enabled/disabled from settings
- [ ] App-specific backends load with their apps
- [ ] Apps can be tested independently
- [ ] Migration guide documented for future apps
- [ ] Home grid dynamically populated from manifests

## Files to Create/Modify

- `device/apps/core/` - New core framework directory
- `device/apps/{app}/manifest.json` - App manifests
- `device/apps/{app}/` - Restructured app directories
- `device/apps/core/app_loader.py` - App discovery and loading
- `docs/developer/app-structure.md` - Documentation

## Tests Required

- [ ] Test app discovery finds all valid apps
- [ ] Test manifest validation
- [ ] Test app loading and unloading
- [ ] Test app backend registration
- [ ] Test Home grid reflects enabled apps
- [ ] Individual app tests in isolation

## Implementation Notes

{Add notes during implementation}

## Validation Commands

```bash
# Run core tests
pytest device/apps/core/tests/ -v

# Run individual app tests
pytest device/apps/compass/tests/ -v
pytest device/apps/notes/tests/ -v

# Verify app discovery
python -c "from device.apps.core.app_loader import AppLoader; print(AppLoader().discover_apps())"
```

## Completion Checklist

- [ ] Code implemented
- [ ] Tests written
- [ ] Tests passing
- [ ] Linting passing
- [ ] Documentation updated
- [ ] Migration guide written
- [ ] Files committed

## Blockers

None

## Related Tasks

- Enables: P-3.2 (Third-party app ecosystem)
- Related to: Current app implementations
- Future: App store / package installation
