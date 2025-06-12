"""
Sidebar Component for STARK AI Desktop Application
Reserved for future navigation features.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QFrame
from PySide6.QtCore import Qt


class Sidebar(QFrame):
    """Sidebar widget for future navigation features"""

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.apply_styles()

    def init_ui(self):
        """Initialize the sidebar UI"""
        self.setFixedWidth(80)
        self.setFrameStyle(QFrame.NoFrame)

        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 20, 10, 20)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignTop)

        # Placeholder for future navigation items
        # This can be expanded later with navigation buttons

    def apply_styles(self):
        """Apply custom styles to the sidebar"""
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 42, 53, 0.8);
                border-right: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
