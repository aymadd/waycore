import QtQuick 2.15
import QtQuick.Layouts 1.15
import "." as App

Rectangle {
	id: home
	color: App.Theme.background

	ColumnLayout {
		anchors.fill: parent
		anchors.margins: App.Theme.spacingLarge
		spacing: App.Theme.spacingLarge

		Text {
			text: "Waycore"
			color: App.Theme.textPrimary
			font.pixelSize: App.Theme.h2Size
			Layout.alignment: Qt.AlignHCenter
		}

		GridLayout {
			id: grid
			columns: 3
			rowSpacing: App.Theme.spacingLarge
			columnSpacing: App.Theme.spacingLarge
			Layout.alignment: Qt.AlignHCenter

			repeater: Repeater {
				model: [
					{ name: "AI", color: App.Theme.surfaceElevated },
					{ name: "Map", color: App.Theme.surfaceElevated },
					{ name: "Settings", color: App.Theme.surfaceElevated }
				]
				delegate: Rectangle {
					width: 96; height: 96
					color: modelData.color
					radius: 8
					Text {
						anchors.centerIn: parent
						text: modelData.name
						color: App.Theme.textPrimary
						font.pixelSize: App.Theme.bodySize
					}
					MouseArea {
						anchors.fill: parent
						onClicked: console.log("Open", modelData.name)
					}
				}
			}
		}
	}
}
