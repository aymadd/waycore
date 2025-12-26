import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "." as App
import "components" as UI

Rectangle {
    id: meshChat
    color: App.Theme.background

    // Chat state
    property var messages: []
    property var nodes: []
    property bool isConnected: false
    property string channelName: "LongFast"
    property int onlineNodeCount: 0

    Component.onCompleted: {
        refreshMessages()
        refreshStatus()
    }

    function refreshMessages() {
        console.log("MeshChat: refreshMessages called, MeshBridge =", MeshBridge)
        if (MeshBridge) {
            var result = MeshBridge.getMessages(50)
            console.log("MeshChat: getMessages result =", JSON.stringify(result))
            if (result && result.messages) {
                messages = result.messages
                console.log("MeshChat: loaded", messages.length, "messages")
            }
        } else {
            console.log("MeshChat: MeshBridge not available, using inline mock")
            // Mock data for development
            messages = [
                { id: "1", from_node: "!a1b2c3d4", from_name: "ALPH", text: "Hello from Alpha!", timestamp: new Date().toISOString(), is_mine: false },
                { id: "2", from_node: "!00000001", from_name: "WAYC", text: "Hello Alpha!", timestamp: new Date().toISOString(), is_mine: true },
                { id: "3", from_node: "!b2c3d4e5", from_name: "BRVO", text: "Bravo checking in", timestamp: new Date().toISOString(), is_mine: false },
            ]
        }
    }

    function refreshStatus() {
        console.log("MeshChat: refreshStatus called")
        if (MeshBridge) {
            var status = MeshBridge.getStatus()
            console.log("MeshChat: getStatus result =", JSON.stringify(status))
            if (status) {
                isConnected = status.connected !== undefined ? status.connected : true
                channelName = status.channel_name || "LongFast"
                onlineNodeCount = status.nodes ? status.nodes.online : 0
                console.log("MeshChat: status updated - connected:", isConnected, "channel:", channelName, "nodes:", onlineNodeCount)
            }
        } else {
            // Mock
            isConnected = true
            channelName = "LongFast"
            onlineNodeCount = 4
        }
    }

    function sendMessage(text) {
        if (!text.trim()) return

        // Show sending state
        sendButton.text = "..."
        sendButton.enabled = false

        if (MeshBridge) {
            var result = MeshBridge.sendMessage(text)
            if (result && result.success) {
                messageInput.text = ""
                refreshMessages()
            }
        } else {
            // Mock: add to local list
            var newMsg = {
                id: "mock_" + Date.now(),
                from_node: "!00000001",
                from_name: "WAYC",
                text: text,
                timestamp: new Date().toISOString(),
                is_mine: true
            }
            messages = messages.concat([newMsg])
            messageInput.text = ""
        }

        // Reset button state
        sendButton.text = "Send"
        sendButton.enabled = messageInput.text.trim().length > 0

        // Scroll to bottom
        messageList.positionViewAtEnd()
    }

    // Refresh timer
    Timer {
        interval: 5000
        running: true
        repeat: true
        onTriggered: {
            refreshMessages()
            refreshStatus()
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
                        var shell = meshChat.parent
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
                        text: "📡 " + channelName
                        color: App.Theme.textPrimary
                        font.pixelSize: App.Theme.h2Size
                        font.bold: true
                    }

                    Text {
                        text: isConnected
                            ? "🟢 " + onlineNodeCount + " nodes online"
                            : "🔴 Disconnected"
                        color: isConnected ? App.Theme.success : App.Theme.error
                        font.pixelSize: App.Theme.captionSize
                    }
                }

                Button {
                    text: "👥"
                    font.pixelSize: 20
                    onClicked: {
                        var shell = meshChat.parent
                        while (shell && !shell.hasOwnProperty("navigateTo")) {
                            shell = shell.parent
                        }
                        if (shell && shell.navigateTo) {
                            shell.navigateTo("MeshNodes")
                        }
                    }
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

                property bool isMine: modelData.is_mine || modelData.from_node === "!00000001"

                Rectangle {
                    id: messageBubble
                    width: Math.min(parent.width * 0.8, messageContent.implicitWidth + 24)
                    height: messageContent.implicitHeight + 16
                    radius: 12
                    color: isMine ? App.Theme.primary : App.Theme.surface
                    anchors.right: isMine ? parent.right : undefined
                    anchors.left: isMine ? undefined : parent.left
                    anchors.margins: App.Theme.spacingSmall

                    ColumnLayout {
                        id: messageContent
                        anchors.fill: parent
                        anchors.margins: 8
                        spacing: 4

                        // Sender name (for received messages)
                        Text {
                            visible: !isMine
                            text: modelData.from_name || modelData.from_node
                            color: App.Theme.accent
                            font.pixelSize: App.Theme.captionSize
                            font.bold: true
                        }

                        // Message text
                        Text {
                            text: modelData.text
                            color: isMine ? "#FFFFFF" : App.Theme.textPrimary
                            font.pixelSize: App.Theme.bodySize
                            wrapMode: Text.WordWrap
                            Layout.maximumWidth: messageList.width * 0.75
                        }

                        // Timestamp
                        Text {
                            text: formatTime(modelData.timestamp)
                            color: isMine ? "#CCCCCC" : App.Theme.textSecondary
                            font.pixelSize: 10
                            Layout.alignment: Qt.AlignRight
                        }
                    }
                }
            }

            // Empty state
            Text {
                visible: messages.length === 0
                anchors.centerIn: parent
                text: "No messages yet\n\nSend a message to start!"
                color: App.Theme.textSecondary
                font.pixelSize: App.Theme.bodySize
                horizontalAlignment: Text.AlignHCenter
            }

            // Scroll to bottom on new messages
            onCountChanged: {
                positionViewAtEnd()
            }
        }

        // Divider
        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: App.Theme.divider
        }

        // Warning banner when no nodes online
        Rectangle {
            Layout.fillWidth: true
            height: onlineNodeCount === 0 ? 32 : 0
            visible: onlineNodeCount === 0
            color: App.Theme.warning

            Text {
                anchors.centerIn: parent
                text: "⚠️ No nodes online - messages will broadcast when nodes connect"
                color: "#000000"
                font.pixelSize: App.Theme.captionSize
            }

            Behavior on height { NumberAnimation { duration: 200 } }
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

                TextField {
                    id: messageInput
                    Layout.fillWidth: true
                    placeholderText: onlineNodeCount === 0
                        ? "Broadcast message..."
                        : "Type a message..."
                    font.pixelSize: App.Theme.bodySize

                    Keys.onReturnPressed: {
                        sendMessage(text)
                    }
                }

                Button {
                    id: sendButton
                    text: "Send"
                    enabled: messageInput.text.trim().length > 0
                    onClicked: {
                        sendMessage(messageInput.text)
                    }
                }
            }
        }
    }

    // Helper function to format timestamp
    function formatTime(isoString) {
        if (!isoString) return ""
        var date = new Date(isoString)
        var hours = date.getHours().toString().padStart(2, '0')
        var mins = date.getMinutes().toString().padStart(2, '0')
        return hours + ":" + mins
    }
}
