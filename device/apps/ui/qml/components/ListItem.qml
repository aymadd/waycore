import QtQuick 2.15
import ".." as App

Rectangle {
	id: item
	height: 56
	color: "transparent"
	border.color: App.Theme.divider
	property string text: ""
	property string secondaryText: ""
	signal clicked()

	Column {
		anchors.fill: parent
		anchors.margins: App.Theme.spacingMedium
		spacing: App.Theme.spacingXS
		Text { text: item.text; color: App.Theme.textPrimary; font.pixelSize: App.Theme.bodySize }
		Text { text: item.secondaryText; color: App.Theme.textSecondary; font.pixelSize: App.Theme.bodySize }
	}
	MouseArea { anchors.fill: parent; onClicked: item.clicked() }
}
