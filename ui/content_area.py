"""
Content Area Component for STARK AI Desktop Application
Contains the main interface with input field and action buttons.
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
                              QPushButton, QLabel, QFrame, QSpacerItem,
                              QSizePolicy)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QFont
import os

from utils.config_manager import config_manager


class ContentArea(QFrame):
    """Main content area with input field and action buttons"""

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.apply_styles()

    def init_ui(self):
        """Initialize the content area UI"""
        self.setFrameStyle(QFrame.NoFrame)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(60, 60, 60, 60)
        main_layout.setSpacing(0)

        # Top spacer to center content vertically
        top_spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        main_layout.addItem(top_spacer)

        # Input section
        input_section = self.create_input_section()
        main_layout.addWidget(input_section, 0, Qt.AlignCenter)

        # Spacing between input and actions
        main_layout.addSpacing(50)

        # Action buttons section
        actions_section = self.create_actions_section()
        main_layout.addWidget(actions_section, 0, Qt.AlignCenter)

        # Bottom spacer
        bottom_spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        main_layout.addItem(bottom_spacer)

    def create_input_section(self):
        """Create the input field section"""
        input_widget = QWidget()
        input_layout = QHBoxLayout(input_widget)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(0)

        # Container for the input field with icons
        input_container = QWidget()
        input_container.setObjectName("inputContainer")
        input_container_layout = QHBoxLayout(input_container)
        input_container_layout.setContentsMargins(25, 0, 25, 0)
        input_container_layout.setSpacing(15)

        # Microphone icon (left side)
        mic_button = QPushButton()
        mic_button.setObjectName("micButton")
        mic_button.setFixedSize(QSize(24, 24))
        mic_button.setToolTip("Voice input")
        mic_button.setText("🎤")  # Using emoji as fallback

        # Input field with placeholder from config
        self.input_field = QLineEdit()
        self.input_field.setObjectName("mainInput")
        placeholder_text = config_manager.get_placeholder_text()
        self.input_field.setPlaceholderText(placeholder_text)
        self.input_field.setFixedHeight(60)
        self.input_field.setMinimumWidth(600)
        self.input_field.setAttribute(Qt.WA_MacShowFocusRect, False)

        # Globe icon (right side)
        globe_button = QPushButton()
        globe_button.setObjectName("globeButton")
        globe_button.setFixedSize(QSize(24, 24))
        globe_button.setToolTip("Language")
        globe_button.setText("🌐")  # Using emoji as fallback

        # Send button
        self.send_button = QPushButton("send")
        self.send_button.setObjectName("sendButton")
        self.send_button.setFixedSize(QSize(80, 40))
        self.send_button.setToolTip("Send")

        # Try to load send icon from config path
        icons_path = config_manager.get_icons_path()
        send_path = os.path.join(icons_path, "send.button.png")
        send_pixmap = QPixmap(send_path)

        if not send_pixmap.isNull():
            scaled_send = send_pixmap.scaled(
                20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.send_button.setIcon(scaled_send)
            self.send_button.setIconSize(QSize(20, 20))
            self.send_button.setText("")  # Remove text if icon is loaded

        # Add widgets to container
        input_container_layout.addWidget(mic_button)
        input_container_layout.addWidget(self.input_field, 1)
        input_container_layout.addWidget(globe_button)
        input_container_layout.addWidget(self.send_button)

        input_layout.addWidget(input_container)

        return input_widget

    def create_actions_section(self):
        """Create the action buttons section"""
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(80)

        # Get icons path from config
        icons_path = config_manager.get_icons_path()

        # Translate button
        translate_icon_path = os.path.join(icons_path, "translation.icon.png")
        translate_button = self.create_action_button(
            translate_icon_path,
            "Translate",
            "translateButton"
        )

        # Task button
        task_icon_path = os.path.join(icons_path, "tasks.icon.png")
        task_button = self.create_action_button(
            task_icon_path,
            "Task",
            "taskButton"
        )

        actions_layout.addWidget(translate_button)
        actions_layout.addWidget(task_button)

        return actions_widget

    def create_action_button(self, icon_path, text, object_name):
        """Create an action button with icon and text"""
        button_widget = QWidget()
        button_layout = QVBoxLayout(button_widget)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(15)
        button_layout.setAlignment(Qt.AlignCenter)

        # Icon button
        icon_button = QPushButton()
        icon_button.setObjectName(object_name)
        icon_button.setFixedSize(QSize(64, 64))
        icon_button.setToolTip(text)

        # Try to load icon
        icon_pixmap = QPixmap(icon_path)
        if not icon_pixmap.isNull():
            icon_size = config_manager.get_icon_size()
            scaled_icon = icon_pixmap.scaled(
                icon_size, icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            icon_button.setIcon(scaled_icon)
            icon_button.setIconSize(QSize(icon_size, icon_size))
        else:
            # Use emoji fallbacks
            if "translation" in icon_path:
                icon_button.setText("📝")
            elif "tasks" in icon_path:
                icon_button.setText("⚙️")
            else:
                icon_button.setText(text[:1])

        # Text label
        text_label = QLabel(text)
        text_label.setObjectName("actionLabel")
        text_label.setAlignment(Qt.AlignCenter)

        button_layout.addWidget(icon_button)
        button_layout.addWidget(text_label)

        return button_widget

    def apply_styles(self):
        """Apply custom styles to the content area"""
        font_size = config_manager.get_font_size()
        theme = config_manager.get_theme()

        # Adjust colors based on theme
        if theme == 'dark':
            input_bg = "#2a3441"
            border_color = "rgba(255, 255, 255, 0.1)"
            text_color = "#ffffff"
            placeholder_color = "rgba(255, 255, 255, 0.5)"
        else:
            input_bg = "#f5f5f5"
            border_color = "rgba(0, 0, 0, 0.1)"
            text_color = "#000000"
            placeholder_color = "rgba(0, 0, 0, 0.5)"

        self.setStyleSheet(f"""
            QFrame {{
                background: transparent;
            }}
            
            QWidget#inputContainer {{
                background-color: {input_bg};
                border: 1px solid {border_color};
                border-radius: 30px;
                min-height: 60px;
            }}
            
            QLineEdit#mainInput {{
                background-color: transparent;
                border: none;
                color: {text_color};
                font-size: {font_size + 4}px;
                padding: 0;
            }}
            
            QLineEdit#mainInput::placeholder {{
                color: {placeholder_color};
            }}
            
            QLineEdit#mainInput:focus {{
                outline: none;
                border: none;
            }}
            
            QPushButton#micButton, QPushButton#globeButton {{
                background-color: transparent;
                border: none;
                color: rgba(255, 255, 255, 0.6);
                font-size: {font_size + 4}px;
            }}
            
            QPushButton#micButton:hover, QPushButton#globeButton:hover {{
                color: rgba(255, 255, 255, 0.8);
            }}
            
            QPushButton#sendButton {{
                background-color: #4A90E2;
                border: none;
                border-radius: 20px;
                color: #ffffff;
                font-weight: 600;
                font-size: {font_size + 2}px;
            }}
            
            QPushButton#sendButton:hover {{
                background-color: #5BA0F2;
            }}
            
            QPushButton#sendButton:pressed {{
                background-color: #3A80D2;
            }}
            
            QPushButton#translateButton, QPushButton#taskButton {{
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 32px;
                color: #ffffff;
                font-size: {font_size + 12}px;
            }}
            
            QPushButton#translateButton:hover, QPushButton#taskButton:hover {{
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }}
            
            QPushButton#translateButton:pressed, QPushButton#taskButton:pressed {{
                background-color: rgba(255, 255, 255, 0.08);
            }}
            
            QLabel#actionLabel {{
                color: rgba(255, 255, 255, 0.8);
                font-size: {font_size + 2}px;
                font-weight: 500;
            }}
        """)







