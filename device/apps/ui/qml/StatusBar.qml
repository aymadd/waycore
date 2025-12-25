import QtQuick 2.15
import QtQuick.Layouts 1.15
import "." as App

Rectangle {
	id: bar
	color: App.Theme.surface
	height: App.Theme.appBarHeight

	// Sensor data singleton (shared across all components)

	RowLayout {
		anchors.fill: parent
		anchors.margins: App.Theme.spacingSmall
		spacing: App.Theme.spacingMedium

		// Battery indicator
		Row {
			spacing: 4
			Layout.alignment: Qt.AlignVCenter

			Text {
				text: App.SensorData.getBatteryIcon()
				color: App.SensorData.getBatteryColor()
				font.pixelSize: App.Theme.bodySize
			}
			Text {
				text: App.SensorData.batteryLevel + "%"
				color: App.SensorData.getBatteryColor()
				font.pixelSize: App.Theme.bodySize
			}
		}

		// Temperature indicator
		Text {
			text: App.SensorData.temperatureString
			color: App.Theme.textPrimary
			font.pixelSize: App.Theme.bodySize
		}

		Item { Layout.fillWidth: true }  // Spacer

		// Time indicator
		Column {
			Layout.alignment: Qt.AlignVCenter
			spacing: 2

			Text {
				text: App.SensorData.currentTime
				color: App.Theme.textPrimary
				font.pixelSize: App.Theme.bodySize
				font.bold: true
			}
			Text {
				text: App.SensorData.currentDate
				color: App.Theme.textSecondary
				font.pixelSize: 10
			}
		}
	}
}
