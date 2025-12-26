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
            // Use enriched endpoint with contact/favorite info
            var result = MeshBridge.getNodesWithContacts()
            console.log("MeshNodes: getNodesWithContacts result =", JSON.stringify(result))
            if (result && result.nodes) {
                nodes = result.nodes
                console.log("MeshNodes: loaded", nodes.length, "nodes")
            }
        } else {
            console.log("MeshNodes: MeshBridge not available, using inline mock")
            // Mock data with favorites
            nodes = [
                { node_id: "!a1b2c3d4", short_name: "ALPH", long_name: "Alpha", status: "online", battery_level: 85, last_seen: new Date().toISOString(), hops_away: 0, is_favorite: true },
                { node_id: "!b2c3d4e5", short_name: "BRVO", long_name: "Bravo", status: "online", battery_level: 72, last_seen: new Date().toISOString(), hops_away: 1, is_favorite: false },
                { node_id: "!c3d4e5f6", short_name: "CHRL", long_name: "Charlie", status: "offline", battery_level: 45, last_seen: "2025-12-24T10:00:00Z", hops_away: 2, is_favorite: false },
                { node_id: "!d4e5f6g7", short_name: "DELT", long_name: "Delta", status: "online", battery_level: 95, last_seen: new Date().toISOString(), hops_away: 1, is_favorite: false },
            ]
        }
    }

    function toggleFavorite(nodeId, index) {
        if (MeshBridge) {
            var result = MeshBridge.toggleFavorite(nodeId)
            console.log("Toggle favorite result:", JSON.stringify(result))
            // Update local array
            var updatedNodes = nodes.slice()
            updatedNodes[index].is_favorite = result.is_favorite
            // Re-sort: favorites first
            updatedNodes.sort(function(a, b) {
                if (a.is_favorite && !b.is_favorite) return -1
                if (!a.is_favorite && b.is_favorite) return 1
                return a.short_name.localeCompare(b.short_name)
            })
            nodes = updatedNodes
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
                property bool isFavorite: modelData.is_favorite || false

                // Make the whole row tappable
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        // Navigate to node details
                        var shell = meshNodes.parent
                        while (shell && !shell.hasOwnProperty("openNodeDetails")) {
                            shell = shell.parent
                        }
                        if (shell && shell.openNodeDetails) {
                            shell.openNodeDetails(modelData.node_id)
                        }
                    }
                }

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: App.Theme.spacingSmall
                    spacing: App.Theme.spacingSmall

                    // Favorite button
                    Button {
                        text: isFavorite ? "⭐" : "☆"
                        font.pixelSize: 20
                        flat: true
                        onClicked: toggleFavorite(modelData.node_id, index)
                        ToolTip.visible: hovered
                        ToolTip.text: isFavorite ? "Remove from favorites" : "Add to favorites"
                    }

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
                                // Show alias if set, otherwise short_name
                                text: modelData.alias || modelData.short_name
                                color: App.Theme.textPrimary
                                font.pixelSize: App.Theme.h3Size
                                font.bold: true
                            }

                            Text {
                                // Show original name if alias is set
                                text: modelData.alias ? ("(" + modelData.short_name + ")") : (modelData.long_name || "")
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

                            // Signal strength bars
                            UI.SignalBars {
                                visible: modelData.snr !== undefined && modelData.snr !== null
                                snr: modelData.snr || 0
                                width: 20
                                height: 14
                            }

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
