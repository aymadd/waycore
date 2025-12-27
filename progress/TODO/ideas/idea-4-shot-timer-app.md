# Idea: Shot Timer App

**Category**: Ideas
**Task ID**: IDEA-4
**Status**: TODO
**Started**: Not started
**Completed**: Not completed
**Priority**: Medium

## Description

Create a shot timer app for shooting practice that uses microphone input to detect and track gunshots. The app records shot times, splits between shots, and provides statistics for training analysis. Essential for competitive shooters and those looking to improve their shooting speed and consistency.

### Use Cases

1. **Competitive Shooting** - Track draw-to-first-shot and split times for USPSA/IDPA
2. **Defensive Training** - Practice and measure defensive shooting drills
3. **Dry Fire Practice** - Works with dry fire systems that produce audible clicks
4. **Accuracy Training** - Combine timing with hit verification
5. **Personal Records** - Track improvement over time

### How It Works

1. User configures timer settings (sensitivity, par time, delay)
2. User presses START or waits for random delay beep
3. Audible START signal sounds
4. App listens for shots via microphone
5. Each shot is timestamped and displayed
6. Session ends manually or at par time
7. Results show splits, total time, and statistics

## Feature Components

### Timer Display
- Large, readable time display (total elapsed)
- Shot count
- Split times list (time since last shot)
- Par time indicator (optional)
- Visual feedback on shot detection

### Timer Controls
- START button (with optional random delay)
- STOP/RESET button
- PAR TIME setting
- Sensitivity adjustment
- Review previous sessions

### Audio Detection
- Microphone input monitoring
- Threshold-based shot detection
- Configurable sensitivity (for different firearms/environments)
- Filter out non-shot sounds (echo, background noise)

### Statistics & Review
- Total time (first shot to last shot)
- Individual split times
- Average split time
- Fastest/slowest split
- Shot count
- Session history

### Audio Output
- Configurable start beep
- Optional par time beep
- Shot confirmation beep (optional)

## Acceptance Criteria

- [ ] Shot Timer app accessible from Home grid (⏱️ or 🎯 icon)
- [ ] START button begins timing session
- [ ] Random delay option before start beep
- [ ] Audible start signal sounds
- [ ] Microphone detects shots and records timestamps
- [ ] Split times calculated and displayed
- [ ] Total time displayed prominently
- [ ] STOP/RESET ends session and shows results
- [ ] Sensitivity adjustment available
- [ ] Par time setting (optional audible signal)
- [ ] Session review shows all shots with splits
- [ ] Works reliably in outdoor environments
- [ ] Battery-efficient microphone monitoring

## Files to Create/Modify

- `device/apps/ui/qml/ShotTimer.qml` - Main shot timer UI
- `device/apps/ui/qml/Home.qml` - Add Shot Timer app to grid
- `device/apps/ui/qml/AppShell.qml` - Add shot timer navigation
- `device/apps/ui/qml/qmldir` - Register ShotTimer component
- `device/apps/ui/audio_bridge.py` - Audio input processing (if needed)
- Backend service may be needed for audio processing

## Technical Notes

### Audio Detection Algorithm

The app needs to detect sharp, loud sounds (gunshots) and filter out ambient noise:

```javascript
// Simplified shot detection concept
property real threshold: 0.8  // Adjustable sensitivity
property real lastShotTime: 0
property real minShotInterval: 50  // ms, prevents double-detection

function processAudioSample(amplitude, timestamp) {
    if (amplitude > threshold &&
        timestamp - lastShotTime > minShotInterval) {
        recordShot(timestamp);
        lastShotTime = timestamp;
    }
}
```

### Timer State Machine

```
IDLE -> COUNTDOWN -> RUNNING -> STOPPED -> REVIEW
  ^                                          |
  +------------------------------------------+
```

### Shot Data Structure

```javascript
property var shots: []
// Each shot: { time: ms_since_start, split: ms_since_last_shot }

function recordShot(timestamp) {
    var elapsed = timestamp - sessionStartTime;
    var split = shots.length > 0 ?
                elapsed - shots[shots.length-1].time :
                elapsed;
    shots.push({ time: elapsed, split: split });
}
```

### UI Layout Concept

```
┌─────────────────────────────┐
│         12.847s             │  ← Total time (large)
│         Shot 5              │
├─────────────────────────────┤
│  #1   2.31s   2.31s         │  ← Split times
│  #2   0.42s   2.73s         │
│  #3   0.38s   3.11s         │
│  #4   0.51s   3.62s         │
│  #5   0.44s   4.06s         │
├─────────────────────────────┤
│ Avg: 0.44s  Best: 0.38s     │  ← Statistics
├─────────────────────────────┤
│    [START]     [RESET]      │
└─────────────────────────────┘
```

## Implementation Notes

{Add notes during implementation}

## Validation Commands

```bash
# Run the UI application
cd device/apps/ui && python main.py

# Navigate to Shot Timer app
# Test with clapping or simulated sounds
```

## Completion Checklist

- [ ] Code implemented
- [ ] Tests written
- [ ] Tests passing
- [ ] Linting passing
- [ ] Documentation updated
- [ ] Files committed

## Blockers

- Requires microphone access and audio processing capability
- May need native audio processing for low latency

## Related Tasks

- Depends on: Audio input capability (microphone driver/bridge)
- Related to: Timer functionality patterns
- Future: Integration with training log/notes
