import QtQuick 2.15
import QtQuick.Layouts 1.15
import ".." as App

/**
 * SignalBars - Visual signal quality indicator
 *
 * Shows 4 bars representing signal quality based on SNR:
 * - 4 bars (excellent): SNR > 5 dB
 * - 3 bars (good): SNR > 0 dB
 * - 2 bars (fair): SNR > -5 dB
 * - 1 bar (weak): SNR > -10 dB
 * - 0 bars (very weak): SNR <= -10 dB
 *
 * Usage:
 *   SignalBars {
 *       snr: 8.5
 *       width: 24
 *       height: 16
 *   }
 */
Item {
    id: signalBars

    property real snr: 0
    property bool hasSignal: !isNaN(snr) && snr !== null
    property int barCount: calculateBars(snr)

    width: 24
    height: 16

    // Colors
    property color excellentColor: "#4CAF50"  // Green
    property color goodColor: "#8BC34A"       // Light green
    property color fairColor: "#FFC107"       // Amber/Yellow
    property color weakColor: "#FF9800"       // Orange
    property color veryWeakColor: "#F44336"   // Red
    property color inactiveColor: "#424242"   // Dark gray

    function calculateBars(snrValue) {
        if (!hasSignal) return 0
        if (snrValue > 5) return 4
        if (snrValue > 0) return 3
        if (snrValue > -5) return 2
        if (snrValue > -10) return 1
        return 0
    }

    function getColor() {
        if (!hasSignal) return inactiveColor
        if (barCount === 4) return excellentColor
        if (barCount === 3) return goodColor
        if (barCount === 2) return fairColor
        if (barCount === 1) return weakColor
        return veryWeakColor
    }

    Row {
        anchors.fill: parent
        anchors.bottom: parent.bottom
        spacing: 2
        anchors.verticalCenter: parent.verticalCenter

        Repeater {
            model: 4

            Rectangle {
                property int barIndex: index
                property bool isActive: barIndex < signalBars.barCount

                width: (signalBars.width - 6) / 4  // 4 bars with 3 gaps
                height: {
                    // Bars increase in height: 25%, 50%, 75%, 100%
                    var baseHeight = signalBars.height
                    return baseHeight * (0.25 + (barIndex * 0.25))
                }
                anchors.bottom: parent.bottom
                radius: 1

                color: isActive ? signalBars.getColor() : signalBars.inactiveColor
                opacity: isActive ? 1.0 : 0.3

                Behavior on color {
                    ColorAnimation { duration: 200 }
                }

                Behavior on opacity {
                    NumberAnimation { duration: 200 }
                }
            }
        }
    }

    // Tooltip with actual values
    ToolTip {
        id: tooltip
        visible: mouseArea.containsMouse
        text: hasSignal ? "SNR: " + snr.toFixed(1) + " dB" : "No signal data"
        delay: 500
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
    }
}
