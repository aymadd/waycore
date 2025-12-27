# Developer Mode

> Advanced options for debugging and development

## Overview

Developer Mode enables advanced features for debugging, testing, and development. These options are intended for technical users and app developers.

⚠️ **Warning**: Developer options can affect device stability. Only enable if you understand the implications.

## Enabling Developer Mode

1. Go to **Settings → Info**
2. Tap **Software Version** 7 times rapidly
3. "Developer Mode enabled" message appears
4. New **Developer** section appears in Settings

## Developer Options

### Debug Information

- **Show FPS**: Display frame rate overlay
- **Show Touch Points**: Visualize touch locations
- **Verbose Logging**: Enable detailed system logs
- **Show Sensor Data**: Real-time sensor overlay

### Network

- **API Inspector**: View API calls and responses
- **Mock Backend**: Use simulated services
- **Network Latency**: Add artificial delay (testing)

### Performance

- **CPU Usage**: Display processor usage
- **Memory Monitor**: Show RAM usage
- **GPU Rendering**: Visualize rendering performance

### AI Development

- **Model Info**: View loaded AI model details
- **Inference Timing**: Show response generation time
- **Token Counter**: Display token usage
- **Raw Output**: Show unformatted AI responses

### Testing

- **Mock Sensors**: Use simulated sensor data
- **Test Notifications**: Trigger test alerts
- **Crash Reporter**: Enable detailed crash logs

## Exporting Logs

For troubleshooting or bug reports:

1. Go to **Settings → Developer**
2. Tap **Export Logs**
3. Select log types to include
4. Logs saved to `/logs/` directory

### Log Contents
- System events
- App crashes
- Sensor readings
- Network activity
- Error messages

## Disabling Developer Mode

1. Go to **Settings → Developer**
2. Toggle **Developer Mode** off
3. All developer options become hidden
4. Normal operation resumes

## Safety Considerations

### Performance Impact
Debug overlays and logging can:
- Reduce battery life
- Slow down the device
- Use additional storage

### Stability Risks
Some developer options may cause:
- App crashes
- Unexpected behavior
- Data corruption (rare)

### Recommendations
- Disable after troubleshooting
- Don't enable on trips where reliability is critical
- Keep logs enabled only when debugging

## For App Developers

If developing apps for Waycore:

### API Access
- View endpoint documentation in `/docs/api/`
- Use API Inspector to test calls
- Mock Backend allows offline development

### Sensor Testing
- Mock Sensors provides consistent test data
- Useful for apps requiring specific conditions

### Performance Profiling
- Use FPS counter and GPU overlay
- Monitor memory for leaks
- Profile on actual hardware

## Related

- [Factory Reset](./factory-reset.md) - Reset if issues occur
- [Troubleshooting](../reference/troubleshooting.md) - Common issues
- [Specifications](../reference/specifications.md) - Hardware details
