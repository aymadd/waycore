pragma Singleton
import QtQuick 2.15

QtObject {
	// Primary Colors (Dark Green)
	readonly property color primary: "#2B3D33"
	readonly property color primaryDark: "#1F2D26"
	readonly property color primaryLight: "#3D5447"
	readonly property color primaryAccent: "#5C7A65"

	// Secondary Colors (Sage)
	readonly property color secondary: "#7A9984"
	readonly property color secondaryDark: "#5C7A65"
	readonly property color secondaryLight: "#9CB5A3"

	// Semantic Colors
	readonly property color success: "#6B9B6F"
	readonly property color warning: "#D4A574"
	readonly property color error: "#C97064"
	readonly property color info: "#7A9984"

	// Neutral Colors
	readonly property color background: "#1A1F1C"
	readonly property color surface: "#2B3D33"
	readonly property color surfaceElevated: "#3D5447"
	readonly property color divider: "#5C7A65"
	readonly property color disabled: "#758A7D"

	// Text Colors
	readonly property color textPrimary: "#E8F0EC"
	readonly property color textSecondary: "#9CB5A3"
	readonly property color textDisabled: "#758A7D"

	// Typography
	readonly property int h1Size: 32
	readonly property int h2Size: 24
	readonly property int h3Size: 18
	readonly property int bodySize: 14
	readonly property int captionSize: 12

	// Spacing
	readonly property int spacingExtraSmall: 4
	readonly property int spacingXS: 4
	readonly property int spacingSmall: 8
	readonly property int spacingMedium: 16
	readonly property int spacingLarge: 24

	// Dimensions
	readonly property int touchTargetMin: 48
	readonly property int appBarHeight: 56
	readonly property int buttonHeight: 48
}
