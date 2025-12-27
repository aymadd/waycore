import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import ".." as App

/**
 * ToolConfirmationDialog - Dialog for confirming AI tool execution
 *
 * This dialog is shown when the AI wants to execute a tool that requires
 * user confirmation (e.g., sending mesh messages, deleting notes).
 */
Dialog {
    id: confirmDialog
    modal: true
    anchors.centerIn: parent
    width: Math.min(parent.width - App.Theme.spacingLarge * 2, 400)

    // Properties
    property string toolName: ""
    property var toolParams: ({})
    property string warningText: ""
    property string description: ""

    // Signals
    signal confirmed()
    signal cancelled()

    background: Rectangle {
        color: App.Theme.surface
        radius: 8
        border.color: App.Theme.divider
        border.width: 1
    }

    header: Rectangle {
        color: App.Theme.warning
        height: 48
        radius: 8

        // Bottom corners should be square
        Rectangle {
            anchors.bottom: parent.bottom
            width: parent.width
            height: 8
            color: parent.color
        }

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: App.Theme.spacingMedium
            anchors.rightMargin: App.Theme.spacingMedium

            Text {
                text: "⚠️"
                font.pixelSize: 20
            }

            Text {
                text: "Confirm Action"
                font.pixelSize: App.Theme.h3Size
                font.bold: true
                color: App.Theme.background
                Layout.fillWidth: true
            }
        }
    }

    contentItem: ColumnLayout {
        spacing: App.Theme.spacingMedium

        // Tool name
        Text {
            text: "AI wants to execute:"
            font.pixelSize: App.Theme.captionSize
            color: App.Theme.textSecondary
        }

        Text {
            text: confirmDialog.toolName
            font.pixelSize: App.Theme.h3Size
            font.bold: true
            color: App.Theme.textPrimary
            Layout.fillWidth: true
        }

        // Description if provided
        Text {
            visible: confirmDialog.description !== ""
            text: confirmDialog.description
            font.pixelSize: App.Theme.bodySize
            color: App.Theme.textSecondary
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        // Parameters section
        Rectangle {
            visible: Object.keys(confirmDialog.toolParams).length > 0
            Layout.fillWidth: true
            Layout.preferredHeight: paramsColumn.height + App.Theme.spacingSmall * 2
            color: App.Theme.background
            radius: 4

            ColumnLayout {
                id: paramsColumn
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: App.Theme.spacingSmall
                spacing: 4

                Text {
                    text: "Parameters:"
                    font.pixelSize: App.Theme.captionSize
                    color: App.Theme.textSecondary
                }

                Repeater {
                    model: Object.keys(confirmDialog.toolParams)

                    RowLayout {
                        spacing: App.Theme.spacingSmall

                        Text {
                            text: modelData + ":"
                            font.pixelSize: App.Theme.bodySize
                            font.family: "monospace"
                            color: App.Theme.textSecondary
                        }

                        Text {
                            text: JSON.stringify(confirmDialog.toolParams[modelData])
                            font.pixelSize: App.Theme.bodySize
                            font.family: "monospace"
                            color: App.Theme.textPrimary
                            Layout.fillWidth: true
                            elide: Text.ElideRight
                        }
                    }
                }
            }
        }

        // Warning text
        Rectangle {
            visible: confirmDialog.warningText !== ""
            Layout.fillWidth: true
            Layout.preferredHeight: warningRow.height + App.Theme.spacingSmall * 2
            color: Qt.rgba(App.Theme.warning.r, App.Theme.warning.g, App.Theme.warning.b, 0.2)
            radius: 4

            RowLayout {
                id: warningRow
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                anchors.margins: App.Theme.spacingSmall
                spacing: App.Theme.spacingSmall

                Text {
                    text: "⚠️"
                    font.pixelSize: 16
                }

                Text {
                    text: confirmDialog.warningText
                    font.pixelSize: App.Theme.bodySize
                    color: App.Theme.warning
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
            }
        }
    }

    footer: Rectangle {
        color: "transparent"
        height: 64

        RowLayout {
            anchors.fill: parent
            anchors.margins: App.Theme.spacingMedium
            spacing: App.Theme.spacingMedium

            // Cancel button
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: App.Theme.buttonHeight
                color: cancelMouseArea.pressed ? App.Theme.primaryLight : App.Theme.surface
                radius: 4
                border.color: App.Theme.divider
                border.width: 1

                Text {
                    anchors.centerIn: parent
                    text: "Cancel"
                    font.pixelSize: App.Theme.bodySize
                    color: App.Theme.textPrimary
                }

                MouseArea {
                    id: cancelMouseArea
                    anchors.fill: parent
                    onClicked: {
                        confirmDialog.cancelled()
                        confirmDialog.close()
                    }
                }
            }

            // Confirm button
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: App.Theme.buttonHeight
                color: confirmMouseArea.pressed ? App.Theme.secondaryDark : App.Theme.accent
                radius: 4

                Text {
                    anchors.centerIn: parent
                    text: "Confirm & Execute"
                    font.pixelSize: App.Theme.bodySize
                    font.bold: true
                    color: App.Theme.background
                }

                MouseArea {
                    id: confirmMouseArea
                    anchors.fill: parent
                    onClicked: {
                        confirmDialog.confirmed()
                        confirmDialog.close()
                    }
                }
            }
        }
    }

    // Helper function to show the dialog
    function showConfirmation(name, params, warning, desc) {
        confirmDialog.toolName = name || ""
        confirmDialog.toolParams = params || {}
        confirmDialog.warningText = warning || ""
        confirmDialog.description = desc || ""
        confirmDialog.open()
    }
}
