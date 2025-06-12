"""
Top Bar Component for STARK AI Desktop Application
Contains the logo and settings icon.
"""

from PySide6.QtWidgets import (QWidget, QHBoxLayout, QLabel, QPushButton,
                              QFrame, QSpacerItem, QSizePolicy)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QFont
import os

from utils.config_manager import config_manager


class TopBar(QFrame):
    """Top bar widget containing logo and settings"""

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.apply_styles()

    def init_ui(self):
        """Initialize the top bar UI"""
        # Set height from config
        topbar_height = config_manager.get_topbar_height()
        self.setFixedHeight(topbar_height)
        self.setFrameStyle(QFrame.NoFrame)

        # Create layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(40, 20, 40, 20)
        layout.setSpacing(10)

        # Logo section
        app_name = config_manager.get_app_name()
        self.logo_label = QLabel(app_name)
        self.logo_label.setObjectName("logoLabel")

        # Try to load logo image from config path
        icons_path = config_manager.get_icons_path()
        logo_path = os.path.join(icons_path, "logo.png")

        logo_pixmap = QPixmap(logo_path)
        if not logo_pixmap.isNull():
            icon_size = config_manager.get_icon_size()
            scaled_pixmap = logo_pixmap.scaled(
                icon_size + 8, icon_size + 8, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            logo_image = QLabel()
            logo_image.setPixmap(scaled_pixmap)

            # Create horizontal layout for logo
            logo_layout = QHBoxLayout()
            logo_layout.setSpacing(15)
            logo_layout.addWidget(logo_image)
            logo_layout.addWidget(self.logo_label)

            logo_widget = QWidget()
            logo_widget.setLayout(logo_layout)
            layout.addWidget(logo_widget)
        else:
            layout.addWidget(self.logo_label)

        # Spacer to push settings to the right
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout.addItem(spacer)

        # Settings button
        self.settings_button = QPushButton()
        self.settings_button.setObjectName("settingsButton")
        self.settings_button.setFixedSize(QSize(48, 48))
        self.settings_button.setToolTip("Settings")

        # Try to load settings icon from config path
        settings_path = os.path.join(icons_path, "settings.icon.png")
        settings_pixmap = QPixmap(settings_path)

        if not settings_pixmap.isNull():
            icon_size = config_manager.get_icon_size()
            scaled_settings = settings_pixmap.scaled(
                icon_size - 8, icon_size - 8, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.settings_button.setIcon(scaled_settings)
            self.settings_button.setIconSize(QSize(icon_size - 8, icon_size - 8))
        else:
            self.settings_button.setText("⚙")

        layout.addWidget(self.settings_button)

    def apply_styles(self):
        """Apply custom styles to the top bar"""
        font_size = config_manager.get_font_size()

        self.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                border: none;
            }}
            
            QLabel#logoLabel {{
                color: #ffffff;
                font-size: {font_size + 12}px;
                font-weight: bold;
                letter-spacing: 2px;
            }}
            
            QPushButton#settingsButton {{
                background-color: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 24px;
                color: #ffffff;
                font-size: {font_size + 6}px;
            }}
            
            QPushButton#settingsButton:hover {{
                background-color: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }}
            
            QPushButton#settingsButton:pressed {{
                background-color: rgba(255, 255, 255, 0.1);
            }}
        """)





