import QtQuick 2.15
import QtQuick.Controls 2.15
import ".." as App

TextField {
	id: tf
	font.pixelSize: App.Theme.bodySize
	background: Rectangle {
		color: App.Theme.surfaceElevated
		radius: 4
		border.color: App.Theme.divider
	}
	color: App.Theme.textPrimary
	placeholderTextColor: App.Theme.textSecondary
}
