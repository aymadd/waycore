import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Dialogs
import "." as App
import "components" as UI

Rectangle {
    id: aiChat
    color: App.Theme.background

    // Chat state
    property var messages: []
    property bool isLoading: AIBridge ? AIBridge.isLoading : false
    property string selectedModel: "phi3-mini"
    property var availableModels: []
    property int currentConversationId: 0
    property bool wasLoading: false  // Track loading state transitions

    Component.onCompleted: {
        loadMessages()
        loadModels()
        updateConversationId()
        // Sync loading state from bridge
        if (AIBridge) {
            isLoading = AIBridge.isLoading
        }
    }

    function loadMessages() {
        if (AIBridge) {
            messages = AIBridge.getMessages()
        }
    }

    function loadModels() {
        if (AIBridge) {
            availableModels = AIBridge.getAvailableModels()
            selectedModel = AIBridge.getModelId()
        } else {
            // Mock models
            availableModels = [
                { id: "phi3-mini", name: "Phi-3 Mini" },
                { id: "llama2-7b", name: "Llama 2 7B" }
            ]
        }
    }

    function updateConversationId() {
        if (AIBridge) {
            currentConversationId = AIBridge.currentConversationId
        }
    }

    function sendMessage(text) {
        if (!text.trim() || isLoading) return

        // Clear input immediately for better UX
        var messageText = text
        messageInput.text = ""
        messageInput.enabled = false

        if (AIBridge) {
            AIBridge.setModelId(selectedModel)
            // Set loading immediately for instant feedback
            wasLoading = true
            isLoading = true
            // Async call - result comes via chatCompleted signal
            AIBridge.sendChat(messageText)
        } else {
            // Mock: add messages locally
            var userMsg = {
                role: "user",
                content: messageText,
                timestamp: new Date().toISOString()
            }
            var assistantMsg = {
                role: "assistant",
                content: "This is a mock response. Connect to the AI service for real answers.",
                timestamp: new Date().toISOString()
            }
            messages = messages.concat([userMsg, assistantMsg])
            messageInput.enabled = true
        }
    }

    function clearChat() {
        if (AIBridge) {
            AIBridge.clearMessages()
        }
        messages = []
    }

    function newChat() {
        if (AIBridge) {
            AIBridge.newConversation()
            messages = []
            updateConversationId()
        }
    }

    function openHistory() {
        var shell = aiChat.parent
        while (shell && !shell.hasOwnProperty("navigateTo")) {
            shell = shell.parent
        }
        if (shell && shell.navigateTo) {
            shell.navigateTo("AIHistory")
        }
    }

    function classifyMockImage() {
        // For MVP: use a mock base64 image to test classification
        // This is a fallback when camera capture returns mock data
        if (isLoading) return

        if (AIBridge) {
            // Set loading immediately for instant feedback
            wasLoading = true
            isLoading = true
            messageInput.enabled = false
            // Mock base64 image (small placeholder)
            var mockImageB64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
            // Async call - result comes via imageClassifyCompleted signal
            AIBridge.classifyImageAndChat(mockImageB64)
        } else {
            // Mock: add messages locally
            var userMsg = {
                role: "user",
                content: "📷 [Image for classification]",
                timestamp: new Date().toISOString()
            }
            var assistantMsg = {
                role: "assistant",
                content: "**Image Classification Results:**\n\n• **Mountain**: 85.0%\n• **Tree**: 72.3%\n• **Rock**: 65.1%",
                timestamp: new Date().toISOString()
            }
            messages = messages.concat([userMsg, assistantMsg])
        }
    }

    function openGalleryPicker() {
        if (isLoading) return
        imageFileDialog.open()
    }

    function classifyImageFromFile(filePath) {
        if (isLoading || !filePath) return

        if (AIBridge) {
            // Set loading immediately for instant feedback
            wasLoading = true
            isLoading = true
            messageInput.enabled = false
            // Async call - loads image and classifies it
            AIBridge.classifyImageFromPath(filePath)
        } else {
            classifyMockImage()
        }
    }

    // Listen to AIBridge signals
    Connections {
        target: AIBridge || null

        function onLoadingChanged() {
            var newLoading = AIBridge.isLoading

            // Re-enable input when loading transitions from true to false
            if (wasLoading && !newLoading) {
                messageInput.enabled = true
                // Use a timer to avoid focus race conditions
                focusTimer.start()
            }

            wasLoading = newLoading
            isLoading = newLoading
        }

        function onMessagesChanged() {
            messages = AIBridge.getMessages()
            messageList.positionViewAtEnd()
        }

        function onErrorChanged() {
            if (AIBridge.error) {
                toast.show(AIBridge.error)
            }
        }

        function onCurrentConversationChanged() {
            updateConversationId()
        }

        function onChatCompleted(result) {
            // Chat completed (success or error)
            if (!result.success) {
                toast.show("Error: " + (result.error || "Unknown error"))
            }
            updateConversationId()
        }

        function onImageClassifyCompleted(result) {
            // Image classification completed
            if (!result.success) {
                toast.show("Error: " + (result.error || "Unknown error"))
            }
            updateConversationId()
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // Header bar
        Rectangle {
            Layout.fillWidth: true
            height: 56
            color: App.Theme.surface

            RowLayout {
                anchors.fill: parent
                anchors.margins: App.Theme.spacingSmall
                spacing: App.Theme.spacingSmall

                Button {
                    text: "←"
                    font.pixelSize: 20
                    onClicked: {
                        var shell = aiChat.parent
                        while (shell && !shell.hasOwnProperty("navigateBack")) {
                            shell = shell.parent
                        }
                        if (shell && shell.navigateBack) {
                            shell.navigateBack()
                        }
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2

                    Text {
                        text: "🤖 AI Assistant"
                        color: App.Theme.textPrimary
                        font.pixelSize: App.Theme.h2Size
                        font.bold: true
                    }

                    Text {
                        text: getModelDisplayName(selectedModel)
                        color: App.Theme.textSecondary
                        font.pixelSize: App.Theme.captionSize
                    }
                }

                // History button
                Button {
                    text: "📜"
                    font.pixelSize: 18
                    onClicked: openHistory()

                    ToolTip.visible: hovered
                    ToolTip.text: "Chat history"
                }

                // New chat button
                Button {
                    text: "✨"
                    font.pixelSize: 18
                    onClicked: newChat()

                    ToolTip.visible: hovered
                    ToolTip.text: "New chat"
                }

                // Active model indicator (one model per type)
                Rectangle {
                    id: modelIndicator
                    height: 28
                    width: modelLabel.width + 16
                    color: App.Theme.surfaceElevated
                    radius: 4
                    border.color: App.Theme.divider

                    Text {
                        id: modelLabel
                        anchors.centerIn: parent
                        text: getModelDisplayName(selectedModel)
                        color: App.Theme.textSecondary
                        font.pixelSize: App.Theme.captionSize
                    }

                    ToolTip.visible: modelMouseArea.containsMouse
                    ToolTip.text: "Active AI model"

                    MouseArea {
                        id: modelMouseArea
                        anchors.fill: parent
                        hoverEnabled: true
                    }
                }

                // Clear chat button
                Button {
                    text: "🗑️"
                    font.pixelSize: 18
                    enabled: messages.length > 0
                    onClicked: clearChatDialog.open()

                    ToolTip.visible: hovered
                    ToolTip.text: "Clear chat"
                }
            }
        }

        // Divider
        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: App.Theme.divider
        }

        // Message list
        ListView {
            id: messageList
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            spacing: App.Theme.spacingSmall
            verticalLayoutDirection: ListView.TopToBottom

            model: messages

            delegate: Item {
                width: messageList.width
                height: messageBubble.height + App.Theme.spacingSmall

                property bool isUser: modelData.role === "user"

                Rectangle {
                    id: messageBubble
                    width: Math.min(parent.width * 0.85, messageContent.implicitWidth + 24)
                    height: messageContent.implicitHeight + 16
                    radius: 16
                    color: isUser ? App.Theme.primary : App.Theme.surfaceElevated
                    anchors.right: isUser ? parent.right : undefined
                    anchors.left: isUser ? undefined : parent.left
                    anchors.margins: App.Theme.spacingSmall

                    ColumnLayout {
                        id: messageContent
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 4

                        // Role indicator (for assistant)
                        Text {
                            visible: !isUser
                            text: "🤖 AI"
                            color: App.Theme.accent
                            font.pixelSize: App.Theme.captionSize
                            font.bold: true
                        }

                        // Message text
                        Text {
                            text: modelData.content
                            color: isUser ? "#FFFFFF" : App.Theme.textPrimary
                            font.pixelSize: App.Theme.bodySize
                            wrapMode: Text.WordWrap
                            Layout.maximumWidth: messageList.width * 0.75

                            // Enable text selection
                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.IBeamCursor
                                onPressAndHold: {
                                    // Could implement copy functionality here
                                }
                            }
                        }

                        // Timestamp
                        Text {
                            Layout.alignment: Qt.AlignRight
                            text: formatTime(modelData.timestamp)
                            color: isUser ? "#CCCCCC" : App.Theme.textSecondary
                            font.pixelSize: 10
                        }
                    }
                }
            }

            // Empty state
            Column {
                visible: messages.length === 0
                anchors.centerIn: parent
                spacing: App.Theme.spacingMedium

                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "🤖"
                    font.pixelSize: 64
                }

                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "AI Assistant"
                    color: App.Theme.textPrimary
                    font.pixelSize: App.Theme.h2Size
                    font.bold: true
                }

                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "Ask me anything!\nI can help with outdoor tips,\nidentification, and more."
                    color: App.Theme.textSecondary
                    font.pixelSize: App.Theme.bodySize
                    horizontalAlignment: Text.AlignHCenter
                }
            }

            // Scroll to bottom on new messages
            onCountChanged: {
                positionViewAtEnd()
            }
        }

        // Loading indicator
        Rectangle {
            id: loadingIndicator
            Layout.fillWidth: true
            Layout.preferredHeight: isLoading ? 48 : 0
            visible: isLoading
            color: App.Theme.surface
            clip: true

            RowLayout {
                anchors.centerIn: parent
                spacing: App.Theme.spacingMedium
                visible: isLoading

                // Animated dots
                Row {
                    spacing: 4
                    Repeater {
                        model: 3
                        Rectangle {
                            width: 8
                            height: 8
                            radius: 4
                            color: App.Theme.accent
                            opacity: 0.3

                            SequentialAnimation on opacity {
                                running: isLoading
                                loops: Animation.Infinite
                                PauseAnimation { duration: index * 200 }
                                NumberAnimation { to: 1.0; duration: 300 }
                                NumberAnimation { to: 0.3; duration: 300 }
                                PauseAnimation { duration: (2 - index) * 200 }
                            }
                        }
                    }
                }

                Text {
                    text: "Thinking..."
                    color: App.Theme.textSecondary
                    font.pixelSize: App.Theme.bodySize
                    font.italic: true
                }
            }

            Behavior on Layout.preferredHeight {
                NumberAnimation { duration: 200; easing.type: Easing.OutCubic }
            }
        }

        // Divider
        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: App.Theme.divider
        }

        // Input bar
        Rectangle {
            Layout.fillWidth: true
            height: 60
            color: App.Theme.surface

            RowLayout {
                anchors.fill: parent
                anchors.margins: App.Theme.spacingSmall
                spacing: App.Theme.spacingSmall

                // Gallery picker button
                Button {
                    id: galleryButton
                    text: "🖼️"
                    font.pixelSize: 20
                    enabled: !isLoading
                    onClicked: openGalleryPicker()

                    ToolTip.visible: hovered
                    ToolTip.text: "Pick from gallery"

                    background: Rectangle {
                        color: galleryButton.hovered ? App.Theme.surfaceElevated : "transparent"
                        radius: 20
                    }
                }

                // Camera capture button
                Button {
                    id: cameraButton
                    text: "📷"
                    font.pixelSize: 20
                    enabled: !isLoading
                    onClicked: classifyMockImage()

                    ToolTip.visible: hovered
                    ToolTip.text: "Capture photo"

                    background: Rectangle {
                        color: cameraButton.hovered ? App.Theme.surfaceElevated : "transparent"
                        radius: 20
                    }
                }

                TextField {
                    id: messageInput
                    Layout.fillWidth: true
                    placeholderText: "Ask me anything..."
                    font.pixelSize: App.Theme.bodySize
                    enabled: !isLoading

                    background: Rectangle {
                        color: App.Theme.background
                        radius: 20
                        border.color: messageInput.activeFocus ? App.Theme.accent : App.Theme.divider
                        border.width: messageInput.activeFocus ? 2 : 1
                    }

                    leftPadding: 16
                    rightPadding: 16

                    Keys.onReturnPressed: {
                        sendMessage(text)
                    }
                }

                Button {
                    id: sendButton
                    text: isLoading ? "..." : "Send"
                    enabled: messageInput.text.trim().length > 0 && !isLoading

                    background: Rectangle {
                        color: sendButton.enabled ? App.Theme.primary : App.Theme.disabled
                        radius: 20
                    }

                    contentItem: Text {
                        text: sendButton.text
                        color: sendButton.enabled ? "#FFFFFF" : App.Theme.textDisabled
                        font.pixelSize: App.Theme.bodySize
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }

                    onClicked: {
                        sendMessage(messageInput.text)
                    }
                }
            }
        }
    }

    // Toast for errors
    UI.Toast {
        id: toast
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 80
    }

    // Timer to delay focus restoration (prevents keyboard issues)
    Timer {
        id: focusTimer
        interval: 100
        repeat: false
        onTriggered: {
            if (messageInput.enabled) {
                messageInput.forceActiveFocus()
            }
        }
    }

    // Clear chat confirmation dialog
    Dialog {
        id: clearChatDialog
        title: "Clear Chat"
        modal: true
        anchors.centerIn: parent
        width: 280

        background: Rectangle {
            color: App.Theme.surface
            radius: 12
        }

        contentItem: ColumnLayout {
            spacing: App.Theme.spacingMedium

            Text {
                text: "Are you sure you want to clear all messages?"
                color: App.Theme.textPrimary
                font.pixelSize: App.Theme.bodySize
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: App.Theme.spacingSmall

                Button {
                    text: "Cancel"
                    Layout.fillWidth: true
                    onClicked: clearChatDialog.close()
                }

                Button {
                    text: "Clear"
                    Layout.fillWidth: true
                    onClicked: {
                        clearChat()
                        clearChatDialog.close()
                    }

                    background: Rectangle {
                        color: App.Theme.error
                        radius: 4
                    }

                    contentItem: Text {
                        text: "Clear"
                        color: "#FFFFFF"
                        font.pixelSize: App.Theme.bodySize
                        horizontalAlignment: Text.AlignHCenter
                    }
                }
            }
        }
    }

    // File dialog for gallery image picker
    FileDialog {
        id: imageFileDialog
        title: "Select an image to classify"
        nameFilters: ["Image files (*.jpg *.jpeg *.png *.gif *.webp)", "All files (*)"]
        fileMode: FileDialog.OpenFile

        onAccepted: {
            classifyImageFromFile(selectedFile.toString())
        }
    }

    // Helper functions
    function formatTime(isoString) {
        if (!isoString) return ""
        var date = new Date(isoString)
        var hours = date.getHours().toString().padStart(2, '0')
        var mins = date.getMinutes().toString().padStart(2, '0')
        return hours + ":" + mins
    }

    function getModelDisplayName(modelId) {
        for (var i = 0; i < availableModels.length; i++) {
            if (availableModels[i].id === modelId) {
                return availableModels[i].name
            }
        }
        return modelId
    }

    function getModelIndex(modelId) {
        for (var i = 0; i < availableModels.length; i++) {
            if (availableModels[i].id === modelId) {
                return i
            }
        }
        return 0
    }
}
