# Meshtastic

> Off-grid mesh messaging without cellular or internet

## Overview

Meshtastic enables text messaging over long-range radio without any infrastructure. Messages hop between devices to extend range — perfect for groups in the backcountry.

**Key Features:**
- No cell service or internet required
- Range of 2-10+ miles depending on terrain
- Messages relay through other Meshtastic devices
- Low power consumption

## Requirements

To use Meshtastic, you need:
- A compatible Meshtastic radio module
- The radio connected to your Waycore device
- At least one other Meshtastic user in range

## Getting Started

### First-Time Setup
1. Connect your Meshtastic radio to Waycore
2. Go to **Settings → Mesh** to verify connection
3. The radio status should show "Connected"

### Sending Messages
1. From Home, tap **Meshtastic** (📻)
2. Select a channel or direct message
3. Type your message
4. Tap **Send**

## Features

### Channels
Channels are group conversations. The default channel is visible to all nearby Meshtastic users.

- **Primary Channel**: Default public channel
- **Secondary Channels**: Private group channels (require shared key)

### Direct Messages
Message specific users:
1. Tap **Nodes** to see nearby users
2. Tap a user's name
3. Select **Direct Message**
4. Type and send

### Node List
View all Meshtastic devices in range:
- **Name**: Device name or ID
- **Distance**: Approximate distance (if GPS enabled)
- **Signal**: Connection quality
- **Last Seen**: When last heard

### Position Sharing
Share your GPS location:
1. In a chat, tap **📍 Share Location**
2. Confirm sharing
3. Recipients see your position on their map

## Range and Coverage

### Typical Range
| Terrain | Expected Range |
|---------|----------------|
| Open water/desert | 5-10+ miles |
| Hills/forest | 2-5 miles |
| Urban/mountains | 1-3 miles |
| Obstructed | Under 1 mile |

### Extending Range
- Higher elevation improves range significantly
- Line-of-sight is ideal
- Messages hop through other devices automatically

## Power Management

Meshtastic radio uses additional battery:
- **Active use**: Higher power draw
- **Background**: Minimal power (listening mode)
- **Sleep**: Radio can be disabled to save power

To disable radio:
1. Go to **Settings → Mesh**
2. Toggle **Radio Enabled** off

## Troubleshooting

### Radio not detected
1. Check physical connection
2. Go to Settings → Mesh and tap **Reconnect**
3. Restart the device

### No other nodes visible
- Other users may be out of range
- Check radio is enabled and connected
- Wait 1-2 minutes for discovery

### Messages not sending
- Check radio connection in Settings
- Verify at least one node is visible
- Move to higher ground if possible

### Poor signal/short range
- Elevate your position
- Check for obstructions
- Verify antenna is properly connected

## Best Practices

### For Groups
- Agree on channel settings before the trip
- Share channel keys securely
- Designate check-in times

### For Emergencies
- Meshtastic is NOT for emergencies — use SOS feature instead
- Can supplement emergency communication if SOS unavailable
- Include GPS coordinates in emergency messages

### Battery Conservation
- Disable radio when not needed
- Use shorter message intervals
- Keep radio firmware updated

## Related

- [Settings → Mesh](./settings.md#mesh) - Radio configuration
- [Compass](./compass.md) - Get coordinates to share
- [Offline Mode](../features/offline-mode.md) - Working without internet
