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

	// Direct Home without StackView for testing
	App.Home {
		id: homeScreen
		anchors.top: status.bottom
		anchors.bottom: parent.bottom
		anchors.left: parent.left
		anchors.right: parent.right
	}

	function navigateToSettings() {
		console.log("Navigate to settings")
	}
}
