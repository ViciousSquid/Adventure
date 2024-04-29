import zipfile
import json
from PyQt5.QtWidgets import QMessageBox, QFileDialog
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QByteArray, QBuffer, QIODevice
from editordata.exit_widget import ExitWidget

def open_load_story_dialog(story_editor_widget):
    file_dialog = QFileDialog()
    file_dialog.setNameFilter("ZIP Files (*.zip)")
    if file_dialog.exec_():
        selected_files = file_dialog.selectedFiles()
        if selected_files:
            load_story(story_editor_widget, selected_files[0])

def open_save_story_dialog(story_editor_widget):
    file_dialog = QFileDialog()
    file_dialog.setDefaultSuffix("zip")
    file_dialog.setNameFilter("ZIP Files (*.zip)")
    file_dialog.setAcceptMode(QFileDialog.AcceptSave)
    if file_dialog.exec_():
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
                        room_widget.roomImageLabel.setPixmap(pixmap.scaled(256, 192, Qt.KeepAspectRatio, Qt.SmoothTransformation))

                # Load inventory data
                if 'inventory' in room_data:
                    room_widget.inventoryWidget.setInventoryData(
                        True,
                        room_data.get('item_requirement', ''),
                        room_data.get('use_item', {}),
                        room_data['inventory']
                    )
                else:
                    room_widget.inventoryWidget.setInventoryData(False, '', {}, [])

                # Load exits
                for exit_name, exit_data in room_data.get('exits', {}).items():
                    room_widget.addExit()
                    exit_widget = room_widget.exitsLayout.itemAt(room_widget.exitsLayout.count() - 1).widget()
                    exit_widget.exitNameInput.setText(exit_name)
                    if isinstance(exit_data, str):
                        exit_widget.exitDestinationInput.setText(exit_data)
                    elif isinstance(exit_data, dict):
                        if isinstance(exit_widget, ExitWidget):
                            exit_widget.skillCheckData = exit_data.get('skill_check', None)
                            if exit_widget.skillCheckData:
                                exit_widget.skillCheckIndicator.setVisible(True)
                            else:
                                exit_widget.skillCheckIndicator.setVisible(False)
                        else:
                            QMessageBox.warning(story_editor_widget, "Error", f"Invalid exit widget encountered: {type(exit_widget)}")

                # Remove any invalid exits from the room_widget
                room_widget.removeInvalidExits()

                # Update icons
                room_widget.updateIcons()

    except Exception as e:
        QMessageBox.warning(story_editor_widget, "Error", f"Failed to load story: {str(e)}")

def save_story(story_editor_widget, filename):
    try:
        story_data = {
            'name': story_editor_widget.storyNameInput.text(),
            'button_color': story_editor_widget.buttonColorButton.styleSheet().split(':')[1].strip(),
            'start_room': story_editor_widget.startRoomInput.currentText(),
            'rooms': {}
        }

        with zipfile.ZipFile(filename, 'w') as zip_file:
            # Save story.json
            for i in range(story_editor_widget.roomsTabWidget.count()):
                room_widget = story_editor_widget.roomsTabWidget.widget(i)
                room_name = room_widget.roomNameInput.text()
                room_description = room_widget.roomDescriptionInput.toPlainText()
                room_exits = {}

                for j in range(room_widget.exitsLayout.count()):
                    exit_widget = room_widget.exitsLayout.itemAt(j).widget()
                    exit_name = exit_widget.exitNameInput.text()
                    if exit_widget.skillCheckData:
                        room_exits[exit_name] = {'skill_check': exit_widget.skillCheckData}
                    else:
                        room_exits[exit_name] = exit_widget.exitDestinationInput.text()

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
                else:
                    room_data['image'] = None

                has_inventory, item_requirement, use_item_data, inventory_items = room_widget.inventoryWidget.getInventoryData()
                if has_inventory:
                    room_data['inventory'] = inventory_items
                    if item_requirement:
                        room_data['item_requirement'] = item_requirement
                    if use_item_data:
                        room_data['use_item'] = use_item_data

                story_data['rooms'][room_name] = room_data

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

        QMessageBox.information(story_editor_widget, "Success", "Story saved successfully.")
    except Exception as e:
        QMessageBox.warning(story_editor_widget, "Error", f"Failed to save story: {str(e)}")