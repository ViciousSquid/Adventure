from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton, QCheckBox, QSizePolicy, QFileDialog
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import pyqtSignal, Qt, QSize
from editordata.exit_widget import ExitWidget
from editordata.revisit_dialog import RevisitDialog
from editordata.inventory import InventoryWidget, InventoryDialog

class RoomWidget(QWidget):
    roomNameChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUserInterface()
        self.revisit_data = {}
        self.revisitDialog = None
        self.room_image_path = None

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

        # Track revisits and Has Inventory checkboxes
        checkboxLayout = QHBoxLayout()
        self.trackRevisitsCheckbox = QCheckBox("Track revisits")
        self.trackRevisitsCheckbox.stateChanged.connect(self.onTrackRevisitsStateChanged)
        checkboxLayout.addWidget(self.trackRevisitsCheckbox)

        self.inventoryWidget = InventoryWidget(self)
        self.inventoryWidget.inventoryChanged.connect(self.onInventoryChanged)
        checkboxLayout.addWidget(self.inventoryWidget)

        layout.addLayout(checkboxLayout)

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

        # Skill check, revisit, and inventory icons
        iconLayout = QHBoxLayout()
        iconLayout.setSpacing(2)
        iconWidget = QWidget()
        iconWidget.setLayout(iconLayout)
        iconWidget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.skillCheckIconLabel = QLabel()
        self.skillCheckIconLabel.setVisible(False)
        self.revisitIconLabel = QLabel()
        self.revisitIconLabel.setVisible(False)
        self.revisitIconLabel.mousePressEvent = self.showRevisitDialog
        self.inventoryIconLabel = QLabel()
        self.inventoryIconLabel.setVisible(False)
        self.inventoryIconLabel.mousePressEvent = self.showInventoryDialog
        iconLayout.addWidget(self.skillCheckIconLabel)
        iconLayout.addWidget(self.revisitIconLabel)
        iconLayout.addWidget(self.inventoryIconLabel)
        layout.addWidget(iconWidget)

        # Exits
        self.exitsLayout = QVBoxLayout()
        self.exitsLayout.setSpacing(2)
        exitsLabel = QLabel("Exits:")
        self.exitsLayout.addWidget(exitsLabel)
        layout.addLayout(self.exitsLayout)

        self.setLayout(layout)

    def openImageDialog(self):
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("Image Files (*.png *.jpg *.bmp)")
        if file_dialog.exec_():
            selected_file = file_dialog.selectedFiles()[0]
            self.room_image_path = selected_file
            pixmap = QPixmap(selected_file)
            self.roomImageLabel.setPixmap(pixmap.scaled(256, 192, Qt.KeepAspectRatio, Qt.SmoothTransformation))

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
            self.revisitDialog.accepted.connect(self.revisitDialog.saveRevisitData)
        self.revisitDialog.setRevisitData(self.revisit_data)
        self.revisitDialog.show()

    def closeRevisitDialog(self):
        if self.revisitDialog is not None:
            self.revisitDialog.close()
            self.revisitDialog = None

    def addExit(self):
        exitWidget = ExitWidget(self)
        self.exitsLayout.addWidget(exitWidget)
        self.updateIcons()

    def emitRoomNameChanged(self):
        self.roomNameChanged.emit(self.roomNameInput.text())

    def hasSkillCheck(self):
        for index in range(self.exitsLayout.count()):
            widget = self.exitsLayout.itemAt(index).widget()
            if isinstance(widget, ExitWidget) and widget.skillCheckData:
                return True
        return False

    def hasRevisitData(self):
        return bool(self.revisit_data)

    def hasInventory(self):
        return self.inventoryWidget.inventoryCheckbox.isChecked()

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

        if self.hasInventory():
            self.inventoryIconLabel.setPixmap(QPixmap("editordata/key.png").scaled(24, 24))
            self.inventoryIconLabel.setVisible(True)
        else:
            self.inventoryIconLabel.setVisible(False)

        self.updateTabIcon()

    def updateTabIcon(self):
        tabWidget = self.parent().parent()
        tabIndex = tabWidget.indexOf(self)
        if self.hasSkillCheck() and self.hasRevisitData() and self.hasInventory():
            icon = QIcon("editordata/all_three.png")
            icon.addPixmap(QPixmap("editordata/all_three.png"), QIcon.Normal, QIcon.Off)
            tabWidget.setTabIcon(tabIndex, icon)
            tabWidget.setIconSize(QSize(64, 24))
        elif self.hasSkillCheck() and self.hasRevisitData():
            icon = QIcon("editordata/both.png")
            icon.addPixmap(QPixmap("editordata/both.png"), QIcon.Normal, QIcon.Off)
            tabWidget.setTabIcon(tabIndex, icon)
            tabWidget.setIconSize(QSize(34, 18))
        elif self.hasSkillCheck() and self.hasInventory():
            icon = QIcon("editordata/skill_inventory.png")
            icon.addPixmap(QPixmap("editordata/skill_inventory.png"), QIcon.Normal, QIcon.Off)
            tabWidget.setTabIcon(tabIndex, icon)
            tabWidget.setIconSize(QSize(34, 18))
        elif self.hasRevisitData() and self.hasInventory():
            icon = QIcon("editordata/revisit_inventory.png")
            icon.addPixmap(QPixmap("editordata/revisit_inventory.png"), QIcon.Normal, QIcon.Off)
            tabWidget.setTabIcon(tabIndex, icon)
            tabWidget.setIconSize(QSize(34, 18))
        elif self.hasSkillCheck():
            tabWidget.setTabIcon(tabIndex, QIcon("editordata/dice.png"))
            tabWidget.setIconSize(QSize(18, 18))
        elif self.hasRevisitData():
            tabWidget.setTabIcon(tabIndex, QIcon("editordata/revisit.png"))
            tabWidget.setIconSize(QSize(18, 18))
        elif self.hasInventory():
            tabWidget.setTabIcon(tabIndex, QIcon("editordata/key.png"))
            tabWidget.setIconSize(QSize(18, 18))
        else:
            tabWidget.setTabIcon(tabIndex, QIcon())

    def removeInvalidExits(self):
        for index in range(self.exitsLayout.count() - 1, -1, -1):
            widget = self.exitsLayout.itemAt(index).widget()
            if not isinstance(widget, ExitWidget):
                self.exitsLayout.removeWidget(widget)
                widget.deleteLater()

    def showInventoryDialog(self, event):
        dialog = InventoryDialog(self)
        dialog.setInventoryData(
            self.inventoryWidget.inventoryCheckbox.isChecked(),
            self.inventoryWidget.item_requirement,
            self.inventoryWidget.use_item_data,
            self.inventoryWidget.inventory_items
        )
        dialog.exec_()

    def onInventoryChanged(self, has_inventory, item_requirement, use_item_data, inventory_items):
        self.updateIcons()

    def setRevisitData(self, revisit_data):
        self.revisit_data = revisit_data
        self.trackRevisitsCheckbox.setChecked(bool(revisit_data))
        self.updateIcons()