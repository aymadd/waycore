# Idea: App Loading Screen

**Category**: Ideas
**Task ID**: IDEA-2
**Status**: TODO
**Started**: Not started
**Completed**: Not completed
**Priority**: Medium

## Description

Create a polished loading/splash screen that displays during app startup while backend services are initializing. This provides visual feedback to the user that the app is loading and establishes brand identity from the first moment of interaction.

### Current Behavior

The app currently launches directly into the main UI, which may show incomplete data or loading states while backend services connect. This can feel jarring or unpolished.

### Proposed Behavior

1. App launches and immediately shows a branded splash screen
2. Splash screen displays Waycore logo with subtle animation
3. Optional loading progress indicator or status messages
4. Once backend services are connected and ready, transition smoothly to main UI
5. If connection fails, show error state with retry option

### Use Cases

1. **First Impression** - Professional loading screen creates positive first impression
2. **Feedback** - User knows the app is working, not frozen
3. **Branding** - Reinforces Waycore identity
4. **Graceful Degradation** - Handle slow startup or connection issues elegantly

## Feature Components

### Splash Screen UI
- Waycore logo (centered, properly sized)
- Subtle animation (fade in, pulse, or logo animation)
- Loading indicator (spinner, progress bar, or animated dots)
- Optional status text ("Connecting to services...", "Loading sensors...")
- Background matching app theme

### Service Connection Logic
- Check connection status of backend services
- Track which services are ready (core daemon, comms bridge, etc.)
- Timeout handling for slow/failed connections
- Retry mechanism for transient failures

### Transition Animation
- Smooth fade or slide transition to main app
- No jarring jump between screens

### Error Handling
- Connection timeout message
- Retry button
- Option to continue in offline/limited mode

## Acceptance Criteria

- [ ] Splash screen appears immediately on app launch
- [ ] Waycore logo displayed prominently
- [ ] Loading animation provides visual feedback
- [ ] Splash screen waits for backend services to be ready
- [ ] Smooth transition to main UI when ready
- [ ] Timeout after reasonable period (e.g., 10 seconds)
- [ ] Error state shown if connection fails
- [ ] Retry option available on failure
- [ ] Works in both online and offline modes

## Files to Create/Modify

- `device/apps/ui/qml/SplashScreen.qml` - New splash screen component
- `device/apps/ui/qml/main.qml` - Load splash screen first, then transition
- `device/apps/ui/api_client.py` - Add connection status checking
- `device/apps/ui/qml/components/LoadingSpinner.qml` - Reusable loading indicator (if needed)

## Technical Notes

### Service Readiness Check

The splash screen should verify:
1. API client can reach backend (HTTP connection)
2. Core daemon is responding
3. Sensor data is flowing (optional, may take longer)

### Suggested Animation Approach

Use QML animations for smooth, performant effects:
- `OpacityAnimator` for fade effects
- `ScaleAnimator` for logo pulse
- `SequentialAnimation` for multi-stage loading

### Example Structure

```qml
Item {
    id: splashScreen

    // Logo with fade-in animation
    Image {
        source: "assets/waycore_logo.svg"
        OpacityAnimator on opacity {
            from: 0; to: 1; duration: 500
        }
    }

    // Loading indicator
    BusyIndicator {
        running: true
    }

    // Status text
    Text {
        text: statusMessage
    }

    // Connection check timer
    Timer {
        interval: 500
        running: true
        repeat: true
        onTriggered: checkServices()
    }
}
```

## Implementation Notes

{Add notes during implementation}

## Validation Commands

```bash
# Run the UI application
cd device/apps/ui && python main.py

# Verify splash screen appears
# Stop backend services and verify timeout/error handling
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

- Related to: App Theme/Design System (10-design-system.md)
- Related to: API Client (existing)
- Optional dependency: Logo assets in assets/logo/
