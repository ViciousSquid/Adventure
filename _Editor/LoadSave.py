import zipfile
import json
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QLineEdit
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QByteArray, QBuffer, QIODevice
from editordata.exit_widget import ExitWidget
import logging

# Configure logging
logging.basicConfig(filename='editor.log', level=logging.ERROR)

def load_story(story_editor_widget, filename):
    try:
        with zipfile.ZipFile(filename, 'r') as zip_file:
            # Load story.json
            with zip_file.open('story.json') as json_file:
                story_data = json.load(json_file)

            # Load items.json if available
            item_data = {}
            if 'items.json' in zip_file.namelist():
                try:
                    with zip_file.open('items.json') as items_file:
                        item_data = json.load(items_file)
                except json.JSONDecodeError as e:
                    logging.error(f"Error loading items.json: {str(e)}")
                    item_data = {}  # Fallback to empty item data

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
                try:
                    cover_image_data = zip_file.read('cover.jpg')
                    pixmap = QPixmap()
                    pixmap.loadFromData(cover_image_data)
                    story_editor_widget.coverImageLabel.setPixmap(pixmap)
                except Exception as e:
                    logging.error(f"Error loading cover image: {str(e)}")
                    story_editor_widget.coverImageLabel.setText("Failed to load cover image")
            else:
                story_editor_widget.coverImageLabel.setText("No cover image")

            if 'summary.txt' in zip_file.namelist():
                try:
                    summary_text = zip_file.read('summary.txt').decode('utf-8')
                    story_editor_widget.summaryInput.setText(summary_text)
                except UnicodeDecodeError as e:
                    logging.error(f"Error decoding summary text: {str(e)}")
                    story_editor_widget.summaryInput.setText("Failed to load summary")
            else:
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
                        try:
                            room_image_data = zip_file.read(room_image_filename)
                            pixmap = QPixmap()
                            pixmap.loadFromData(room_image_data)
                            room_widget.roomImageLabel.setPixmap(pixmap)
                        except Exception as e:
                            logging.error(f"Error loading room image {room_image_filename}: {str(e)}")
                            room_widget.roomImageLabel.setText(f"Failed to load room image: {room_image_filename}")

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
                            logging.error(f"Invalid exit widget encountered: {type(exit_widget)}")
                    else:
                        logging.error("Failed to retrieve exit widget from layout.")

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

    except FileNotFoundError:
        logging.error(f"Story file not found: {filename}")
        QMessageBox.warning(story_editor_widget, "Error", f"Story file not found: {filename}")
    except zipfile.BadZipFile:
        logging.error(f"Invalid ZIP file: {filename}")
        QMessageBox.warning(story_editor_widget, "Error", f"Invalid ZIP file: {filename}")
    except Exception as e:
        logging.exception(f"Error loading story: {str(e)}")
        QMessageBox.warning(story_editor_widget, "Error", f"Failed to load story: {str(e)}")

def save_story(story_editor_widget, filename):
    try:
        story_data = {
            'name': story_editor_widget.storyNameInput.text() if story_editor_widget.storyNameInput else '',
            'button_color': story_editor_widget.buttonColorButton.styleSheet().split(':')[1].strip() if story_editor_widget.buttonColorButton else '',
            'start_room': story_editor_widget.startRoomInput.currentText() if story_editor_widget.startRoomInput else '',
            'rooms': collect_room_data(story_editor_widget)
        }

        with zipfile.ZipFile(filename, 'w') as zip_file:
            try:
                # Save story.json
                zip_file.writestr('story.json', json.dumps(story_data, indent=2))

                # Save items.json
                item_data = story_editor_widget.item_data
                item_json_data = json.dumps(item_data, indent=2).encode('utf-8')
                zip_file.writestr('items.json', item_json_data)

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

                # Save room images
                for room_name, room_data in story_data['rooms'].items():
                    if 'image' in room_data:
                        room_image_filename = room_data['image']
                        room_widget = story_editor_widget.roomsTabWidget.widget(story_editor_widget.startRoomInput.findText(room_name))
                        if room_widget.room_image_path:
                            try:
                                zip_file.write(room_widget.room_image_path, room_image_filename)
                            except FileNotFoundError:
                                logging.error(f"Room image file not found: {room_widget.room_image_path}")
                        else:
                            logging.warning(f"Room image path not set for room: {room_name}")

            except Exception as e:
                logging.exception(f"Error writing files to ZIP: {str(e)}")
                raise

        QMessageBox.information(story_editor_widget, "Success", "Story saved successfully.")

    except FileNotFoundError:
        logging.error(f"Error saving story: {filename}")
        QMessageBox.warning(story_editor_widget, "Error", f"Failed to save story: {filename}")
    except Exception as e:
        logging.exception(f"Error saving story: {str(e)}")
        QMessageBox.warning(story_editor_widget, "Error", f"Failed to save story: {str(e)}")