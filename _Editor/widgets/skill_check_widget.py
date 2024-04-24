from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QTextEdit

class SkillCheckWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Dice type label and input
        diceTypeLabel = QLabel("Dice Type:")
        self.diceTypeInput = QLineEdit()
        diceTypeLabel.setBuddy(self.diceTypeInput)
        layout.addWidget(diceTypeLabel)
        layout.addWidget(self.diceTypeInput)

        # Target label and input
        targetLabel = QLabel("Target:")
        self.targetInput = QLineEdit()
        targetLabel.setBuddy(self.targetInput)
        layout.addWidget(targetLabel)
        layout.addWidget(self.targetInput)

        # Success consequence
        successConsequenceLabel = QLabel("Success Consequence:")
        self.successConsequenceLayout = QVBoxLayout()
        self.successConsequenceDescriptionInput = QTextEdit()
        self.successConsequenceLayout.addWidget(self.successConsequenceDescriptionInput)
        self.successConsequenceRoomLabel = QLabel("Room:")
        self.successConsequenceRoomInput = QLineEdit()
        self.successConsequenceLayout.addWidget(self.successConsequenceRoomLabel)
        self.successConsequenceLayout.addWidget(self.successConsequenceRoomInput)
        layout.addWidget(successConsequenceLabel)
        layout.addLayout(self.successConsequenceLayout)

        # Failure consequence
        failureConsequenceLabel = QLabel("Failure Consequence:")
        self.failureConsequenceLayout = QVBoxLayout()
        self.failureConsequenceDescriptionInput = QTextEdit()
        self.failureConsequenceLayout.addWidget(self.failureConsequenceDescriptionInput)
        self.failureConsequenceRoomLabel = QLabel("Room:")
        self.failureConsequenceRoomInput = QLineEdit()
        self.failureConsequenceLayout.addWidget(self.failureConsequenceRoomLabel)
        self.failureConsequenceLayout.addWidget(self.failureConsequenceRoomInput)
        layout.addWidget(failureConsequenceLabel)
        layout.addLayout(self.failureConsequenceLayout)

        self.setLayout(layout)

    def getSkillCheckData(self):
        data = {
            "dice_type": self.diceTypeInput.text(),
            "target": int(self.targetInput.text()) if self.targetInput.text() else 0,
            "success": {
                "description": self.successConsequenceDescriptionInput.toPlainText(),
                "room": self.successConsequenceRoomInput.text(),
            },
            "failure": {
                "description": self.failureConsequenceDescriptionInput.toPlainText(),
                "room": self.failureConsequenceRoomInput.text(),
            },
        }
        return data

    def setSkillCheckData(self, data):
        self.diceTypeInput.setText(data.get("dice_type", ""))
        self.targetInput.setText(str(data.get("target", "")))
        self.successConsequenceDescriptionInput.setText(data.get("success", {}).get("description", ""))
        self.successConsequenceRoomInput.setText(data.get("success", {}).get("room", ""))
        self.failureConsequenceDescriptionInput.setText(data.get("failure", {}).get("description", ""))
        self.failureConsequenceRoomInput.setText(data.get("failure", {}).get("room", ""))