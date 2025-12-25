pragma Singleton
import QtQuick 2.15

/**
 * Sensor Data Model (Singleton)
 * Provides mock sensor data for battery and temperature
 *
 * NOTE: In production:
 * - Data should come from backend services via MQTT/API
 * - Time comes from system clock (Raspberry Pi gets time from NTP/RTC)
 * - Battery and temperature should come from actual sensor drivers
 */
Item {
    id: sensorData

    // Battery properties
    property int batteryLevel: 85  // 0-100
    property bool batteryCharging: false
    property string batteryStatus: batteryCharging ? "charging" : (batteryLevel > 20 ? "good" : (batteryLevel > 10 ? "low" : "critical"))

    // Temperature properties
    property real temperatureCelsius: 22.5  // Temperature in Celsius
    property string temperatureUnit: "C"  // "C" or "F"

    // Computed temperature based on unit
    property real temperatureDisplay: temperatureUnit === "F" ? (temperatureCelsius * 9/5 + 32) : temperatureCelsius
    property string temperatureString: temperatureDisplay.toFixed(1) + "°" + temperatureUnit

    // Time property (from system clock)
    property string currentTime: Qt.formatDateTime(new Date(), "HH:mm")
    property string currentDate: Qt.formatDateTime(new Date(), "MMM dd")

    // Timer to update time every minute
    Timer {
        id: timeTimer
        interval: 60000  // Update every minute
        running: true
        repeat: true
        onTriggered: {
            sensorData.currentTime = Qt.formatDateTime(new Date(), "HH:mm")
            sensorData.currentDate = Qt.formatDateTime(new Date(), "MMM dd")
        }
    }

    // Timer to simulate battery drain (for testing)
    Timer {
        id: batteryTimer
        interval: 30000  // Update every 30 seconds
        running: false  // Disabled by default, enable for testing
        repeat: true
        onTriggered: {
            if (!batteryCharging && batteryLevel > 0) {
                batteryLevel = Math.max(0, batteryLevel - 1)
            } else if (batteryCharging && batteryLevel < 100) {
                batteryLevel = Math.min(100, batteryLevel + 1)
            }
        }
    }

    // Timer to simulate temperature variation (for testing)
    Timer {
        id: tempTimer
        interval: 10000  // Update every 10 seconds
        running: false  // Disabled by default, enable for testing
        repeat: true
        onTriggered: {
            // Simulate small temperature variations
            var variation = (Math.random() - 0.5) * 2  // -1 to +1
            temperatureCelsius = Math.max(-10, Math.min(50, temperatureCelsius + variation))
        }
    }

    // Function to get battery icon based on level
    function getBatteryIcon() {
        if (batteryCharging) return "🔌"
        if (batteryLevel > 80) return "🔋"
        if (batteryLevel > 50) return "🔋"
        if (batteryLevel > 20) return "🔋"
        if (batteryLevel > 10) return "🔋"
        return "🔋"  // Critical/low
    }

    // Function to get battery color based on level
    // Returns color string - caller should use App.Theme colors
    function getBatteryColor() {
        if (batteryCharging) return "#7A9984"  // info color
        if (batteryLevel > 50) return "#6B9B6F"  // success color
        if (batteryLevel > 20) return "#D4A574"  // warning color
        return "#C97064"  // error color
    }
}
