import json
import zipfile
import sys
import tempfile
import shutil
import os
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox, QVBoxLayout, QHBoxLayout, QTextEdit, QWidget, QPushButton, QScrollArea, QLabel
from PyQt5.QtGui import QTextCharFormat, QBrush, QColor
from PyQt5.QtCore import Qt

def escape_json_characters(json_data):
    try:
        # Escape double quotes, backslashes, speech marks, and question marks
        escaped_data = json_data.replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'").replace('?', '\\?')
        # Replace new lines with \n
        escaped_data = escaped_data.replace('\n', '\\n')
        return escaped_data, True
    except Exception as e:
        return str(e), False

def highlight_escaped_characters(text_edit, escaped_data):
    # Highlight escaped characters in the QTextEdit
    format = QTextCharFormat()
    format.setBackground(QBrush(QColor("yellow")))
    text_edit.setTextColor(QColor("black"))

    for char in ['\\"', '\\\\', "\\'", '\\?', '\\t']:
        start = 0
        while True:
            index = escaped_data.find(char, start)
            if index == -1:
                break
            text_edit.setCurrentCharFormat(format)
            text_edit.setTextCursor(text_edit.textCursor())
            text_edit.insertPlainText(char)
            start = index + len(char)

    # Highlight \n escape sequences
    format.setBackground(QBrush(QColor("lightblue")))
    start = 0
    while True:
        index = escaped_data.find("\\n", start)
        if index == -1:
            break
        text_edit.setCurrentCharFormat(format)
        text_edit.setTextCursor(text_edit.textCursor())
        text_edit.insertPlainText("\\n")
        start = index + 2

def show_room_descriptions(story_data, zip_file_path):
    # Create a window to display room descriptions
    window = QWidget()
    layout = QVBoxLayout()

    # Create a scroll area
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    layout.addWidget(scroll_area)

    # Create a widget to hold the room descriptions
    content_widget = QWidget()
    content_layout = QVBoxLayout(content_widget)

    all_escaped_successfully = True

    for room_name, room_data in story_data.get('rooms', {}).items():
        description = room_data.get('description', '')

        # Remove leading newline characters from the description
        description = description.lstrip('\n')

        # Create a label for the room title
        room_title = QLabel(f"Room: {room_name}")
        room_title.setStyleSheet("color: white; background-color: black; padding: 5px;")

        # Create top pane for original description
        original_pane = QTextEdit()
        original_pane.setPlainText(description)
        original_pane.setReadOnly(True)
        original_pane.setMinimumHeight(150)  # Set a minimum height for the description box
        original_pane.setStyleSheet("background-color: #f0f0f0;")  # Set light grey background color

        # Create bottom pane for modified description
        modified_pane = QTextEdit()
        escaped_description, escaped_successfully = escape_json_characters(description)
        modified_pane.setPlainText(escaped_description)
        modified_pane.setMinimumHeight(150)  # Set a minimum height for the description box
        highlight_escaped_characters(modified_pane, escaped_description)

        all_escaped_successfully = all_escaped_successfully and escaped_successfully

        # Create a layout for the room descriptions
        room_layout = QVBoxLayout()
        room_layout.addWidget(room_title)
        room_layout.addWidget(original_pane)
        room_layout.addWidget(modified_pane)

        content_layout.addLayout(room_layout)

    scroll_area.setWidget(content_widget)

    # Create a Save button
    save_button = QPushButton("Save")
    save_button.setStyleSheet("background-color: green; color: white; padding: 10px;")
    save_button.clicked.connect(lambda: save_edited_json(content_layout, zip_file_path))
    save_button.setFixedWidth(300)  # Set a fixed width for the Save button

    if not all_escaped_successfully:
        save_button.setStyleSheet("background-color: #808080; color: white; padding: 10px;")
        save_button.setEnabled(False)

    # Create a layout for the Save button
    button_layout = QHBoxLayout()
    button_layout.addStretch()
    button_layout.addWidget(save_button)
    button_layout.addStretch()

    layout.addLayout(button_layout)

    window.setLayout(layout)
    window.setWindowTitle("Validator v1.0")  # Set the window title to "Validator v1.0"
    window.setGeometry(100, 100, 800, 400)
    window.show()

    return window

def save_edited_json(content_layout, zip_file_path):
    # Extract the edited descriptions from the content layout
    edited_descriptions = {}
    for i in range(content_layout.count()):
        room_layout = content_layout.itemAt(i).layout()
        room_name = room_layout.itemAt(0).widget().text().replace("Room: ", "")
        edited_description = room_layout.itemAt(2).widget().toPlainText()
        edited_descriptions[room_name] = edited_description

    # Load the original JSON data from the ZIP file
    with zipfile.ZipFile(zip_file_path, 'r') as zip_file:
        with zip_file.open('story.json') as json_file:
            json_data = json.loads(json_file.read().decode('utf-8'))

    # Update the descriptions in the JSON data with the edited descriptions
    for room_name, edited_description in edited_descriptions.items():
        json_data['rooms'][room_name]['description'] = edited_description

    # Create a temporary directory to store the updated ZIP file
    with tempfile.TemporaryDirectory() as temp_dir:
        # Save the updated JSON data to a temporary file
        temp_json_file = os.path.join(temp_dir, 'story.json')
        with open(temp_json_file, 'w') as json_file:
            json.dump(json_data, json_file, indent=2)

        # Create a new ZIP file with the updated story.json
        temp_zip_file = os.path.join(temp_dir, 'updated.zip')
        with zipfile.ZipFile(temp_zip_file, 'w') as zip_file:
            zip_file.write(temp_json_file, 'story.json')

        # Replace the original ZIP file with the updated one
        shutil.move(temp_zip_file, zip_file_path)

    QMessageBox.information(None, "Success", "The story has been successfully updated.")

def main():
    app = QApplication([])

    try:
        # Prompt the user to select a story ZIP file
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("ZIP Files (*.zip)")
        if file_dialog.exec_():
            selected_file = file_dialog.selectedFiles()[0]

            try:
                # Extract the story.json file from the ZIP file
                with zipfile.ZipFile(selected_file, 'r') as zip_file:
                    with zip_file.open('story.json') as json_file:
                        json_data = json_file.read().decode('utf-8')

                # Load the JSON data
                story_data = json.loads(json_data)

                # Show the room descriptions in a window
                window = show_room_descriptions(story_data, selected_file)
                window.show()

                sys.exit(app.exec_())

            except (zipfile.BadZipFile, KeyError, json.JSONDecodeError) as e:
                QMessageBox.critical(None, "Error", f"Failed to load the story JSON: {str(e)}")

    except Exception as e:
        QMessageBox.critical(None, "Error", f"An unexpected error occurred: {str(e)}")

if __name__ == '__main__':
    main()
