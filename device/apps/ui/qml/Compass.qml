import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "." as App
import "components" as UI

Rectangle {
    id: compass
    color: App.Theme.background

    // Compass data from SensorBridge
    property real heading: SensorBridge ? SensorBridge.compassHeading : 0
    property string cardinal: SensorBridge ? SensorBridge.compassCardinal : "N"
    property bool calibrated: SensorBridge ? SensorBridge.compassCalibrated : false
    property bool connected: SensorBridge ? SensorBridge.connected : false

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: App.Theme.spacingMedium
        spacing: App.Theme.spacingSmall

        // Header with back button
        RowLayout {
            Layout.fillWidth: true
            spacing: App.Theme.spacingSmall

            Button {
                text: "← Back"
                onClicked: {
                    var parentItem = compass.parent
                    while (parentItem && !parentItem.hasOwnProperty("navigateBack")) {
                        parentItem = parentItem.parent
                    }
                    if (parentItem && parentItem.navigateBack) {
                        parentItem.navigateBack()
                    }
                }
            }

            Text {
                text: "Compass"
                color: App.Theme.textPrimary
                font.pixelSize: App.Theme.h2Size
                font.bold: true
                Layout.fillWidth: true
            }

            // Status indicators
            Row {
                spacing: 8
                Rectangle {
                    width: 10; height: 10; radius: 5
                    color: connected ? App.Theme.success : App.Theme.warning
                }
                Text {
                    text: connected ? "Live" : "Mock"
                    color: App.Theme.textSecondary
                    font.pixelSize: 12
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
        }

        // Main compass display - takes remaining space
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            // Compass rose
            Rectangle {
                id: compassRose
                anchors.centerIn: parent
                width: Math.min(parent.width, parent.height - 20)
                height: width
                radius: width / 2
                color: App.Theme.surface
                border.color: App.Theme.divider
                border.width: 2

                // Cardinal directions (rotates with heading)
                Item {
                    anchors.fill: parent
                    rotation: -heading

                    Behavior on rotation {
                        NumberAnimation { duration: 150; easing.type: Easing.OutQuad }
                    }

                    // North marker
                    Text {
                        text: "N"
                        color: App.Theme.error
                        font.pixelSize: 22
                        font.bold: true
                        anchors.horizontalCenter: parent.horizontalCenter
                        anchors.top: parent.top
                        anchors.topMargin: 12
                    }

                    // South
                    Text {
                        text: "S"
                        color: App.Theme.textSecondary
                        font.pixelSize: 18
                        anchors.horizontalCenter: parent.horizontalCenter
                        anchors.bottom: parent.bottom
                        anchors.bottomMargin: 12
                    }

                    // East
                    Text {
                        text: "E"
                        color: App.Theme.textSecondary
                        font.pixelSize: 18
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.right: parent.right
                        anchors.rightMargin: 12
                    }

                    // West
                    Text {
                        text: "W"
                        color: App.Theme.textSecondary
                        font.pixelSize: 18
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.left: parent.left
                        anchors.leftMargin: 12
                    }

                    // Degree marks
                    Repeater {
                        model: 36
                        Rectangle {
                            width: index % 9 === 0 ? 3 : 1
                            height: index % 9 === 0 ? 15 : 8
                            color: App.Theme.textSecondary
                            anchors.horizontalCenter: parent.horizontalCenter
                            anchors.top: parent.top
                            anchors.topMargin: 4
                            transformOrigin: Item.Bottom
                            transform: Rotation {
                                origin.x: width / 2
                                origin.y: compassRose.height / 2 - 4
                                angle: index * 10
                            }
                        }
                    }
                }

                // Fixed needle indicator (pointing up)
                Rectangle {
                    width: 4
                    height: compassRose.height / 2 - 60
                    color: App.Theme.primary
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.top: parent.top
                    anchors.topMargin: 40
                    radius: 2
                }

                // Center circle with heading display
                Rectangle {
                    width: 100
                    height: 100
                    radius: 50
                    color: App.Theme.surfaceElevated
                    border.color: App.Theme.primary
                    border.width: 2
                    anchors.centerIn: parent

                    Column {
                        anchors.centerIn: parent
                        spacing: 2

                        Text {
                            text: heading.toFixed(0) + "°"
                            color: App.Theme.textPrimary
                            font.pixelSize: 28
                            font.bold: true
                            anchors.horizontalCenter: parent.horizontalCenter
                        }
                        Text {
                            text: cardinal
                            color: App.Theme.textSecondary
                            font.pixelSize: 16
                            anchors.horizontalCenter: parent.horizontalCenter
                        }
                    }
                }
            }
        }

        // Bottom status bar
        Rectangle {
            Layout.fillWidth: true
            height: 40
            color: App.Theme.surface
            radius: 8

            RowLayout {
                anchors.fill: parent
                anchors.margins: App.Theme.spacingSmall

                Text {
                    text: "Calibration: " + (calibrated ? "✓ OK" : "⚠ Needed")
                    color: calibrated ? App.Theme.success : App.Theme.warning
                    font.pixelSize: App.Theme.bodySize
                }

                Item { Layout.fillWidth: true }

                Button {
                    text: "Calibrate"
                    visible: !calibrated
                    onClicked: {
                        if (SensorBridge) {
                            SensorBridge.calibrateCompass()
                        }
                    }
                }
            }
        }
    }

    // Refresh timer for smooth updates
    Timer {
        interval: 100
        running: true
        repeat: true
        onTriggered: {
            if (SensorBridge) {
                SensorBridge.refreshCompass()
            }
        }
    }
}
