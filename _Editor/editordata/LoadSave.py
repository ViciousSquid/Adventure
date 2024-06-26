import zipfile
import json
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QLineEdit
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QByteArray, QBuffer, QIODevice
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

            # Load items.json if available
            item_data = {}
            if 'items.json' in zip_file.namelist():
                with zip_file.open('items.json') as items_file:
                    item_data = json.load(items_file)

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

                if "revisits" in room_data:
                    revisits = room_data["revisits"]
                    if isinstance(revisits, list):
                        room_widget.revisit_data = {
                            "revisit_count": revisits[-1]["count"] if revisits else 0,
                            "revisit_content": revisits[-1]["content"] if revisits else "",
                            "show_all_revisits": room_data.get("show_all_revisits", False)
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
                        room_widget.roomImageLabel.setPixmap(pixmap)

                # Load exits
                for exit_name, exit_data in room_data.get('exits', {}).items():
                    room_widget.addExit()
                    exit_widget = room_widget.exitsLayout.itemAt(room_widget.exitsLayout.count() - 1).widget()
                    if exit_widget is not None:
                        if isinstance(exit_widget, ExitWidget):
                            exit_widget.exitNameInput.setText(exit_name)
                            if isinstance(exit_data, str):
                                exit_widget.exitDestinationInput.setText(exit_data)
                            elif isinstance(exit_data, dict):
                                exit_widget.skillCheckData = exit_data.get('skill_check', None)
                                if exit_widget.skillCheckData:
                                    exit_widget.skillCheckIndicator.setVisible(True)
                                else:
                                    exit_widget.skillCheckIndicator.setVisible(False)
                        else:
                            QMessageBox.warning(story_editor_widget, "Error", f"Invalid exit widget encountered: {type(exit_widget)}")
                    else:
                        QMessageBox.warning(story_editor_widget, "Error", "Failed to retrieve exit widget from layout.")

                # Remove any invalid exits from the roomWidget
                room_widget.removeInvalidExits()

                # Update icons
                room_widget.updateIcons()

                # Load inventory-related data
                room_widget.inventory_data = {
                    "items": room_data.get("items", []),
                    "item_needed": room_data.get("item_needed", None),
                    "skill_check": room_data.get("item_skill_check", None)
                }

            # Load item data from items.json
            story_editor_widget.item_data = item_data

    except Exception as e:
        QMessageBox.warning(story_editor_widget, "Error", f"Failed to load story: {str(e)}")

def collect_room_data(story_editor_widget):
    room_data = {}
    for i in range(story_editor_widget.roomsTabWidget.count()):
        room_widget = story_editor_widget.roomsTabWidget.widget(i)
        room_name = room_widget.roomNameInput.text() if room_widget.roomNameInput else ''

       # print(f"Collecting room data for room {i + 1}: {room_name}")  Debug logging

        if not room_name:
            raise ValueError(f"Empty room name for room at index {i}")

        room_description = room_widget.roomDescriptionInput.toPlainText() if room_widget.roomDescriptionInput else ''

        # print(f"Room description: {room_description}")  # Debug logging

        room_exits = {}

        # Collect revisit data
        revisit_data = {}
        if hasattr(room_widget, 'revisitDialog') and room_widget.revisitDialog is not None:
            revisit_data = room_widget.revisitDialog.getRevisitData()
            if revisit_data["revisit_count"] > 0 or revisit_data["revisit_content"]:
                revisit_data = [
                    {
                        "count": revisit_data["revisit_count"],
                        "content": revisit_data["revisit_content"]
                    }
                ]
                revisit_data["show_all_revisits"] = revisit_data["show_all_revisits"]

        # Collect exits
        for j in range(room_widget.exitsLayout.count()):
            exit_widget = room_widget.exitsLayout.itemAt(j).widget()
            exit_name_input = exit_widget.findChild(QLineEdit, "exitNameInput")
            exit_name = exit_name_input.text() if exit_name_input else ''
            exit_destination_input = exit_widget.findChild(QLineEdit, "exitDestinationInput")
            exit_destination = exit_destination_input.text() if exit_destination_input else ''

#            print(f"Exit {j + 1}: {exit_name} - Destination: {exit_destination}")  # Debug logging

            if exit_widget.skillCheckData:
                room_exits[exit_name] = {'skill_check': exit_widget.skillCheckData}
            else:
                room_exits[exit_name] = exit_destination

        room_data[room_name] = {
            'description': room_description,
            'exits': room_exits,
            'revisits': revisit_data,
            'items': room_widget.inventory_data.get("items", []),
            'item_needed': room_widget.inventory_data.get("item_needed", None),
            'item_skill_check': room_widget.inventory_data.get("skill_check", None)
        }

        if room_widget.room_image_path:
            room_image_filename = f"room_{i + 1}.jpg"
            room_data[room_name]['image'] = room_image_filename
            # The image file will be written to the ZIP file in the save_story function

        # print(f"Collected room data for room {room_name}: {room_data[room_name]}")  # Debug logging

    return room_data

def save_story(story_editor_widget, filename):
    try:
        story_data = {
            'name': story_editor_widget.storyNameInput.text() if story_editor_widget.storyNameInput else '',
            'button_color': story_editor_widget.buttonColorButton.styleSheet().split(':')[1].strip() if story_editor_widget.buttonColorButton else '',
            'start_room': story_editor_widget.startRoomInput.currentText() if story_editor_widget.startRoomInput else '',
            'rooms': collect_room_data(story_editor_widget)
        }

        # print(f"Collected story data: {story_data}")  # Debug logging

        with zipfile.ZipFile(filename, 'w') as zip_file:
            try:
                # Save story.json
                zip_file.writestr('story.json', json.dumps(story_data, indent=2))
                print("story.json written to ZIP file")  # Debug logging

                # Save items.json
                item_data = story_editor_widget.item_data
                item_json_data = json.dumps(item_data, indent=2).encode('utf-8')
                zip_file.writestr('items.json', item_json_data)
                print("items.json written to ZIP file")  # Debug logging

                # Save summary.txt
                summary_text = story_editor_widget.summaryInput.toPlainText().encode('utf-8')
                zip_file.writestr('summary.txt', summary_text)
                print("summary.txt written to ZIP file")  # Debug logging

                # Save cover image
                pixmap = story_editor_widget.coverImageLabel.pixmap()
                if pixmap:
                    image = pixmap.toImage()
                    byte_array = QByteArray()
                    buffer = QBuffer(byte_array)
                    buffer.open(QIODevice.WriteOnly)
                    image.save(buffer, "JPG")
                    zip_file.writestr('cover.jpg', byte_array.data())
                    print("cover.jpg written to ZIP file")  # Debug logging

                # Save room images
                for room_name, room_data in story_data['rooms'].items():
                    if 'image' in room_data:
                        room_image_filename = room_data['image']
                        room_widget = story_editor_widget.roomsTabWidget.widget(story_editor_widget.startRoomInput.findText(room_name))
                        if room_widget.room_image_path:
                            zip_file.write(room_widget.room_image_path, room_image_filename)
                            print(f"Room image {room_image_filename} written to ZIP file")  # Debug logging

            except Exception as e:
                print(f"Error writing files to ZIP: {str(e)}")  # Debug logging
                raise

        print(f"Story saved to: {filename}")  # Debug logging
        QMessageBox.information(story_editor_widget, "Success", "Story saved successfully.")

    except Exception as e:
        QMessageBox.warning(story_editor_widget, "Error", f"Failed to save story: {str(e)}")
        print(f"Error saving story: {str(e)}")  # Debug logging