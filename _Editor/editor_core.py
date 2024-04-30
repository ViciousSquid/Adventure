print("== STORY EDITOR == (beta) \nstarting up..")
try:
    from editordata.LoadSave import open_load_story_dialog, openSaveStoryDialog
except ImportError:
    pass

from editordata.LoadSave import open_load_story_dialog, open_save_story_dialog

import sys
import os
import json
import zipfile
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QTextEdit, QFileDialog, QLabel, QColorDialog, QComboBox,
    QTabWidget, QScrollArea, QMessageBox, QMenu, QAction, QDialog, QSplitter,
    QCheckBox, QPlainTextEdit, QDialogButtonBox, QSizePolicy
)
from PyQt5.QtGui import QPixmap, QColor, QFont, QImage, QIcon
from PyQt5.QtCore import Qt, QRect, QSize, QByteArray, QBuffer, QIODevice, pyqtSignal

from editordata.skill_check_widget import SkillCheckWidget
from editordata.json import loadRawJson
from editordata.exit_widget import ExitWidget
from editordata.revisit_dialog import RevisitDialog
from editordata.RoomWidget import RoomWidget
from editordata.skill_check_dialog import SkillCheckDialog
from editordata.json import show_json_error_dialog
from editordata.theme import set_theme, CURRENT_THEME
from editordata.settings_window import SettingsWindow

print("Imports loaded \nPyQt5 loaded")

class SkillCheckDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Skill Check")
        self.initUserInterface()

    def initUserInterface(self):
        layout = QVBoxLayout()

        self.skillCheckWidget = SkillCheckWidget()
        layout.addWidget(self.skillCheckWidget)

        buttonLayout = QHBoxLayout()
        okButton = QPushButton("OK")
        okButton.clicked.connect(self.accept)
        buttonLayout.addWidget(okButton)

        cancelButton = QPushButton("Cancel")
        cancelButton.clicked.connect(self.reject)
        buttonLayout.addWidget(cancelButton)

        layout.addLayout(buttonLayout)
        layout.setSizeConstraint(QLayout.SetFixedSize)

        self.setLayout(layout)

    def getSkillCheckData(self):
        return self.skillCheckWidget.getSkillCheckData()

    def setSkillCheckData(self, data):
        self.skillCheckWidget.setSkillCheckData(data)

class StoryEditorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUserInterface()
        self.addRoomButton.clicked.connect(self.addRoom)
        self.addRoomButton.setStyleSheet("background-color: orange; color: black;")
        self.addRoomButton.setFixedHeight(35)
        self.addRoomButton.setFixedWidth(160)


    def initUserInterface(self):
        mainLayout = QHBoxLayout()

        # Left column
        self.left_column = QWidget()
        self.left_column.setFixedWidth(300)
        left_layout = QVBoxLayout()
        left_layout.setSpacing(4)  # Reduce the spacing between elements

        # Story name input
        storyNameLayout = QHBoxLayout()
        storyNameLabel = QLabel("Story Name:")
        self.storyNameInput = QLineEdit()
        self.storyNameInput.setMaxLength(60)
        storyNameLayout.addWidget(storyNameLabel)
        storyNameLayout.addWidget(self.storyNameInput)
        left_layout.addLayout(storyNameLayout)

        # Button color input
        buttonColorLayout = QHBoxLayout()
        buttonColorLabel = QLabel("Button Color:")
        self.buttonColorButton = QPushButton()
        self.buttonColorButton.setStyleSheet("background-color: #000000;")
        buttonColorLayout.addWidget(buttonColorLabel)
        buttonColorLayout.addWidget(self.buttonColorButton)
        left_layout.addLayout(buttonColorLayout)

        # Cover image input
        coverImageLayout = QHBoxLayout()
        coverImageLabel = QLabel("Cover Image:")
        self.coverImageButton = QPushButton("Choose Image")
        self.coverImageButton.setObjectName("chooseImageButton")
        coverImageLayout.addWidget(coverImageLabel)
        coverImageLayout.addWidget(self.coverImageButton)
        left_layout.addLayout(coverImageLayout)

        # Cover image preview
        self.coverImageLabel = QLabel()
        left_layout.addWidget(self.coverImageLabel)

        # Summary input
        summaryLayout = QVBoxLayout()
        summaryLabel = QLabel("Summary:")
        self.summaryInput = QTextEdit()
        self.summaryInput.setMaximumHeight(100)
        summaryLayout.addWidget(summaryLabel)
        summaryLayout.addWidget(self.summaryInput)
        left_layout.addLayout(summaryLayout)

        # Start room input
        startRoomLayout = QHBoxLayout()
        startRoomLabel = QLabel("Start Room:")
        self.startRoomInput = QComboBox()
        startRoomLayout.addWidget(startRoomLabel)
        startRoomLayout.addWidget(self.startRoomInput)
        left_layout.addLayout(startRoomLayout)

        self.left_column.setLayout(left_layout)
        mainLayout.addWidget(self.left_column)

        # Splitter for right section
        splitter = QSplitter(Qt.Vertical)

        # Bottom section
        bottomSection = QWidget()
        bottomLayout = QVBoxLayout()

        # Rooms
        self.roomsTabWidget = QTabWidget()
        self.roomsTabWidget.setTabPosition(QTabWidget.South)
        self.roomsTabWidget.setMovable(True)
        self.roomsTabWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.roomsTabWidget.customContextMenuRequested.connect(self.showContextMenu)
        bottomLayout.addWidget(self.roomsTabWidget)

        # Add room and add exit buttons
        buttonsLayout = QHBoxLayout()
        self.addRoomButton = QPushButton("Add Room")
        self.addRoomButton.setStyleSheet("background-color: orange; color: black;")
        self.addRoomButton.setObjectName("addRoomButton")
        self.addExitButton = QPushButton("Add Exit")
        self.addExitButton.setObjectName("addExitButton")
        buttonsLayout.addWidget(self.addRoomButton)
        bottomLayout.addLayout(buttonsLayout)

        bottomSection.setLayout(bottomLayout)
        splitter.addWidget(bottomSection)
        splitter.setSizes([400, 200])  # Initial sizes for top and bottom sections

        mainLayout.addWidget(splitter)
        self.setLayout(mainLayout)

    def updateFonts(self, font):
        def updateWidgetFont(widget, font):
            widget.setFont(font)
            for child in widget.children():
                if isinstance(child, QWidget):
                    updateWidgetFont(child, font)

        updateWidgetFont(self, font)
        self.setStyleSheet("QWidget {font-family: '" + font.family() + "';}")

    def addRoom(self):
        roomWidget = RoomWidget(self)
        tabIndex = self.roomsTabWidget.addTab(roomWidget, "New Room")
        self.startRoomInput.addItem("New Room")
        roomWidget.roomNameChanged.connect(lambda name: self.updateTabText(tabIndex, name))

    def addExit(self):
        currentRoom = self.roomsTabWidget.currentWidget()
        if currentRoom:
            currentRoom.addExit()

    def updateTabText(self, tabIndex, name):
        self.roomsTabWidget.setTabText(tabIndex, name)
        self.startRoomInput.setItemText(tabIndex, name)

    def showContextMenu(self, position):
        tabBar = self.roomsTabWidget.tabBar()
        if tabBar.tabAt(position) != -1:
            contextMenu = QMenu(self)
            deleteAction = QAction("Delete Room", self)
            deleteAction.triggered.connect(lambda: self.deleteRoom(tabBar.tabAt(position)))
            contextMenu.addAction(deleteAction)
            contextMenu.exec_(tabBar.mapToGlobal(position))

    def deleteRoom(self, tabIndex):
        confirmation = QMessageBox.question(
            self,
            "Delete Room",
            "Are you sure?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if confirmation == QMessageBox.Yes:
            self.roomsTabWidget.removeTab(tabIndex)
            self.startRoomInput.removeItem(tabIndex)

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Story Editor")
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        about_label = QLabel("Development build \nInv107")
        layout.addWidget(about_label)

        informative_label = QLabel("https://github.com/ViciousSquid/Adventure")
        layout.addWidget(informative_label)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def sizeHint(self):
        return QSize(400, 200)  # Adjust the size as needed

class JsonViewDialog(QDialog):
    def __init__(self, parent=None, json_data=None, mode="Complete"):
        super().__init__(parent)
        self.setWindowTitle("View Story JSON")
        self.initUI(json_data, mode)

    def initUI(self, json_data, mode):
        layout = QVBoxLayout()

        json_text_edit = QPlainTextEdit()
        json_text_edit.setReadOnly(True)

        if mode == "Complete":
            json_text_edit.setPlainText(json.dumps(json_data, indent=2))
        elif mode == "Rooms":
            json_text_edit.setPlainText(json.dumps(list(json_data['rooms'].keys()), indent=2))
        elif mode == "Rooms with Exits":
            rooms_with_exits = {room: data['exits'] for room, data in json_data['rooms'].items() if data['exits']}
            json_text_edit.setPlainText(json.dumps(rooms_with_exits, indent=2))
        elif mode == "Rooms without Exits":
            rooms_without_exits = [room for room, data in json_data['rooms'].items() if not data['exits']]
            json_text_edit.setPlainText(json.dumps(rooms_without_exits, indent=2))
        elif mode == "Room Count":
            room_count = len(json_data['rooms'])
            room_names = list(json_data['rooms'].keys())
            text = f"Number of rooms: {room_count}\n\nRoom names:\n"
            text += "\n".join(room_names)
            json_text_edit.setPlainText(text)

        # Add a maximize button control
        maximize_button = QPushButton("Maximize")  # Use QPushButton instead of QToolButton
        maximize_button.clicked.connect(self.showMaximized)

        layout.addWidget(json_text_edit)
        layout.addWidget(maximize_button, alignment=Qt.AlignRight)  # Add the maximize button to the layout
        self.setLayout(layout)

import json
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QMessageBox
from editordata.json import show_json_error_dialog

import json
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QMessageBox
from editordata.json import show_json_error_dialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initialize_user_interface()
        self.errors = []  # Initialize an empty list to store errors

    def initialize_user_interface(self):
        self.setWindowTitle("Story Editor")
        self.setMinimumSize(800, 600)

        # Create the story editor widget and set it as the central widget
        self.story_editor_widget = StoryEditorWidget(self)
        self.setCentralWidget(self.story_editor_widget)

        # Create menu bar
        self.menu_bar = self.menuBar()
        file_menu = self.menu_bar.addMenu("File")
        view_menu = self.menu_bar.addMenu("View")
        settings_menu = self.menu_bar.addMenu("Settings")
        help_menu = self.menu_bar.addMenu("Help")

        # New Story action
        new_story_action = file_menu.addAction("New Story")
        new_story_action.triggered.connect(self.new_story)

        # Load story action
        load_story_action = file_menu.addAction("Load Story")
        load_story_action.triggered.connect(lambda: open_load_story_dialog(self.story_editor_widget))

        # Save story action
        save_story_action = file_menu.addAction("Save Story")
        save_story_action.triggered.connect(lambda: open_save_story_dialog(self.story_editor_widget))

        # Import menu
        import_menu = file_menu.addMenu("Import")
        load_raw_json_action = import_menu.addAction("Import Raw JSON")
        load_raw_json_action.triggered.connect(lambda: self.load_raw_json_dialog())

        # Toggle sidebar action
        self.toggle_sidebar_action = view_menu.addAction("Toggle Sidebar")
        self.toggle_sidebar_action.setCheckable(True)
        self.toggle_sidebar_action.setChecked(True)
        self.toggle_sidebar_action.triggered.connect(self.toggle_sidebar)

        # View Story Data menu
        view_story_data_menu = view_menu.addMenu("View Story Data")
        view_story_json_action = view_story_data_menu.addAction("Complete")
        view_story_json_action.triggered.connect(lambda: self.view_story_json("Complete"))
        view_room_count_action = view_story_data_menu.addAction("Room Count")
        view_room_count_action.triggered.connect(lambda: self.view_story_json("Room Count"))
        view_rooms_with_exits_action = view_story_data_menu.addAction("Rooms with Exits")
        view_rooms_with_exits_action.triggered.connect(lambda: self.view_story_json("Rooms with Exits"))
        view_rooms_without_exits_action = view_story_data_menu.addAction("Rooms without Exits")
        view_rooms_without_exits_action.triggered.connect(lambda: self.view_story_json("Rooms without Exits"))

        # Settings action
        settings_action = settings_menu.addAction("Settings")
        settings_action.triggered.connect(self.show_settings_window)

        # About action
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self.show_about_dialog)

        # Connect signals and slots
        self.story_editor_widget.buttonColorButton.clicked.connect(self.show_color_dialog)
        self.story_editor_widget.coverImageButton.clicked.connect(self.open_cover_image_dialog)

    def toggle_sidebar(self, checked):
        if checked:
            self.story_editor_widget.left_column.show()
        else:
            self.story_editor_widget.left_column.hide()

    def show_color_dialog(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.story_editor_widget.buttonColorButton.setStyleSheet(
                f"background-color: {color.name()};"
            )

    def open_cover_image_dialog(self):
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("Image Files (*.png *.jpg *.bmp)")
        if file_dialog.exec_():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                pixmap = QPixmap(selected_files[0])
                scaled_pixmap = pixmap.scaled(
                    QSize(256, 192), Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.story_editor_widget.cover_image_label.setPixmap(scaled_pixmap)

    def show_about_dialog(self):
        about_dialog = AboutDialog(self)
        about_dialog.exec_()

    def show_settings_window(self):
        settings_window = SettingsWindow(self)
        settings_window.exec_()

    def update_application_font(self, font):
        QApplication.setFont(font)
        self.story_editor_widget.updateFonts(font)
        self.story_editor_widget.setStyleSheet("QWidget {font-family: '" + font.family() + "';}")

    def view_story_json(self, mode):
        # Load the story data from the story_editor_widget
        story_data = {
            'name': self.story_editor_widget.storyNameInput.text(),
            'button_color': self.story_editor_widget.buttonColorButton.styleSheet().split(':')[1].strip(),
            'start_room': self.story_editor_widget.startRoomInput.currentText(),
            'rooms': {}
        }

        for i in range(self.story_editor_widget.roomsTabWidget.count()):
            room_widget = self.story_editor_widget.roomsTabWidget.widget(i)
            room_name = room_widget.roomNameInput.text()
            room_description = room_widget.roomDescriptionInput.toPlainText()
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

            story_data['rooms'][room_name] = room_data

        # Create and show the JsonViewDialog
        json_view_dialog = JsonViewDialog(self, story_data, mode)
        json_view_dialog.exec_()

    def load_raw_json_dialog(self):
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("JSON Files (*.json)")
        if file_dialog.exec_():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                self.load_raw_json_data(selected_files[0])

    def load_raw_json_data(self, filename):
        self.errors = []  # Clear the errors list
        try:
            with open(filename, 'r') as json_file:
                raw_json_data = json.load(json_file)

            # Clear existing data
            self.story_editor_widget.storyNameInput.clear()
            self.story_editor_widget.buttonColorButton.setStyleSheet("background-color: #000000;")
            self.story_editor_widget.coverImageLabel.clear()
            self.story_editor_widget.summaryInput.clear()
            self.story_editor_widget.startRoomInput.clear()
            self.story_editor_widget.roomsTabWidget.clear()

            # Populate fields from raw JSON data
            self.story_editor_widget.storyNameInput.setText(raw_json_data.get('name', ''))
            button_color = raw_json_data.get('button_color', '#000000')
            self.story_editor_widget.buttonColorButton.setStyleSheet(f"background-color: {button_color};")
            self.story_editor_widget.summaryInput.setText(raw_json_data.get('summary', ''))

            # Load rooms
            for room_name, room_data in raw_json_data.get('rooms', {}).items():
                self.story_editor_widget.addRoom()
                room_widget = self.story_editor_widget.roomsTabWidget.widget(self.story_editor_widget.roomsTabWidget.count() - 1)
                room_widget.roomNameInput.setText(room_name)
                room_widget.roomDescriptionInput.setText(room_data.get('description', ''))

                # Load exits
                for exit_name, exit_data in room_data.get('exits', {}).items():
                    room_widget.addExit()
                    exit_widget = room_widget.exitsLayout.itemAt(room_widget.exitsLayout.count() - 1).widget()
                    exit_widget.exitNameInput.setText(exit_name)
                    if isinstance(exit_data, str):
                        exit_widget.exitDestinationInput.setText(exit_data)
                    elif isinstance(exit_data, dict):
                        exit_widget.skillCheckData = exit_data.get('skill_check', None)
                        if exit_widget.skillCheckData:
                            exit_widget.skillCheckIndicator.setVisible(True)
                        else:
                            exit_widget.skillCheckIndicator.setVisible(False)

                # Remove any invalid exits from the room_widget
                room_widget.removeInvalidExits()

                # Update icons
                room_widget.updateIcons()

            # Add room names to the startRoomInput combobox
            self.story_editor_widget.startRoomInput.addItems(raw_json_data.get('rooms', {}).keys())

        except json.JSONDecodeError as e:
            error_message = str(e)
            error_dialog, current_error_index, total_errors = show_json_error_dialog(error_message, filename)
            if error_dialog is not None:
                error_dialog.exec_()
                if current_error_index is not None:
                    self.errors.append(f"Error {current_error_index} of {total_errors}: {error_message}")
                else:
                    self.errors.append(f"Error: {error_message}")
            else:
                self.errors.append(f"Error: {error_message}")
        except Exception as e:
            self.errors.append(f"Error: {str(e)}")

        if self.errors:
            self.save_errors_to_file(filename)

    def save_errors_to_file(self, filename):
        try:
            # Remove the extra 'json' extension from the filename
            filename_without_ext = filename.rsplit('.', 1)[0]

            with open("errors.log", "w", encoding="utf-8") as file:
                file.write(f"Attempted to load {filename_without_ext}\n\n")
                file.write(f"Total errors: {len(self.errors)}\n\n")
                for error in self.errors:
                    file.write(error + "\n")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save errors to file: {str(e)}")

    def new_story(self):
        confirmation = QMessageBox.question(
            self,
            "New Story",
            "Are you sure you want to start a new story? All unsaved data will be lost.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if confirmation == QMessageBox.Yes:
            self.clear_editor_fields()

    def clear_editor_fields(self):
        # Clear fields in the story_editor_widget
        self.story_editor_widget.storyNameInput.clear()
        self.story_editor_widget.buttonColorButton.setStyleSheet("background-color: #000000;")
        self.story_editor_widget.coverImageLabel.clear()
        self.story_editor_widget.summaryInput.clear()
        self.story_editor_widget.startRoomInput.clear()
        self.story_editor_widget.roomsTabWidget.clear()

if __name__ == "__main__":
    application = QApplication(sys.argv)

    # Set the theme
    set_theme()

    window = MainWindow()
    window.show()
    sys.exit(application.exec_())