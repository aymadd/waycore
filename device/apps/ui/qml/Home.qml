import QtQuick 2.15
import "." as App

Rectangle {
	id: home
	color: App.Theme.background

	Component.onCompleted: {
		console.log("Home component loaded, size:", width, "x", height)
	}

		Text {
		id: title
			text: "Waycore"
			color: App.Theme.textPrimary
			font.pixelSize: App.Theme.h2Size
		anchors.top: parent.top
		anchors.horizontalCenter: parent.horizontalCenter
		anchors.topMargin: App.Theme.spacingLarge
	}

	GridView {
			id: grid
		anchors.top: title.bottom
		anchors.bottom: parent.bottom
		anchors.left: parent.left
		anchors.right: parent.right
		anchors.margins: App.Theme.spacingLarge
		clip: true

		cellWidth: Math.max(100, Math.floor(width / 3))
		cellHeight: 120

		Component.onCompleted: {
			console.log("GridView loaded - size:", width, "x", height, "cellWidth:", cellWidth, "model count:", model.count)
		}

		model: ListModel {
			ListElement { name: "AI"; icon: "🤖" }
			ListElement { name: "Maps"; icon: "🗺️" }
			ListElement { name: "Compass"; icon: "🧭" }
			ListElement { name: "Meshtastic"; icon: "📡" }
			ListElement { name: "Settings"; icon: "⚙️" }
		}

				delegate: Rectangle {
			width: grid.cellWidth - App.Theme.spacingSmall
			height: grid.cellHeight - App.Theme.spacingSmall
			color: App.Theme.surfaceElevated
					radius: 8
					border.color: App.Theme.divider
					border.width: 1

					Column {
						anchors.centerIn: parent
						spacing: App.Theme.spacingSmall

						Text {
							anchors.horizontalCenter: parent.horizontalCenter
					text: model.icon
							font.pixelSize: 32
						}
						Text {
							anchors.horizontalCenter: parent.horizontalCenter
					text: model.name
							color: App.Theme.textPrimary
							font.pixelSize: App.Theme.bodySize
						}
					}

					MouseArea {
						anchors.fill: parent
						onClicked: {
					console.log("Open", model.name)
					if (model.name === "Settings") {
								var parentItem = home.parent
								while (parentItem && !parentItem.hasOwnProperty("navigateToSettings")) {
									parentItem = parentItem.parent
								}
								if (parentItem && parentItem.navigateToSettings) {
									parentItem.navigateToSettings()
						}
					}
				}
			}
		}
	}
}
