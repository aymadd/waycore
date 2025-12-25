import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "." as App
import "components" as UI

Rectangle {
    id: noteEditor
    color: App.Theme.background

    // Note data
    property int noteId: -1  // -1 = new note
    property string noteTitle: ""
    property string noteContent: ""
    property bool isModified: false
    property bool isSaving: false

    // Load note data when noteId changes
    Connections {
        target: NotesBridge
        function onCurrentNoteChanged() {
            if (NotesBridge.currentNote) {
                noteTitle = NotesBridge.currentNote.title || ""
                noteContent = NotesBridge.currentNote.content || ""
                isModified = false
            }
        }
        function onErrorOccurred(message) {
            saveStatus.text = "Error: " + message
            saveStatus.color = App.Theme.error
            saveStatus.visible = true
            isSaving = false
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
                    if (isModified) {
                        saveNote()
                    }
                    goBack()
                }
            }

            Text {
                text: noteId < 0 ? "New Note" : "Edit Note"
                color: App.Theme.textPrimary
                font.pixelSize: App.Theme.h2Size
                font.bold: true
                Layout.fillWidth: true
            }

            Button {
                text: isSaving ? "Saving..." : "Save"
                enabled: isModified && !isSaving
                onClicked: saveNote()
            }
        }

        // Title input
        TextField {
            id: titleField
            Layout.fillWidth: true
            placeholderText: "Note title..."
            text: noteTitle
            font.pixelSize: App.Theme.h2Size
            font.bold: true
            onTextChanged: {
                if (noteTitle !== text) {
                    noteTitle = text
                    isModified = true
                }
            }
            // Virtual keyboard hint
            inputMethodHints: Qt.ImhNoPredictiveText
        }

        // Formatting toolbar
        RowLayout {
            Layout.fillWidth: true
            spacing: App.Theme.spacingSmall

            Button {
                text: "H1"
                onClicked: insertFormatting("# ")
                ToolTip.text: "Heading 1"
            }
            Button {
                text: "H2"
                onClicked: insertFormatting("## ")
                ToolTip.text: "Heading 2"
            }
            Button {
                text: "•"
                font.pixelSize: 18
                onClicked: insertFormatting("- ")
                ToolTip.text: "Bullet point"
            }
            Button {
                text: "B"
                font.bold: true
                onClicked: wrapSelection("**", "**")
                ToolTip.text: "Bold"
            }
            Button {
                text: "I"
                font.italic: true
                onClicked: wrapSelection("*", "*")
                ToolTip.text: "Italic"
            }

            Item { Layout.fillWidth: true }

            Text {
                text: contentArea.text.length + " chars"
                color: App.Theme.textSecondary
                font.pixelSize: 11
            }
        }

        // Content area
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true

            TextArea {
                id: contentArea
                text: noteContent
                placeholderText: "Start writing...\n\nTip: Use the formatting buttons above for headers and lists."
                wrapMode: TextEdit.Wrap
                font.pixelSize: App.Theme.bodySize
                onTextChanged: {
                    if (noteContent !== text) {
                        noteContent = text
                        isModified = true
                    }
                }
                // Virtual keyboard hint
                inputMethodHints: Qt.ImhNoPredictiveText | Qt.ImhMultiLine
            }
        }

        // Save status
        Text {
            id: saveStatus
            visible: false
            color: App.Theme.success
            font.pixelSize: App.Theme.bodySize
            Layout.alignment: Qt.AlignHCenter

            Timer {
                id: statusTimer
                interval: 2000
                onTriggered: saveStatus.visible = false
            }
        }
    }

    function insertFormatting(prefix) {
        var pos = contentArea.cursorPosition
        var text = contentArea.text

        var lineStart = text.lastIndexOf("\n", pos - 1) + 1

        contentArea.text = text.substring(0, lineStart) + prefix + text.substring(lineStart)
        contentArea.cursorPosition = pos + prefix.length
    }

    function wrapSelection(before, after) {
        var start = contentArea.selectionStart
        var end = contentArea.selectionEnd

        if (start === end) {
            var text = contentArea.text
            var pos = contentArea.cursorPosition
            contentArea.text = text.substring(0, pos) + before + after + text.substring(pos)
            contentArea.cursorPosition = pos + before.length
        } else {
            var text = contentArea.text
            var selected = text.substring(start, end)
            contentArea.text = text.substring(0, start) + before + selected + after + text.substring(end)
            contentArea.cursorPosition = end + before.length + after.length
        }
    }

    function saveNote() {
        if (!NotesBridge) {
            console.log("NotesBridge not available")
            return
        }

        isSaving = true
        var result = NotesBridge.saveNote(noteId, noteTitle, noteContent)

        if (result >= 0) {
            if (noteId < 0) {
                noteId = result  // Update ID for new notes
            }
            isModified = false
            saveStatus.text = "✓ Saved"
            saveStatus.color = App.Theme.success
            saveStatus.visible = true
            statusTimer.start()
        } else {
            saveStatus.text = "Failed to save"
            saveStatus.color = App.Theme.error
            saveStatus.visible = true
        }
        isSaving = false
    }

    function goBack() {
        var parentItem = noteEditor.parent
        while (parentItem && !parentItem.hasOwnProperty("navigateBack")) {
            parentItem = parentItem.parent
        }
        if (parentItem && parentItem.navigateBack) {
            parentItem.navigateBack()
        }
    }

    Component.onCompleted: {
        if (NotesBridge && noteId >= 0) {
            NotesBridge.loadNote(noteId)
        }
    }
}
