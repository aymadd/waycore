# Improvement: WiFi Connectivity Management

**Category**: Improvements
**Task ID**: IMP-2
**Status**: TODO
**Started**: Not started
**Completed**: Not completed
**Priority**: Medium

## Description

Implement comprehensive WiFi management functionality in the Settings Controls submenu. Users need the ability to scan for available networks, connect to networks (open and secured), view connection details, manage saved networks, and troubleshoot connectivity issues.

### Features

1. **Network Scanning**
   - Scan for available WiFi networks
   - Display network list with signal strength indicators
   - Auto-refresh or manual rescan option
   - Show security type (Open, WPA2, WPA3, etc.)

2. **Network Connection**
   - Connect to open networks with one tap
   - Password entry dialog for secured networks
   - "Show password" toggle for entry verification
   - Remember network option (save credentials)
   - Connect automatically to known networks

3. **Connection Status**
   - Current network name (SSID)
   - Signal strength indicator
   - IP address
   - Connection speed/link quality
   - Connected duration

4. **Saved Networks Management**
   - List of saved/known networks
   - Forget network option
   - Priority ordering (which to prefer)
   - View saved password (with authentication)

5. **Advanced Settings** (optional)
   - Static IP configuration
   - DNS settings
   - Proxy configuration
   - MAC address display

### UI Design

#### Network List View
```
┌─────────────────────────────────┐
│ WiFi Networks          [Scan]  │
├─────────────────────────────────┤
│ ████ HomeNetwork       🔒 ━━━━ │
│ ███  CoffeeShop        🔒 ━━━  │
│ ██   OpenWifi             ━━   │
│ █    Neighbor_5G       🔒 ━    │
└─────────────────────────────────┘
```

#### Connected Network View
```
┌─────────────────────────────────┐
│ Connected to: HomeNetwork      │
│ Signal: Excellent (━━━━)       │
│ IP: 192.168.1.42               │
│ Speed: 72 Mbps                 │
│                                │
│ [Disconnect]  [Network Details]│
└─────────────────────────────────┘
```

### Backend Requirements

The backend needs to interface with Linux network management:

1. **NetworkManager D-Bus API** (preferred)
   - Scan for networks
   - Connect/disconnect
   - Manage saved connections
   - Monitor connection state

2. **Alternative: wpa_supplicant**
   - Direct wpa_cli interface
   - More low-level control

### API Endpoints

```
GET  /api/wifi/networks          # List available networks
GET  /api/wifi/status            # Current connection status
POST /api/wifi/connect           # Connect to network
POST /api/wifi/disconnect        # Disconnect from current
GET  /api/wifi/saved             # List saved networks
DELETE /api/wifi/saved/{ssid}    # Forget a network
POST /api/wifi/scan              # Trigger network scan
```

## Dependencies

- [ ] Task 12.10 - Settings Controls Submenu (architecture)
- [ ] Linux NetworkManager or wpa_supplicant access

## Acceptance Criteria

- [ ] WiFi section in Settings > Controls
- [ ] Toggle to enable/disable WiFi radio
- [ ] Scan and display available networks
- [ ] Signal strength indicators (bars or percentage)
- [ ] Security type shown (lock icon for secured)
- [ ] Connect to open networks
- [ ] Password dialog for secured networks
- [ ] Show current connection status
- [ ] Disconnect from current network
- [ ] View saved networks list
- [ ] Forget saved network functionality
- [ ] Error handling (wrong password, network unavailable)
- [ ] Loading states during scan/connect

## Files to Create/Modify

- `device/apps/ui/qml/SettingsControls.qml` - Add WiFi management section
- `device/apps/ui/qml/WiFiNetworkList.qml` - Network list component (new)
- `device/apps/ui/qml/WiFiPasswordDialog.qml` - Password entry dialog (new)
- `device/services/core_daemon/api.py` - Add WiFi API endpoints
- `device/services/core_daemon/wifi_manager.py` - WiFi management logic (new)
- `device/drivers/mock/wifi.py` - Mock WiFi driver for development (new)

## Tests Required

- [ ] Manual verification: WiFi toggle works
- [ ] Manual verification: Network scan displays results
- [ ] Manual verification: Connect to open network
- [ ] Manual verification: Connect with password
- [ ] Manual verification: Connection status accurate
- [ ] Manual verification: Forget network works
- [ ] Test file: `device/services/core_daemon/tests/test_wifi_manager.py`
- [ ] Coverage target: 80%

## Implementation Notes

### Mock WiFi Driver

For development without actual WiFi hardware:

```python
class MockWiFiManager:
    def __init__(self):
        self.networks = [
            {"ssid": "HomeNetwork", "signal": -45, "security": "WPA2", "connected": True},
            {"ssid": "CoffeeShop", "signal": -60, "security": "WPA2", "connected": False},
            {"ssid": "OpenWifi", "signal": -70, "security": "Open", "connected": False},
            {"ssid": "Neighbor_5G", "signal": -80, "security": "WPA3", "connected": False},
        ]

    async def scan(self) -> list[dict]:
        await asyncio.sleep(2)  # Simulate scan time
        return self.networks

    async def connect(self, ssid: str, password: str = None) -> bool:
        await asyncio.sleep(1)  # Simulate connection time
        # Simulate success/failure
        return True
```

### NetworkManager D-Bus Example

```python
import dbus

bus = dbus.SystemBus()
nm = bus.get_object('org.freedesktop.NetworkManager', '/org/freedesktop/NetworkManager')
nm_iface = dbus.Interface(nm, 'org.freedesktop.NetworkManager')

# Get WiFi device
devices = nm_iface.GetDevices()
for d in devices:
    dev = bus.get_object('org.freedesktop.NetworkManager', d)
    dev_iface = dbus.Interface(dev, 'org.freedesktop.DBus.Properties')
    if dev_iface.Get('org.freedesktop.NetworkManager.Device', 'DeviceType') == 2:  # WiFi
        wifi_dev = dev
        break
```

## Validation Commands

```bash
# Run the UI application
cd device/apps/ui && python main.py

# Navigate to Settings > Controls > WiFi
# Test scanning and connection

# Run backend tests
pytest device/services/core_daemon/tests/test_wifi_manager.py -v
```

## Completion Checklist

- [ ] Code implemented
- [ ] Tests written
- [ ] Tests passing
- [ ] Coverage target met
- [ ] Linting passing
- [ ] Documentation updated
- [ ] Files committed



## Blockers

None

## Related Tasks

- Related to: 12.10 (Settings Controls Submenu)
- Related to: Bluetooth/LTE controls (similar patterns)
- Future: WiFi hotspot mode for device sharing
