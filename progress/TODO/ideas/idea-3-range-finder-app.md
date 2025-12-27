# Idea: Range Finder App

**Category**: Ideas
**Task ID**: IDEA-3
**Status**: TODO
**Started**: Not started
**Completed**: Not completed
**Priority**: Medium

## Description

Create a range finder app that combines distance sensor data with camera feed to measure and display distances to objects in the field of view. This tool would be invaluable for outdoor activities requiring distance estimation - hunting, surveying, photography, or navigation.

### Use Cases

1. **Hunting** - Estimate distance to target for accurate shot placement
2. **Photography** - Determine subject distance for lens selection and composition
3. **Surveying** - Quick distance measurements in the field
4. **Navigation** - Estimate distances to landmarks or waypoints
5. **Sports** - Measure distances for golf, archery, or other precision activities

### How It Works

1. User opens Range Finder app
2. Camera view displays with distance overlay
3. Distance sensor provides real-time readings
4. Crosshair or target indicator shows measurement point
5. Distance displayed prominently on screen
6. Optional: Tap to freeze/save measurement

## Feature Components

### Camera View
- Full-screen camera feed as background
- Crosshair or target reticle overlay (centered)
- Semi-transparent distance readout
- Clean, minimal UI to maximize camera view

### Distance Display
- Large, readable distance value
- Unit toggle (meters/feet/yards)
- Accuracy indicator if available
- Min/max range indicator

### Measurement Controls
- Hold/freeze current measurement
- Save measurement with screenshot
- Clear/reset functionality
- Unit switching

### Optional Enhancements
- Multiple measurement points
- Angle compensation for elevation differences
- Height estimation (using trigonometry)
- History of recent measurements

## Acceptance Criteria

- [ ] Range Finder app accessible from Home grid
- [ ] Camera feed displays as background
- [ ] Crosshair/reticle overlay visible
- [ ] Distance sensor data displayed in real-time
- [ ] Distance updates smoothly (not jumpy)
- [ ] Unit toggle between meters/feet/yards
- [ ] Hold button freezes current measurement
- [ ] Clear returns to live measurement mode
- [ ] Works in both portrait and landscape
- [ ] UI readable in bright outdoor conditions

## Files to Create/Modify

- `device/apps/ui/qml/RangeFinder.qml` - Main range finder UI
- `device/apps/ui/qml/Home.qml` - Add Range Finder app to grid (📏 or 🎯 icon)
- `device/apps/ui/qml/AppShell.qml` - Add range finder navigation
- `device/apps/ui/qml/qmldir` - Register RangeFinder component
- May need distance sensor driver in `device/drivers/`

## Technical Notes

### Distance Sensor Integration

The app will need to integrate with a distance sensor (e.g., ultrasonic, laser, or ToF sensor):
- Read distance data via sensor bridge
- Handle sensor calibration
- Manage sensor range limits (min/max distances)
- Graceful handling when sensor unavailable

### Camera Overlay

```qml
Item {
    // Camera feed
    Camera {
        id: camera
    }
    VideoOutput {
        source: camera
        anchors.fill: parent
    }

    // Crosshair overlay
    Canvas {
        anchors.centerIn: parent
        // Draw crosshair/reticle
    }

    // Distance display
    Rectangle {
        anchors.bottom: parent.bottom
        color: Qt.rgba(0, 0, 0, 0.7)

        Text {
            text: distanceValue.toFixed(1) + " " + unit
            font.pixelSize: 48
            color: "white"
        }
    }
}
```

### Unit Conversions

```javascript
function convertDistance(meters, targetUnit) {
    switch (targetUnit) {
        case "ft": return meters * 3.28084;
        case "yd": return meters * 1.09361;
        case "m":
        default: return meters;
    }
}
```

## Implementation Notes

{Add notes during implementation}

## Validation Commands

```bash
# Run the UI application
cd device/apps/ui && python main.py

# Navigate to Range Finder app
# Point at objects and verify distance readings
```

## Completion Checklist

- [ ] Code implemented
- [ ] Tests written
- [ ] Tests passing
- [ ] Linting passing
- [ ] Documentation updated
- [ ] Files committed

## Blockers

- Requires distance sensor hardware/driver

## Related Tasks

- Depends on: Camera Service (Phase 14)
- Depends on: Distance sensor driver (not yet implemented)
- Related to: Compass app (sensor integration patterns)
