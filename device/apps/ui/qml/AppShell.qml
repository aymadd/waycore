import QtQuick 2.15
import QtQuick.Controls 2.15
import "." as App
import "components" as UI

Item {
	id: shell

	App.StatusBar {
		id: status
		anchors.top: parent.top
		anchors.left: parent.left
		anchors.right: parent.right
		height: App.Theme.appBarHeight
	}

	StackView {
		id: router
		anchors.top: status.bottom
		anchors.bottom: parent.bottom
		anchors.left: parent.left
		anchors.right: parent.right

		initialItem: homeComponent

		Component {
			id: homeComponent
			App.Home {}
		}

		Component {
			id: settingsComponent
			App.Settings {}
		}
	}

	function navigateToSettings() {
		console.log("Navigate to settings")
		router.push(settingsComponent)
	}

	function navigateBack() {
		if (router.depth > 1) {
			router.pop()
		}
	}

	function navigateHome() {
		router.pop(null)  // Pop to root
	}
}
