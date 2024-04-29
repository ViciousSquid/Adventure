from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QLabel
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

class ExitWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.skillCheckData = None
        self.initUI()

    def initUI(self):
        layout = QHBoxLayout()

        self.exitNameInput = QLineEdit()
        self.exitNameInput.setPlaceholderText("Exit Name")
        layout.addWidget(self.exitNameInput)

        self.exitDestinationInput = QLineEdit()
        self.exitDestinationInput.setPlaceholderText("Destination")
        layout.addWidget(self.exitDestinationInput)

        addSkillCheckButton = QPushButton("Add Skill Check")
        addSkillCheckButton.clicked.connect(self.addSkillCheck)
        layout.addWidget(addSkillCheckButton)

        self.skillCheckIndicator = QLabel()
        self.skillCheckIndicator.setPixmap(QPixmap("editordata/dice.png").scaled(16, 16))
        self.skillCheckIndicator.setVisible(False)
        self.skillCheckIndicator.mousePressEvent = self.showSkillCheckDialog
        layout.addWidget(self.skillCheckIndicator)

        self.setLayout(layout)

    def addSkillCheck(self):
        from editordata.skill_check_dialog import SkillCheckDialog
        skillCheckDialog = SkillCheckDialog(self)
        if skillCheckDialog.exec_():
            self.skillCheckData = skillCheckDialog.getSkillCheckData()
            self.updateIcon()

    def showSkillCheckDialog(self, event):
        from editordata.skill_check_dialog import SkillCheckDialog
        skillCheckDialog = SkillCheckDialog(self)
        skillCheckDialog.setSkillCheckData(self.skillCheckData)
        if skillCheckDialog.exec_():
            self.skillCheckData = skillCheckDialog.getSkillCheckData()
            self.updateIcon()

    def updateIcon(self):
        if self.skillCheckData:
            self.skillCheckIndicator.setVisible(True)
        else:
            self.skillCheckIndicator.setVisible(False)
        self.updateRoomWidgetIcons()

    def updateRoomWidgetIcons(self):
        room_widget = self.findRoomWidget()
        if room_widget:
            room_widget.updateIcons()

    def findRoomWidget(self):
        parent = self.parent()
        while parent:
            if isinstance(parent, QWidget) and hasattr(parent, 'updateIcons'):
                return parent
            parent = parent.parent()
        return None