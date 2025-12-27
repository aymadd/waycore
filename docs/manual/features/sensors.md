# Sensors

> Understanding your device's sensor data

## Overview

Waycore includes multiple sensors that provide environmental and positional data. This guide explains each sensor and how to interpret its readings.

## Available Sensors

| Sensor | Measures | Accuracy |
|--------|----------|----------|
| GPS | Position, altitude | ±5-15m horizontal |
| Compass | Heading | ±2-5° when calibrated |
| Altimeter | Elevation | ±10-30m |
| Temperature | Ambient temp | ±1°C |
| Accelerometer | Motion, orientation | High |
| Barometer | Air pressure | ±1 hPa |

## GPS

### What It Measures
- **Latitude/Longitude**: Your position on Earth
- **Altitude**: Height above sea level
- **Accuracy**: Estimated precision of the reading
- **Speed**: Movement speed (when moving)

### Reading GPS Data
- Coordinates shown in decimal degrees (e.g., 37.7749°N, 122.4194°W)
- Accuracy in meters (lower is better)
- "No Fix" means satellites not yet acquired

### GPS Tips
- First fix may take 1-2 minutes
- Clear sky view improves accuracy
- Dense tree cover or canyons reduce accuracy
- Urban environments may cause multipath errors

### Common GPS Issues
- **No Fix**: Move to open area with sky view
- **Drifting**: Normal when stationary, average multiple readings
- **Altitude Error**: GPS altitude can be off by 30m+; use barometric altimeter for precision

## Compass (Magnetometer)

### What It Measures
- **Heading**: Direction you're facing in degrees (0-360°)
- **Cardinal Direction**: N, NE, E, SE, S, SW, W, NW

### Reading the Compass
- 0°/360° = North
- 90° = East
- 180° = South
- 270° = West

### Compass Tips
- Hold device flat and level
- Keep away from metal objects
- Calibrate regularly for accuracy
- Magnetic declination is automatically compensated

### Calibration
When readings seem inaccurate:
1. Go to **Settings → Sensors → Calibrate Compass**
2. Hold device and rotate in figure-8 pattern
3. Continue for 15-20 seconds
4. Status shows "Calibrated" when complete

## Altimeter (Barometer)

### What It Measures
- **Elevation**: Height above sea level
- **Pressure**: Atmospheric pressure in hPa/mbar

### Reading Altitude
- Displayed in meters and feet
- Based on barometric pressure
- More accurate than GPS altitude for relative changes

### Altitude Tips
- Set known altitude at trailhead for best accuracy
- Weather changes affect pressure-based readings
- Calibrate if reading seems significantly off
- Track elevation gain/loss accurately once calibrated

### Calibration
1. Go to **Settings → Sensors → Set Altitude**
2. Enter known elevation (from map, trail sign, etc.)
3. Tap **Save**

## Temperature

### What It Measures
- Ambient air temperature
- Displayed in Celsius and Fahrenheit

### Temperature Tips
- Sensor may be affected by device heat
- Let device acclimate for accurate readings
- Keep in shade for best results
- Device operation generates some heat

### Accuracy
- ±1°C typical accuracy
- Device warmth may add 2-5°C
- Best readings when device is cool

## Accelerometer

### What It Measures
- Device orientation
- Motion and movement
- Used for screen rotation and step counting

### Applications
- Auto-rotate display
- Compass tilt compensation
- Activity tracking (future feature)

## Using Sensors with AI

Ask the AI about sensor data:
- "What's my current location?"
- "What's the temperature?"
- "What direction am I facing?"
- "What's my elevation?"

The AI reads sensors in real-time to answer these questions.

## Sensor Status

Check sensor health:
1. Go to **Settings → Sensors**
2. View status for each sensor:
   - **Online**: Working normally
   - **Calibrating**: In calibration mode
   - **Error**: Sensor issue detected
   - **Offline**: Sensor not available

## Troubleshooting

### Sensor shows "Offline"
- Sensor may not be available on your hardware
- Restart device if sensor was previously working
- Check Settings → Info for hardware details

### Readings seem stuck
- Sensor may need a moment to update
- Try the refresh button in Settings → Sensors
- Movement may be needed to trigger GPS update

### Inaccurate readings
- Calibrate the specific sensor
- Move away from interference sources
- Check sensor status in Settings

### Battery drain from sensors
- GPS uses the most power
- Consider disabling unused sensors if available
- Sensors are optimized for low power use

## Related

- [Compass App](../apps/compass.md) - Navigation with compass
- [AI Assistant](../apps/ai-assistant.md) - Ask about sensor data
- [Battery](./battery.md) - Power usage by sensors
