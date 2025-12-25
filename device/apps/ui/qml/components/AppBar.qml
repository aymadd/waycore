import QtQuick 2.15
import QtQuick.Layouts 1.15
import ".." as App

Rectangle {
	id: bar
	color: App.Theme.surface
	height: App.Theme.appBarHeight
	property string title: ""
	property bool showBackButton: false
	signal backClicked()

	RowLayout {
		anchors.fill: parent
		anchors.margins: App.Theme.spacingSmall
		spacing: App.Theme.spacingSmall

		Rectangle {
			id: backBtn
			visible: bar.showBackButton
			width: App.Theme.appBarHeight - App.Theme.spacingSmall * 2
			height: App.Theme.appBarHeight - App.Theme.spacingSmall * 2
			color: "transparent"
			border.color: App.Theme.divider
			radius: 4
			Text { anchors.centerIn: parent; text: "<"; color: App.Theme.textPrimary; font.pixelSize: App.Theme.h2Size }
			MouseArea { anchors.fill: parent; onClicked: bar.backClicked() }
			Layout.alignment: Qt.AlignVCenter
		}

		Text {
			text: bar.title
			color: App.Theme.textPrimary
			font.pixelSize: App.Theme.h2Size
			Layout.alignment: Qt.AlignVCenter
		}
	}
}
