# Improvement: Click-to-Copy & Text Selection

**Category**: Improvements
**Task ID**: IMP-4
**Status**: TODO
**Started**: Not started
**Completed**: Not completed
**Priority**: Medium

## Description

Implement a click-to-copy and highlight-to-copy functionality throughout the UI, similar to iOS text selection behavior. This allows users to easily copy coordinates, sensor readings, messages, and other text content to share or use elsewhere.

### Use Cases

1. **Copy GPS Coordinates** - Tap coordinates in Compass to copy for sharing
2. **Copy Sensor Readings** - Copy altitude, temperature, etc. for logging
3. **Copy Messages** - Select and copy text from Meshtastic messages
4. **Copy Error Messages** - Copy error details for troubleshooting
5. **Copy AI Responses** - Select portions of AI assistant responses

### Features

1. **Tap-to-Copy (Quick Copy)**
   - Single tap on copyable elements shows "Copied!" feedback
   - Works for discrete values: coordinates, readings, IDs
   - Visual indicator (icon or styling) shows element is copyable
   - Haptic feedback on copy (if available)

2. **Long-Press Text Selection**
   - Long press to enter selection mode
   - Drag handles to adjust selection
   - Selection toolbar appears with Copy button
   - Works for multi-line text: notes, messages, AI responses

3. **Visual Feedback**
   - Toast/snackbar notification: "Copied to clipboard"
   - Brief highlight animation on copied element
   - Selection highlight color matching theme

4. **Copyable Elements**
   - GPS coordinates (lat, lon, altitude)
   - Sensor readings with units
   - Node IDs and addresses
   - Message content
   - Notes content
   - AI responses
   - Error messages and logs

## UI Design

### Tap-to-Copy Indicator
```
┌─────────────────────────────────┐
│ Coordinates           📋        │
│ 40.7128° N, 74.0060° W         │
└─────────────────────────────────┘
         ↓ (tap)
┌─────────────────────────────────┐
│ ✓ Copied to clipboard          │
└─────────────────────────────────┘
```

### Text Selection Mode
```
┌─────────────────────────────────┐
│ AI Response:                    │
│                                 │
│ The ●━━━━━━━━━━━━● is about    │
│      [selected text]            │
│ 50 km to the northeast...       │
│                                 │
│        [Copy] [Select All]      │
└─────────────────────────────────┘
```

## Implementation

### QML Copyable Text Component

```qml
// components/CopyableText.qml
Item {
    id: root
    property string text: ""
    property bool showCopyIcon: true

    signal copied()

    Row {
        spacing: Theme.spacingSmall

        Text {
            text: root.text
            color: Theme.textPrimary
        }

        Image {
            visible: showCopyIcon
            source: "icons/copy.svg"
            opacity: 0.5

            MouseArea {
                anchors.fill: parent
                onClicked: copyToClipboard()
            }
        }
    }

    function copyToClipboard() {
        clipboard.setText(root.text)
        toast.show("Copied to clipboard")
        root.copied()
    }
}
```

### QML Text Selection Component

```qml
// components/SelectableText.qml
TextEdit {
    id: textEdit
    readOnly: true
    selectByMouse: true
    selectionColor: Theme.accent
    selectedTextColor: Theme.textPrimary

    // Long press to show selection handles
    MouseArea {
        anchors.fill: parent
        onPressAndHold: {
            textEdit.selectAll()
            copyToolbar.visible = true
        }
    }

    // Copy toolbar
    Rectangle {
        id: copyToolbar
        visible: false
        // ... Copy button implementation
    }
}
```

### Python Clipboard Bridge

```python
# clipboard_bridge.py
from PySide6.QtCore import QObject, Slot
from PySide6.QtGui import QClipboard, QGuiApplication

class ClipboardBridge(QObject):
    @Slot(str)
    def copy(self, text: str) -> None:
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(text)

    @Slot(result=str)
    def paste(self) -> str:
        clipboard = QGuiApplication.clipboard()
        return clipboard.text()
```

## Acceptance Criteria

- [ ] CopyableText component created and styled
- [ ] SelectableText component with selection handles
- [ ] Clipboard bridge for Python/QML integration
- [ ] Tap-to-copy works on coordinates in Compass
- [ ] Tap-to-copy works on sensor readings
- [ ] Text selection works in Notes app
- [ ] Text selection works in AI chat responses
- [ ] Text selection works in Meshtastic messages
- [ ] "Copied" toast notification appears
- [ ] Visual feedback on copy action
- [ ] Copy icon indicates copyable elements
- [ ] Works with both mouse and touch input

## Files to Create/Modify

- `device/apps/ui/qml/components/CopyableText.qml` - New reusable component
- `device/apps/ui/qml/components/SelectableText.qml` - New selectable text component
- `device/apps/ui/qml/components/CopyToast.qml` - Toast notification component
- `device/apps/ui/clipboard_bridge.py` - Python clipboard access
- `device/apps/ui/main.py` - Register clipboard bridge
- `device/apps/ui/qml/Compass.qml` - Use CopyableText for coordinates
- `device/apps/ui/qml/SensorData.qml` - Use CopyableText for readings
- `device/apps/ui/qml/AIChat.qml` - Use SelectableText for responses
- `device/apps/ui/qml/NoteEditor.qml` - Enable text selection
- `device/apps/ui/qml/MeshConversation.qml` - Use SelectableText for messages

## Tests Required

- [ ] Manual verification: Tap-to-copy on coordinates
- [ ] Manual verification: Tap-to-copy shows toast
- [ ] Manual verification: Long-press enables selection
- [ ] Manual verification: Selection handles work
- [ ] Manual verification: Copy from selection works
- [ ] Manual verification: Works on touch devices
- [ ] Unit test: ClipboardBridge.copy() works
- [ ] Unit test: ClipboardBridge.paste() works

## Validation Commands

```bash
# Run the UI application
cd device/apps/ui && python main.py

# Test in Compass - tap coordinates
# Test in AI Chat - select response text
# Test in Notes - select note content
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

## Related Tasks

- Related to: All apps with text content
- Enables: Better UX for sharing coordinates/data
- Future: Share functionality (share to Meshtastic, etc.)
