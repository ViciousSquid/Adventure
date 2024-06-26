import json
from PyQt5.QtWidgets import QPlainTextEdit, QDialog, QVBoxLayout, QPushButton, QMessageBox
from PyQt5.QtCore import Qt
from widgets.exit_widget import ExitWidget

def show_json_error_dialog(error_message, filename):
    try:
        # Parse the error message to extract the line and column information
        line_number = int(error_message.split("line ")[1].split(" ")[0])
        column_number = int(error_message.split("column ")[1].split(" ")[0])
    except (IndexError, ValueError):
        # If the error message doesn't contain line and column information, return None for line and column
        line_number = None
        column_number = None

    try:
        # Load the JSON file to get the content
        with open(filename, "r") as json_file:
            json_content = json_file.readlines()
    except FileNotFoundError:
        # If the JSON file is not found, display the error message and return appropriate values
        QMessageBox.warning(None, "Error", f"Failed to load JSON file: {filename}")
        return None, None, 1  # Assume a single error
    except Exception as e:
        # If there's any other error while opening the file, display the error and return appropriate values
        QMessageBox.warning(None, "Error", f"Failed to load JSON file: {str(e)}")
        return None, None, 1  # Assume a single error

    # Count the total number of errors in the JSON file
    error_lines = [line for line in json_content if "line" in line]
    total_errors = len(error_lines)

    # Find the current error index
    if line_number is not None:
        current_error_index = next((i for i, line in enumerate(error_lines, start=1) if str(line_number) in line), None)
    else:
        current_error_index = None

    # Create a dialog to display the offending line
    error_dialog = QDialog()
    error_dialog.setWindowTitle("JSON Error")

    layout = QVBoxLayout()

    # Display the error message
    error_label = QPlainTextEdit()
    error_label.setPlainText(error_message)
    layout.addWidget(error_label)

    # Display the offending line
    if line_number is not None:
        line_label = QPlainTextEdit()
        offending_line = json_content[line_number - 1].rstrip()
        line_label.setPlainText(f"Offending line ({line_number}):\n{offending_line}")
        layout.addWidget(line_label)

    # Add a close button
    close_button = QPushButton("Close")
    close_button.clicked.connect(error_dialog.close)
    layout.addWidget(close_button, alignment=Qt.AlignRight)

    error_dialog.setLayout(layout)
    error_dialog.exec_()

    return error_dialog, current_error_index, total_errors

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