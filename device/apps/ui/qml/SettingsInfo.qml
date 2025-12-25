import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "." as App
import "components" as UI

Rectangle {
	id: settingsInfo
	color: App.Theme.background

	// System info from SensorBridge
	property string appVersion: SensorBridge ? SensorBridge.appVersion : "0.1.0-dev"
	property string deviceModel: SensorBridge ? SensorBridge.deviceModel : "Waycore Dev Board"
	property string hostname: SensorBridge ? SensorBridge.hostname : "waycore"
	property bool connected: SensorBridge ? SensorBridge.connected : false

	// Runtime tracking
	property int appUptime: 0
	Timer {
		interval: 1000
		running: true
		repeat: true
		onTriggered: appUptime++
	}

	function formatUptime(seconds) {
		var hours = Math.floor(seconds / 3600)
		var mins = Math.floor((seconds % 3600) / 60)
		var secs = seconds % 60
		if (hours > 0) {
			return hours + "h " + mins + "m " + secs + "s"
		} else if (mins > 0) {
			return mins + "m " + secs + "s"
		}
		return secs + "s"
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
						var parentItem = settingsInfo.parent
						while (parentItem && !parentItem.hasOwnProperty("navigateBack")) {
							parentItem = parentItem.parent
						}
						if (parentItem && parentItem.navigateBack) {
							parentItem.navigateBack()
						}
					}
				}

				Text {
					text: "ℹ️ Info"
					color: App.Theme.textPrimary
					font.pixelSize: App.Theme.h1Size
					font.bold: true
					Layout.fillWidth: true
				}
			}

			// Device Information
			UI.Card {
				Layout.fillWidth: true

				Text { text: "Device"; color: App.Theme.textPrimary; font.pixelSize: App.Theme.h2Size }

				GridLayout {
					columns: 2
					width: parent.width
					rowSpacing: App.Theme.spacingExtraSmall
					columnSpacing: App.Theme.spacingLarge

					Text { text: "Model"; color: App.Theme.textSecondary; font.pixelSize: App.Theme.captionSize }
					Text { text: deviceModel; color: App.Theme.textPrimary; font.pixelSize: App.Theme.captionSize; wrapMode: Text.WordWrap; Layout.fillWidth: true }

					Text { text: "Serial"; color: App.Theme.textSecondary; font.pixelSize: App.Theme.captionSize }
					Text { text: "WC-2024-001234"; color: App.Theme.textPrimary; font.pixelSize: App.Theme.captionSize }

					Text { text: "Hardware Rev"; color: App.Theme.textSecondary; font.pixelSize: App.Theme.captionSize }
					Text { text: "v1.0"; color: App.Theme.textPrimary; font.pixelSize: App.Theme.captionSize }

					Text { text: "Hostname"; color: App.Theme.textSecondary; font.pixelSize: App.Theme.captionSize }
					Text { text: hostname; color: App.Theme.textPrimary; font.pixelSize: App.Theme.captionSize }

					Text { text: "CPU"; color: App.Theme.textSecondary; font.pixelSize: App.Theme.captionSize }
					Text { text: "ARM Cortex-A76 (4 cores)"; color: App.Theme.textPrimary; font.pixelSize: App.Theme.captionSize; wrapMode: Text.WordWrap; Layout.fillWidth: true }

					Text { text: "RAM"; color: App.Theme.textSecondary; font.pixelSize: App.Theme.captionSize }
					Text { text: "8 GB"; color: App.Theme.textPrimary; font.pixelSize: App.Theme.captionSize }

					Text { text: "Storage"; color: App.Theme.textSecondary; font.pixelSize: App.Theme.captionSize }
					Text { text: "32 GB eMMC"; color: App.Theme.textPrimary; font.pixelSize: App.Theme.captionSize }
				}
			}

			// Software Information
			UI.Card {
				Layout.fillWidth: true

				Text { text: "Software"; color: App.Theme.textPrimary; font.pixelSize: App.Theme.h2Size }

				GridLayout {
					columns: 2
					width: parent.width
					rowSpacing: App.Theme.spacingExtraSmall
					columnSpacing: App.Theme.spacingLarge

					Text { text: "App Version"; color: App.Theme.textSecondary; font.pixelSize: App.Theme.captionSize }
					Text { text: appVersion; color: App.Theme.textPrimary; font.pixelSize: App.Theme.captionSize }

					Text { text: "Build"; color: App.Theme.textSecondary; font.pixelSize: App.Theme.captionSize }
					Text { text: "2024.12.25-abc1234"; color: App.Theme.textPrimary; font.pixelSize: App.Theme.captionSize }

					Text { text: "Python"; color: App.Theme.textSecondary; font.pixelSize: App.Theme.captionSize }
					Text { text: "3.11.0"; color: App.Theme.textPrimary; font.pixelSize: App.Theme.captionSize }

					Text { text: "Qt/QML"; color: App.Theme.textSecondary; font.pixelSize: App.Theme.captionSize }
					Text { text: "6.5.0"; color: App.Theme.textPrimary; font.pixelSize: App.Theme.captionSize }

					Text { text: "OS"; color: App.Theme.textSecondary; font.pixelSize: App.Theme.captionSize }
					Text { text: "Raspberry Pi OS Lite (Bookworm)"; color: App.Theme.textPrimary; font.pixelSize: App.Theme.captionSize; wrapMode: Text.WordWrap; Layout.fillWidth: true }

					Text { text: "Kernel"; color: App.Theme.textSecondary; font.pixelSize: App.Theme.captionSize }
					Text { text: "Linux 6.1.0-rpi7-rpi-v8"; color: App.Theme.textPrimary; font.pixelSize: App.Theme.captionSize; wrapMode: Text.WordWrap; Layout.fillWidth: true }
				}
			}

			// Network Information
			UI.Card {
				Layout.fillWidth: true

				Text { text: "Network"; color: App.Theme.textPrimary; font.pixelSize: App.Theme.h2Size }

				GridLayout {
					columns: 2
					width: parent.width
					rowSpacing: App.Theme.spacingExtraSmall
					columnSpacing: App.Theme.spacingLarge

					Text { text: "WiFi IP"; color: App.Theme.textSecondary; font.pixelSize: App.Theme.captionSize }
					Text { text: "192.168.1.42"; color: App.Theme.textPrimary; font.pixelSize: App.Theme.captionSize }

					Text { text: "WiFi MAC"; color: App.Theme.textSecondary; font.pixelSize: App.Theme.captionSize }
					Text { text: "DC:A6:32:XX:XX:XX"; color: App.Theme.textPrimary; font.pixelSize: App.Theme.captionSize }

					Text { text: "BT MAC"; color: App.Theme.textSecondary; font.pixelSize: App.Theme.captionSize }
					Text { text: "DC:A6:32:XX:XX:XY"; color: App.Theme.textPrimary; font.pixelSize: App.Theme.captionSize }

					Text { text: "LoRA Node"; color: App.Theme.textSecondary; font.pixelSize: App.Theme.captionSize }
					Text { text: "!abc12345"; color: App.Theme.textPrimary; font.pixelSize: App.Theme.captionSize }

					Text { text: "Gateway"; color: App.Theme.textSecondary; font.pixelSize: App.Theme.captionSize }
					Text { text: "192.168.1.1"; color: App.Theme.textPrimary; font.pixelSize: App.Theme.captionSize }

					Text { text: "DNS"; color: App.Theme.textSecondary; font.pixelSize: App.Theme.captionSize }
					Text { text: "8.8.8.8, 8.8.4.4"; color: App.Theme.textPrimary; font.pixelSize: App.Theme.captionSize }
				}
			}

			// Runtime Information
			UI.Card {
				Layout.fillWidth: true

				Text { text: "Runtime"; color: App.Theme.textPrimary; font.pixelSize: App.Theme.h2Size }

				GridLayout {
					columns: 2
					width: parent.width
					rowSpacing: App.Theme.spacingExtraSmall
					columnSpacing: App.Theme.spacingLarge

					Text { text: "System Uptime"; color: App.Theme.textSecondary; font.pixelSize: App.Theme.captionSize }
					Text {
						text: SensorBridge ? formatUptime(SensorBridge.uptimeSeconds) : "Unknown"
						color: App.Theme.textPrimary
						font.pixelSize: App.Theme.captionSize
					}

					Text { text: "App Uptime"; color: App.Theme.textSecondary; font.pixelSize: App.Theme.captionSize }
					Text { text: formatUptime(appUptime); color: App.Theme.textPrimary; font.pixelSize: App.Theme.captionSize }

					Text { text: "Memory Usage"; color: App.Theme.textSecondary; font.pixelSize: App.Theme.captionSize }
					Text { text: "512 MB / 8 GB (6%)"; color: App.Theme.textPrimary; font.pixelSize: App.Theme.captionSize }

					Text { text: "CPU Temp"; color: App.Theme.textSecondary; font.pixelSize: App.Theme.captionSize }
					Text { text: "45°C"; color: App.Theme.success; font.pixelSize: App.Theme.captionSize }

					Text { text: "Battery"; color: App.Theme.textSecondary; font.pixelSize: App.Theme.captionSize }
					Text {
						text: (SensorBridge ? SensorBridge.batteryLevel : 85) + "%" + (SensorBridge && SensorBridge.batteryCharging ? " ⚡" : "")
						color: (SensorBridge ? SensorBridge.batteryLevel : 85) > 20 ? App.Theme.success : App.Theme.error
						font.pixelSize: App.Theme.captionSize
					}

					Text { text: "Backend"; color: App.Theme.textSecondary; font.pixelSize: App.Theme.captionSize }
					Text {
						text: connected ? "Connected" : "Offline"
						color: connected ? App.Theme.success : App.Theme.warning
						font.pixelSize: App.Theme.captionSize
					}
				}
			}

			Item { Layout.preferredHeight: App.Theme.spacingLarge }
		}
	}
}
