import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import Qt.labs.settings 1.1
import "." as App
import "components" as UI

Rectangle {
	id: settings
	color: App.Theme.background

	Flickable {
		anchors.fill: parent
		anchors.margins: App.Theme.spacingLarge
		contentHeight: contentColumn.height
		clip: true

		ColumnLayout {
			id: contentColumn
			width: parent.width
			spacing: App.Theme.spacingLarge

			// Header with back button
			RowLayout {
				Layout.fillWidth: true
				spacing: App.Theme.spacingSmall

				Button {
					text: "← Back"
					onClicked: {
						var parentItem = settings.parent
						while (parentItem && !parentItem.hasOwnProperty("navigateBack")) {
							parentItem = parentItem.parent
						}
						if (parentItem && parentItem.navigateBack) {
							parentItem.navigateBack()
						}
					}
				}

				Text {
					text: "Settings"
					color: App.Theme.textPrimary
					font.pixelSize: App.Theme.h1Size
					font.bold: true
					Layout.fillWidth: true
				}
			}

			// Persistent app preferences
			Settings {
				id: appSettings
				category: "waycore.ui"
				property bool debug: false
				property string theme: "dark"
				property int brightness: 75
				property string temperatureUnit: "C"
				property string distanceUnit: "km"
				property string weightUnit: "kg"
			}

			Component.onCompleted: {
				App.SensorData.temperatureUnit = appSettings.temperatureUnit
			}

			// About Card
			UI.Card {
				Layout.fillWidth: true

				Text { text: "About"; color: App.Theme.textPrimary; font.pixelSize: App.Theme.h2Size }

				GridLayout {
					columns: 2
					rowSpacing: App.Theme.spacingSmall
					columnSpacing: App.Theme.spacingLarge
					width: parent.width

					Text { text: "Version"; color: App.Theme.textSecondary; font.pixelSize: App.Theme.bodySize }
					Text { text: SensorBridge ? SensorBridge.appVersion : "0.1.0-dev"; color: App.Theme.textPrimary; font.pixelSize: App.Theme.bodySize }

					Text { text: "Device"; color: App.Theme.textSecondary; font.pixelSize: App.Theme.bodySize }
					Text { text: SensorBridge ? SensorBridge.deviceModel : "Unknown"; color: App.Theme.textPrimary; font.pixelSize: App.Theme.bodySize; wrapMode: Text.WordWrap; Layout.fillWidth: true }

					Text { text: "Hostname"; color: App.Theme.textSecondary; font.pixelSize: App.Theme.bodySize }
					Text { text: SensorBridge ? SensorBridge.hostname : "waycore"; color: App.Theme.textPrimary; font.pixelSize: App.Theme.bodySize }

					Text { text: "Backend"; color: App.Theme.textSecondary; font.pixelSize: App.Theme.bodySize }
					Text {
						text: SensorBridge && SensorBridge.connected ? "Connected" : "Offline (mock data)"
						color: SensorBridge && SensorBridge.connected ? App.Theme.success : App.Theme.warning
						font.pixelSize: App.Theme.bodySize
					}
				}
			}

			// Display Card
			UI.Card {
				Layout.fillWidth: true

				Text { text: "Display"; color: App.Theme.textPrimary; font.pixelSize: App.Theme.h2Size }

				RowLayout {
					width: parent.width
					spacing: App.Theme.spacingSmall
					Text { text: "Brightness"; color: App.Theme.textSecondary; font.pixelSize: App.Theme.bodySize }
					Slider {
						from: 0; to: 100; value: appSettings.brightness
						onValueChanged: appSettings.brightness = Math.round(value)
						Layout.fillWidth: true
					}
					Text { text: appSettings.brightness + "%"; color: App.Theme.textPrimary }
				}
			}

			// Units Card
			UI.Card {
				Layout.fillWidth: true

				Text { text: "Units"; color: App.Theme.textPrimary; font.pixelSize: App.Theme.h2Size }

				RowLayout {
					width: parent.width
					spacing: App.Theme.spacingSmall
					Text { text: "Temperature"; color: App.Theme.textSecondary; font.pixelSize: App.Theme.bodySize; Layout.preferredWidth: 100 }
					ComboBox {
						model: ["Celsius (°C)", "Fahrenheit (°F)"]
						currentIndex: appSettings.temperatureUnit === "C" ? 0 : 1
						onActivated: {
							appSettings.temperatureUnit = currentIndex === 0 ? "C" : "F"
							App.SensorData.temperatureUnit = appSettings.temperatureUnit
						}
						Layout.fillWidth: true
					}
				}

				RowLayout {
					width: parent.width
					spacing: App.Theme.spacingSmall
					Text { text: "Distance"; color: App.Theme.textSecondary; font.pixelSize: App.Theme.bodySize; Layout.preferredWidth: 100 }
					ComboBox {
						model: ["Kilometers (km)", "Miles (mi)"]
						currentIndex: appSettings.distanceUnit === "km" ? 0 : 1
						onActivated: appSettings.distanceUnit = currentIndex === 0 ? "km" : "mi"
						Layout.fillWidth: true
					}
				}

				RowLayout {
					width: parent.width
					spacing: App.Theme.spacingSmall
					Text { text: "Weight"; color: App.Theme.textSecondary; font.pixelSize: App.Theme.bodySize; Layout.preferredWidth: 100 }
					ComboBox {
						model: ["Kilograms (kg)", "Pounds (lb)"]
						currentIndex: appSettings.weightUnit === "kg" ? 0 : 1
						onActivated: appSettings.weightUnit = currentIndex === 0 ? "kg" : "lb"
						Layout.fillWidth: true
					}
				}
			}

			// Developer Settings Card
			UI.Card {
				Layout.fillWidth: true

				Text { text: "Developer"; color: App.Theme.textPrimary; font.pixelSize: App.Theme.h2Size }

				RowLayout {
					width: parent.width
					spacing: App.Theme.spacingSmall
					Text { text: "Debug mode"; color: App.Theme.textSecondary; font.pixelSize: App.Theme.bodySize }
					CheckBox {
						checked: appSettings.debug
						onToggled: appSettings.debug = checked
					}
				}

				RowLayout {
					width: parent.width
					spacing: App.Theme.spacingSmall
					Text { text: "Theme"; color: App.Theme.textSecondary; font.pixelSize: App.Theme.bodySize }
					ComboBox {
						model: ["dark", "light"]
						currentIndex: appSettings.theme === "dark" ? 0 : 1
						onActivated: appSettings.theme = currentText
					}
				}
			}

			// Spacer at bottom
			Item { Layout.fillHeight: true }
		}
	}
}
