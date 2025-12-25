import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "." as App
import "components" as UI

Rectangle {
    id: notesList
    color: App.Theme.background

    // Notes data from bridge
    property var notes: NotesBridge ? NotesBridge.notes : []

    // Refresh when bridge data changes
    Connections {
        target: NotesBridge
        function onNotesChanged() {
            notes = NotesBridge.notes
        }
        function onErrorOccurred(message) {
            console.error("Notes error:", message)
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: App.Theme.spacingMedium
        spacing: App.Theme.spacingSmall

        // Header
        RowLayout {
            Layout.fillWidth: true
            spacing: App.Theme.spacingSmall

            Button {
                text: "← Back"
                onClicked: {
                    var parentItem = notesList.parent
                    while (parentItem && !parentItem.hasOwnProperty("navigateBack")) {
                        parentItem = parentItem.parent
                    }
                    if (parentItem && parentItem.navigateBack) {
                        parentItem.navigateBack()
                    }
                }
            }

            Text {
                text: "Notes"
                color: App.Theme.textPrimary
                font.pixelSize: App.Theme.h2Size
                font.bold: true
                Layout.fillWidth: true
            }

            Button {
                text: "+ New"
                onClicked: createNewNote()
            }
        }

        // Notes list
        ListView {
            id: listView
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            spacing: App.Theme.spacingSmall

            model: notes

            delegate: Rectangle {
                width: listView.width
                height: 70
                color: App.Theme.surface
                radius: 8
                border.color: App.Theme.divider
                border.width: 1

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: App.Theme.spacingSmall
                    spacing: App.Theme.spacingSmall

                    Column {
                        Layout.fillWidth: true
                        spacing: 4

                        Text {
                            text: modelData.title || "Untitled"
                            color: App.Theme.textPrimary
                            font.pixelSize: App.Theme.bodySize
                            font.bold: true
                            elide: Text.ElideRight
                            width: parent.width
                        }

                        Text {
                            text: getPreview(modelData.content)
                            color: App.Theme.textSecondary
                            font.pixelSize: 12
                            elide: Text.ElideRight
                            width: parent.width
                        }

                        Text {
                            text: formatDate(modelData.updated_at)
                            color: App.Theme.textSecondary
                            font.pixelSize: 10
                        }
                    }

                    Button {
                        text: "🗑️"
                        onClicked: {
                            deleteConfirmDialog.noteId = modelData.id
                            deleteConfirmDialog.noteTitle = modelData.title
                            deleteConfirmDialog.open()
                        }
                    }
                }

                MouseArea {
                    anchors.fill: parent
                    z: -1
                    onClicked: openNote(modelData.id)
                }
            }

            // Empty state
            Text {
                anchors.centerIn: parent
                visible: notes.length === 0
                text: "No notes yet.\nTap '+ New' to create one."
                color: App.Theme.textSecondary
                font.pixelSize: App.Theme.bodySize
                horizontalAlignment: Text.AlignHCenter
            }
        }
    }

    // Delete confirmation dialog
    Dialog {
        id: deleteConfirmDialog
        title: "Delete Note?"
        modal: true
        anchors.centerIn: parent
        width: 280

        property int noteId: -1
        property string noteTitle: ""

        contentItem: Column {
            spacing: 10
            width: parent.width

            Text {
                text: "Delete \"" + deleteConfirmDialog.noteTitle + "\"?"
                color: App.Theme.textPrimary
                wrapMode: Text.WordWrap
                width: parent.width
            }
            Text {
                text: "This cannot be undone."
                color: App.Theme.textSecondary
                font.pixelSize: 12
            }
        }

        standardButtons: Dialog.Cancel | Dialog.Ok

        onAccepted: {
            if (NotesBridge) {
                NotesBridge.deleteNote(noteId)
            }
        }
    }

    function getPreview(content) {
        if (!content) return "No content"
        var clean = content.replace(/[#*_\-\[\]]/g, "").trim()
        return clean.substring(0, 60) + (clean.length > 60 ? "..." : "")
    }

    function formatDate(isoDate) {
        if (!isoDate) return ""
        var d = new Date(isoDate)
        return d.toLocaleDateString() + " " + d.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})
    }

    function loadNotes() {
        if (NotesBridge) {
            NotesBridge.loadNotes()
        }
    }

    function createNewNote() {
        var shell = notesList.parent
        while (shell && !shell.hasOwnProperty("openNoteEditor")) {
            shell = shell.parent
        }
        if (shell && shell.openNoteEditor) {
            shell.openNoteEditor(-1)
        }
    }

    function openNote(noteId) {
        var shell = notesList.parent
        while (shell && !shell.hasOwnProperty("openNoteEditor")) {
            shell = shell.parent
        }
        if (shell && shell.openNoteEditor) {
            shell.openNoteEditor(noteId)
        }
    }

    Component.onCompleted: {
        loadNotes()
    }
}
