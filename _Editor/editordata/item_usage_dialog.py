from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QDialogButtonBox, QWidget, QTextEdit
from PyQt5.QtCore import Qt

class ItemUsageDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Item Usage")
        self.initUserInterface()

    def initUserInterface(self):
        layout = QVBoxLayout()

        nameLabel = QLabel("Item Name:")
        self.nameInput = QLineEdit()
        layout.addWidget(nameLabel)
        layout.addWidget(self.nameInput)

        descriptionLabel = QLabel("Item Description:")
        self.descriptionInput = QLineEdit()
        layout.addWidget(descriptionLabel)
        layout.addWidget(self.descriptionInput)

        usageLabel = QLabel("Usage Scenario:")
        self.usageComboBox = QComboBox()
        self.usageComboBox.addItems(["Unlock Path", "Reveal Object", "Trigger Event", "Restore Health"])
        self.usageComboBox.currentIndexChanged.connect(self.onUsageScenarioChanged)
        layout.addWidget(usageLabel)
        layout.addWidget(self.usageComboBox)

        self.unlockPathWidget = QWidget()
        self.unlockPathLayout = QHBoxLayout()
        self.unlockPathLayout.addWidget(QLabel("Path Name:"))
        self.unlockPathInput = QLineEdit()
        self.unlockPathLayout.addWidget(self.unlockPathInput)
        self.unlockPathLayout.addWidget(QLabel("Destination Room:"))
        self.unlockDestinationInput = QLineEdit()
        self.unlockPathLayout.addWidget(self.unlockDestinationInput)
        self.unlockPathWidget.setLayout(self.unlockPathLayout)
        layout.addWidget(self.unlockPathWidget)

        self.revealObjectWidget = QWidget()
        self.revealObjectLayout = QHBoxLayout()
        self.revealObjectLayout.addWidget(QLabel("Object Description:"))
        self.revealObjectInput = QLineEdit()
        self.revealObjectLayout.addWidget(self.revealObjectInput)
        self.revealObjectWidget.setLayout(self.revealObjectLayout)
        layout.addWidget(self.revealObjectWidget)

        self.triggerEventWidget = QWidget()
        self.triggerEventLayout = QHBoxLayout()
        self.triggerEventLayout.addWidget(QLabel("Event Type:"))
        self.triggerEventInput = QLineEdit()
        self.triggerEventLayout.addWidget(self.triggerEventInput)
        self.triggerEventWidget.setLayout(self.triggerEventLayout)
        layout.addWidget(self.triggerEventWidget)

        self.restoreHealthWidget = QWidget()
        self.restoreHealthLayout = QHBoxLayout()
        self.restoreHealthLayout.addWidget(QLabel("Health Points:"))
        self.restoreHealthInput = QLineEdit()
        self.restoreHealthLayout.addWidget(self.restoreHealthInput)
        self.restoreHealthWidget.setLayout(self.restoreHealthLayout)
        layout.addWidget(self.restoreHealthWidget)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        layout.addWidget(buttonBox)

        self.setLayout(layout)

        self.onUsageScenarioChanged(0)

    def onUsageScenarioChanged(self, index):
        self.unlockPathWidget.setVisible(index == 0)
        self.revealObjectWidget.setVisible(index == 1)
        self.triggerEventWidget.setVisible(index == 2)
        self.restoreHealthWidget.setVisible(index == 3)

    def getItemData(self):
        item_data = {
            "name": self.sanitizeInput(self.nameInput.text()),
            "description": self.sanitizeInput(self.descriptionInput.text()),
            "usage": {}
        }

        usage_scenario = self.usageComboBox.currentText()
        if usage_scenario == "Unlock Path":
            item_data["usage"]["unlock_path"] = {
                "path_name": self.sanitizeInput(self.unlockPathInput.text()),
                "destination_room": self.sanitizeInput(self.unlockDestinationInput.text())
            }
        elif usage_scenario == "Reveal Object":
            item_data["usage"]["reveal_object"] = {
                "object_description": self.sanitizeInput(self.revealObjectInput.text())
            }
        elif usage_scenario == "Trigger Event":
            item_data["usage"]["trigger_event"] = {
                "event_type": self.sanitizeInput(self.triggerEventInput.text())
            }
        elif usage_scenario == "Restore Health":
            item_data["usage"]["restore_health"] = {
                "amount": int(self.restoreHealthInput.text())
            }

        return item_data

    def setItemData(self, item_data):
        self.nameInput.setText(item_data.get("name", ""))
        self.descriptionInput.setText(item_data.get("description", ""))

        usage_scenario = next(iter(item_data.get("usage", {}).keys()), "")
        if usage_scenario == "unlock_path":
            self.usageComboBox.setCurrentIndex(0)
            self.unlockPathInput.setText(item_data["usage"]["unlock_path"].get("path_name", ""))
            self.unlockDestinationInput.setText(item_data["usage"]["unlock_path"].get("destination_room", ""))
        elif usage_scenario == "reveal_object":
            self.usageComboBox.setCurrentIndex(1)
            self.revealObjectInput.setText(item_data["usage"]["reveal_object"].get("object_description", ""))
        elif usage_scenario == "trigger_event":
            self.usageComboBox.setCurrentIndex(2)
            self.triggerEventInput.setText(item_data["usage"]["trigger_event"].get("event_type", ""))
        elif usage_scenario == "restore_health":
            self.usageComboBox.setCurrentIndex(3)
            self.restoreHealthInput.setText(str(item_data["usage"]["restore_health"].get("amount", 0)))

    def sanitizeInput(self, text):
        sanitized_text = text.replace('"', '').replace('\n', '\\n')
        return sanitized_text