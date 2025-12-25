import QtQuick 2.15
import QtQuick.Controls 2.15
import "." as App
import "components" as UI

Item {
	id: shell

	Column {
		anchors.fill: parent
		spacing: App.Theme.spacingSmall

		StatusBar {
			id: status
			width: parent.width
			height: App.Theme.appBarHeight
		}

		// Simple navigation controls for MVP
		Row {
			spacing: App.Theme.spacingSmall
			anchors.horizontalCenter: parent.horizontalCenter
			UI.Button { text: "Home"; onClicked: { router.clear(); router.push("Home.qml") } }
			UI.Button { text: "Settings"; onClicked: { router.push("Settings.qml") } }
			UI.Button { text: "Back"; onClicked: { if (router.depth > 1) router.pop() } }
		}

		StackView {
			id: router
			anchors.left: parent.left
			anchors.right: parent.right
			anchors.top: status.bottom
			anchors.bottom: parent.bottom
			initialItem: Qt.resolvedUrl("Home.qml")
		}
	}

	function navigateToSettings() {
		router.push("Settings.qml")
	}
}
