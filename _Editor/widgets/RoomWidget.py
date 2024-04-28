from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton, QCheckBox, QSizePolicy, QFileDialog
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import pyqtSignal, Qt, QSize
from widgets.exit_widget import ExitWidget
from widgets.revisit_dialog import RevisitDialog

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

        # Track revisits checkbox
        self.trackRevisitsCheckbox = QCheckBox("Track revisits")
        self.trackRevisitsCheckbox.stateChanged.connect(self.onTrackRevisitsStateChanged)
        layout.addWidget(self.trackRevisitsCheckbox)

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

        self.updateTabIcon()

    def updateTabIcon(self):
        tabWidget = self.parent().parent()
        tabIndex = tabWidget.indexOf(self)
        if self.hasSkillCheck() and self.hasRevisitData():
            icon = QIcon("editordata/both.png")
            icon.addPixmap(QPixmap("editordata/both.png"), QIcon.Normal, QIcon.Off)
            tabWidget.setTabIcon(tabIndex, icon)
            tabWidget.setIconSize(QSize(34, 18))  # Set the icon size to 32x24 pixels
        elif self.hasSkillCheck():
            tabWidget.setTabIcon(tabIndex, QIcon("editordata/dice.png"))
            tabWidget.setIconSize(QSize(18, 18))  # Set the icon size to 24x24 pixels
        elif self.hasRevisitData():
            tabWidget.setTabIcon(tabIndex, QIcon("editordata/revisit.png"))
            tabWidget.setIconSize(QSize(18, 18))  # Set the icon size to 24x24 pixels
        else:
            tabWidget.setTabIcon(tabIndex, QIcon())

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