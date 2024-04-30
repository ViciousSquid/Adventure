from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QDialogButtonBox

class InventoryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Inventory Settings")
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

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        layout.addWidget(buttonBox)

        self.setLayout(layout)

    def getInventoryData(self):
        inventory_data = {
            "item": self.itemInput.text(),
            "item_needed": self.itemNeededInput.text()
        }
        return inventory_data

    def setInventoryData(self, inventory_data):
        self.itemInput.setText(inventory_data.get("item", ""))
        self.itemNeededInput.setText(inventory_data.get("item_needed", ""))