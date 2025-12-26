import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "." as App

Rectangle {
    id: nodeDetails
    color: App.Theme.background

    property string nodeId: ""
    property var node: null
    property var contact: null

    Component.onCompleted: {
        loadNodeDetails()
    }

    function loadNodeDetails() {
        if (!nodeId) return

        console.log("Loading details for node:", nodeId)

        if (MeshBridge) {
            // Get node info from the nodes list
            var nodesResult = MeshBridge.getNodes()
            if (nodesResult && nodesResult.nodes) {
                for (var i = 0; i < nodesResult.nodes.length; i++) {
                    if (nodesResult.nodes[i].node_id === nodeId) {
                        node = nodesResult.nodes[i]
                        break
                    }
                }
            }

            // Get contact info
            var contactResult = MeshBridge.getContact(nodeId)
            if (contactResult && contactResult.contact) {
                contact = contactResult.contact
            }
        } else {
            // Mock data
            node = {
                node_id: nodeId,
                short_name: "ALPH",
                long_name: "Alpha Station",
                hardware: "tbeam",
                status: "online",
                battery_level: 85,
                snr: 8.5,
                rssi: -75,
                hops_away: 1,
                last_seen: new Date().toISOString(),
                position: {
                    latitude: 37.7749,
                    longitude: -122.4194,
                    altitude: 15
                }
            }
            contact = { is_favorite: true, alias: null, notes: null }
        }
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
                    onClicked: navigateBack()
                }

                Text {
                    text: contact && contact.alias ? contact.alias : (node ? node.short_name : "Node")
                    color: App.Theme.textPrimary
                    font.pixelSize: App.Theme.h2Size
                    font.bold: true
                    Layout.fillWidth: true
                }

                // Favorite button
                Button {
                    text: (contact && contact.is_favorite) ? "⭐" : "☆"
                    font.pixelSize: 20
                    flat: true
                    onClicked: {
                        if (MeshBridge) {
                            var result = MeshBridge.toggleFavorite(nodeId)
                            contact = { ...contact, is_favorite: result.is_favorite }
                        }
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: App.Theme.divider
        }

        // Content
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            ColumnLayout {
                width: parent.width
                spacing: App.Theme.spacingSmall
                visible: node !== null

                // Node ID card
                InfoCard {
                    title: "Node ID"
                    value: node ? node.node_id : ""
                    icon: "🔗"
                    monospace: true
                }

                // Status card
                InfoCard {
                    title: "Status"
                    value: node ? (node.status === "online" ? "Online" : "Offline") : ""
                    icon: node && node.status === "online" ? "🟢" : "⚫"
                    valueColor: node && node.status === "online" ? App.Theme.success : App.Theme.textSecondary
                }

                // Names section
                SectionHeader { text: "Identity" }

                InfoCard {
                    title: "Short Name"
                    value: node ? node.short_name : ""
                    icon: "📛"
                }

                InfoCard {
                    title: "Long Name"
                    value: node ? (node.long_name || "Not set") : ""
                    icon: "📋"
                }

                InfoCard {
                    visible: contact && contact.alias
                    title: "Your Alias"
                    value: contact ? (contact.alias || "") : ""
                    icon: "✏️"
                }

                // Hardware section
                SectionHeader { text: "Hardware" }

                InfoCard {
                    title: "Device"
                    value: node ? formatHardware(node.hardware) : ""
                    icon: "📟"
                }

                InfoCard {
                    title: "Battery"
                    value: node && node.battery_level !== undefined ? node.battery_level + "%" : "Unknown"
                    icon: getBatteryIcon(node ? node.battery_level : null)
                    valueColor: getBatteryColor(node ? node.battery_level : null)
                }

                // Signal section
                SectionHeader { text: "Signal Quality" }

                InfoCard {
                    title: "SNR (Signal-to-Noise)"
                    value: node && node.snr !== undefined ? node.snr.toFixed(1) + " dB" : "N/A"
                    icon: getSignalIcon(node ? node.snr : null)
                    valueColor: getSnrColor(node ? node.snr : null)
                }

                InfoCard {
                    title: "RSSI (Signal Strength)"
                    value: node && node.rssi !== undefined ? node.rssi + " dBm" : "N/A"
                    icon: "📶"
                }

                InfoCard {
                    title: "Hops Away"
                    value: node && node.hops_away !== undefined
                           ? (node.hops_away === 0 ? "Direct connection" : node.hops_away + " hop" + (node.hops_away > 1 ? "s" : ""))
                           : "Unknown"
                    icon: "🔀"
                }

                // Position section (if available)
                SectionHeader {
                    text: "Position"
                    visible: node && node.position
                }

                InfoCard {
                    visible: node && node.position
                    title: "Coordinates"
                    value: node && node.position
                           ? node.position.latitude.toFixed(6) + ", " + node.position.longitude.toFixed(6)
                           : ""
                    icon: "📍"
                    monospace: true
                }

                InfoCard {
                    visible: node && node.position && node.position.altitude
                    title: "Altitude"
                    value: node && node.position && node.position.altitude
                           ? node.position.altitude + " m"
                           : ""
                    icon: "⛰️"
                }

                // Last seen
                SectionHeader { text: "Activity" }

                InfoCard {
                    title: "Last Seen"
                    value: node ? formatLastSeen(node.last_seen) : ""
                    icon: "🕐"
                }

                // Actions
                SectionHeader { text: "Actions" }

                Button {
                    Layout.fillWidth: true
                    Layout.margins: App.Theme.spacingMedium
                    text: "💬 Send Message"
                    enabled: node && node.status === "online"
                    onClicked: {
                        // Navigate to chat
                        var shell = nodeDetails.parent
                        while (shell && !shell.hasOwnProperty("navigateTo")) {
                            shell = shell.parent
                        }
                        if (shell && shell.navigateTo) {
                            shell.navigateTo("Meshtastic")
                        }
                    }
                }

                // Bottom spacing
                Item { Layout.preferredHeight: App.Theme.spacingLarge }
            }
        }

        // Loading state
        Text {
            visible: node === null
            anchors.centerIn: parent
            text: "Loading..."
            color: App.Theme.textSecondary
            font.pixelSize: App.Theme.bodySize
        }
    }

    function navigateBack() {
        var shell = nodeDetails.parent
        while (shell && !shell.hasOwnProperty("navigateBack")) {
            shell = shell.parent
        }
        if (shell && shell.navigateBack) {
            shell.navigateBack()
        }
    }

    function formatHardware(hw) {
        if (!hw) return "Unknown"
        var names = {
            "tbeam": "LilyGo T-Beam",
            "tlora": "LilyGo T-LoRa",
            "heltec": "Heltec LoRa 32",
            "rak4631": "RAK4631",
            "station_g1": "Station G1",
            "techo": "LilyGo T-Echo",
            "nano_g1": "Nano G1"
        }
        return names[hw.toLowerCase()] || hw
    }

    function getBatteryIcon(level) {
        if (level === undefined || level === null) return "🔋"
        if (level < 20) return "🪫"
        if (level < 50) return "🔋"
        return "🔋"
    }

    function getBatteryColor(level) {
        if (level === undefined || level === null) return App.Theme.textSecondary
        if (level < 20) return App.Theme.error
        if (level < 50) return App.Theme.warning
        return App.Theme.success
    }

    function getSignalIcon(snr) {
        if (snr === undefined || snr === null) return "📶"
        if (snr > 5) return "📶"
        if (snr > 0) return "📶"
        if (snr > -5) return "📶"
        return "📶"
    }

    function getSnrColor(snr) {
        if (snr === undefined || snr === null) return App.Theme.textSecondary
        if (snr > 5) return App.Theme.success
        if (snr > 0) return "#8BC34A"  // Light green
        if (snr > -5) return App.Theme.warning
        return App.Theme.error
    }

    function formatLastSeen(isoString) {
        if (!isoString) return "Unknown"
        var date = new Date(isoString)
        var now = new Date()
        var diff = now - date
        var mins = Math.floor(diff / 60000)
        var hours = Math.floor(diff / 3600000)
        var days = Math.floor(diff / 86400000)

        if (mins < 1) return "Just now"
        if (mins < 60) return mins + " minute" + (mins > 1 ? "s" : "") + " ago"
        if (hours < 24) return hours + " hour" + (hours > 1 ? "s" : "") + " ago"
        return days + " day" + (days > 1 ? "s" : "") + " ago"
    }

    // Info Card component
    component InfoCard: Rectangle {
        property string title: ""
        property string value: ""
        property string icon: ""
        property bool monospace: false
        property color valueColor: App.Theme.textPrimary

        Layout.fillWidth: true
        Layout.margins: App.Theme.spacingSmall
        Layout.leftMargin: App.Theme.spacingMedium
        Layout.rightMargin: App.Theme.spacingMedium
        height: 60
        color: App.Theme.surface
        radius: 8

        RowLayout {
            anchors.fill: parent
            anchors.margins: App.Theme.spacingSmall
            spacing: App.Theme.spacingSmall

            Text {
                text: icon
                font.pixelSize: 24
                Layout.preferredWidth: 40
                horizontalAlignment: Text.AlignHCenter
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2

                Text {
                    text: title
                    color: App.Theme.textSecondary
                    font.pixelSize: App.Theme.captionSize
                }

                Text {
                    text: value
                    color: valueColor
                    font.pixelSize: App.Theme.bodySize
                    font.bold: true
                    font.family: monospace ? "monospace" : undefined
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                }
            }
        }
    }

    // Section Header component
    component SectionHeader: Item {
        property string text: ""

        Layout.fillWidth: true
        Layout.preferredHeight: 40
        Layout.topMargin: App.Theme.spacingSmall

        Text {
            anchors.left: parent.left
            anchors.leftMargin: App.Theme.spacingMedium
            anchors.verticalCenter: parent.verticalCenter
            text: parent.text
            color: App.Theme.textSecondary
            font.pixelSize: App.Theme.captionSize
            font.bold: true
            font.capitalization: Font.AllUppercase
        }
    }
}
