from PyQt5.QtWidgets import QDialog, QVBoxLayout, QGridLayout, QLabel, QTextEdit, QSpinBox, QInputDialog, QDialogButtonBox, QCheckBox, QListWidget, QListWidgetItem, QPushButton
from PyQt5.QtCore import Qt

class RevisitDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Revisit Settings")
        self.initUserInterface()

    def initUserInterface(self):
        layout = QVBoxLayout()

        # Revisit List
        self.revisitList = QListWidget()
        self.revisitList.itemDoubleClicked.connect(self.editRevisitData)
        layout.addWidget(self.revisitList)

        # Revisit Buttons
        revisitButtonsLayout = QGridLayout()

        addRevisitButton = QPushButton("Add Revisit")
        addRevisitButton.clicked.connect(self.addRevisitData)
        revisitButtonsLayout.addWidget(addRevisitButton, 0, 0)

        removeRevisitButton = QPushButton("Remove Revisit")
        removeRevisitButton.clicked.connect(self.removeRevisitData)
        revisitButtonsLayout.addWidget(removeRevisitButton, 0, 1)

        layout.addLayout(revisitButtonsLayout)

        # Show All Revisits Checkbox
        self.showAllRevisitsCheckbox = QCheckBox("Show All")
        self.showAllRevisitsCheckbox.setChecked(True)
        layout.addWidget(self.showAllRevisitsCheckbox)

        # Create a QLabel widget
        self.label = QLabel("True = Always show all revisit data \nFalse = Show only the most recent revisit data\n")

        # Add the QLabel widget to the layout
        layout.addWidget(self.label)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        layout.addWidget(buttonBox)

        self.setLayout(layout)

    def addRevisitData(self):
        revisit_count, ok = QInputDialog.getInt(self, "Revisit Count", "Revisit count:")
        if ok:
            revisit_content, ok = QInputDialog.getMultiLineText(self, "Revisit Content", "Revisit content:")
            if ok:
                revisit_data = {
                    "revisit_count": revisit_count,
                    "revisit_content": revisit_content
                }
                item = QListWidgetItem(f"Revisit Count: {revisit_count}")
                item.setData(Qt.UserRole, revisit_data)
                self.revisitList.addItem(item)

    def editRevisitData(self, item):
        revisit_data = item.data(Qt.UserRole)
        revisit_count = revisit_data["revisit_count"]
        revisit_content = revisit_data["revisit_content"]

        revisit_count, ok = QInputDialog.getInt(self, "Revisit Count", "Enter the revisit count:", value=revisit_count)
        if ok:
            revisit_content, ok = QInputDialog.getMultiLineText(self, "Revisit Content", "Enter the revisit content:", text=revisit_content)
            if ok:
                revisit_data = {
                    "revisit_count": revisit_count,
                    "revisit_content": revisit_content
                }
                item.setData(Qt.UserRole, revisit_data)
                item.setText(f"Revisit Count: {revisit_count}")

    def removeRevisitData(self):
        current_row = self.revisitList.currentRow()
        if current_row >= 0:
            self.revisitList.takeItem(current_row)

    def getRevisitDataList(self):
        revisit_data_list = []
        for i in range(self.revisitList.count()):
            item = self.revisitList.item(i)
            revisit_data = item.data(Qt.UserRole)
            revisit_data["show_all_revisits"] = self.showAllRevisitsCheckbox.isChecked()
            revisit_data_list.append(revisit_data)
        return revisit_data_list

    def setRevisitDataList(self, revisit_data_list):
        self.revisitList.clear()
        for revisit_data in revisit_data_list:
            revisit_count = revisit_data["revisit_count"]
            revisit_content = revisit_data["revisit_content"]
            item = QListWidgetItem(f"Revisit Count: {revisit_count}")
            item.setData(Qt.UserRole, revisit_data)
            self.revisitList.addItem(item)
        self.showAllRevisitsCheckbox.setChecked(revisit_data_list[0].get("show_all_revisits", True) if revisit_data_list else True)