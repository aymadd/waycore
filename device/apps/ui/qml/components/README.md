# QML Components

Design system components live here and should import `../Theme.qml` for colors,
spacing and typography.

Example usage:

```qml
import QtQuick 2.15
import "../" as Design

Rectangle {
	color: Design.Theme.surface
}
```
