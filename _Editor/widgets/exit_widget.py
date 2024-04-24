from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QLabel, QPushButton, QDialog
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSignal

class ExitWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        self.skillCheckData = None

    def initUI(self):
        layout = QHBoxLayout()

        # Exit name input
        exitNameLabel = QLabel("Exit Name:")
        self.exitNameInput = QLineEdit()
        self.exitNameInput.setObjectName("exitNameInput")
        self.exitNameInput.setMaxLength(20)
        layout.addWidget(exitNameLabel)
        layout.addWidget(self.exitNameInput)

        # Exit destination input
        exitDestinationLabel = QLabel("Destination:")
        self.exitDestinationInput = QLineEdit()
        self.exitDestinationInput.setObjectName("exitDestinationInput")
        self.exitDestinationInput.setMaxLength(20)
        layout.addWidget(exitDestinationLabel)
        layout.addWidget(self.exitDestinationInput)

        # Add skill check button
        self.addSkillCheckButton = QPushButton("Add Skill Check")
        self.addSkillCheckButton.clicked.connect(self.openSkillCheckDialog)
        layout.addWidget(self.addSkillCheckButton)

        # Skill check indicator
        self.skillCheckIndicator = QLabel()
        self.skillCheckIndicator.setPixmap(QIcon("editordata/dice.png").pixmap(20, 20))
        self.skillCheckIndicator.setVisible(False)
        self.skillCheckIndicator.mousePressEvent = self.openSkillCheckDialog
        layout.addWidget(self.skillCheckIndicator)

        self.setLayout(layout)

    def openSkillCheckDialog(self, event=None):
        # Import SkillCheckDialog here when it's actually needed
        from editor_core import SkillCheckDialog

        dialog = SkillCheckDialog(self)
        if self.skillCheckData:
            dialog.setSkillCheckData(self.skillCheckData)
        if dialog.exec() == QDialog.Accepted:
            self.skillCheckData = dialog.getSkillCheckData()
            self.skillCheckIndicator.setVisible(True)
            self.parent().updateTabIcon()  # Update the tab icon when skill check data changes
        else:
            self.skillCheckIndicator.setVisible(False)
            self.parent().updateTabIcon()  # Update the tab icon when skill check data changes