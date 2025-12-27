# Idea: Step Counter App

**Category**: Ideas
**Task ID**: IDEA-5
**Status**: TODO
**Started**: Not started
**Completed**: Not completed
**Priority**: Low

## Description

Create a step counter (pedometer) app that tracks steps, distance walked, and activity over time. Uses accelerometer data to detect walking/running motion and provides daily statistics and historical tracking for fitness monitoring.

### Use Cases

1. **Hiking** - Track distance and steps during trail hikes
2. **Fitness Goals** - Monitor daily step count toward health targets
3. **Navigation** - Rough distance estimation when GPS is unavailable
4. **Training** - Track walking/running activity during outdoor training
5. **Patrol/Reconnaissance** - Log distance covered during extended operations

### How It Works

1. Accelerometer continuously monitors device motion
2. Step detection algorithm identifies walking/running gait
3. Steps are counted and stored
4. Distance calculated using estimated stride length
5. Daily totals and historical data available for review

## Feature Components

### Step Counter Display
- Current step count (large, prominent)
- Distance walked (km/miles)
- Calories burned estimate (optional)
- Active time today
- Daily goal progress indicator

### Historical Tracking
- Daily step totals (past 7 days chart)
- Weekly/monthly summaries
- Personal records
- Trend analysis

### Settings
- Daily step goal
- Stride length (auto-calibrate or manual)
- Distance units (km/miles)
- Reset daily at midnight

### Background Tracking
- Counts steps even when app is in background
- Runs efficiently without draining battery
- Syncs when app opened

## Acceptance Criteria

- [ ] Step Counter app accessible from Home grid (👟 or 🚶 icon)
- [ ] Step count displayed prominently
- [ ] Distance calculated from steps
- [ ] Steps detected accurately via accelerometer
- [ ] Daily total resets at midnight
- [ ] Historical data saved for past 30+ days
- [ ] Daily goal can be set by user
- [ ] Progress toward goal visualized
- [ ] Chart showing recent days' activity
- [ ] Unit toggle (km/miles)
- [ ] Stride length configurable
- [ ] Works in background (battery efficient)

## Files to Create/Modify

- `device/apps/ui/qml/StepCounter.qml` - Main step counter UI
- `device/apps/ui/qml/Home.qml` - Add Step Counter app to grid
- `device/apps/ui/qml/AppShell.qml` - Add step counter navigation
- `device/apps/ui/qml/qmldir` - Register StepCounter component
- `device/libs/database/` - Step history storage
- `device/services/data_logger/` - Step data logging
- Accelerometer driver/bridge for step detection

## Technical Notes

### Step Detection Algorithm

Basic peak detection on accelerometer magnitude:

```python
import math

def calculate_magnitude(x, y, z):
    return math.sqrt(x*x + y*y + z*z)

class StepDetector:
    def __init__(self, threshold=1.2, min_interval_ms=250):
        self.threshold = threshold
        self.min_interval = min_interval_ms
        self.last_step_time = 0
        self.previous_magnitude = 0
        self.step_count = 0

    def process_sample(self, x, y, z, timestamp_ms):
        magnitude = calculate_magnitude(x, y, z)

        # Detect peak (crossing threshold going down)
        if (self.previous_magnitude > self.threshold and
            magnitude <= self.threshold and
            timestamp_ms - self.last_step_time > self.min_interval):
            self.step_count += 1
            self.last_step_time = timestamp_ms

        self.previous_magnitude = magnitude
        return self.step_count
```

### Distance Calculation

```javascript
property real strideLength: 0.75  // meters, adjustable
property int steps: 0

function getDistance(unit) {
    var meters = steps * strideLength;
    if (unit === "miles") {
        return meters / 1609.34;
    } else if (unit === "km") {
        return meters / 1000;
    }
    return meters;
}
```

### Calorie Estimation (Rough)

```javascript
// Very rough estimate: ~0.04 calories per step
function estimateCalories(steps) {
    return Math.round(steps * 0.04);
}
```

### Database Schema

```sql
CREATE TABLE step_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL UNIQUE,
    steps INTEGER NOT NULL DEFAULT 0,
    distance_meters REAL,
    active_minutes INTEGER,
    goal INTEGER DEFAULT 10000,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### UI Layout Concept

```
┌─────────────────────────────┐
│         8,247               │  ← Step count (large)
│      steps today            │
├─────────────────────────────┤
│   📏 5.6 km    🔥 330 cal   │  ← Stats row
│   ⏱️ 68 min active          │
├─────────────────────────────┤
│  Goal: 10,000 steps         │
│  ██████████░░░░░ 82%        │  ← Progress bar
├─────────────────────────────┤
│  Weekly Activity:           │
│  M  T  W  T  F  S  S        │
│  █  █  █  ▄  ▂  _  _        │  ← Simple chart
└─────────────────────────────┘
```

## Implementation Notes

{Add notes during implementation}

## Validation Commands

```bash
# Run the UI application
cd device/apps/ui && python main.py

# Navigate to Step Counter app
# Walk around to test step detection
```

## Completion Checklist

- [ ] Code implemented
- [ ] Tests written
- [ ] Tests passing
- [ ] Linting passing
- [ ] Documentation updated
- [ ] Files committed

## Blockers

- Requires accelerometer hardware/driver

## Related Tasks

- Depends on: Accelerometer sensor driver
- Related to: Health/fitness tracking features
- Related to: Background service capability
- Future: Integration with GPS for more accurate distance
