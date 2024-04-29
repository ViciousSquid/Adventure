from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton, QCheckBox, QSizePolicy, QFileDialog, QComboBox, QSplitter, QMenu, QAction, QTabWidget, QMessageBox, QTabBar
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import pyqtSignal, Qt, QSize, QRect, QPoint

from editordata.exit_widget import ExitWidget
from editordata.revisit_dialog import RevisitDialog
from editordata.inventory import InventoryWidget, InventoryDialog
from editordata.RoomWidget import RoomWidget

class TabBar(QTabBar):
    def __init__(self, parent=None, storyEditorWidget=None):
        super().__init__(parent)
        self.storyEditorWidget = storyEditorWidget

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            tabIndex = self.tabAt(event.pos())
            if tabIndex != -1:
                self.storyEditorWidget.showContextMenu(tabIndex, event.globalPos())
        super().mouseReleaseEvent(event)

class StoryEditorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUserInterface()
        self.addRoomButton.clicked.connect(self.addRoom)
        self.addExitButton.clicked.connect(self.addExit)

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
        tabBar = TabBar(self.roomsTabWidget, self)
        self.roomsTabWidget.setTabBar(tabBar)
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

    def showContextMenu(self, tabIndex, globalPos):
        if tabIndex != -1:
            roomWidget = self.roomsTabWidget.widget(tabIndex)
            contextMenu = QMenu(self)

            deleteAction = QAction("Delete Room", self)
            deleteAction.triggered.connect(lambda: self.deleteRoom(roomWidget))
            contextMenu.addAction(deleteAction)

            if roomWidget.exitsLayout.count() > 1:
                removeExitAction = QAction("Remove Exit", self)
                removeExitAction.triggered.connect(lambda: self.removeLastExit(roomWidget))
                contextMenu.addAction(removeExitAction)

            contextMenu.exec_(globalPos)

    def deleteRoom(self, roomWidget):
        confirmation = QMessageBox.question(
            self,
            "Delete Room",
            "Are you sure?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if confirmation == QMessageBox.Yes:
            tabIndex = self.roomsTabWidget.indexOf(roomWidget)
            self.roomsTabWidget.removeTab(tabIndex)
            self.startRoomInput.removeItem(tabIndex)

    def removeLastExit(self, roomWidget):
        confirmation = QMessageBox.question(
            self,
            "Remove Exit",
            "Are you sure you want to remove the most recent exit?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if confirmation == QMessageBox.Yes:
            if roomWidget.exitsLayout.count() > 1:  # Check if the room has exits (excluding the "Exits:" label)
                lastExitIndex = roomWidget.exitsLayout.count() - 1
                exitWidget = roomWidget.exitsLayout.itemAt(lastExitIndex).widget()
                roomWidget.exitsLayout.removeWidget(exitWidget)
                exitWidget.deleteLater()
                roomWidget.updateIcons()