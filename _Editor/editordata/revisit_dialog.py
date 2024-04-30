from PyQt5.QtWidgets import QDialog, QVBoxLayout, QGridLayout, QLabel, QTextEdit, QSpinBox, QDialogButtonBox

class RevisitDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Revisit Settings")
        self.initUserInterface()

    def initUserInterface(self):
        layout = QVBoxLayout()

        # Revisit Settings
        revisitSettingsLayout = QGridLayout()

        revisitCountLabel = QLabel("Revisit Count:")
        self.revisitCountSpinBox = QSpinBox()
        self.revisitCountSpinBox.setMinimum(0)
        revisitSettingsLayout.addWidget(revisitCountLabel, 0, 0)
        revisitSettingsLayout.addWidget(self.revisitCountSpinBox, 0, 1)

        revisitContentLabel = QLabel("Revisit Content:")
        self.revisitContentInput = QTextEdit()
        revisitSettingsLayout.addWidget(revisitContentLabel, 1, 0)
        revisitSettingsLayout.addWidget(self.revisitContentInput, 1, 1)

        layout.addLayout(revisitSettingsLayout)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        layout.addWidget(buttonBox)

        self.setLayout(layout)

    def getRevisitData(self):
        revisit_data = {
            "revisit_count": self.revisitCountSpinBox.value(),
            "revisit_content": self.revisitContentInput.toPlainText()
        }
        return revisit_data

    def setRevisitData(self, revisit_data):
        self.revisitCountSpinBox.setValue(revisit_data.get("revisit_count", 0))
        self.revisitContentInput.setPlainText(revisit_data.get("revisit_content", ""))