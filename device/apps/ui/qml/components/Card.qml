import QtQuick 2.15
import ".." as App

Rectangle {
	id: card
	color: App.Theme.surface
	radius: 8
	border.color: App.Theme.divider
	property alias contentItem: content
	default property alias data: content.data

	Column {
		id: content
		anchors.fill: parent
		anchors.margins: App.Theme.spacingMedium
		spacing: App.Theme.spacingSmall
	}
}
