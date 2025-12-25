pragma Singleton
import QtQuick 2.15

/**
 * Sensor Data Model (Singleton)
 *
 * Bridges to Python SensorBridge for backend communication.
 * Falls back to mock values when backend is unavailable.
 *
 * Data sources:
 * - Time: Backend Core Daemon (or local system clock as fallback)
 * - Battery: Backend Core Daemon (mock driver)
 * - Temperature: Backend Core Daemon (mock driver)
 */
Item {
    id: sensorData

    // --- Time Properties (from SensorBridge) ---
    property string currentTime: SensorBridge ? SensorBridge.currentTime : Qt.formatDateTime(new Date(), "HH:mm")
    property string currentDate: SensorBridge ? SensorBridge.currentDate : Qt.formatDateTime(new Date(), "MMM dd")
    property int uptimeSeconds: SensorBridge ? SensorBridge.uptimeSeconds : 0

    // --- Battery Properties (from SensorBridge) ---
    property int batteryLevel: SensorBridge ? SensorBridge.batteryLevel : 85
    property bool batteryCharging: SensorBridge ? SensorBridge.batteryCharging : false
    property string batteryStatus: batteryCharging ? "charging" : (batteryLevel > 20 ? "good" : (batteryLevel > 10 ? "low" : "critical"))

    // --- Temperature Properties ---
    property real temperatureCelsius: SensorBridge ? SensorBridge.temperatureCelsius : 22.5
    property string temperatureUnit: "C"  // "C" or "F" - set from Settings
    property string temperatureSource: SensorBridge ? SensorBridge.temperatureSource : "mock"

    // Computed temperature based on unit
    property real temperatureDisplay: temperatureUnit === "F" ? (temperatureCelsius * 9/5 + 32) : temperatureCelsius
    property string temperatureString: temperatureDisplay.toFixed(1) + "°" + temperatureUnit

    // --- Connection Status ---
    property bool backendConnected: SensorBridge ? SensorBridge.connected : false

    // Fallback timer for when backend is not available
    Timer {
        id: fallbackTimer
        interval: 60000  // Update every minute
        running: !backendConnected
        repeat: true
        onTriggered: {
            if (!SensorBridge) {
                sensorData.currentTime = Qt.formatDateTime(new Date(), "HH:mm")
                sensorData.currentDate = Qt.formatDateTime(new Date(), "MMM dd")
            }
        }
    }

    // Function to get battery icon based on level
    function getBatteryIcon() {
        if (SensorBridge) {
            return SensorBridge.getBatteryIcon()
        }
        if (batteryCharging) return "🔌"
        if (batteryLevel > 80) return "🔋"
        if (batteryLevel > 20) return "🔋"
        return "🪫"
    }

    // Function to get battery color based on level
    function getBatteryColor() {
        if (SensorBridge) {
            return SensorBridge.getBatteryColor()
        }
        if (batteryCharging) return "#7A9984"  // info color
        if (batteryLevel > 50) return "#6B9B6F"  // success color
        if (batteryLevel > 20) return "#D4A574"  // warning color
        return "#C97064"  // error color
    }

    // Force refresh data from backend
    function refresh() {
        if (SensorBridge) {
            SensorBridge.refresh()
        }
    }
}
