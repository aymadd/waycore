# Improvement: Automated Localization Framework

**Category**: Improvements
**Task ID**: IMP-6
**Status**: TODO
**Started**: Not started
**Completed**: Not completed
**Priority**: High (Structural)

## Description

Currently, the Waycore UI uses hardcoded English strings. While manual translation is possible, it is brittle and hard to maintain as the codebase evolves rapidly. A structural approach is needed to ensure localization (l10n) scales with development.

This improvement focuses on implementing an automated localization framework that:
- Wraps UI strings in `qsTr()` for Qt/QML compatibility.
- Provides a script to automatically extract these strings into translation files (`.ts` / `.qm`).
- Tracks translation coverage programmatically (as demonstrated in `scripts/generate-summary.py`).
- Supports Right-to-Left (RTL) layouts for Arabic and other languages.

### Current Behavior
- Strings are hardcoded (e.g., `text: "Settings"`).
- No mechanism to switch languages.
- No RTL support for Arabic layouts.

### Expected Behavior
- Strings are wrapped (e.g., `text: qsTr("Settings")`).
- A `scripts/update-translations.py` tool scans the codebase and updates translation source files.
- The UI detects system language or allows manual toggling.
- Layouts automatically mirror (RTL) when Arabic is selected.

## Technical Approaches

### 1. QML String Wrapping
Systematically refactor QML files to wrap user-visible text in `qsTr()`.
- Use a regex-based script to identify hardcoded strings in `Text`, `Label`, `Button`, etc.
- Ignore property keys and log strings.

### 2. Qt Translation Tools (lupdate/lrelease)
Integrate Qt's standard localization tools into the `scripts/` directory.
- `lupdate`: Scans QML/Python files and generates `.ts` (XML) files.
- `lrelease`: Compiles `.ts` files into binary `.qm` files for efficient loading.
- Create `scripts/update-translations.py` to wrap these commands for developer ease.

### 3. RTL Layout Support
Implement a global `LayoutMirroring` manager in `Main.qml`.
- Bind `LayoutMirroring.enabled` and `LayoutMirroring.childrenInherit` to the active language direction.
- Ensure icons (like back arrows) flip correctly or are swapped.

## Acceptance Criteria

- [ ] All user-facing strings in `device/apps/ui/qml/` are wrapped in `qsTr()`.
- [ ] A `locales/` directory is established with `waycore_ar.ts` and `waycore_en.ts`.
- [ ] `scripts/update-translations.py` successfully extracts new strings.
- [ ] UI Settings allow switching between English and Arabic.
- [ ] Arabic interface correctly mirrors layout (RTL).
- [ ] CI pipeline (summary generator) tracks % of translated strings.

## Files to Modify

- `device/apps/ui/qml/**/*.qml` - String wrapping.
- `device/apps/ui/main.py` - Load translation binaries (`.qm`).
- `device/apps/ui/qml/SettingsGeneral.qml` - Add language selector.
- `scripts/` - Add translation automation scripts.

## Tests Required

- [ ] Manual verification: Switch language to Arabic -> UI Text updates.
- [ ] Manual verification: Switch language to Arabic -> UI Layout mirrors (RTL).
- [ ] Script verification: Add a new dummy button with `qsTr("Test")`, run script -> "Test" appears in `.ts` file.

## Implementation Notes

This task prepares the architecture for "Production Phase" localization without slowing down current feature development.

## Validation Commands

```bash
# Update translations
python scripts/update-translations.py

# Run UI
cd device/apps/ui && python main.py
```

## Completion Checklist

- [ ] Code implemented
- [ ] Tests written
- [ ] Tests passing
- [ ] Linting passing
- [ ] Documentation updated
- [ ] Files committed

## Blockers

None
