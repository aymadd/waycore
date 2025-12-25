import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "." as App
import "components" as UI

Rectangle {
	id: settingsControls
	color: App.Theme.background

	// Radio states (would come from backend in production)
	property bool loraEnabled: true
	property bool wifiEnabled: true
	property bool bluetoothEnabled: false
	property bool lteEnabled: false

	// Mock status data
	property string loraStatus: loraEnabled ? "Connected" : "Off"
	property string wifiStatus: wifiEnabled ? "Connected" : "Off"
	property string bluetoothStatus: bluetoothEnabled ? "On" : "Off"
	property string lteStatus: lteEnabled ? "No Signal" : "Off"

	Flickable {
		anchors.fill: parent
		anchors.margins: App.Theme.spacingLarge
		contentHeight: contentColumn.height
		clip: true

		ColumnLayout {
			id: contentColumn
			width: parent.width
			spacing: App.Theme.spacingLarge

			// Header
			RowLayout {
				Layout.fillWidth: true
				spacing: App.Theme.spacingSmall

				Button {
					text: "← Back"
					onClicked: {
						var parentItem = settingsControls.parent
						while (parentItem && !parentItem.hasOwnProperty("navigateBack")) {
							parentItem = parentItem.parent
						}
						if (parentItem && parentItem.navigateBack) {
							parentItem.navigateBack()
						}
					}
				}

				Text {
					text: "📡 Controls"
					color: App.Theme.textPrimary
					font.pixelSize: App.Theme.h1Size
					font.bold: true
					Layout.fillWidth: true
				}
			}

			// LoRA Card
			UI.Card {
				Layout.fillWidth: true

				RowLayout {
					width: parent.width

					Text { text: "📡"; font.pixelSize: 24 }

					ColumnLayout {
						Layout.fillWidth: true
						spacing: 2

						Text {
							text: "LoRA (Meshtastic)"
							color: App.Theme.textPrimary
							font.pixelSize: App.Theme.bodySize
							font.bold: true
						}
						Text {
							text: loraStatus
							color: loraEnabled ? App.Theme.success : App.Theme.textSecondary
							font.pixelSize: App.Theme.captionSize
						}
					}

					Switch {
						checked: loraEnabled
						onToggled: {
							loraEnabled = checked
							loraStatus = checked ? "Connecting..." : "Off"
							if (checked) {
								loraConnectTimer.start()
							}
						}
					}
				}

				// Expandable details
				ColumnLayout {
					width: parent.width
					visible: loraEnabled
					spacing: App.Theme.spacingExtraSmall

					Rectangle { width: parent.width; height: 1; color: App.Theme.divider }

					GridLayout {
						columns: 2
						width: parent.width

						Text { text: "Channel"; color: App.Theme.textSecondary; font.pixelSize: App.Theme.captionSize }
						Text { text: "LongFast"; color: App.Theme.textPrimary; font.pixelSize: App.Theme.captionSize }

						Text { text: "TX Power"; color: App.Theme.textSecondary; font.pixelSize: App.Theme.captionSize }
						Text { text: "20 dBm"; color: App.Theme.textPrimary; font.pixelSize: App.Theme.captionSize }

						Text { text: "Nodes"; color: App.Theme.textSecondary; font.pixelSize: App.Theme.captionSize }
						Text { text: "3 in range"; color: App.Theme.textPrimary; font.pixelSize: App.Theme.captionSize }
					}
				}

				Timer {
					id: loraConnectTimer
					interval: 1500
					onTriggered: loraStatus = "Connected"
				}
			}

			// WiFi Card
			UI.Card {
				Layout.fillWidth: true

				RowLayout {
					width: parent.width

					Text { text: "📶"; font.pixelSize: 24 }

					ColumnLayout {
						Layout.fillWidth: true
						spacing: 2

						Text {
							text: "WiFi"
							color: App.Theme.textPrimary
							font.pixelSize: App.Theme.bodySize
							font.bold: true
						}
						Text {
							text: wifiStatus
							color: wifiEnabled ? App.Theme.success : App.Theme.textSecondary
							font.pixelSize: App.Theme.captionSize
						}
					}

					Switch {
						checked: wifiEnabled
						onToggled: {
							wifiEnabled = checked
							wifiStatus = checked ? "Scanning..." : "Off"
							if (checked) {
								wifiConnectTimer.start()
							}
						}
					}
				}

				ColumnLayout {
					width: parent.width
					visible: wifiEnabled
					spacing: App.Theme.spacingExtraSmall

					Rectangle { width: parent.width; height: 1; color: App.Theme.divider }

					GridLayout {
						columns: 2
						width: parent.width

						Text { text: "Network"; color: App.Theme.textSecondary; font.pixelSize: App.Theme.captionSize }
						Text { text: "HomeNetwork"; color: App.Theme.textPrimary; font.pixelSize: App.Theme.captionSize }

						Text { text: "Signal"; color: App.Theme.textSecondary; font.pixelSize: App.Theme.captionSize }
						Text { text: "████░ Strong"; color: App.Theme.success; font.pixelSize: App.Theme.captionSize }

						Text { text: "IP"; color: App.Theme.textSecondary; font.pixelSize: App.Theme.captionSize }
						Text { text: "192.168.1.42"; color: App.Theme.textPrimary; font.pixelSize: App.Theme.captionSize }
					}
				}

				Timer {
					id: wifiConnectTimer
					interval: 2000
					onTriggered: wifiStatus = "Connected"
				}
			}

			// Bluetooth Card
			UI.Card {
				Layout.fillWidth: true

				RowLayout {
					width: parent.width

					Text { text: "🔵"; font.pixelSize: 24 }

					ColumnLayout {
						Layout.fillWidth: true
						spacing: 2

						Text {
							text: "Bluetooth"
							color: App.Theme.textPrimary
							font.pixelSize: App.Theme.bodySize
							font.bold: true
						}
						Text {
							text: bluetoothStatus
							color: bluetoothEnabled ? App.Theme.info : App.Theme.textSecondary
							font.pixelSize: App.Theme.captionSize
						}
					}

					Switch {
						checked: bluetoothEnabled
						onToggled: {
							bluetoothEnabled = checked
							bluetoothStatus = checked ? "On" : "Off"
						}
					}
				}

				ColumnLayout {
					width: parent.width
					visible: bluetoothEnabled
					spacing: App.Theme.spacingExtraSmall

					Rectangle { width: parent.width; height: 1; color: App.Theme.divider }

					Text {
						text: "No paired devices"
						color: App.Theme.textSecondary
						font.pixelSize: App.Theme.captionSize
					}

					Button {
						text: "Scan for devices"
						width: parent.width
						onClicked: console.log("Scanning for Bluetooth devices...")
					}
				}
			}

			// LTE Card
			UI.Card {
				Layout.fillWidth: true

				RowLayout {
					width: parent.width

					Text { text: "📱"; font.pixelSize: 24 }

					ColumnLayout {
						Layout.fillWidth: true
						spacing: 2

						Text {
							text: "LTE / Cellular"
							color: App.Theme.textPrimary
							font.pixelSize: App.Theme.bodySize
							font.bold: true
						}
						Text {
							text: lteStatus
							color: lteEnabled ? (lteStatus === "Connected" ? App.Theme.success : App.Theme.warning) : App.Theme.textSecondary
							font.pixelSize: App.Theme.captionSize
						}
					}

					Switch {
						checked: lteEnabled
						onToggled: {
							lteEnabled = checked
							lteStatus = checked ? "Searching..." : "Off"
							if (checked) {
								lteConnectTimer.start()
							}
						}
					}
				}

				ColumnLayout {
					width: parent.width
					visible: lteEnabled
					spacing: App.Theme.spacingExtraSmall

					Rectangle { width: parent.width; height: 1; color: App.Theme.divider }

					GridLayout {
						columns: 2
						width: parent.width

						Text { text: "Carrier"; color: App.Theme.textSecondary; font.pixelSize: App.Theme.captionSize }
						Text { text: "No Service"; color: App.Theme.warning; font.pixelSize: App.Theme.captionSize }

						Text { text: "Signal"; color: App.Theme.textSecondary; font.pixelSize: App.Theme.captionSize }
						Text { text: "░░░░░ None"; color: App.Theme.error; font.pixelSize: App.Theme.captionSize }
					}
				}

				Timer {
					id: lteConnectTimer
					interval: 3000
					onTriggered: lteStatus = "No Signal"
				}
			}

			Item { Layout.preferredHeight: App.Theme.spacingLarge }
		}
	}
}
