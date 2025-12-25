import QtQuick 2.15
import ".." as App

Rectangle {
	id: btn
	property string text: ""
	property string variant: "contained" // contained | outlined | text
	signal clicked()
	height: App.Theme.buttonHeight
	radius: 4
	color: variant === "contained" ? App.Theme.primary : "transparent"
	border.color: variant === "outlined" ? App.Theme.primaryLight : "transparent"
	border.width: variant === "outlined" ? 1 : 0

	Text {
		anchors.centerIn: parent
		text: btn.text
		color: variant === "contained" ? App.Theme.textPrimary : App.Theme.textPrimary
		font.pixelSize: App.Theme.bodySize
	}
	MouseArea { anchors.fill: parent; onClicked: btn.clicked() }
}
