import QtQuick 2.15
import QtQuick.Controls 2.15
import "." as App
import "components" as UI

Item {
	id: shell

	App.StatusBar {
		id: status
		anchors.top: parent.top
		anchors.left: parent.left
		anchors.right: parent.right
		height: App.Theme.appBarHeight
	}

	StackView {
		id: router
		anchors.top: status.bottom
		anchors.bottom: parent.bottom
		anchors.left: parent.left
		anchors.right: parent.right

		initialItem: homeComponent

		Component {
			id: homeComponent
			App.Home {}
		}

		Component {
			id: settingsComponent
			App.Settings {}
		}

		Component {
			id: settingsGeneralComponent
			App.SettingsGeneral {}
		}

		Component {
			id: settingsControlsComponent
			App.SettingsControls {}
		}

		Component {
			id: settingsSensorsComponent
			App.SettingsSensors {}
		}

		Component {
			id: settingsInfoComponent
			App.SettingsInfo {}
		}

		Component {
			id: compassComponent
			App.Compass {}
		}

		Component {
			id: notesListComponent
			App.NotesList {}
		}

		Component {
			id: noteEditorComponent
			App.NoteEditor {}
		}

		Component {
			id: meshChatComponent
			App.MeshChat {}
		}

		Component {
			id: meshNodesComponent
			App.MeshNodes {}
		}

		Component {
			id: meshNodeDetailsComponent
			App.MeshNodeDetails {}
		}

	Component {
		id: meshConversationComponent
		App.MeshConversation {}
	}

	Component {
		id: cameraComponent
		App.Camera {}
	}

	Component {
		id: galleryComponent
		App.Gallery {}
	}

	Component {
		id: photoViewerComponent
		App.PhotoViewer {}
	}

	Component {
		id: aiChatComponent
		App.AIChat {}
	}

	Component {
		id: aiConversationListComponent
		App.AIConversationList {
			onConversationSelected: function(conversationId) {
				if (AIBridge) {
					AIBridge.loadConversation(conversationId)
				}
				router.pop()
			}
			onNewChatRequested: {
				if (AIBridge) {
					AIBridge.newConversation()
				}
				router.pop()
			}
		}
	}
}

	function navigateTo(appName) {
		console.log("Navigate to:", appName)
		switch (appName) {
			case "Settings":
				router.push(settingsComponent)
				break
			case "SettingsGeneral":
				router.push(settingsGeneralComponent)
				break
			case "SettingsControls":
				router.push(settingsControlsComponent)
				break
			case "SettingsSensors":
				router.push(settingsSensorsComponent)
				break
			case "SettingsInfo":
				router.push(settingsInfoComponent)
				break
			case "Compass":
				router.push(compassComponent)
				break
			case "Notes":
				router.push(notesListComponent)
				break
		case "Meshtastic":
			router.push(meshChatComponent)
			break
		case "MeshNodes":
			router.push(meshNodesComponent)
			break
		case "Camera":
			router.push(cameraComponent)
			break
		case "Gallery":
			router.push(galleryComponent)
			break
		case "AI":
			router.push(aiChatComponent)
			break
		case "AIHistory":
			router.push(aiConversationListComponent)
			break
		default:
			console.log("App not yet implemented:", appName)
	}
	}

	function openNoteEditor(noteId) {
		var editor = noteEditorComponent.createObject(null, {noteId: noteId})
		router.push(editor)
	}

	function openNodeDetails(nodeId) {
		var details = meshNodeDetailsComponent.createObject(null, {nodeId: nodeId})
		router.push(details)
	}

function openConversation(nodeId) {
	var conversation = meshConversationComponent.createObject(null, {node_id: nodeId})
	router.push(conversation)
}

function openPhotoViewer(photoId, photoIndex) {
	var viewer = photoViewerComponent.createObject(null, {photoId: photoId, photoIndex: photoIndex || 0})
	router.push(viewer)
}

	function navigateToSettings() {
		navigateTo("Settings")
	}

	function navigateBack() {
		if (router.depth > 1) {
			router.pop()
		}
	}

	function navigateHome() {
		router.pop(null)  // Pop to root
	}
}
