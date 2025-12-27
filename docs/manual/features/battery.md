# Battery & Power

> Managing power and extending battery life

## Overview

Waycore is designed for extended field use. Understanding power management helps you get the most from each charge.

## Battery Basics

### Battery Indicator
The status bar shows:
- **🔋 80-100%**: Full/near-full charge
- **🔋 50-79%**: Good charge
- **🔋 20-49%**: Moderate charge
- **🪫 1-19%**: Low battery warning
- **⚡**: Charging indicator

### Expected Battery Life
| Usage Mode | Typical Duration |
|------------|------------------|
| Light use (screen off mostly) | 10-12 hours |
| Normal use (intermittent) | 6-8 hours |
| Heavy use (constant screen) | 4-6 hours |
| With radio active | 4-6 hours |

## Checking Battery Status

### Quick Check
Look at the battery icon in the status bar.

### Detailed Info
1. Go to **Settings → Info**
2. View battery section:
   - Current percentage
   - Charging status
   - Estimated time remaining
   - Battery health

### Via AI
Ask: "How's my battery?" or "What's the battery level?"

## Charging

### How to Charge
1. Connect USB-C cable to the charging port
2. Connect to a power source (charger, power bank, etc.)
3. The ⚡ icon appears in the status bar
4. Full charge takes approximately 2-3 hours

### Charging Tips
- Use a quality USB-C cable
- 5V/2A or higher charger recommended
- Device can be used while charging
- Avoid extreme temperatures while charging

### Charging Sources
| Source | Notes |
|--------|-------|
| Wall charger | Fastest charging |
| USB power bank | Good for field use |
| Solar panel | Works but slower |
| Vehicle USB | Typically slower |

## Extending Battery Life

### Display Settings
The display is the biggest power consumer:
- **Reduce brightness**: Lower = longer battery
- **Shorter auto-sleep**: 30s or 1m recommended
- **Avoid max brightness** unless necessary

### Radio Management
If not using Meshtastic:
1. Go to **Settings → Mesh**
2. Disable radio when not needed
3. Re-enable when ready to communicate

### GPS Usage
GPS is power-hungry:
- Compass app uses continuous GPS
- Close GPS-dependent apps when not needed
- Position updates consume power

### General Tips
- Close unused apps
- Keep device cool
- Use airplane mode if available
- Disable Bluetooth if not used

## Power Modes

### Normal Mode
Default operation with all features available.

### Low Power Mode (Future)
Reduces background activity to extend battery:
- Longer sensor update intervals
- Reduced screen brightness
- Limited background sync

### Critical Power
Below 5% battery:
- Warning displayed
- Consider saving important data
- Connect to power soon

## Battery Health

### Maintaining Battery Health
- Avoid complete discharge regularly
- Don't leave at 0% for extended periods
- Charge before long-term storage (to ~50%)
- Avoid extreme heat or cold

### Battery Degradation
Over time, all batteries lose capacity:
- Normal after 300-500 charge cycles
- May notice shorter runtime after 1-2 years
- Battery health visible in Settings → Info

## Emergency Power

### When Battery is Critical
1. Save any important notes
2. Note your last GPS position
3. Close all apps
4. Turn off display
5. Connect to power as soon as possible

### Field Charging Options
- Portable power bank (recommended)
- Solar charger (for extended trips)
- Vehicle charging
- Hand-crank charger (emergency)

## Troubleshooting

### Battery draining quickly
- Check for apps using GPS continuously
- Reduce display brightness
- Disable unused radios
- Check battery health in Settings

### Device won't charge
- Try a different cable
- Check the USB-C port for debris
- Try a different power source
- Restart device and try again

### Battery percentage stuck
- May need a full discharge/charge cycle
- Restart device
- If persists, battery calibration may be needed

### Overheating while charging
- Remove from direct sunlight
- Pause charging until cooled
- Don't charge in hot environments
- Use in shade when possible

## Related

- [Settings](../apps/settings.md) - Battery settings
- [Sensors](./sensors.md) - Sensor power usage
- [Offline Mode](./offline-mode.md) - Conserving power offline
