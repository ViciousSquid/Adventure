import zipfile
import json
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QLineEdit, QTextEdit, QWidget, QLabel, QPushButton, QVBoxLayout
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QByteArray, QBuffer, QIODevice
from widgets.skill_check_widget import SkillCheckWidget
from widgets.exit_widget import ExitWidget

def open_load_story_dialog(story_editor_widget):
    file_dialog = QFileDialog()
    file_dialog.setNameFilter("ZIP Files (*.zip)")
    if file_dialog.exec():
        selected_files = file_dialog.selectedFiles()
        if selected_files:
            load_story(story_editor_widget, selected_files[0])

def open_save_story_dialog(story_editor_widget):
    file_dialog = QFileDialog()
    file_dialog.setDefaultSuffix("zip")
    file_dialog.setNameFilter("ZIP Files (*.zip)")
    file_dialog.setAcceptMode(QFileDialog.AcceptSave)
    if file_dialog.exec():
        selected_file = file_dialog.selectedFiles()[0]
        if not selected_file.lower().endswith(".zip"):
            selected_file += ".zip"
        save_story(story_editor_widget, selected_file)

def load_story(story_editor_widget, filename):
    try:
        with zipfile.ZipFile(filename, 'r') as zip_file:
            # Load story.json
            with zip_file.open('story.json') as json_file:
                story_data = json.load(json_file)

            # Clear existing data
            story_editor_widget.storyNameInput.clear()
            story_editor_widget.buttonColorButton.setStyleSheet("background-color: #000000;")
            story_editor_widget.coverImageLabel.clear()
            story_editor_widget.summaryInput.clear()
            story_editor_widget.startRoomInput.clear()
            story_editor_widget.roomsTabWidget.clear()

            # Populate story data
            story_editor_widget.storyNameInput.setText(story_data.get('name', ''))
            button_color = story_data.get('button_color', '#000000')
            story_editor_widget.buttonColorButton.setStyleSheet(f"background-color: {button_color};")

            if 'cover.jpg' in zip_file.namelist():
                cover_image_data = zip_file.read('cover.jpg')
                pixmap = QPixmap()
                pixmap.loadFromData(cover_image_data)
                story_editor_widget.coverImageLabel.setPixmap(pixmap)
            else:
                # Use a placeholder image if cover.jpg is not present
                story_editor_widget.coverImageLabel.setText("No cover image")

            if 'summary.txt' in zip_file.namelist():
                summary_text = zip_file.read('summary.txt').decode('utf-8')
                story_editor_widget.summaryInput.setText(summary_text)
            else:
                # Use a placeholder text if summary.txt is not present
                story_editor_widget.summaryInput.setText("No summary available")

            story_editor_widget.startRoomInput.addItems(story_data.get('rooms', {}).keys())

            # Load rooms
            for room_name, room_data in story_data.get('rooms', {}).items():
                story_editor_widget.addRoom()
                room_widget = story_editor_widget.roomsTabWidget.widget(story_editor_widget.roomsTabWidget.count() - 1)
                room_widget.roomNameInput.setText(room_name)
                room_widget.roomDescriptionInput.setText(room_data.get('description', ''))

                if "revisit_count" in room_data and "revisit_content" in room_data:
                    room_widget.revisit_data = {
                        "revisit_count": room_data["revisit_count"],
                        "revisit_content": room_data["revisit_content"]
                    }
                else:
                    room_widget.revisit_data = {}

                # Load room image
                if 'image' in room_data:
                    room_image_filename = room_data['image']
                    if room_image_filename in zip_file.namelist():
                        room_image_data = zip_file.read(room_image_filename)
                        pixmap = QPixmap()
                        pixmap.loadFromData(room_image_data)
                        room_widget.roomImageLabel.setPixmap(pixmap.scaled(256, 192, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))

                # Load exits
                for exit_name, exit_data in room_data.get('exits', {}).items():
                    room_widget.addExit()
                    exit_widget = room_widget.exitsLayout.itemAt(room_widget.exitsLayout.count() - 1).widget()
                    exit_widget.exitNameInput.setText(exit_name)
                    if isinstance(exit_data, str):
                        exit_widget.exitDestinationInput.setText(exit_data)
                    elif isinstance(exit_data, dict):
                        # Load skill check data only if exitWidget is an instance of ExitWidget
                        if isinstance(exit_widget, ExitWidget):
                            exit_widget.skillCheckData = exit_data.get('skill_check', None)
                            if exit_widget.skillCheckData:
                                exit_widget.skillCheckIndicator.setVisible(True)
                            else:
                                exit_widget.skillCheckIndicator.setVisible(False)
                        else:
                            QMessageBox.warning(story_editor_widget, "Error", f"Invalid exit widget encountered: {type(exit_widget)}")

                # Remove any invalid exits from the roomWidget
                room_widget.removeInvalidExits()

                # Update icons
                room_widget.updateIcons()

    except Exception as e:
        QMessageBox.warning(story_editor_widget, "Error", f"Failed to load story: {str(e)}")

def save_story(story_editor_widget, filename):
    try:
        story_data = {
            'name': story_editor_widget.storyNameInput.text() if story_editor_widget.storyNameInput else '',
            'button_color': story_editor_widget.buttonColorButton.styleSheet().split(':')[1].strip() if story_editor_widget.buttonColorButton else '',
            'start_room': story_editor_widget.startRoomInput.currentText() if story_editor_widget.startRoomInput else '',
            'rooms': {}
        }

        with zipfile.ZipFile(filename, 'w') as zip_file:
            # Save story.json
            json_data = json.dumps(story_data, indent=2).encode('utf-8')
            zip_file.writestr('story.json', json_data)

            # Save summary.txt
            summary_text = story_editor_widget.summaryInput.toPlainText().encode('utf-8')
            zip_file.writestr('summary.txt', summary_text)

            # Save cover image
            pixmap = story_editor_widget.coverImageLabel.pixmap()
            if pixmap:
                image = pixmap.toImage()
                byte_array = QByteArray()
                buffer = QBuffer(byte_array)
                buffer.open(QIODevice.WriteOnly)
                image.save(buffer, "JPG")
                zip_file.writestr('cover.jpg', byte_array.data())

            # Save room data
            for i in range(story_editor_widget.roomsTabWidget.count()):
                room_widget = story_editor_widget.roomsTabWidget.widget(i)
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

                room_data = {
                    'description': room_description,
                    'exits': room_exits
                }

                if hasattr(room_widget, 'revisitDialog') and room_widget.revisitDialog is not None:
                    revisit_data = room_widget.revisitDialog.getRevisitData()
                    if revisit_data["revisit_count"] > 0 or revisit_data["revisit_content"]:
                        room_data["revisit_count"] = revisit_data["revisit_count"]
                        room_data["revisit_content"] = revisit_data["revisit_content"]

                if room_widget.room_image_path:
                    room_image_filename = f"room_{i + 1}.jpg"
                    room_data['image'] = room_image_filename
                    zip_file.write(room_widget.room_image_path, room_image_filename)

                story_data['rooms'][room_name] = room_data

        QMessageBox.information(story_editor_widget, "Success", "Story saved successfully.")
    except Exception as e:
        QMessageBox.warning(story_editor_widget, "Error", f"Failed to save story: {str(e)}")