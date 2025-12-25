import QtQuick 2.15
import ".." as App

Rectangle {
	id: card
	color: App.Theme.surface
	radius: 8
	border.color: App.Theme.divider
	implicitHeight: content.implicitHeight + App.Theme.spacingMedium * 2

	default property alias children: content.data

	Column {
		id: content
		anchors.fill: parent
		anchors.margins: App.Theme.spacingMedium
		spacing: App.Theme.spacingSmall
	}
}
