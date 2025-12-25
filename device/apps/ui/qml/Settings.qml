import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "." as App
import "components" as UI

Rectangle {
	id: settings
	color: App.Theme.background

	// Settings categories with icons and descriptions
	ListModel {
		id: categoriesModel
		ListElement {
			name: "General"
			icon: "⚙️"
			description: "Units, display, storage & reset"
			route: "SettingsGeneral"
		}
		ListElement {
			name: "Controls"
			icon: "📡"
			description: "LoRA, WiFi, Bluetooth & LTE"
			route: "SettingsControls"
		}
		ListElement {
			name: "Sensors"
			icon: "🌡️"
			description: "GPS, temperature, compass & more"
			route: "SettingsSensors"
		}
		ListElement {
			name: "Info"
			icon: "ℹ️"
			description: "Device & software information"
			route: "SettingsInfo"
		}
	}

	ColumnLayout {
		anchors.fill: parent
		anchors.margins: App.Theme.spacingLarge
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

		// Category tiles grid
		GridView {
			id: categoryGrid
			Layout.fillWidth: true
			Layout.fillHeight: true
			clip: true

			cellWidth: width / 2
			cellHeight: 140

			model: categoriesModel

			delegate: Item {
				width: categoryGrid.cellWidth
				height: categoryGrid.cellHeight

				Rectangle {
					anchors.fill: parent
					anchors.margins: App.Theme.spacingSmall
					color: App.Theme.surface
					radius: 12
					border.color: App.Theme.divider
					border.width: 1

					ColumnLayout {
						anchors.fill: parent
						anchors.margins: App.Theme.spacingMedium
						spacing: App.Theme.spacingSmall

						Text {
							text: model.icon
							font.pixelSize: 32
							Layout.alignment: Qt.AlignHCenter
						}

						Text {
							text: model.name
							color: App.Theme.textPrimary
							font.pixelSize: App.Theme.h3Size
							font.bold: true
							Layout.alignment: Qt.AlignHCenter
						}

						Text {
							text: model.description
							color: App.Theme.textSecondary
							font.pixelSize: App.Theme.captionSize
							horizontalAlignment: Text.AlignHCenter
							wrapMode: Text.WordWrap
							Layout.fillWidth: true
							Layout.alignment: Qt.AlignHCenter
						}
					}

					MouseArea {
						anchors.fill: parent
						onClicked: {
							console.log("Navigate to:", model.route)
							var shell = settings.parent
							while (shell && !shell.hasOwnProperty("navigateTo")) {
								shell = shell.parent
							}
							if (shell && shell.navigateTo) {
								shell.navigateTo(model.route)
							}
						}
					}
				}
			}
		}

		// Connection status indicator at bottom
		Rectangle {
			Layout.fillWidth: true
			height: 40
			color: App.Theme.surface
			radius: 8

			RowLayout {
				anchors.fill: parent
				anchors.margins: App.Theme.spacingSmall

				Text {
					text: SensorBridge && SensorBridge.connected ? "🟢 Backend Connected" : "🟡 Offline Mode"
					color: SensorBridge && SensorBridge.connected ? App.Theme.success : App.Theme.warning
					font.pixelSize: App.Theme.captionSize
				}

				Item { Layout.fillWidth: true }

				Text {
					text: "v" + (SensorBridge ? SensorBridge.appVersion : "0.1.0")
					color: App.Theme.textSecondary
					font.pixelSize: App.Theme.captionSize
				}
			}
		}
	}
}
