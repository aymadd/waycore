import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "." as App
import "components" as UI

Rectangle {
    id: meshNodes
    color: App.Theme.background

    property var nodes: []

    Component.onCompleted: {
        refreshNodes()
    }

    function refreshNodes() {
        console.log("MeshNodes: refreshNodes called, MeshBridge =", MeshBridge)
        if (MeshBridge) {
            var result = MeshBridge.getNodes()
            console.log("MeshNodes: getNodes result =", JSON.stringify(result))
            if (result && result.nodes) {
                nodes = result.nodes
                console.log("MeshNodes: loaded", nodes.length, "nodes")
            }
        } else {
            console.log("MeshNodes: MeshBridge not available, using inline mock")
            // Mock data
            nodes = [
                { node_id: "!a1b2c3d4", short_name: "ALPH", long_name: "Alpha", status: "online", battery_level: 85, last_seen: new Date().toISOString(), hops_away: 0 },
                { node_id: "!b2c3d4e5", short_name: "BRVO", long_name: "Bravo", status: "online", battery_level: 72, last_seen: new Date().toISOString(), hops_away: 1 },
                { node_id: "!c3d4e5f6", short_name: "CHRL", long_name: "Charlie", status: "offline", battery_level: 45, last_seen: "2025-12-24T10:00:00Z", hops_away: 2 },
                { node_id: "!d4e5f6g7", short_name: "DELT", long_name: "Delta", status: "online", battery_level: 95, last_seen: new Date().toISOString(), hops_away: 1 },
            ]
        }
    }

    // Refresh timer
    Timer {
        interval: 10000
        running: true
        repeat: true
        onTriggered: refreshNodes()
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // Header
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
                        var shell = meshNodes.parent
                        while (shell && !shell.hasOwnProperty("navigateBack")) {
                            shell = shell.parent
                        }
                        if (shell && shell.navigateBack) {
                            shell.navigateBack()
                        }
                    }
                }

                Text {
                    text: "👥 Mesh Nodes"
                    color: App.Theme.textPrimary
                    font.pixelSize: App.Theme.h2Size
                    font.bold: true
                    Layout.fillWidth: true
                }

                Button {
                    text: "⟳"
                    font.pixelSize: 18
                    onClicked: refreshNodes()
                }
            }
        }

        // Divider
        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: App.Theme.divider
        }

        // Nodes summary
        Rectangle {
            Layout.fillWidth: true
            height: 40
            color: App.Theme.surface

            Text {
                anchors.centerIn: parent
                text: getOnlineCount() + " of " + nodes.length + " nodes online"
                color: App.Theme.textSecondary
                font.pixelSize: App.Theme.captionSize
            }
        }

        // Nodes list
        ListView {
            id: nodeList
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            spacing: 1

            model: nodes

            delegate: Rectangle {
                width: nodeList.width
                height: 80
                color: App.Theme.surface

                property bool isOnline: modelData.status === "online"

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: App.Theme.spacingSmall
                    spacing: App.Theme.spacingSmall

                    // Status indicator
                    Rectangle {
                        width: 12
                        height: 12
                        radius: 6
                        color: isOnline ? App.Theme.success : App.Theme.textSecondary
                    }

                    // Node info
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4

                        RowLayout {
                            spacing: App.Theme.spacingSmall

                            Text {
                                text: modelData.short_name
                                color: App.Theme.textPrimary
                                font.pixelSize: App.Theme.h3Size
                                font.bold: true
                            }

                            Text {
                                text: modelData.long_name || ""
                                color: App.Theme.textSecondary
                                font.pixelSize: App.Theme.bodySize
                            }
                        }

                        Text {
                            text: modelData.node_id
                            color: App.Theme.textSecondary
                            font.pixelSize: App.Theme.captionSize
                            font.family: "monospace"
                        }

                        RowLayout {
                            spacing: App.Theme.spacingMedium

                            // Battery
                            Text {
                                visible: modelData.battery_level !== undefined
                                text: "🔋 " + modelData.battery_level + "%"
                                color: getBatteryColor(modelData.battery_level)
                                font.pixelSize: App.Theme.captionSize
                            }

                            // Hops
                            Text {
                                visible: modelData.hops_away !== undefined
                                text: modelData.hops_away === 0 ? "Direct" : modelData.hops_away + " hop" + (modelData.hops_away > 1 ? "s" : "")
                                color: App.Theme.textSecondary
                                font.pixelSize: App.Theme.captionSize
                            }

                            // Last seen
                            Text {
                                text: isOnline ? "Online" : "Last seen " + formatLastSeen(modelData.last_seen)
                                color: isOnline ? App.Theme.success : App.Theme.textSecondary
                                font.pixelSize: App.Theme.captionSize
                            }
                        }
                    }

                    // Message button
                    Button {
                        text: "💬"
                        font.pixelSize: 16
                        visible: isOnline
                        onClicked: {
                            // Navigate to chat with this node
                            // For now, just go back to chat
                            var shell = meshNodes.parent
                            while (shell && !shell.hasOwnProperty("navigateTo")) {
                                shell = shell.parent
                            }
                            if (shell && shell.navigateTo) {
                                shell.navigateTo("Meshtastic")
                            }
                        }
                    }
                }
            }

            // Empty state
            Text {
                visible: nodes.length === 0
                anchors.centerIn: parent
                text: "No nodes found\n\nMake sure mesh radio is connected"
                color: App.Theme.textSecondary
                font.pixelSize: App.Theme.bodySize
                horizontalAlignment: Text.AlignHCenter
            }
        }
    }

    function getOnlineCount() {
        return nodes.filter(function(n) { return n.status === "online"; }).length
    }

    function getBatteryColor(level) {
        if (level === undefined) return App.Theme.textSecondary
        if (level < 20) return App.Theme.error
        if (level < 50) return App.Theme.warning
        return App.Theme.success
    }

    function formatLastSeen(isoString) {
        if (!isoString) return "unknown"
        var date = new Date(isoString)
        var now = new Date()
        var diff = now - date
        var mins = Math.floor(diff / 60000)
        var hours = Math.floor(diff / 3600000)
        var days = Math.floor(diff / 86400000)

        if (mins < 1) return "just now"
        if (mins < 60) return mins + "m ago"
        if (hours < 24) return hours + "h ago"
        return days + "d ago"
    }
}
