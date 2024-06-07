from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QPalette, QColor

CURRENT_THEME = "light"

def set_theme():
    app = QApplication.instance()
    if app is not None:
        if CURRENT_THEME == "dark":
            set_dark_theme(app)
        else:
            set_light_theme(app)

        # Apply the theme to all the widgets recursively
        for widget in app.topLevelWidgets():
            apply_theme_recursively(widget)

def apply_theme_recursively(widget):
    apply_theme(widget)
    for child in widget.children():
        if isinstance(child, QWidget):
            apply_theme_recursively(child)

def apply_theme(widget):
    if CURRENT_THEME == "dark":
        set_dark_theme_for_widget(widget)
    else:
        set_light_theme_for_widget(widget)

def set_light_theme_for_widget(widget):
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(255, 255, 255))
    palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
    palette.setColor(QPalette.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.Text, QColor(0, 0, 0))
    widget.setPalette(palette)

def set_dark_theme_for_widget(widget):
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(43, 43, 43))
    palette.setColor(QPalette.WindowText, QColor(212, 212, 212))
    palette.setColor(QPalette.Base, QColor(77, 77, 77))
    palette.setColor(QPalette.Text, QColor(212, 212, 212))
    widget.setPalette(palette)

def set_light_theme(app):
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(255, 255, 255))
    palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
    palette.setColor(QPalette.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.Text, QColor(0, 0, 0))
    app.setPalette(palette)

def set_dark_theme(app):
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(43, 43, 43))
    palette.setColor(QPalette.WindowText, QColor(212, 212, 212))
    palette.setColor(QPalette.Base, QColor(77, 77, 77))
    palette.setColor(QPalette.Text, QColor(212, 212, 212))
    app.setPalette(palette)