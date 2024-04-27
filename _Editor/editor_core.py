print("== STORY EDITOR == (beta) \nstarting up..")
try:
    from LoadSave import openLoadStoryDialog, openSaveStoryDialog
except ImportError:
    pass

import sys
import os
import json
import zipfile
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QTextEdit, QFileDialog, QLabel, QColorDialog, QComboBox,
    QTabWidget, QScrollArea, QMessageBox, QMenu, QAction, QDialog, QSplitter,
    QCheckBox, QPlainTextEdit, QDialogButtonBox
)
from PyQt5.QtGui import QPixmap, QColor, QFont, QImage, QIcon
from PyQt5.QtCore import Qt, QRect, QSize, QByteArray, QBuffer, QIODevice, pyqtSignal

from widgets.skill_check_widget import SkillCheckWidget
from widgets.exit_widget import ExitWidget
from widgets.revisit_dialog import RevisitDialog
from widgets.RoomWidget import RoomWidget
from widgets.skill_check_dialog import SkillCheckDialog
from theme import set_theme, CURRENT_THEME
from settings_window import SettingsWindow

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
        self.addExitButton.clicked.connect(self.addExit)

    def initUserInterface(self):
        mainLayout = QHBoxLayout()

        # Left column
        self.leftColumn = QWidget()
        self.leftColumn.setFixedWidth(300)
        leftLayout = QVBoxLayout()

        # Story name input
        storyNameLayout = QHBoxLayout()
        storyNameLabel = QLabel("Story Name:")
        self.storyNameInput = QLineEdit()
        self.storyNameInput.setMaxLength(25)
        storyNameLayout.addWidget(storyNameLabel)
        storyNameLayout.addWidget(self.storyNameInput)
        leftLayout.addLayout(storyNameLayout)

        # Button color input
        buttonColorLayout = QHBoxLayout()
        buttonColorLabel = QLabel("Button Color:")
        self.buttonColorButton = QPushButton()
        self.buttonColorButton.setStyleSheet("background-color: #000000;")
        buttonColorLayout.addWidget(buttonColorLabel)
        buttonColorLayout.addWidget(self.buttonColorButton)
        leftLayout.addLayout(buttonColorLayout)

        # Cover image input
        coverImageLayout = QHBoxLayout()
        coverImageLabel = QLabel("Cover Image:")
        self.coverImageButton = QPushButton("Choose Image")
        self.coverImageButton.setObjectName("chooseImageButton")
        coverImageLayout.addWidget(coverImageLabel)
        coverImageLayout.addWidget(self.coverImageButton)
        leftLayout.addLayout(coverImageLayout)

        # Cover image preview
        self.coverImageLabel = QLabel()
        leftLayout.addWidget(self.coverImageLabel)

        # Summary input
        summaryLabel = QLabel("Summary:")
        self.summaryInput = QTextEdit()
        self.summaryInput.setMaximumHeight(100)
        leftLayout.addWidget(summaryLabel)
        leftLayout.addWidget(self.summaryInput)

        # Start room input
        startRoomLayout = QHBoxLayout()
        startRoomLabel = QLabel("Start Room:")
        self.startRoomInput = QComboBox()
        startRoomLayout.addWidget(startRoomLabel)
        startRoomLayout.addWidget(self.startRoomInput)
        leftLayout.addLayout(startRoomLayout)

        self.leftColumn.setLayout(leftLayout)
        mainLayout.addWidget(self.leftColumn)

        # Splitter for right section
        splitter = QSplitter(Qt.Vertical)

        # Top section (room details)
        topSection = QWidget()
        topLayout = QVBoxLayout()

        # Room name input
        roomNameLayout = QHBoxLayout()
        roomNameLabel = QLabel("Room Name:")
        self.roomNameInput = QLineEdit()
        self.roomNameInput.setMaxLength(60)
        roomNameLayout.addWidget(roomNameLabel)
        roomNameLayout.addWidget(self.roomNameInput)
        topLayout.addLayout(roomNameLayout)

        # Room description input
        roomDescriptionLabel = QLabel("Room Description:")
        self.roomDescriptionInput = QTextEdit()
        topLayout.addWidget(roomDescriptionLabel)
        topLayout.addWidget(self.roomDescriptionInput)

        topSection.setLayout(topLayout)
        splitter.addWidget(topSection)

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
        self.addRoomButton.setObjectName("addRoomButton")
        self.addExitButton = QPushButton("Add Exit")
        self.addExitButton.setObjectName("addExitButton")
        buttonsLayout.addWidget(self.addRoomButton)
        buttonsLayout.addWidget(self.addExitButton)
        bottomLayout.addLayout(buttonsLayout)

        bottomSection.setLayout(bottomLayout)
        splitter.addWidget(bottomSection)
        splitter.setSizes([400, 200])  # Initial sizes for top and bottom sections

        mainLayout.addWidget(splitter)
        self.setLayout(mainLayout)

    def updateFonts(self, font):
        def updateWidgetFont(widget):
            widget.setFont(font)
            for child in widget.findChildren(QWidget):
                updateWidgetFont(child)

        updateWidgetFont(self)
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
            "Are you sure you want to delete this room?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if confirmation == QMessageBox.Yes:
            self.roomsTabWidget.removeTab(tabIndex)
            self.startRoomInput.removeItem(tabIndex)

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About Story Editor")
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        about_label = QLabel("Development build 107")
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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUserInterface()

    def initUserInterface(self):
        self.setWindowTitle("Story Editor")
        self.setMinimumSize(800, 600)

        # Create the story editor widget and set it as the central widget
        self.storyEditorWidget = StoryEditorWidget(self)
        self.setCentralWidget(self.storyEditorWidget)

        # Create menu bar
        self.menubar = self.menuBar()
        fileMenu = self.menubar.addMenu("File")
        viewMenu = self.menubar.addMenu("View")
        settingsMenu = self.menubar.addMenu("Settings")  # Add Settings menu
        helpMenu = self.menubar.addMenu("Help")  # Move Help menu after Settings

        # Load story action
        loadStoryAction = fileMenu.addAction("Load Story")
        loadStoryAction.triggered.connect(lambda: openLoadStoryDialog(self.storyEditorWidget))

        # Save story action
        saveStoryAction = fileMenu.addAction("Save Story")
        saveStoryAction.triggered.connect(lambda: openSaveStoryDialog(self.storyEditorWidget))

        # Toggle sidebar action
        self.toggleSidebarAction = viewMenu.addAction("Toggle Sidebar")
        self.toggleSidebarAction.setCheckable(True)
        self.toggleSidebarAction.setChecked(True)
        self.toggleSidebarAction.triggered.connect(self.toggleSidebar)

        # View Story Data menu
        viewStoryDataMenu = viewMenu.addMenu("View Story Data")
        viewStoryJsonAction = viewStoryDataMenu.addAction("Complete")
        viewStoryJsonAction.triggered.connect(lambda: self.viewStoryJson("Complete"))
        viewRoomsAction = viewStoryDataMenu.addAction("Rooms")
        viewRoomsAction.triggered.connect(lambda: self.viewStoryJson("Rooms"))
        viewRoomsWithExitsAction = viewStoryDataMenu.addAction("Rooms with Exits")
        viewRoomsWithExitsAction.triggered.connect(lambda: self.viewStoryJson("Rooms with Exits"))
        viewRoomsWithoutExitsAction = viewStoryDataMenu.addAction("Rooms without Exits")
        viewRoomsWithoutExitsAction.triggered.connect(lambda: self.viewStoryJson("Rooms without Exits"))
        viewRoomCountAction = viewStoryDataMenu.addAction("Room Count")
        viewRoomCountAction.triggered.connect(lambda: self.viewStoryJson("Room Count"))

        # Settings action
        settingsAction = settingsMenu.addAction("Settings")
        settingsAction.triggered.connect(self.showSettingsWindow)

        # About action
        aboutAction = helpMenu.addAction("About")
        aboutAction.triggered.connect(self.showAboutDialog)

        # Connect signals and slots
        self.storyEditorWidget.buttonColorButton.clicked.connect(self.showColorDialog)
        self.storyEditorWidget.coverImageButton.clicked.connect(self.openCoverImageDialog)

    def toggleSidebar(self, checked):
        if checked:
            self.storyEditorWidget.leftColumn.show()
        else:
            self.storyEditorWidget.leftColumn.hide()

    def showColorDialog(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.storyEditorWidget.buttonColorButton.setStyleSheet(
                f"background-color: {color.name()};"
            )

    def openCoverImageDialog(self):
        fileDialog = QFileDialog()
        fileDialog.setNameFilter("Image Files (*.png *.jpg *.bmp)")
        if fileDialog.exec():
            selectedFiles = fileDialog.selectedFiles()
            if selectedFiles:
                pixmap = QPixmap(selectedFiles[0])
                scaledPixmap = pixmap.scaled(
                    QSize(256, 192), Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.storyEditorWidget.coverImageLabel.setPixmap(scaledPixmap)

    def showAboutDialog(self):
        aboutDialog = AboutDialog(self)
        aboutDialog.exec_()

    def showSettingsWindow(self):
        settings_window = SettingsWindow(self)
        settings_window.exec_()

    def updateApplicationFont(self, font):
        QApplication.setFont(font)
        self.storyEditorWidget.updateFonts(font)
        self.storyEditorWidget.setStyleSheet("QWidget {font-family: '" + font.family() + "';}")

    def viewStoryJson(self, mode):
        # Load the story data from the storyEditorWidget
        story_data = {
            'name': self.storyEditorWidget.storyNameInput.text(),
            'button_color': self.storyEditorWidget.buttonColorButton.styleSheet().split(':')[1].strip(),
            'start_room': self.storyEditorWidget.startRoomInput.currentText(),
            'rooms': {}
        }

        for i in range(self.storyEditorWidget.roomsTabWidget.count()):
            roomWidget = self.storyEditorWidget.roomsTabWidget.widget(i)
            roomName = roomWidget.roomNameInput.text()
            roomDescription = roomWidget.roomDescriptionInput.toPlainText()
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

            roomData = {
                'description': roomDescription,
                'exits': roomExits
            }

            story_data['rooms'][roomName] = roomData

        # Create and show the JsonViewDialog
        json_view_dialog = JsonViewDialog(self, story_data, mode)
        json_view_dialog.exec_()

if __name__ == "__main__":
    application = QApplication(sys.argv)

    # Set the theme
    set_theme()

    window = MainWindow()
    window.show()
    sys.exit(application.exec_())