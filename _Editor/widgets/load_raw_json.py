import json
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from widgets.exit_widget import ExitWidget

def loadRawJson(storyEditorWidget):
    fileDialog = QFileDialog()
    fileDialog.setNameFilter("JSON Files (*.json)")
    if fileDialog.exec():
        selectedFiles = fileDialog.selectedFiles()
        if selectedFiles:
            loadRawJsonData(storyEditorWidget, selectedFiles[0])

def loadRawJsonData(storyEditorWidget, filename):
    try:
        with open(filename, 'r') as jsonFile:
            rawJsonData = json.load(jsonFile)

        # Clear existing data
        storyEditorWidget.storyNameInput.clear()
        storyEditorWidget.buttonColorButton.setStyleSheet("background-color: #000000;")
        storyEditorWidget.coverImageLabel.clear()
        storyEditorWidget.summaryInput.clear()
        storyEditorWidget.startRoomInput.clear()
        storyEditorWidget.roomsTabWidget.clear()

        # Populate fields from raw JSON data
        storyEditorWidget.storyNameInput.setText(rawJsonData.get('name', ''))
        buttonColor = rawJsonData.get('button_color', '#000000')
        storyEditorWidget.buttonColorButton.setStyleSheet(f"background-color: {buttonColor};")
        storyEditorWidget.summaryInput.setText(rawJsonData.get('summary', ''))
        storyEditorWidget.startRoomInput.addItem(rawJsonData.get('start_room', ''))

        # Load rooms
        for roomName, roomData in rawJsonData.get('rooms', {}).items():
            storyEditorWidget.addRoom()
            roomWidget = storyEditorWidget.roomsTabWidget.widget(storyEditorWidget.roomsTabWidget.count() - 1)
            roomWidget.roomNameInput.setText(roomName)
            roomWidget.roomDescriptionInput.setText(roomData.get('description', ''))

            # Load exits
            for exitName, exitData in roomData.get('exits', {}).items():
                roomWidget.addExit()
                exitWidget = roomWidget.exitsLayout.itemAt(roomWidget.exitsLayout.count() - 1).widget()
                exitWidget.exitNameInput.setText(exitName)
                if isinstance(exitData, str):
                    exitWidget.exitDestinationInput.setText(exitData)
                elif isinstance(exitData, dict):
                    exitWidget.skillCheckData = exitData.get('skill_check', None)
                    if exitWidget.skillCheckData:
                        exitWidget.skillCheckIndicator.setVisible(True)
                    else:
                        exitWidget.skillCheckIndicator.setVisible(False)

            # Remove any invalid exits from the roomWidget
            roomWidget.removeInvalidExits()

            # Update icons
            roomWidget.updateIcons()

    except Exception as e:
        QMessageBox.warning(storyEditorWidget, "Error", f"Failed to load raw JSON: {str(e)}")