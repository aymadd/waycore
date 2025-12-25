import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "." as App
import "components" as UI

Rectangle {
	id: settingsSensors
	color: App.Theme.background

	// Sensors from registry
	property var sensorsList: SensorBridge ? SensorBridge.sensors : []

	// Refresh timer
	Timer {
		interval: 3000
		running: true
		repeat: true
		onTriggered: {
			if (SensorBridge) {
				SensorBridge.refreshSensors()
			}
		}
	}

	Component.onCompleted: {
		if (SensorBridge) {
			SensorBridge.refreshSensors()
		}
	}

	// Helper functions
	function getSensorIcon(sensorType) {
		switch(sensorType) {
			case "gps": return "📍"
			case "temperature": return "🌡️"
			case "pressure": return "🌀"
			case "accelerometer": return "📐"
			case "magnetometer": return "🧭"
			case "light": return "☀️"
			case "humidity": return "💧"
			case "battery": return "🔋"
			default: return "📟"
		}
	}

	function getStatusColor(status) {
		switch(status) {
			case "online": return App.Theme.success
			case "offline": return App.Theme.error
			case "error": return App.Theme.error
			case "calibrating": return App.Theme.warning
			default: return App.Theme.textSecondary
		}
	}

	function getStatusText(status) {
		switch(status) {
			case "online": return "Online"
			case "offline": return "Offline"
			case "error": return "Error"
			case "calibrating": return "Calibrating"
			default: return "Unknown"
		}
	}

	function formatSensorValue(sensor) {
		if (!sensor.last_value) return "No data"

		var val = sensor.last_value
		switch(sensor.type) {
			case "gps":
				if (!val.has_fix) return "No fix"
				return "Lat: " + val.latitude.toFixed(4) + "°, Lon: " + val.longitude.toFixed(4) + "°"
			case "temperature":
				return val.celsius.toFixed(1) + "°C / " + val.fahrenheit.toFixed(1) + "°F"
			case "pressure":
				return val.hPa.toFixed(1) + " hPa" + (val.altitude_m ? ", Alt: " + val.altitude_m.toFixed(0) + "m" : "")
			case "accelerometer":
				return "X: " + val.x.toFixed(2) + "g, Y: " + val.y.toFixed(2) + "g, Z: " + val.z.toFixed(2) + "g"
			case "magnetometer":
				return val.heading.toFixed(0) + "° " + val.cardinal + (val.calibrated ? " ✓" : " ⚠")
			case "light":
				return val.lux + " lux (" + val.condition + ")"
			case "battery":
				return val.level + "%" + (val.charging ? " ⚡" : "") + " @ " + val.voltage.toFixed(2) + "V"
			default:
				return JSON.stringify(val)
		}
	}

	Flickable {
		anchors.fill: parent
		anchors.margins: App.Theme.spacingLarge
		contentHeight: contentColumn.height
		clip: true

		ColumnLayout {
			id: contentColumn
			width: parent.width
			spacing: App.Theme.spacingMedium

			// Header
			RowLayout {
				Layout.fillWidth: true
				spacing: App.Theme.spacingSmall

				Button {
					text: "← Back"
					onClicked: {
						var parentItem = settingsSensors.parent
						while (parentItem && !parentItem.hasOwnProperty("navigateBack")) {
							parentItem = parentItem.parent
						}
						if (parentItem && parentItem.navigateBack) {
							parentItem.navigateBack()
						}
					}
				}

				Text {
					text: "🌡️ Sensors"
					color: App.Theme.textPrimary
					font.pixelSize: App.Theme.h1Size
					font.bold: true
					Layout.fillWidth: true
				}

				Button {
					text: "🔄"
					onClicked: {
						if (SensorBridge) {
							SensorBridge.discoverSensors()
						}
					}
					ToolTip.visible: hovered
					ToolTip.text: "Run sensor discovery"
				}
			}

			// Status bar
			Rectangle {
				Layout.fillWidth: true
				height: 32
				color: App.Theme.surface
				radius: 4

				RowLayout {
					anchors.fill: parent
					anchors.margins: App.Theme.spacingSmall

					Text {
						text: SensorBridge && SensorBridge.connected ? "🟢 Live data" : "🟡 Mock data"
						color: App.Theme.textSecondary
						font.pixelSize: App.Theme.captionSize
					}

					Item { Layout.fillWidth: true }

					Text {
						text: sensorsList.length + " sensors"
						color: App.Theme.textSecondary
						font.pixelSize: App.Theme.captionSize
					}
				}
			}

			// Sensor list - dynamically generated from registry
			Repeater {
				model: sensorsList

				UI.Card {
					Layout.fillWidth: true

					RowLayout {
						width: parent.width

						Text { text: getSensorIcon(modelData.type); font.pixelSize: 24 }

						ColumnLayout {
							Layout.fillWidth: true
							spacing: 2

							Text {
								text: modelData.name
								color: App.Theme.textPrimary
								font.pixelSize: App.Theme.bodySize
								font.bold: true
							}
							Text {
								text: getStatusText(modelData.status)
								color: getStatusColor(modelData.status)
								font.pixelSize: App.Theme.captionSize
							}
						}

						Rectangle {
							width: 12; height: 12; radius: 6
							color: getStatusColor(modelData.status)
						}
					}

					// Sensor reading
					Text {
						text: formatSensorValue(modelData)
						color: App.Theme.textPrimary
						font.pixelSize: App.Theme.captionSize
						wrapMode: Text.WordWrap
						width: parent.width
					}

					// Driver info (expandable)
					Text {
						text: "Driver: " + modelData.driver
						color: App.Theme.textSecondary
						font.pixelSize: App.Theme.captionSize
						visible: modelData.driver !== undefined
					}

					// Calibration button for magnetometer
					Button {
						text: "Calibrate"
						visible: modelData.type === "magnetometer" && modelData.last_value && !modelData.last_value.calibrated
						onClicked: {
							if (SensorBridge) {
								SensorBridge.calibrateCompass()
							}
						}
					}
				}
			}

			// Empty state
			Text {
				Layout.fillWidth: true
				text: "No sensors discovered.\nTap 🔄 to run discovery."
				color: App.Theme.textSecondary
				font.pixelSize: App.Theme.bodySize
				horizontalAlignment: Text.AlignHCenter
				visible: sensorsList.length === 0
			}

			Item { Layout.preferredHeight: App.Theme.spacingLarge }
		}
	}
}
