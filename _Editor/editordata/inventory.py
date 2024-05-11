from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QDialogButtonBox, QCheckBox, QPushButton, QGroupBox, QListWidget, QListWidgetItem
from PyQt5.QtCore import Qt
from editordata.skill_check_dialog import SkillCheckDialog
from editordata.item_usage_dialog import ItemUsageDialog

class InventoryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Inventory Settings")
        self.skill_check_data = None
        self.items = []
        self.initUserInterface()

    def initUserInterface(self):
        layout = QVBoxLayout()

        itemsGroupBox = QGroupBox("Items")
        itemsLayout = QVBoxLayout()

        self.itemsList = QListWidget()
        self.itemsList.itemDoubleClicked.connect(self.editItem)
        itemsLayout.addWidget(self.itemsList)

        addItemButton = QPushButton("Add Item")
        addItemButton.clicked.connect(self.addItem)
        itemsLayout.addWidget(addItemButton)

        removeItemButton = QPushButton("Remove Item")
        removeItemButton.clicked.connect(self.removeItem)
        itemsLayout.addWidget(removeItemButton)

        itemsGroupBox.setLayout(itemsLayout)
        layout.addWidget(itemsGroupBox)

        itemNeededLabel = QLabel("Item Needed:")
        self.itemNeededInput = QLineEdit()
        layout.addWidget(itemNeededLabel)
        layout.addWidget(self.itemNeededInput)

        self.skillCheckGroupBox = QGroupBox("Item Skill Check")
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
            "items": self.items,
            "item_needed": self.itemNeededInput.text(),
            "skill_check": self.skill_check_data
        }
        return inventory_data

    def setInventoryData(self, inventory_data):
        self.items = inventory_data.get("items", [])
        self.itemsList.clear()
        for item in self.items:
            item_text = f"{item['name']} - {item['description']}"
            self.itemsList.addItem(item_text)
        self.itemNeededInput.setText(inventory_data.get("item_needed", ""))
        self.skill_check_data = inventory_data.get("skill_check", None)
        self.skillCheckCheckBox.setChecked(bool(self.skill_check_data))
        self.configureSkillCheckButton.setEnabled(bool(self.skill_check_data))

    def addItem(self):
        item_dialog = ItemUsageDialog(self)
        if item_dialog.exec_() == QDialog.Accepted:
            item_data = item_dialog.getItemData()
            self.items.append(item_data)
            item_text = f"{item_data['name']} - {item_data['description']}"
            self.itemsList.addItem(item_text)

    def editItem(self, item):
        row = self.itemsList.row(item)
        item_data = self.items[row]
        item_dialog = ItemUsageDialog(self)
        item_dialog.setItemData(item_data)
        if item_dialog.exec_() == QDialog.Accepted:
            updated_item_data = item_dialog.getItemData()
            self.items[row] = updated_item_data
            item_text = f"{updated_item_data['name']} - {updated_item_data['description']}"
            self.itemsList.takeItem(row)
            self.itemsList.insertItem(row, item_text)

    def removeItem(self):
        current_row = self.itemsList.currentRow()
        if current_row >= 0:
            self.itemsList.takeItem(current_row)
            del self.items[current_row]

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