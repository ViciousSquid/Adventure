from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QDialogButtonBox, QCheckBox, QPushButton, QGroupBox
from PyQt5.QtCore import Qt
from editordata.skill_check_dialog import SkillCheckDialog

class InventoryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Inventory Settings")
        self.skill_check_data = None
        self.initUserInterface()

    def initUserInterface(self):
        layout = QVBoxLayout()

        inventorySettingsLayout = QHBoxLayout()

        itemLabel = QLabel("Item:")
        self.itemInput = QLineEdit()
        itemNeededLabel = QLabel("Item Needed:")
        self.itemNeededInput = QLineEdit()
        inventorySettingsLayout.addWidget(itemLabel)
        inventorySettingsLayout.addWidget(self.itemInput)
        inventorySettingsLayout.addWidget(itemNeededLabel)
        inventorySettingsLayout.addWidget(self.itemNeededInput)

        layout.addLayout(inventorySettingsLayout)

        self.skillCheckGroupBox = QGroupBox("Item is acquired when entering the room unless skill check is configured below:")
        skillCheckLayout = QVBoxLayout()

        self.skillCheckCheckBox = QCheckBox("Enable Skill Check")
        self.skillCheckCheckBox.stateChanged.connect(self.onSkillCheckStateChanged)
        skillCheckLayout.addWidget(self.skillCheckCheckBox)

        self.configureSkillCheckButton = QPushButton("Configure Skill Check")
        self.configureSkillCheckButton.clicked.connect(self.showSkillCheckDialog)
        self.configureSkillCheckButton.setEnabled(False)
        skillCheckLayout.addWidget(self.configureSkillCheckButton)

        self.skillCheckGroupBox.setLayout(skillCheckLayout)
        layout.addWidget(self.skillCheckGroupBox)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        layout.addWidget(buttonBox)

        self.setLayout(layout)

    def getInventoryData(self):
        inventory_data = {
            "item": self.itemInput.text(),
            "item_needed": self.itemNeededInput.text(),
            "skill_check": self.skill_check_data
        }
        return inventory_data

    def setInventoryData(self, inventory_data):
        self.itemInput.setText(inventory_data.get("item", ""))
        self.itemNeededInput.setText(inventory_data.get("item_needed", ""))
        self.skill_check_data = inventory_data.get("skill_check", None)
        self.skillCheckCheckBox.setChecked(bool(self.skill_check_data))
        self.configureSkillCheckButton.setEnabled(bool(self.skill_check_data))

    def onSkillCheckStateChanged(self, state):
        self.configureSkillCheckButton.setEnabled(state == Qt.Checked)
        if state == Qt.Unchecked:
            self.skill_check_data = None

    def showSkillCheckDialog(self):
        dialog = SkillCheckDialog(self)
        if self.skill_check_data:
            dialog.setSkillCheckData(self.skill_check_data)
        if dialog.exec_() == QDialog.Accepted:
            self.skill_check_data = dialog.getSkillCheckData()