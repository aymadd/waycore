import QtQuick 2.15
import QtQuick.Window 2.15
import "." as App

Window {
	id: root
	width: 480
	height: 800
	visible: true
	color: App.Theme.background
	title: "Waycore"

	AppShell {
		anchors.fill: parent
	}
}
