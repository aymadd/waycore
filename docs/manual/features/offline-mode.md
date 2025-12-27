# Offline Mode

> Using Waycore without internet connectivity

## Overview

Waycore is designed to work completely offline. Most features function without any internet connection, making it ideal for backcountry use.

## What Works Offline

### Fully Offline Features
| Feature | Offline Status |
|---------|---------------|
| AI Assistant | ✅ Fully functional |
| Compass | ✅ Fully functional |
| GPS | ✅ Fully functional |
| Notes | ✅ Fully functional |
| Camera | ✅ Fully functional |
| Gallery | ✅ Fully functional |
| Sensors | ✅ Fully functional |
| Meshtastic | ✅ Uses radio, not internet |

### Features Requiring Internet
| Feature | Requires Internet |
|---------|-------------------|
| Map tile download | Yes (download before trip) |
| Weather forecast | Yes |
| Software updates | Yes |
| Cloud sync | Yes (if enabled) |

## Preparing for Offline Use

### Before Your Trip

1. **Download Maps**
   - Open Maps app while connected
   - Navigate to your trip area
   - Download offline tiles

2. **Update Software**
   - Check for updates in Settings → Info
   - Install any pending updates

3. **Verify AI Model**
   - Open AI app and test a question
   - Ensure model is loaded and working

4. **Charge Battery**
   - Start with a full charge
   - Bring backup power if needed

## AI Offline Operation

The AI runs entirely on-device:
- No internet needed for any AI features
- Same response quality offline
- Image analysis works offline
- Sensor queries work offline

**First-time note**: The AI model must be downloaded once during initial setup. After that, it works offline forever.

## Maps Offline

### Downloading Tiles
1. While connected to internet, open Maps
2. Navigate to your trip area
3. Tap **Download Area**
4. Select zoom level (higher = more detail, more storage)
5. Wait for download to complete

### Offline Map Tips
- Download more area than you think you need
- Include surrounding regions for context
- Higher zoom levels use more storage
- Downloaded tiles persist until deleted

## Meshtastic Offline

Meshtastic is inherently offline — it uses radio waves:
- Messages transmit via radio
- Other Meshtastic users receive directly
- No cellular or internet infrastructure needed
- Perfect for group communication in the backcountry

## Data Persistence

All your data stays on-device:
- Notes are stored locally
- Photos are stored locally
- Conversations are stored locally
- Settings persist across restarts

**No sync required** — your data is always with you.

## Reconnecting

When internet becomes available:
- No special steps needed
- Device will reconnect automatically
- Pending updates can be downloaded
- Map tiles can be updated

## Tips for Extended Offline Use

### Battery Management
- Reduce screen brightness
- Disable unused radios
- Close apps when not in use
- See [Battery Guide](./battery.md)

### Storage Management
- Delete old photos you don't need
- Clear completed notes
- Check storage in Settings → Info

### Navigation Backup
- Note key coordinates before entering offline areas
- Take photos of physical maps as backup
- Mark waypoints in the Maps app

## Troubleshooting

### "No Connection" warnings
- This is normal offline — ignore for offline features
- Only relevant for features requiring internet

### AI not responding
- AI should work offline
- If stuck, restart the app
- Check if AI model is loaded in Settings → Info

### Maps blank in an area
- Area may not have been downloaded
- Connect to internet and download tiles
- Or use compass coordinates for navigation

### Meshtastic not connecting
- This is a radio connection, not internet
- Check radio is enabled and connected
- Ensure other users are in range

## Related

- [AI Assistant](../apps/ai-assistant.md) - Offline AI use
- [Battery](./battery.md) - Power management offline
- [Meshtastic](../apps/meshtastic.md) - Radio communication
