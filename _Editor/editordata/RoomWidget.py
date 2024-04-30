from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton, QCheckBox, QSizePolicy, QFileDialog, QMessageBox
from PyQt5.QtGui import QPixmap, QIcon, QColor
from PyQt5.QtCore import pyqtSignal, Qt, QSize
from editordata.exit_widget import ExitWidget
from editordata.revisit_dialog import RevisitDialog
from editordata.inventory import InventoryDialog

class RoomWidget(QWidget):
    roomNameChanged = pyqtSignal(str)
    addRoomSignal = pyqtSignal(object)
    removeRoomSignal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUserInterface()
        self.revisit_data = {}
        self.revisitDialog = None
        self.inventoryDialog = None
        self.room_image_path = None
        self.inventory_data = {}
        self.exits = []

    def initUserInterface(self):
        layout = QVBoxLayout()

        # Room name input
        roomNameLayout = QHBoxLayout()
        roomNameLabel = QLabel("Room Name:")
        self.roomNameInput = QLineEdit()
        self.roomNameInput.setMaxLength(60)
        self.roomNameInput.textChanged.connect(self.emitRoomNameChanged)
        roomNameLayout.addWidget(roomNameLabel)
        roomNameLayout.addWidget(self.roomNameInput)
        layout.addLayout(roomNameLayout)

        # Room description input
        roomDescriptionLabel = QLabel("Room Description:")
        self.roomDescriptionInput = QTextEdit()
        layout.addWidget(roomDescriptionLabel)
        layout.addWidget(self.roomDescriptionInput)

        # Track revisits and Has inventory checkboxes
        checkboxesLayout = QHBoxLayout()
        self.trackRevisitsCheckbox = QCheckBox("Track revisits")
        self.trackRevisitsCheckbox.setFixedWidth(100)
        self.trackRevisitsCheckbox.stateChanged.connect(self.onTrackRevisitsStateChanged)
        self.hasInventoryCheckbox = QCheckBox("Has inventory")
        self.hasInventoryCheckbox.stateChanged.connect(self.onHasInventoryStateChanged)
        checkboxesLayout.addWidget(self.trackRevisitsCheckbox)
        checkboxesLayout.addWidget(self.hasInventoryCheckbox)
        layout.addLayout(checkboxesLayout)

        # Room image input
        roomImageLayout = QHBoxLayout()
        roomImageLabel = QLabel("Room Image:")
        self.roomImageButton = QPushButton("Choose Image")
        self.roomImageButton.clicked.connect(self.openImageDialog)
        self.clearImageButton = QPushButton("Clear Image")
        self.clearImageButton.clicked.connect(self.clearImage)
        roomImageLayout.addWidget(roomImageLabel)
        roomImageLayout.addWidget(self.roomImageButton)
        roomImageLayout.addWidget(self.clearImageButton)
        layout.addLayout(roomImageLayout)

        # Room image preview
        self.roomImageLabel = QLabel()
        layout.addWidget(self.roomImageLabel)

        # Skill check and revisit/inventory icons
        iconLayout = QHBoxLayout()
        iconLayout.setSpacing(2)  # Adjust the spacing between icons
        iconWidget = QWidget()
        iconWidget.setLayout(iconLayout)
        iconWidget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # Set size policy to fixed
        self.skillCheckIconLabel = QLabel()
        self.skillCheckIconLabel.setVisible(False)
        self.revisitIconLabel = QLabel()
        self.revisitIconLabel.setVisible(False)
        self.revisitIconLabel.mousePressEvent = self.showRevisitDialog
        self.itemIconLabel = QLabel()
        self.itemIconLabel.setVisible(False)
        self.itemIconLabel.mousePressEvent = self.showInventoryDialog
        self.itemNeededIconLabel = QLabel()
        self.itemNeededIconLabel.setVisible(False)
        self.itemNeededIconLabel.mousePressEvent = self.showInventoryDialog
        iconLayout.addWidget(self.skillCheckIconLabel)
        iconLayout.addWidget(self.revisitIconLabel)
        iconLayout.addWidget(self.itemIconLabel)
        iconLayout.addWidget(self.itemNeededIconLabel)
        layout.addWidget(iconWidget)

        # Room buttons
        roomButtonsLayout = QHBoxLayout()
        self.addExitButton = QPushButton("Add Exit")
        self.addExitButton.setFixedWidth(150)
        self.addExitButton.setStyleSheet("background-color: green; color: white;")
        self.addExitButton.clicked.connect(self.addExit)
        self.removeExitButton = QPushButton("Remove Exit")
        self.removeExitButton.setFixedWidth(150)
        self.removeExitButton.setStyleSheet("background-color: red; color: white;")
        self.removeExitButton.clicked.connect(self.removeExit)
        roomButtonsLayout.addWidget(self.addExitButton)
        roomButtonsLayout.addWidget(self.removeExitButton)
        layout.addLayout(roomButtonsLayout)

        self.setLayout(layout)

    def openImageDialog(self):
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("Image Files (*.png *.jpg *.bmp)")
        if file_dialog.exec_():
            selected_file = file_dialog.selectedFiles()[0]
            self.room_image_path = selected_file
            pixmap = QPixmap(selected_file)
            self.roomImageLabel.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def clearImage(self):
        self.room_image_path = None
        self.roomImageLabel.clear()

    def onTrackRevisitsStateChanged(self, state):
        if state == Qt.Checked:
            self.showRevisitDialog()
        else:
            self.revisit_data = {}
            self.closeRevisitDialog()
        self.updateIcons()

    def showRevisitDialog(self, event=None):
        if self.revisitDialog is None:
            self.revisitDialog = RevisitDialog(self)
            self.revisitDialog.accepted.connect(self.saveRevisitData)
        self.revisitDialog.setRevisitData(self.revisit_data)
        self.revisitDialog.show()

    def closeRevisitDialog(self):
        if self.revisitDialog is not None:
            self.revisitDialog.close()
            self.revisitDialog = None

    def saveRevisitData(self):
        self.revisit_data = self.revisitDialog.getRevisitData()
        self.updateIcons()

    def onHasInventoryStateChanged(self, state):
        if state == Qt.Checked:
            self.showInventoryDialog()
        else:
            self.inventory_data = {}
        self.updateIcons()

    def showInventoryDialog(self, event=None):
        if self.inventoryDialog is None:
            self.inventoryDialog = InventoryDialog(self)
            self.inventoryDialog.accepted.connect(self.saveInventoryData)
        self.inventoryDialog.setInventoryData(self.inventory_data)
        self.inventoryDialog.show()

    def saveInventoryData(self):
        self.inventory_data = self.inventoryDialog.getInventoryData()
        self.updateIcons()

    def addExit(self):
        exitWidget = ExitWidget(self)
        exitLayout = QHBoxLayout()
        exitLayout.addWidget(exitWidget)
        self.exits.append(exitWidget)
        self.layout().addLayout(exitLayout)
        self.updateIcons()

    def removeExit(self):
        if self.exits:
            exitWidget = self.exits.pop()
            for layout in self.findChildren(QHBoxLayout):
                if layout.indexOf(exitWidget) != -1:
                    layout.removeWidget(exitWidget)
                    exitWidget.deleteLater()
                    break
        self.updateIcons()

    def emitRoomNameChanged(self):
        self.roomNameChanged.emit(self.roomNameInput.text())

    def hasSkillCheck(self):
        for exitWidget in self.exits:
            if exitWidget.skillCheckData:
                return True
        return False

    def hasRevisitData(self):
        return bool(self.revisit_data)

    def hasItem(self):
        return bool(self.inventory_data.get("item", ""))

    def hasItemNeeded(self):
        return bool(self.inventory_data.get("item_needed", ""))

    def updateIcons(self):
        if self.hasSkillCheck():
            self.skillCheckIconLabel.setPixmap(QPixmap("editordata/dice.png").scaled(24, 24))
            self.skillCheckIconLabel.setVisible(True)
        else:
            self.skillCheckIconLabel.setVisible(False)

        if self.hasRevisitData():
            self.revisitIconLabel.setPixmap(QPixmap("editordata/revisit.png").scaled(24, 24))
            self.revisitIconLabel.setVisible(True)
        else:
            self.revisitIconLabel.setVisible(False)

        if self.hasItem():
            self.itemIconLabel.setPixmap(QPixmap("editordata/key.png").scaled(24, 24))
            self.itemIconLabel.setVisible(True)
        else:
            self.itemIconLabel.setVisible(False)

        if self.hasItemNeeded():
            self.itemNeededIconLabel.setPixmap(QPixmap("editordata/key.png").scaled(24, 24))
            self.itemNeededIconLabel.setVisible(True)
        else:
            self.itemNeededIconLabel.setVisible(False)

        self.updateTabIcon()

    def updateTabIcon(self):
        tabWidget = self.parent().parent()
        tabIndex = tabWidget.indexOf(self)
        if self.hasSkillCheck() and self.hasRevisitData() and self.hasItem() and self.hasItemNeeded():
            icon = QIcon("editordata/all.png")
            icon.addPixmap(QPixmap("editordata/all.png"), QIcon.Normal, QIcon.Off)
            tabWidget.setTabIcon(tabIndex, icon)
            tabWidget.setIconSize(QSize(34, 18))  # Set the icon size to 32x24 pixels
        elif self.hasSkillCheck() and self.hasRevisitData() and self.hasItem():
            # Add a new icon for skill check, revisit, and item
            pass
        elif self.hasSkillCheck() and self.hasRevisitData() and self.hasItemNeeded():
            # Add a new icon for skill check, revisit, and item needed
            pass
        elif self.hasSkillCheck() and self.hasItem() and self.hasItemNeeded():
            # Add a new icon for skill check, item, and item needed
            pass
        elif self.hasRevisitData() and self.hasItem() and self.hasItemNeeded():
            # Add a new icon for revisit, item, and item needed
            pass
        elif self.hasSkillCheck() and self.hasRevisitData():
            icon = QIcon("editordata/both.png")
            icon.addPixmap(QPixmap("editordata/both.png"), QIcon.Normal, QIcon.Off)
            tabWidget.setTabIcon(tabIndex, icon)
            tabWidget.setIconSize(QSize(34, 18))  # Set the icon size to 32x24 pixels
        elif self.hasSkillCheck() and self.hasItem():
            # Add a new icon for skill check and item
            pass
        elif self.hasSkillCheck() and self.hasItemNeeded():
            # Add a new icon for skill check and item needed
            pass
        elif self.hasRevisitData() and self.hasItem():
            # Add a new icon for revisit and item
            pass
        elif self.hasRevisitData() and self.hasItemNeeded():
            # Add a new icon for revisit and item needed
            pass
        elif self.hasItem() and self.hasItemNeeded():
            # Add a new icon for item and item needed
            pass
        elif self.hasSkillCheck():
            tabWidget.setTabIcon(tabIndex, QIcon("editordata/dice.png"))
            tabWidget.setIconSize(QSize(18, 18))  # Set the icon size to 24x24 pixels
        elif self.hasRevisitData():
            tabWidget.setTabIcon(tabIndex, QIcon("editordata/revisit.png"))
            tabWidget.setIconSize(QSize(18, 18))  # Set the icon size to 24x24 pixels
        elif self.hasItem():
            tabWidget.setTabIcon(tabIndex, QIcon("editordata/key.png"))
            tabWidget.setIconSize(QSize(18, 18))  # Set the icon size to 24x24 pixels
        elif self.hasItemNeeded():
            tabWidget.setTabIcon(tabIndex, QIcon("editordata/key.png"))
            tabWidget.setIconSize(QSize(18, 18))  # Set the icon size to 24x24 pixels
        else:
            tabWidget.setTabIcon(tabIndex, QIcon())

    def confirmRemoveRoom(self):
        confirmation = QMessageBox.question(
            self,
            "Remove Room",
            "Are you sure you want to remove this room?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if confirmation == QMessageBox.Yes:
            self.removeRoomSignal.emit()