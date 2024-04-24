import zipfile
import json
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QLineEdit, QTextEdit, QWidget
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QByteArray, QBuffer, QIODevice, Qt

from widgets.skill_check_widget import SkillCheckWidget
from widgets.exit_widget import ExitWidget

def openLoadStoryDialog(storyEditorWidget):
    file_dialog = QFileDialog()
    file_dialog.setNameFilter("ZIP Files (*.zip)")
    if file_dialog.exec():
        selected_files = file_dialog.selectedFiles()
        if selected_files:
            loadStory(storyEditorWidget, selected_files[0])

def openSaveStoryDialog(storyEditorWidget):
    file_dialog = QFileDialog()
    file_dialog.setDefaultSuffix("zip")
    file_dialog.setNameFilter("ZIP Files (*.zip)")
    file_dialog.setAcceptMode(QFileDialog.AcceptSave)
    if file_dialog.exec():
        selected_file = file_dialog.selectedFiles()[0]
        if not selected_file.lower().endswith(".zip"):
            selected_file += ".zip"
        saveStory(storyEditorWidget, selected_file)

def loadStory(storyEditorWidget, filename):
    try:
        with zipfile.ZipFile(filename, 'r') as zip_file:
            # Load story.json
            with zip_file.open('story.json') as json_file:
                story_data = json.load(json_file)

            # Clear existing data
            storyEditorWidget.storyNameInput.clear()
            storyEditorWidget.buttonColorButton.setStyleSheet("background-color: #000000;")
            storyEditorWidget.coverImageLabel.clear()
            storyEditorWidget.summaryInput.clear()
            storyEditorWidget.startRoomInput.clear()
            storyEditorWidget.roomsTabWidget.clear()

            # Populate story data
            storyEditorWidget.storyNameInput.setText(story_data.get('name', ''))
            button_color = story_data.get('button_color', '#000000')
            storyEditorWidget.buttonColorButton.setStyleSheet(f"background-color: {button_color};")

            cover_image_data = zip_file.read('cover.jpg')
            pixmap = QPixmap()
            pixmap.loadFromData(cover_image_data)
            storyEditorWidget.coverImageLabel.setPixmap(pixmap)

            summary_text = zip_file.read('summary.txt').decode('utf-8')
            storyEditorWidget.summaryInput.setText(summary_text)

            storyEditorWidget.startRoomInput.addItems(story_data.get('rooms', {}).keys())

            # Load rooms
            for room_name, room_data in story_data.get('rooms', {}).items():
                storyEditorWidget.addRoom()
                room_widget = storyEditorWidget.roomsTabWidget.widget(storyEditorWidget.roomsTabWidget.count() - 1)
                room_widget.roomNameInput.setText(room_name)
                room_widget.roomDescriptionInput.setText(room_data.get('description', ''))

                # Load room image
                room_image_filename = f"room_{storyEditorWidget.roomsTabWidget.count()}.jpg"
                if room_image_filename in zip_file.namelist():
                    room_image_data = zip_file.read(room_image_filename)
                    pixmap = QPixmap()
                    pixmap.loadFromData(room_image_data)
                    room_widget.roomImageLabel.setPixmap(pixmap.scaled(room_widget.roomImageLabel.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
                else:
                    room_widget.roomImageLabel.clear()  # Clear the image label if no image is present

                # Load exits
                for exit_name, exit_data in room_data.get('exits', {}).items():
                    room_widget.addExit()
                    exit_widget = room_widget.exitsLayout.itemAt(room_widget.exitsLayout.count() - 1).widget()
                    exit_widget.exitNameInput.setText(exit_name)
                    if isinstance(exit_data, str):
                        exit_widget.exitDestinationInput.setText(exit_data)
                    elif isinstance(exit_data, dict):
                        # Load skill check data only if exit_widget is an instance of ExitWidget
                        if isinstance(exit_widget, ExitWidget):
                            exit_widget.skillCheckData = exit_data.get('skill_check', None)
                            if exit_widget.skillCheckData:
                                exit_widget.skillCheckIndicator.setVisible(True)
                            else:
                                exit_widget.skillCheckIndicator.setVisible(False)
                        else:
                            QMessageBox.warning(storyEditorWidget, "Error", f"Invalid exit widget encountered: {type(exit_widget)}")

                # Remove any invalid exits from the room_widget
                room_widget.removeInvalidExits()

                # Update the tab icon after loading the room data
                room_widget.updateTabIcon()

    except Exception as e:
        QMessageBox.warning(storyEditorWidget, "Error", f"Failed to load story: {str(e)}")

def saveStory(storyEditorWidget, filename):
    try:
        story_data = {
            'name': storyEditorWidget.storyNameInput.text() if storyEditorWidget.storyNameInput else '',
            'button_color': storyEditorWidget.buttonColorButton.styleSheet().split(':')[1].strip() if storyEditorWidget.buttonColorButton else '',
            'start_room': storyEditorWidget.startRoomInput.currentText() if storyEditorWidget.startRoomInput else '',
            'rooms': {}
        }

        for i in range(storyEditorWidget.roomsTabWidget.count()):
            room_widget = storyEditorWidget.roomsTabWidget.widget(i)
            room_name = room_widget.roomNameInput.text() if room_widget.roomNameInput else ''
            room_description = room_widget.roomDescriptionInput.toPlainText() if room_widget.roomDescriptionInput else ''
            room_exits = {}

            for j in range(room_widget.exitsLayout.count()):
                exit_widget = room_widget.exitsLayout.itemAt(j).widget()
                exit_name_input = exit_widget.findChild(QLineEdit, "exitNameInput")
                exit_name = exit_name_input.text() if exit_name_input else ''
                exit_destination_input = exit_widget.findChild(QLineEdit, "exitDestinationInput")
                exit_destination = exit_destination_input.text() if exit_destination_input else ''

                if exit_widget.skillCheckData:
                    room_exits[exit_name] = {'skill_check': exit_widget.skillCheckData}
                else:
                    room_exits[exit_name] = exit_destination

            room_image_filename = f"room_{i + 1}.jpg"
            room_data = {
                'description': room_description,
                'exits': room_exits
            }
            if room_widget.roomImageLabel.pixmap():
                room_data['image'] = room_image_filename
            story_data['rooms'][room_name] = room_data

        with zipfile.ZipFile(filename, 'w') as zip_file:
            # Save story.json
            json_data = json.dumps(story_data, indent=2).encode('utf-8')
            zip_file.writestr('story.json', json_data)

            # Save summary.txt
            summary_text = storyEditorWidget.summaryInput.toPlainText().encode('utf-8')
            zip_file.writestr('summary.txt', summary_text)

            # Save cover image
            pixmap = storyEditorWidget.coverImageLabel.pixmap()
            if pixmap:
                image = pixmap.toImage()
                byte_array = QByteArray()
                buffer = QBuffer(byte_array)
                buffer.open(QIODevice.WriteOnly)
                image.save(buffer, "JPG")
                zip_file.writestr('cover.jpg', byte_array.data())

            # Save room images
            for i in range(storyEditorWidget.roomsTabWidget.count()):
                room_widget = storyEditorWidget.roomsTabWidget.widget(i)
                pixmap = room_widget.roomImageLabel.pixmap()
                if pixmap:
                    image = pixmap.toImage()
                    byte_array = QByteArray()
                    buffer = QBuffer(byte_array)
                    buffer.open(QIODevice.WriteOnly)
                    image.save(buffer, "JPG")
                    room_image_filename = f"room_{i + 1}.jpg"
                    zip_file.writestr(room_image_filename, byte_array.data())

        QMessageBox.information(storyEditorWidget, "Success", "Story saved successfully.")
    except Exception as e:
        QMessageBox.warning(storyEditorWidget, "Error", f"Failed to save story: {str(e)}")