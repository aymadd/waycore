# Improvement: Unified & Polished UI Experience

**Category**: Improvements
**Task ID**: IMP-4
**Status**: TODO
**Started**: Not started
**Completed**: Not completed
**Priority**: High

## Description

Implement a cohesive, field-ready UI experience based on the design principles in `local_plan/13-ui-ideas.md`. The current UI has functional components but lacks the unified, stress-tested design needed for outdoor use. This improvement focuses on making the UI work reliably with wet hands, gloves, in sunlight, and under stress.

### Target Specifications

- **Resolution**: 480 × 800 px (portrait)
- **Physical size**: ~4.0–4.3"
- **Interaction**: Touch-first, usable with wet hands/gloves
- **Viewing conditions**: Sunlight, low light, rain, cold
- **User state**: Moving, tired, stressed, possibly in emergency
- **Design priority**: Fast recognition > density > beauty

## Key Improvements

### 1. Status Bar Redesign

**Current**: Basic time and battery display
**Target**: Always-visible, information-dense status strip

```
┌────────────────────────────────────────────────┐
│ [🔋 78%] [🕒 14:32] [🌡️ 18°C]    [📶] [🛜] [🛰] │
└────────────────────────────────────────────────┘
```

- Height: 56-64px (not smaller)
- Icons + numbers, no text labels
- High contrast, no animations
- Status-only (long-press for details)
- Left: Battery, Time, Temperature
- Right: LTE, WiFi, GPS indicators

### 2. App Grid Optimization

**Current**: 3-column grid with many apps
**Target**: 2×3 primary grid with tier system

```
┌──────────────┬──────────────┐
│   🚨 SOS     │  💬 Messages │
├──────────────┼──────────────┤
│   🗺️ Map     │  📷 Identify │
├──────────────┼──────────────┤
│   🤖 AI      │  ⚙️ System   │
└──────────────┴──────────────┘
```

**Tier 1 (Home Screen)** — Always visible:
- SOS
- Messages (Meshtastic)
- Map
- Identify/Scan
- AI
- System

**Tier 2 (Inside System/subpages)**:
- Notes, Compass, Camera, Gallery
- Sensors, Logs, Modules
- Settings, Integrations

### 3. Quick Action Strip

**Current**: None
**Target**: Bottom strip for instant critical actions

```
┌────────────────────────────────────────────────┐
│  [🔦 FLASH]  [📶 COMMS]  [🛑 LOCK]  [⚡ POWER] │
└────────────────────────────────────────────────┘
```

- Height: 80-96px
- Critical actions without leaving current app
- Muscle memory friendly
- Optional but highly recommended

### 4. App Tile Design

```
┌──────────────────┐
│      ICON        │  (centered, bold, arm's length readable)
│                  │
│     LABEL        │  (ALL CAPS, ≤10 chars)
└──────────────────┘
```

- Large touch targets (minimum 100×100px)
- Works with gloves
- No accidental taps
- Color usage:
  - SOS = Red
  - Warnings = Amber
  - Everything else = Grayscale/muted green

### 5. Navigation Model Simplification

**Remove**:
- ❌ App drawer patterns
- ❌ Swipe-heavy gestures
- ❌ Multi-level hamburger menus

**Implement**:
- ✅ Home = App grid (physical button)
- ✅ Back = Top-left or edge gesture
- ✅ Long-press = Secondary actions
- ✅ Physical button = Home / SOS

### 6. Typography & Contrast

- Sans-serif, heavy weights only
- No thin fonts
- Dark UI by default
- Daylight mode option
- No pure black (use dark gray: #1A1F1C)
- High contrast text (#E8F0EC on dark)

## Layout Structure

```
┌────────────────────────────────┐
│ STATUS BAR (fixed, always on)  │  ~64 px
├────────────────────────────────┤
│                                │
│        APP GRID AREA           │  ~640 px
│                                │
│   (primary interaction zone)   │
│                                │
├────────────────────────────────┤
│ QUICK ACTION STRIP (optional)  │  ~96 px
└────────────────────────────────┘
```

## Dependencies

- [ ] Stable app architecture
- [ ] Core UI components

## Acceptance Criteria

### Status Bar
- [ ] Redesigned to 56-64px height
- [ ] Battery percentage with icon
- [ ] Time in 24h format
- [ ] Temperature display
- [ ] LTE/WiFi/GPS connectivity indicators
- [ ] High contrast, no animations
- [ ] Long-press shows detailed status

### App Grid
- [ ] 2×3 layout for Tier 1 apps
- [ ] Large touch targets (100×100px minimum)
- [ ] Icon + ALL CAPS label per tile
- [ ] SOS tile in red
- [ ] System tile leads to Tier 2 apps
- [ ] Glove-friendly spacing

### Quick Action Strip
- [ ] Bottom strip with 4 quick actions
- [ ] Flashlight toggle
- [ ] Comms quick access
- [ ] Screen lock
- [ ] Power options
- [ ] Visible from any screen (overlay or persistent)

### Navigation
- [ ] Simple back navigation (top-left)
- [ ] Long-press context menus where appropriate
- [ ] No swipe gestures required for basic navigation
- [ ] Home button returns to grid

### Visual Polish
- [ ] Consistent use of Theme.qml colors
- [ ] Heavy font weights throughout
- [ ] Proper spacing and alignment
- [ ] Daylight/high-contrast mode option

## Files to Create/Modify

- `device/apps/ui/qml/StatusBar.qml` - Redesigned status bar
- `device/apps/ui/qml/Home.qml` - 2×3 grid with tiers
- `device/apps/ui/qml/QuickActionStrip.qml` - New bottom strip
- `device/apps/ui/qml/SystemHub.qml` - Tier 2 app launcher
- `device/apps/ui/qml/AppTile.qml` - Standardized tile component
- `device/apps/ui/qml/Theme.qml` - Updated spacing/sizing
- `device/apps/ui/qml/components/` - Updated shared components

## Implementation Notes

### Status Bar Component

```qml
Rectangle {
    height: 64
    color: App.Theme.primaryDark

    Row {
        anchors.left: parent.left
        anchors.leftMargin: App.Theme.spacingMedium
        spacing: App.Theme.spacingLarge

        // Battery
        Row {
            spacing: 4
            Text { text: "🔋"; font.pixelSize: 20 }
            Text { text: batteryPercent + "%"; color: App.Theme.textPrimary; font.bold: true }
        }

        // Time
        Text { text: currentTime; color: App.Theme.textPrimary; font.bold: true; font.pixelSize: 18 }

        // Temperature
        Row {
            spacing: 4
            Text { text: "🌡️"; font.pixelSize: 18 }
            Text { text: temperature + "°C"; color: App.Theme.textPrimary }
        }
    }

    Row {
        anchors.right: parent.right
        anchors.rightMargin: App.Theme.spacingMedium
        spacing: App.Theme.spacingMedium

        // Connectivity indicators
        Text { text: "📶"; opacity: hasLTE ? 1.0 : 0.3 }
        Text { text: "🛜"; opacity: hasWiFi ? 1.0 : 0.3 }
        Text { text: "🛰"; opacity: hasGPS ? 1.0 : 0.3 }
    }
}
```

### Quick Action Strip

```qml
Rectangle {
    height: 96
    color: App.Theme.surface

    Row {
        anchors.centerIn: parent
        spacing: App.Theme.spacingLarge

        QuickAction { icon: "🔦"; label: "FLASH"; onClicked: toggleFlashlight() }
        QuickAction { icon: "📶"; label: "COMMS"; onClicked: openCommsQuick() }
        QuickAction { icon: "🛑"; label: "LOCK"; onClicked: lockScreen() }
        QuickAction { icon: "⚡"; label: "POWER"; onClicked: showPowerMenu() }
    }
}
```

## Validation Commands

```bash
# Run the UI application
cd device/apps/ui && python main.py

# Test at target resolution
# Verify touch targets are large enough
# Test in different lighting conditions (if possible)
```

## Completion Checklist

- [ ] Code implemented
- [ ] Tests written
- [ ] Tests passing
- [ ] Linting passing
- [ ] Documentation updated
- [ ] Design review completed
- [ ] Files committed

## Blockers

None

## Related Tasks

- Related to: All UI tasks
- Reference: `local_plan/13-ui-ideas.md`
- Affects: Home, StatusBar, all app screens
