import QtQuick 2.15
import QtQuick.Layouts 1.15
import Qt.labs.settings 1.1
import "." as App
import "components" as UI

Rectangle {
	id: settings
	color: App.Theme.background

	ColumnLayout {
		anchors.fill: parent
		anchors.margins: App.Theme.spacingLarge
		spacing: App.Theme.spacingLarge

		UI.AppBar { title: "Settings" }

		// Persistent app preferences
		Settings {
			id: appSettings
			category: "waycore.ui"
			property bool debug: false
			property string theme: "dark"
			property int brightness: 75
		}

		UI.Card {
			contentItem: Column {
				spacing: App.Theme.spacingSmall
				UI.ListItem { text: "System Information"; secondaryText: "Version, model, uptime" }
				UI.ListItem { text: "System Actions"; secondaryText: "Reboot, Shutdown" }
				UI.ListItem { text: "Display"; secondaryText: "Brightness, timeout" }
				UI.ListItem { text: "Radio Settings"; secondaryText: "LoRa, Wi‑Fi" }
				UI.ListItem { text: "Power Settings"; secondaryText: "Mode, battery" }
				UI.ListItem { text: "Developer Settings"; secondaryText: "Debug, logging" }
				UI.ListItem { text: "About"; secondaryText: "Licenses, credits" }
			}
		}

		UI.Card {
			contentItem: Column {
				spacing: App.Theme.spacingSmall
				Text { text: "Display"; color: App.Theme.textPrimary; font.pixelSize: App.Theme.h2Size }
				RowLayout {
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
		}

		UI.Card {
			contentItem: Column {
				spacing: App.Theme.spacingSmall
				Text { text: "Developer Settings"; color: App.Theme.textPrimary; font.pixelSize: App.Theme.h2Size }
				RowLayout {
					spacing: App.Theme.spacingSmall
					Text { text: "Debug mode"; color: App.Theme.textSecondary; font.pixelSize: App.Theme.bodySize }
					CheckBox {
						checked: appSettings.debug
						onToggled: appSettings.debug = checked
					}
				}
				RowLayout {
					spacing: App.Theme.spacingSmall
					Text { text: "Theme"; color: App.Theme.textSecondary; font.pixelSize: App.Theme.bodySize }
					ComboBox {
						model: ["dark", "light"]
						currentIndex: appSettings.theme === "dark" ? 0 : 1
						onActivated: appSettings.theme = currentText
					}
				}
			}
		}
	}
}
