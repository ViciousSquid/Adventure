from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton, QCheckBox, QSizePolicy, QFileDialog, QTabBar, QDialog, QListWidget
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import pyqtSignal, Qt, QSize
from widgets.exit_widget import ExitWidget
from widgets.revisit_dialog import RevisitDialog
from widgets.skill_check_dialog import SkillCheckDialog
from inventory_manager import InventoryManager

class RoomWidget(QWidget):
    roomNameChanged = pyqtSignal(str)

    def __init__(self, parent=None, available_items=None, required_item=None):
        super().__init__(parent)
        self.initUserInterface()
        self.revisit_data = {}
        self.revisitDialog = None
        self.room_image_path = None

        if available_items is not None:
            self.availableItemsListWidget.addItems(available_items)
        if required_item is not None:
            self.requiredItemInput.setText(required_item)

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

        # Skill check and revisit icons
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
        iconLayout.addWidget(self.skillCheckIconLabel)
        iconLayout.addWidget(self.revisitIconLabel)
        roomNameLayout.addWidget(iconWidget)

        layout.addLayout(roomNameLayout)

        # Room description input
        roomDescriptionLabel = QLabel("Room Description:")
        self.roomDescriptionInput = QTextEdit()
        layout.addWidget(roomDescriptionLabel)
        layout.addWidget(self.roomDescriptionInput)

        # Track revisits and inventory checkboxes
        checkboxesLayout = QHBoxLayout()
        self.trackRevisitsCheckbox = QCheckBox("Track revisits")
        self.trackRevisitsCheckbox.stateChanged.connect(self.onTrackRevisitsStateChanged)
        checkboxesLayout.addWidget(self.trackRevisitsCheckbox)

        self.hasInventoryCheckbox = QCheckBox("Has Inventory")
        self.hasInventoryCheckbox.stateChanged.connect(self.onHasInventoryStateChanged)
        checkboxesLayout.addWidget(self.hasInventoryCheckbox)

        layout.addLayout(checkboxesLayout)

        # Room image input
        roomImageLayout = QHBoxLayout()
        roomImageLayout.setAlignment(Qt.AlignLeft)  # Align the buttons to the left
        roomImageLabel = QLabel("Room Image:")
        self.roomImageButton = QPushButton("Choose Image")
        self.roomImageButton.clicked.connect(self.openImageDialog)
        self.clearImageButton = QPushButton("Clear Image")
        self.clearImageButton.clicked.connect(self.clearImage)
        roomImageLayout.addWidget(roomImageLabel)
        roomImageLayout.addWidget(self.roomImageButton)
        roomImageLayout.addWidget(self.clearImageButton)
        roomImageLayout.addStretch()  # Add a stretch to push the buttons to the left
        layout.addLayout(roomImageLayout)

        # Room image preview
        self.roomImageLabel = QLabel()
        layout.addWidget(self.roomImageLabel)

        # Available items (hidden by default)
        self.availableItemsWidget = QWidget()
        self.availableItemsLayout = QHBoxLayout(self.availableItemsWidget)
        availableItemsLabel = QLabel("Available Items:")
        self.availableItemsListWidget = QListWidget()
        self.availableItemInput = QLineEdit()
        self.availableItemInput.setPlaceholderText("Enter an item")
        self.addAvailableItemButton = QPushButton("Add Item")
        self.addAvailableItemButton.clicked.connect(self.addAvailableItem)
        self.removeAvailableItemButton = QPushButton("Remove Item")
        self.removeAvailableItemButton.clicked.connect(self.removeAvailableItem)
        self.availableItemsLayout.addWidget(availableItemsLabel)
        self.availableItemsLayout.addWidget(self.availableItemsListWidget)
        self.availableItemsLayout.addWidget(self.availableItemInput)
        self.availableItemsLayout.addWidget(self.addAvailableItemButton)
        self.availableItemsLayout.addWidget(self.removeAvailableItemButton)
        layout.addWidget(self.availableItemsWidget)
        self.availableItemsWidget.setVisible(False)

        # Required item (hidden by default)
        self.requiredItemWidget = QWidget()
        self.requiredItemLayout = QHBoxLayout(self.requiredItemWidget)
        requiredItemLabel = QLabel("Required Item:")
        self.requiredItemInput = QLineEdit()
        self.requiredItemLayout.addWidget(requiredItemLabel)
        self.requiredItemLayout.addWidget(self.requiredItemInput)
        layout.addWidget(self.requiredItemWidget)
        self.requiredItemWidget.setVisible(False)

        # Exits
        self.exitsLayout = QVBoxLayout()
        self.exitsLayout.setSpacing(2)
        exitsLabel = QLabel("Exits:")
        self.exitsLayout.addWidget(exitsLabel)
        layout.addLayout(self.exitsLayout)

        self.setLayout(layout)

    def onHasInventoryStateChanged(self, state):
        if state == Qt.Checked:
            self.availableItemsWidget.setVisible(True)
            self.requiredItemWidget.setVisible(True)
        else:
            self.availableItemsWidget.setVisible(False)
            self.requiredItemWidget.setVisible(False)

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

    def showSkillCheckDialog(self, exitWidget):
        dialog = SkillCheckDialog(self)
        dialog.setSkillCheckData(exitWidget.skillCheckData)
        if dialog.exec_() == QDialog.Accepted:
            exitWidget.skillCheckData = dialog.getSkillCheckData()
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

    def updateIcons(self):
        for index in range(self.exitsLayout.count()):
            widget = self.exitsLayout.itemAt(index).widget()
            if isinstance(widget, ExitWidget):
                diceIconLabel = widget.layout().itemAt(widget.layout().count() - 1).widget()
                if widget.skillCheckData:
                    diceIconLabel.setVisible(True)
                else:
                    diceIconLabel.setVisible(False)

        if self.hasSkillCheck():
            self.skillCheckIconLabel.setPixmap(QPixmap("editordata/skillcheck_grey.png").scaled(24, 24))
            self.skillCheckIconLabel.setVisible(True)
        else:
            self.skillCheckIconLabel.setVisible(False)

        if self.hasRevisitData():
            self.revisitIconLabel.setPixmap(QPixmap("editordata/revisit.png").scaled(24, 24))
            self.revisitIconLabel.setVisible(True)
            self.trackRevisitsCheckbox.setChecked(True)
        else:
            self.revisitIconLabel.setVisible(False)
            self.trackRevisitsCheckbox.setChecked(False)

        self.updateTabIcon()

    def updateTabIcon(self):
        tabWidget = self.parent().parent()
        tabIndex = tabWidget.indexOf(self)
        if self.hasSkillCheck() and self.hasRevisitData():
            skillcheck_icon = QIcon("editordata/skillcheck.png")
            revisit_icon = QIcon("editordata/revisit.png")
            tabWidget.setTabIcon(tabIndex, QIcon())  # Clear the left icon
            tabWidget.setIconSize(QSize(16, 16))
            iconWidget = QWidget()
            iconLayout = QHBoxLayout(iconWidget)
            skillcheck_label = QLabel()
            skillcheck_label.setPixmap(skillcheck_icon.pixmap(16, 16))
            iconLayout.addWidget(skillcheck_label)
            revisit_label = QLabel()
            revisit_label.setPixmap(revisit_icon.pixmap(16, 16))
            iconLayout.addWidget(revisit_label)
            tabWidget.tabBar().setTabButton(tabIndex, QTabBar.LeftSide, iconWidget)
        elif self.hasSkillCheck():
            tabWidget.setTabIcon(tabIndex, QIcon("editordata/skillcheck.png"))
            tabWidget.setIconSize(QSize(16, 16))
            tabWidget.tabBar().setTabButton(tabIndex, QTabBar.LeftSide, None)
        elif self.hasRevisitData():
            tabWidget.setTabIcon(tabIndex, QIcon("editordata/revisit.png"))
            tabWidget.setIconSize(QSize(16, 16))
            tabWidget.tabBar().setTabButton(tabIndex, QTabBar.LeftSide, None)
        else:
            tabWidget.setTabIcon(tabIndex, QIcon())
            tabWidget.tabBar().setTabButton(tabIndex, QTabBar.LeftSide, None)

    def removeInvalidExits(self):
        for index in range(self.exitsLayout.count() - 1, -1, -1):
            widget = self.exitsLayout.itemAt(index).widget()
            if not isinstance(widget, ExitWidget):
                self.exitsLayout.removeWidget(widget)
                widget.deleteLater()

    def setRevisitData(self, revisit_data):
        self.revisit_data = revisit_data
        self.trackRevisitsCheckbox.setChecked(bool(revisit_data))
        self.updateIcons()

    def addAvailableItem(self):
        item = self.availableItemInput.text().strip()
        if item:
            self.availableItemsListWidget.addItem(item)
            self.availableItemInput.clear()

    def removeAvailableItem(self):
        selected_items = self.availableItemsListWidget.selectedItems()
        for item in selected_items:
            self.availableItemsListWidget.takeItem(self.availableItemsListWidget.row(item))

    def getAvailableItems(self):
        return [self.availableItemsListWidget.item(i).text() for i in range(self.availableItemsListWidget.count())]

    def getRequiredItem(self):
        return self.requiredItemInput.text().strip()