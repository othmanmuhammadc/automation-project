#!/usr/bin/env python3
"""
STARK AI Desktop Application
Main entry point for the smart assistant GUI application.
"""

import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontDatabase

from ui.main_window import MainWindow
from utils.config_manager import config_manager


def load_custom_fonts():
    """Load custom fonts from assets directory"""
    fonts_path = config_manager.get_fonts_path()
    font_path = os.path.join(fonts_path, "custom_font.ttf")

    if os.path.exists(font_path):
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id != -1:
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if font_families:
                return font_families[0]
    return None


def setup_application_properties(app):
    """Set up application properties from config"""
    app_name = config_manager.get_app_name()
    app.setApplicationName(app_name)
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName(app_name)

    # Enable high DPI scaling
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)


def setup_application_font(app):
    """Set up application font from config"""
    # Try to load custom fonts first
    custom_font_family = load_custom_fonts()

    if custom_font_family:
        font_size = config_manager.get_font_size()
        app.setFont(QFont(custom_font_family, font_size))
    else:
        # Use configured font family and size
        font_family = config_manager.get_font_family()
        font_size = config_manager.get_font_size()
        app.setFont(QFont(font_family, font_size))


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)

    # Set up application properties from config
    setup_application_properties(app)

    # Set up application font from config
    setup_application_font(app)

    # Create and show main window
    window = MainWindow()
    window.show()

    # Mark first time launch as complete if it was the first time
    if config_manager.is_first_time_launch():
        config_manager.set_first_time_launch(False)

    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()



