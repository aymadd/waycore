import QtQuick 2.15
import "." as App

Rectangle {
	id: bar
	color: App.Theme.surface

	Row {
		anchors.fill: parent
		anchors.margins: App.Theme.spacingSmall
		spacing: App.Theme.spacingMedium

		Text { text: "Battery"; color: App.Theme.textPrimary; font.pixelSize: App.Theme.bodySize }
		Text { text: "GPS"; color: App.Theme.textPrimary; font.pixelSize: App.Theme.bodySize }
		Text { text: "Radios"; color: App.Theme.textPrimary; font.pixelSize: App.Theme.bodySize }
		Text { text: "Time"; color: App.Theme.textPrimary; font.pixelSize: App.Theme.bodySize }
	}
}
