from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QCheckBox, QDialog, QLineEdit, QTextEdit, QDialogButtonBox, QHBoxLayout, QPushButton
from PyQt5.QtCore import pyqtSignal, Qt, QSize

class InventoryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Inventory Settings")
        self.initUserInterface()

    def initUserInterface(self):
        layout = QVBoxLayout()

        # Has Inventory checkbox
        self.inventoryCheckbox = QCheckBox("Room requires an inventory item")
        self.inventoryCheckbox.setChecked(False)  # Set the checkbox to unchecked by default
        self.inventoryCheckbox.stateChanged.connect(self.toggleInventoryFields)
        layout.addWidget(self.inventoryCheckbox)

        # Item requirement input
        itemRequirementLabel = QLabel("Item Requirement:")
        self.itemRequirementInput = QLineEdit()
        self.itemRequirementInput.setPlaceholderText("Item name")
        layout.addWidget(itemRequirementLabel)
        layout.addWidget(self.itemRequirementInput)

        # Use Item input
        useItemLabel = QLabel("Use Item:")
        self.use_item_layout = QVBoxLayout()
        layout.addWidget(useItemLabel)
        layout.addLayout(self.use_item_layout)

        # Add 'Use Item' button
        addUseItemButton = QPushButton("Add Use Item")
        addUseItemButton.clicked.connect(self.addUseItemEntry)
        layout.addWidget(addUseItemButton)

        # Inventory items input
        inventoryItemsLabel = QLabel("Inventory Items:")
        self.inventoryItemsInput = QTextEdit()
        layout.addWidget(inventoryItemsLabel)
        layout.addWidget(self.inventoryItemsInput)

        # Dialog buttons
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        layout.addWidget(buttonBox)

        self.setLayout(layout)
        self.toggleInventoryFields(self.inventoryCheckbox.checkState())

    def sizeHint(self):
        return QSize(400, 500)  # Set the desired width and height

    def addUseItemEntry(self):
        useItemEntryLayout = QHBoxLayout()
        useItemNameInput = QLineEdit()
        useItemNameInput.setPlaceholderText("Item name")
        useItemDescriptionInput = QTextEdit()
        useItemDescriptionInput.setPlaceholderText("Description")
        useItemEntryLayout.addWidget(useItemNameInput)
        useItemEntryLayout.addWidget(useItemDescriptionInput)
        self.use_item_layout.addLayout(useItemEntryLayout)

    def setInventoryData(self, has_inventory, item_requirement, use_item_data, inventory_items):
        self.inventoryCheckbox.setChecked(has_inventory)
        self.itemRequirementInput.setText(item_requirement)
        self.clearUseItemEntries()
        for item_name, item_description in use_item_data.items():
            self.addUseItemEntry()
            useItemEntryLayout = self.use_item_layout.itemAt(self.use_item_layout.count() - 1)
            useItemEntryLayout.itemAt(0).widget().setText(item_name)
            useItemEntryLayout.itemAt(1).widget().setPlainText(item_description)
        self.inventoryItemsInput.setText(", ".join(inventory_items))

    def clearUseItemEntries(self):
        while self.use_item_layout.count() > 0:
            item = self.use_item_layout.takeAt(0)
            if item.layout():
                item.layout().deleteLater()

    def getInventoryData(self):
        has_inventory = self.inventoryCheckbox.isChecked()
        item_requirement = self.itemRequirementInput.text().strip()
        use_item_data = {}
        for i in range(self.use_item_layout.count()):
            useItemEntryLayout = self.use_item_layout.itemAt(i).layout()
            item_name = useItemEntryLayout.itemAt(0).widget().text().strip()
            item_description = useItemEntryLayout.itemAt(1).widget().toPlainText().strip()
            if item_name and item_description:
                use_item_data[item_name] = item_description
        inventory_items = [item.strip() for item in self.inventoryItemsInput.toPlainText().split(",") if item.strip()]
        return has_inventory, item_requirement, use_item_data, inventory_items

    def toggleInventoryFields(self, state):
        visible = state == Qt.Checked
        self.itemRequirementInput.setVisible(visible)
        useItemLabel = self.use_item_layout.parent().layout().itemAt(1).widget()
        useItemLabel.setVisible(visible)
        addUseItemButton = self.use_item_layout.parent().layout().itemAt(3).widget()
        addUseItemButton.setVisible(visible)
        for i in range(self.use_item_layout.count()):
            useItemEntryLayout = self.use_item_layout.itemAt(i).layout()
            useItemEntryLayout.itemAt(0).widget().setVisible(visible)
            useItemEntryLayout.itemAt(1).widget().setVisible(visible)

class InventoryWidget(QWidget):
    inventoryChanged = pyqtSignal(bool, str, dict, list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUserInterface()
        self.item_requirement = ""
        self.use_item_data = {}
        self.inventory_items = []

    def initUserInterface(self):
        layout = QVBoxLayout()

        self.inventoryCheckbox = QCheckBox("Has Inventory")
        self.inventoryCheckbox.stateChanged.connect(self.onInventoryCheckboxStateChanged)
        layout.addWidget(self.inventoryCheckbox)

        self.setLayout(layout)

    def onInventoryCheckboxStateChanged(self, state):
        self.emitInventoryChanged()

    def showInventoryDialog(self, event):
        dialog = InventoryDialog(self)
        dialog.setInventoryData(self.inventoryCheckbox.isChecked(), self.item_requirement, self.use_item_data, self.inventory_items)
        if dialog.exec_() == InventoryDialog.Accepted:
            has_inventory, item_requirement, use_item_data, inventory_items = dialog.getInventoryData()
            self.inventoryCheckbox.setChecked(has_inventory)
            self.item_requirement = item_requirement
            self.use_item_data = use_item_data
            self.inventory_items = inventory_items
            self.emitInventoryChanged()

    def emitInventoryChanged(self):
        self.inventoryChanged.emit(
            self.inventoryCheckbox.isChecked(),
            self.item_requirement,
            self.use_item_data,
            self.inventory_items
        )

    def setInventoryData(self, has_inventory, item_requirement, use_item_data, inventory_items):
        self.inventoryCheckbox.setChecked(has_inventory)
        self.item_requirement = item_requirement
        self.use_item_data = use_item_data
        self.inventory_items = inventory_items

    def getInventoryData(self):
        return (
            self.inventoryCheckbox.isChecked(),
            self.item_requirement,
            self.use_item_data,
            self.inventory_items
        )