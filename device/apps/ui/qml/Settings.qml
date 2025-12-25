import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import Qt.labs.settings 1.1
import "." as App
import "components" as UI

Rectangle {
	id: settings
	color: App.Theme.background

	// Factory reset function (at root scope so it's accessible from Button)
	function performFactoryReset() {
		console.log("Factory reset: calling backend...")

		// Call backend factory reset via SensorBridge
		var success = false
		if (SensorBridge) {
			success = SensorBridge.factoryReset()
		}

		if (success) {
			resetStatusText.text = "✅ Factory reset complete"
			resetStatusText.color = App.Theme.success
			console.log("Factory reset successful")
		} else {
			resetStatusText.text = "⚠️ Reset completed (offline mode)"
			resetStatusText.color = App.Theme.warning
			console.log("Factory reset: backend not available, local settings reset")
		}

		resetButton.isResetting = false

		// Navigate home after a delay
		resetCompleteTimer.start()
	}

	// Timer at root scope for navigation after reset
	Timer {
		id: resetCompleteTimer
		interval: 1500
		onTriggered: {
			var shell = settings.parent
			while (shell && !shell.hasOwnProperty("navigateHome")) {
				shell = shell.parent
			}
			if (shell && shell.navigateHome) {
				shell.navigateHome()
			}
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

			// Persistent app preferences (defaults match backend: F, mi, lb)
			Settings {
				id: appSettings
				category: "waycore.ui"
				property bool debug: false
				property string theme: "dark"
				property int brightness: 75
				property string temperatureUnit: "F"
				property string distanceUnit: "mi"
				property string weightUnit: "lb"
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
						id: temperatureCombo
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
						id: distanceCombo
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
						id: weightCombo
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

			// Factory Reset Card
			UI.Card {
				Layout.fillWidth: true

				Text { text: "Reset"; color: App.Theme.textPrimary; font.pixelSize: App.Theme.h2Size }

				Text {
					text: "Factory reset will delete all notes, preferences, and restore default settings."
					color: App.Theme.textSecondary
					font.pixelSize: App.Theme.bodySize
					wrapMode: Text.WordWrap
					width: parent.width
				}

				Button {
					id: resetButton
					text: isResetting ? "Resetting..." : (confirmReset ? "Tap again to confirm" : "Factory Reset")
					width: parent.width
					enabled: !isResetting

					property bool confirmReset: false
					property bool isResetting: false

					onClicked: {
						if (isResetting) return

						if (confirmReset) {
							// Perform actual factory reset
							isResetting = true
							confirmReset = false
							resetStatusText.text = "Resetting..."
							resetStatusText.color = App.Theme.warning
							resetStatusText.visible = true

							// Reset local app settings to defaults
							appSettings.temperatureUnit = "F"
							appSettings.distanceUnit = "mi"
							appSettings.weightUnit = "lb"
							appSettings.brightness = 75
							appSettings.debug = false
							appSettings.theme = "dark"
							App.SensorData.temperatureUnit = "F"

							// Force ComboBox UI to update
							temperatureCombo.currentIndex = 1  // Fahrenheit
							distanceCombo.currentIndex = 1     // Miles
							weightCombo.currentIndex = 1       // Pounds

							// Call backend to reset data (function at root scope)
							settings.performFactoryReset()
						} else {
							confirmReset = true
							confirmTimer.start()
						}
					}

					Timer {
						id: confirmTimer
						interval: 3000
						onTriggered: resetButton.confirmReset = false
					}
				}

				Text {
					id: resetStatusText
					visible: false
					color: App.Theme.warning
					font.pixelSize: App.Theme.bodySize
				}
			}

			// Spacer at bottom
			Item { Layout.fillHeight: true }
		}
	}
}
