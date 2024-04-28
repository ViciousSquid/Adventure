from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QCheckBox, QHBoxLayout, QPushButton, QApplication
from PyQt5.QtGui import QFont

class SettingsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.main_window = parent
        self.default_font_size = QApplication.font().pointSize()  # Store the default font size
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Font size buttons
        font_size_layout = QHBoxLayout()
        self.font_size_label = QLabel("Font Size:")
        font_size_layout.addWidget(self.font_size_label)

        decrease_font_button = QPushButton("-")
        decrease_font_button.setMaximumWidth(30)  # Set maximum width for the decrease button
        decrease_font_button.clicked.connect(self.decreaseFontSize)
        font_size_layout.addWidget(decrease_font_button)

        self.font_size_value_label = QLabel(str(self.default_font_size))  # Set the default font size label
        font_size_layout.addWidget(self.font_size_value_label)

        increase_font_button = QPushButton("+")
        increase_font_button.setMaximumWidth(30)  # Set maximum width for the increase button
        increase_font_button.clicked.connect(self.increaseFontSize)
        font_size_layout.addWidget(increase_font_button)

        reset_font_button = QPushButton("Reset")
        reset_font_button.setMaximumWidth(60)  # Set maximum width for the reset button
        font_size_layout.addWidget(reset_font_button)
        reset_font_button.clicked.connect(self.resetFontSize)

        layout.addLayout(font_size_layout)
        self.setLayout(layout)

    def increaseFontSize(self):
        font = QApplication.font()
        font.setPointSize(font.pointSize() + 1)
        self.main_window.updateApplicationFont(font)
        self.font_size_value_label.setText(str(font.pointSize()))

    def decreaseFontSize(self):
        font = QApplication.font()
        font.setPointSize(max(font.pointSize() - 1, 9))  # Minimum font size of 9
        self.main_window.updateApplicationFont(font)
        self.font_size_value_label.setText(str(font.pointSize()))

    def resetFontSize(self):
        default_font = QApplication.font()
        default_font.setPointSize(self.default_font_size)  # Set the font size to the stored default
        self.main_window.updateApplicationFont(default_font)
        self.font_size_value_label.setText(str(self.default_font_size))