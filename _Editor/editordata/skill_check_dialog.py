from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton
from editordata.skill_check_widget import SkillCheckWidget

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