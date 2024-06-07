from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton, QWidget

class RevisitDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Revisit Settings")
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Revisit count input
        revisitCountLayout = QHBoxLayout()
        revisitCountLabel = QLabel("Revisit Count:")
        self.revisitCountInput = QLineEdit()
        revisitCountLayout.addWidget(revisitCountLabel)
        revisitCountLayout.addWidget(self.revisitCountInput)
        layout.addLayout(revisitCountLayout)

        # Revisit content input
        revisitContentLabel = QLabel("Revisit Content:")
        self.revisitContentInput = QTextEdit()
        layout.addWidget(revisitContentLabel)
        layout.addWidget(self.revisitContentInput)

        # OK button
        okButton = QPushButton("OK")
        okButton.clicked.connect(self.saveRevisitData)
        layout.addWidget(okButton)

        self.setLayout(layout)

    def getRevisitData(self):
        return {
            "revisit_count": int(self.revisitCountInput.text()) if self.revisitCountInput.text() else 0,
            "revisit_content": self.revisitContentInput.toPlainText()
        }

    def setRevisitData(self, data):
        self.revisitCountInput.setText(str(data.get("revisit_count", 0)))
        self.revisitContentInput.setText(data.get("revisit_content", ""))

    def saveRevisitData(self):
        revisit_data = self.getRevisitData()
        parent_widget = self.parent()
        if isinstance(parent_widget, QWidget):
            parent_widget.setRevisitData(revisit_data)
        self.close()