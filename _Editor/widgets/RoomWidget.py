from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton, QCheckBox
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import pyqtSignal, Qt
from widgets.exit_widget import ExitWidget
from widgets.revisit_dialog import RevisitDialog

class RoomWidget(QWidget):
    roomNameChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUserInterface()
        self.revisit_data = {}
        self.revisitDialog = None

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
        roomImageLayout.addWidget(roomImageLabel)
        roomImageLayout.addWidget(self.roomImageButton)
        layout.addLayout(roomImageLayout)

        # Room image preview
        self.roomImageLabel = QLabel()
        layout.addWidget(self.roomImageLabel)

        # Skill check and revisit icon
        self.iconLabel = QLabel()
        self.iconLabel.setVisible(False)
        self.iconLabel.mousePressEvent = self.showRevisitDialog
        layout.addWidget(self.iconLabel)

        # Exits
        self.exitsLayout = QVBoxLayout()
        self.exitsLayout.setSpacing(2)
        exitsLabel = QLabel("Exits:")
        self.exitsLayout.addWidget(exitsLabel)
        layout.addLayout(self.exitsLayout)

        self.setLayout(layout)

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
        if self.hasSkillCheck() and self.hasRevisitData():
            self.iconLabel.setPixmap(QPixmap("editordata/both.png").scaled(48, 24))
            self.iconLabel.setVisible(True)
        elif self.hasSkillCheck():
            self.iconLabel.setPixmap(QPixmap("editordata/dice.png").scaled(24, 24))
            self.iconLabel.setVisible(True)
        elif self.hasRevisitData():
            self.iconLabel.setPixmap(QPixmap("editordata/revisit.png").scaled(24, 24))
            self.iconLabel.setVisible(True)
        else:
            self.iconLabel.setVisible(False)

        self.updateTabIcon()

    def updateTabIcon(self):
        tabWidget = self.parent().parent()
        tabIndex = tabWidget.indexOf(self)
        if self.hasSkillCheck() and self.hasRevisitData():
            tabWidget.setTabIcon(tabIndex, QIcon("editordata/both.png"))
        elif self.hasSkillCheck():
            tabWidget.setTabIcon(tabIndex, QIcon("editordata/dice.png"))
        elif self.hasRevisitData():
            tabWidget.setTabIcon(tabIndex, QIcon("editordata/revisit.png"))
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