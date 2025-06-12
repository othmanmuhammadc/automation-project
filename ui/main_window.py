"""
Main Window for STARK AI Desktop Application
Coordinates all UI components and manages the overall layout.
"""

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                              QHBoxLayout, QFrame)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPalette, QColor

from .topbar import TopBar
from .content_area import ContentArea
from utils.config_manager import config_manager


class MainWindow(QMainWindow):
    """Main application window containing all UI components"""

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.apply_styles()

    def init_ui(self):
        """Initialize the user interface"""
        # Set window title from config
        app_name = config_manager.get_app_name()
        self.setWindowTitle(app_name)

        # Set window size from config
        width, height = config_manager.get_window_size()
        self.setMinimumSize(QSize(width, height))
        self.resize(width, height)

        # Set resizable property from config
        if not config_manager.is_resizable():
            self.setFixedSize(width, height)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create and add components
        self.top_bar = TopBar()
        self.content_area = ContentArea()

        main_layout.addWidget(self.top_bar)
        main_layout.addWidget(self.content_area, 1)  # Give content area most space

        # Center the window on screen
        self.center_on_screen()

    def center_on_screen(self):
        """Center the window on the screen"""
        screen = self.screen().availableGeometry()
        window_geometry = self.frameGeometry()
        window_geometry.moveCenter(screen.center())
        self.move(window_geometry.topLeft())

    def apply_styles(self):
        """Apply custom styles to the main window"""
        theme = config_manager.get_theme()

        if theme == 'dark':
            background_color = "#1a1f2e"
        else:
            background_color = "#ffffff"

        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {background_color};
                color: #ffffff;
            }}
        """)





