from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSpinBox
from PyQt5.QtGui import QFont

class SettingsWindow(QDialog):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.main_window = main_window
        self.initializeUserInterface()

    def initializeUserInterface(self):
        layout = QVBoxLayout()

        # Font size settings
        font_size_layout = QHBoxLayout()
        font_size_label = QLabel("Font Size:")
        self.font_size_spin_box = QSpinBox()
        self.font_size_spin_box.setRange(8, 24)
        self.font_size_spin_box.setValue(12)
        self.font_size_spin_box.valueChanged.connect(self.update_application_font)
        increase_font_size_button = QPushButton("+")
        increase_font_size_button.clicked.connect(self.increase_font_size)
        decrease_font_size_button = QPushButton("-")
        decrease_font_size_button.clicked.connect(self.decrease_font_size)
        font_size_layout.addWidget(font_size_label)
        font_size_layout.addWidget(self.font_size_spin_box)
        font_size_layout.addWidget(increase_font_size_button)
        font_size_layout.addWidget(decrease_font_size_button)
        layout.addLayout(font_size_layout)

        self.setLayout(layout)

    def update_application_font(self):
        font = self.main_window.font()
        font.setPointSize(self.font_size_spin_box.value())
        self.main_window.update_application_font(font)

    def increase_font_size(self):
        current_size = self.font_size_spin_box.value()
        new_size = current_size + 1
        self.font_size_spin_box.setValue(new_size)
        self.update_application_font()

    def decrease_font_size(self):
        current_size = self.font_size_spin_box.value()
        new_size = current_size - 1
        self.font_size_spin_box.setValue(new_size)
        self.update_application_font()