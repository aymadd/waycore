import QtQuick 2.15
import ".." as App

Rectangle {
	id: toast
	property string message: ""
	property int duration: 3000
	visible: false
	color: "#333333AA"
	radius: 8
	anchors.horizontalCenter: parent ? parent.horizontalCenter : undefined
	anchors.bottom: parent ? parent.bottom : undefined
	anchors.bottomMargin: App.Theme.spacingLarge
	width: Math.max(msg.implicitWidth + App.Theme.spacingLarge * 2, 288)
	height: 56

	Text {
		id: msg
		anchors.centerIn: parent
		text: toast.message
		color: "white"
	}

	function show(text) {
		toast.message = text
		toast.visible = true
		timer.restart()
	}

	Timer {
		id: timer
		interval: toast.duration
		onTriggered: toast.visible = false
	}
}
