# Settings

> Configure your Waycore device

## Overview

The Settings app provides access to all device configuration options, organized into sections.

## Getting Started

From Home, tap **Settings** (⚙️) to access configuration options.

## Settings Sections

### General

Basic device settings:

- **Display Brightness**: Adjust screen brightness
- **Auto-Sleep**: Time before screen dims (30s, 1m, 2m, 5m, Never)
- **Time Zone**: Set your local time zone
- **Date Format**: Choose date display format

### Sensors

View and calibrate device sensors:

- **GPS**: Status, accuracy, last fix time
- **Compass**: Heading, calibration status
- **Altimeter**: Elevation, calibration
- **Temperature**: Current reading, sensor source
- **Battery**: Level, charging status, health

#### Sensor Actions
- **Calibrate Compass**: Start figure-8 calibration
- **Set Altitude**: Manually set known altitude for calibration
- **Refresh**: Update all sensor readings

### Mesh

Meshtastic radio configuration:

- **Radio Status**: Connected/Disconnected
- **Node Name**: Your display name to others
- **Channel Settings**: Configure channels
- **Position Sharing**: Enable/disable GPS sharing
- **Radio Power**: Adjust transmission power

### Info

Device information and diagnostics:

- **Software Version**: Current Waycore version
- **Device Model**: Hardware model
- **Storage**: Used/available space breakdown
- **Uptime**: Time since last restart
- **Hardware IDs**: Serial numbers (for support)

### Advanced

Power user options:

- **Developer Mode**: Enable debug features
- **Factory Reset**: Reset to default settings
- **Export Logs**: Create diagnostic file
- **System Restart**: Restart the device

## Common Tasks

### Calibrating the Compass

1. Go to **Settings → Sensors**
2. Tap **Calibrate Compass**
3. Hold device and rotate in figure-8 pattern
4. Continue for 15-20 seconds
5. "Calibration Complete" appears

### Setting Altitude

For accurate elevation readings:

1. Go to **Settings → Sensors**
2. Tap **Set Altitude**
3. Enter your known altitude (from map or trailhead sign)
4. Tap **Save**

### Checking Storage

1. Go to **Settings → Info**
2. View storage breakdown:
   - System files
   - Applications
   - User data (photos, notes, etc.)
   - Available space

### Adjusting Power Settings

To maximize battery life:
1. Reduce display brightness
2. Set shorter auto-sleep time
3. Disable unused radios in Mesh settings
4. Enable power-saving mode (if available)

## Troubleshooting

### Settings not saving
- Wait a moment for changes to apply
- Restart the app if changes revert
- Check available storage space

### Sensors showing incorrect data
- Calibrate the affected sensor
- Move away from magnetic interference
- Restart if readings stuck

### Cannot access certain settings
- Some settings require reboot to take effect
- Developer options require enabling Developer Mode first
- Factory Reset requires confirmation

## Related

- [Sensors](../features/sensors.md) - Detailed sensor information
- [Battery](../features/battery.md) - Power management
- [Factory Reset](../advanced/factory-reset.md) - Reset procedures
