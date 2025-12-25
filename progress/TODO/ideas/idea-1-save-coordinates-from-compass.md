# Idea: Save Coordinates from Compass to View on Map

**Category**: Ideas
**Task ID**: IDEA-1
**Status**: TODO
**Started**: Not started
**Completed**: Not completed
**Priority**: Low

## Description

Add the ability for users to save GPS coordinates directly from the Compass view. Saved coordinates would be stored with an optional name/label and timestamp, then be viewable as markers on the Maps app. This feature would help outdoor enthusiasts mark trails, waypoints, points of interest, or memorable locations while navigating.

### Use Cases

1. **Trail Marking** - Hikers can drop waypoints along a trail to retrace their path later
2. **Point of Interest** - Save location of a campsite, water source, or scenic viewpoint
3. **Navigation Reference** - Mark a destination before leaving, navigate back later
4. **Emergency Breadcrumbs** - In case of getting lost, review saved coordinates to backtrack
5. **Sharing Locations** - Export coordinates to share with others via Meshtastic

### User Flow

1. User is in Compass view seeing current GPS coordinates
2. User taps "Save Location" button (or long-press for quick save)
3. Dialog appears to enter optional name (default: timestamp-based name)
4. Coordinate saved to database
5. User can later open Maps app and see saved waypoints as pins
6. Tapping a pin shows details (name, coordinates, date saved, distance from current location)

## Feature Components

### Compass View Additions
- "Save Location" button or icon in Compass UI
- Quick-save gesture (long-press or swipe)
- Visual confirmation when location saved
- Badge showing count of saved locations (optional)

### Saved Locations Storage
- New database table: `saved_locations`
  - id, name, latitude, longitude, altitude, accuracy, created_at, notes
- API endpoints for CRUD operations
- Sync with Maps app

### Maps Integration
- Display saved locations as markers/pins
- Different pin colors/icons for categories (optional)
- Tap pin to view details
- Option to navigate to saved location
- Delete/edit saved locations from Maps

### Future Enhancements (out of scope for v1)
- Categories/folders for organizing waypoints
- Import/export GPX files
- Share coordinates via Meshtastic
- Draw trails connecting waypoints
- Offline map caching around saved locations

## Acceptance Criteria

- [ ] "Save Location" button added to Compass view
- [ ] Save dialog with name input and confirm/cancel
- [ ] Coordinates saved to database with timestamp
- [ ] Saved locations appear as pins on Maps
- [ ] Tapping pin shows location details
- [ ] Delete saved location functionality
- [ ] List view of all saved locations (in Maps or separate screen)

## Files to Create/Modify

- `device/apps/ui/qml/Compass.qml` - Add save location button
- `device/apps/ui/qml/Maps.qml` - Display saved location pins
- `device/apps/ui/qml/SavedLocations.qml` - List view of saved locations (new)
- `device/services/data_logger/api.py` - Add saved_locations endpoints
- `device/services/data_logger/service.py` - Implement storage logic
- `device/libs/database/sqlite.py` - Add saved_locations table schema

## Technical Notes

### Database Schema
```sql
CREATE TABLE saved_locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    altitude REAL,
    accuracy REAL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### API Endpoints
- `GET /api/locations` - List all saved locations
- `POST /api/locations` - Save new location
- `GET /api/locations/{id}` - Get single location
- `PUT /api/locations/{id}` - Update location (name, notes)
- `DELETE /api/locations/{id}` - Delete location

## Implementation Notes

{Add notes during implementation}

## Validation Commands

```bash
# Run the UI application
cd device/apps/ui && python main.py

# Test saving a location from Compass
# Verify it appears in Maps app
```

## Completion Checklist

- [ ] Code implemented
- [ ] Tests written
- [ ] Tests passing
- [ ] Linting passing
- [ ] Documentation updated
- [ ] Files committed

## Time Tracking

- Estimated effort: 6-8 hours
- Actual effort: {to be filled}

## Blockers

None

## Related Tasks

- Depends on: Compass with GPS (12.5 - COMPLETED)
- Depends on: Maps UI (16.1)
- Related to: Notes app (similar CRUD patterns)
