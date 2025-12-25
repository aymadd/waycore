import QtQuick 2.15
import ".." as App

Text {
	id: icon
	property string name: ""
	property int size: 24
	text: name
	color: App.Theme.textPrimary
	font.pixelSize: size
}
