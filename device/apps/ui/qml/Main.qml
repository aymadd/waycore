import QtQuick 2.15
import QtQuick.Window 2.15
import QtQuick.VirtualKeyboard 2.15
import "." as App

Window {
	id: root
	width: 480
	height: 800
	visible: true
	color: App.Theme.background
	title: "Waycore"

	App.AppShell {
		anchors.fill: parent
		anchors.bottomMargin: inputPanel.active ? inputPanel.height : 0
	}

	// Virtual keyboard for touchscreen input
	// Only appears when a text input field is focused
	InputPanel {
		id: inputPanel
		z: 99
		y: inputPanel.active ? root.height - inputPanel.height : root.height
		anchors.left: parent.left
		anchors.right: parent.right

		Behavior on y {
			NumberAnimation {
				duration: 200
				easing.type: Easing.InOutQuad
			}
		}
	}
}
