import zipfile
import json
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QLineEdit, QTextEdit, QWidget
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QByteArray, QBuffer, QIODevice
from widgets.skill_check_widget import SkillCheckWidget
from widgets.exit_widget import ExitWidget

def openLoadStoryDialog(storyEditorWidget):
    fileDialog = QFileDialog()
    fileDialog.setNameFilter("ZIP Files (*.zip)")
    if fileDialog.exec():
        selectedFiles = fileDialog.selectedFiles()
        if selectedFiles:
            loadStory(storyEditorWidget, selectedFiles[0])

def openSaveStoryDialog(storyEditorWidget):
    fileDialog = QFileDialog()
    fileDialog.setDefaultSuffix("zip")
    fileDialog.setNameFilter("ZIP Files (*.zip)")
    fileDialog.setAcceptMode(QFileDialog.AcceptSave)
    if fileDialog.exec():
        selectedFile = fileDialog.selectedFiles()[0]
        if not selectedFile.lower().endswith(".zip"):
            selectedFile += ".zip"
        saveStory(storyEditorWidget, selectedFile)

def loadStory(storyEditorWidget, filename):
    try:
        with zipfile.ZipFile(filename, 'r') as zipFile:
            # Load story.json
            with zipFile.open('story.json') as jsonFile:
                storyData = json.load(jsonFile)

            # Clear existing data
            storyEditorWidget.storyNameInput.clear()
            storyEditorWidget.buttonColorButton.setStyleSheet("background-color: #000000;")
            storyEditorWidget.coverImageLabel.clear()
            storyEditorWidget.summaryInput.clear()
            storyEditorWidget.startRoomInput.clear()
            storyEditorWidget.roomsTabWidget.clear()

            # Populate story data
            storyEditorWidget.storyNameInput.setText(storyData.get('name', ''))
            buttonColor = storyData.get('button_color', '#000000')
            storyEditorWidget.buttonColorButton.setStyleSheet(f"background-color: {buttonColor};")

            if 'cover.jpg' in zipFile.namelist():
                coverImageData = zipFile.read('cover.jpg')
                pixmap = QPixmap()
                pixmap.loadFromData(coverImageData)
                storyEditorWidget.coverImageLabel.setPixmap(pixmap)
            else:
                # Use a placeholder image if cover.jpg is not present
                storyEditorWidget.coverImageLabel.setText("No cover image")

            if 'summary.txt' in zipFile.namelist():
                summaryText = zipFile.read('summary.txt').decode('utf-8')
                storyEditorWidget.summaryInput.setText(summaryText)
            else:
                # Use a placeholder text if summary.txt is not present
                storyEditorWidget.summaryInput.setText("No summary available")

            storyEditorWidget.startRoomInput.addItems(storyData.get('rooms', {}).keys())

            # Load rooms
            for roomName, roomData in storyData.get('rooms', {}).items():
                storyEditorWidget.addRoom()
                roomWidget = storyEditorWidget.roomsTabWidget.widget(storyEditorWidget.roomsTabWidget.count() - 1)
                roomWidget.roomNameInput.setText(roomName)
                roomWidget.roomDescriptionInput.setText(roomData.get('description', ''))

                if "revisit_count" in roomData and "revisit_content" in roomData:
                    roomWidget.revisit_data = {
                        "revisit_count": roomData["revisit_count"],
                        "revisit_content": roomData["revisit_content"]
                    }
                else:
                    roomWidget.revisit_data = {}

                # Load room image
                roomImageFilename = f"room_{storyEditorWidget.roomsTabWidget.count()}.jpg"
                if roomImageFilename in zipFile.namelist():
                    roomImageData = zipFile.read(roomImageFilename)
                    pixmap = QPixmap()
                    pixmap.loadFromData(roomImageData)
                    roomWidget.roomImageLabel.setPixmap(pixmap)

                # Load exits
                for exitName, exitData in roomData.get('exits', {}).items():
                    roomWidget.addExit()
                    exitWidget = roomWidget.exitsLayout.itemAt(roomWidget.exitsLayout.count() - 1).widget()
                    exitWidget.exitNameInput.setText(exitName)
                    if isinstance(exitData, str):
                        exitWidget.exitDestinationInput.setText(exitData)
                    elif isinstance(exitData, dict):
                        # Load skill check data only if exitWidget is an instance of ExitWidget
                        if isinstance(exitWidget, ExitWidget):
                            exitWidget.skillCheckData = exitData.get('skill_check', None)
                            if exitWidget.skillCheckData:
                                exitWidget.skillCheckIndicator.setVisible(True)
                            else:
                                exitWidget.skillCheckIndicator.setVisible(False)
                        else:
                            QMessageBox.warning(storyEditorWidget, "Error", f"Invalid exit widget encountered: {type(exitWidget)}")

                # Remove any invalid exits from the roomWidget
                roomWidget.removeInvalidExits()

                # Update icons
                roomWidget.updateIcons()

    except Exception as e:
        QMessageBox.warning(storyEditorWidget, "Error", f"Failed to load story: {str(e)}")

def saveStory(storyEditorWidget, filename):
    try:
        storyData = {
            'name': storyEditorWidget.storyNameInput.text() if storyEditorWidget.storyNameInput else '',
            'button_color': storyEditorWidget.buttonColorButton.styleSheet().split(':')[1].strip() if storyEditorWidget.buttonColorButton else '',
            'start_room': storyEditorWidget.startRoomInput.currentText() if storyEditorWidget.startRoomInput else '',
            'rooms': {}
        }

        for i in range(storyEditorWidget.roomsTabWidget.count()):
            roomWidget = storyEditorWidget.roomsTabWidget.widget(i)
            roomName = roomWidget.roomNameInput.text() if roomWidget.roomNameInput else ''
            roomDescription = roomWidget.roomDescriptionInput.toPlainText() if roomWidget.roomDescriptionInput else ''
            roomExits = {}

            for j in range(roomWidget.exitsLayout.count()):
                exitWidget = roomWidget.exitsLayout.itemAt(j).widget()
                exitNameInput = exitWidget.findChild(QLineEdit, "exitNameInput")
                exitName = exitNameInput.text() if exitNameInput else ''
                exitDestinationInput = exitWidget.findChild(QLineEdit, "exitDestinationInput")
                exitDestination = exitDestinationInput.text() if exitDestinationInput else ''

                if exitWidget.skillCheckData:
                    roomExits[exitName] = {'skill_check': exitWidget.skillCheckData}
                else:
                    roomExits[exitName] = exitDestination

            roomImageFilename = f"room_{i + 1}.jpg"
            roomData = {
                'description': roomDescription,
                'exits': roomExits
            }

            if hasattr(roomWidget, 'revisitDialog'):
                revisitData = roomWidget.revisitDialog.getRevisitData()
                if revisitData["revisit_count"] > 0 or revisitData["revisit_content"]:
                    roomData["revisit_count"] = revisitData["revisit_count"]
                    roomData["revisit_content"] = revisitData["revisit_content"]

            if roomWidget.roomImageLabel.pixmap():
                roomData['image'] = roomImageFilename
            storyData['rooms'][roomName] = roomData

        with zipfile.ZipFile(filename, 'w') as zipFile:
            # Save story.json
            jsonData = json.dumps(storyData, indent=2).encode('utf-8')
            zipFile.writestr('story.json', jsonData)

            # Save summary.txt
            summaryText = storyEditorWidget.summaryInput.toPlainText().encode('utf-8')
            zipFile.writestr('summary.txt', summaryText)

            # Save cover image
            pixmap = storyEditorWidget.coverImageLabel.pixmap()
            if pixmap:
                image = pixmap.toImage()
                byteArray = QByteArray()
                buffer = QBuffer(byteArray)
                buffer.open(QIODevice.WriteOnly)
                image.save(buffer, "JPG")
                zipFile.writestr('cover.jpg', byteArray.data())

            # Save room images
            for i in range(storyEditorWidget.roomsTabWidget.count()):
                roomWidget = storyEditorWidget.roomsTabWidget.widget(i)
                pixmap = roomWidget.roomImageLabel.pixmap()
                if pixmap:
                    image = pixmap.toImage()
                    byteArray = QByteArray()
                    buffer = QBuffer(byteArray)
                    buffer.open(QIODevice.WriteOnly)
                    image.save(buffer, "JPG")
                    roomImageFilename = f"room_{i + 1}.jpg"
                    zipFile.writestr(roomImageFilename, byteArray.data())

        QMessageBox.information(storyEditorWidget, "Success", "Story saved successfully.")
    except Exception as e:
        QMessageBox.warning(storyEditorWidget, "Error", f"Failed to save story: {str(e)}")