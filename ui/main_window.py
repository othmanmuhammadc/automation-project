"""
Main Window for STARK AI Desktop Application
Coordinates all UI components and manages the overall layout.
"""

import os
import logging
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QFrame, QLabel, QPushButton, QSpacerItem, QSizePolicy,
                              QMenuBar, QStatusBar, QSizeGrip)
from PySide6.QtCore import Qt, QSize, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal
from PySide6.QtGui import QPalette, QColor, QPixmap, QIcon, QAction, QKeySequence

from content_area import ContentArea
from config_manager import config_manager


class Sidebar(QFrame):
    """Enhanced sidebar component with navigation features"""

    # Signals
    navigation_requested = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.logger = self._setup_logger()
        self.init_ui()
        self.apply_styles()

    def _setup_logger(self):
        """Set up logger for the sidebar"""
        if config_manager.is_logging_enabled():
            return logging.getLogger(self.__class__.__name__)
        return None

    def init_ui(self):
        """Initialize the sidebar UI"""
        width = config_manager.get_sidebar_width()
        self.setFixedWidth(width)
        self.setFrameStyle(QFrame.NoFrame)
        self.setObjectName("sidebar")

        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 20, 10, 20)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignTop)

        # Navigation buttons
        nav_items = [
            ("home", "🏠", "Home"),
            ("history", "📝", "History"),
            ("settings", "⚙️", "Settings"),
            ("help", "❓", "Help")
        ]

        self.nav_buttons = {}

        for item_id, icon, tooltip in nav_items:
            button = QPushButton()
            button.setObjectName(f"navButton_{item_id}")
            button.setFixedSize(QSize(width - 20, width - 20))
            button.setToolTip(tooltip)
            button.clicked.connect(lambda checked, x=item_id: self.navigation_requested.emit(x))

            # Try to load icon from config path
            icons_path = config_manager.get_icons_path()
            icon_path = os.path.join(icons_path, f"{item_id}.icon.png")

            if os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                if not pixmap.isNull():
                    button.setIcon(QIcon(pixmap))
                    button.setIconSize(QSize(24, 24))
                else:
                    button.setText(icon)
            else:
                button.setText(icon)

            self.nav_buttons[item_id] = button
            layout.addWidget(button)

        # Spacer to push everything to top
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addItem(spacer)

    def set_active_navigation(self, item_id):
        """Set the active navigation item"""
        for nav_id, button in self.nav_buttons.items():
            if nav_id == item_id:
                button.setProperty("active", True)
            else:
                button.setProperty("active", False)

            # Reapply styles
            button.style().unpolish(button)
            button.style().polish(button)

    def apply_styles(self):
        """Apply custom styles to the sidebar"""
        theme = config_manager.get_theme()
        border_color = config_manager.get_border_color()

        if theme == 'dark':
            bg_color = "#1e2329"
            button_color = "rgba(255, 255, 255, 0.05)"
            button_hover = "rgba(255, 255, 255, 0.1)"
            button_active = config_manager.get_primary_color()
            text_color = config_manager.get_text_secondary_color()
        else:
            bg_color = "#f8f9fa"
            button_color = "rgba(0, 0, 0, 0.05)"
            button_hover = "rgba(0, 0, 0, 0.1)"
            button_active = config_manager.get_primary_color()
            text_color = "rgba(0, 0, 0, 0.7)"

        self.setStyleSheet(f"""
            QFrame#sidebar {{
                background-color: {bg_color};
                border-right: 1px solid {border_color};
            }}
            
            QPushButton[objectName^="navButton"] {{
                background-color: {button_color};
                border: 1px solid transparent;
                border-radius: 12px;
                color: {text_color};
                font-size: 18px;
                text-align: center;
            }}
            
            QPushButton[objectName^="navButton"]:hover {{
                background-color: {button_hover};
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
            
            QPushButton[objectName^="navButton"][active="true"] {{
                background-color: {button_active};
                color: #ffffff;
                border: 1px solid {button_active};
            }}
            
            QPushButton[objectName^="navButton"]:pressed {{
                background-color: rgba(255, 255, 255, 0.08);
            }}
        """)


class TopBar(QFrame):
    """Enhanced top bar component with app title and controls"""

    # Signals
    settings_requested = pyqtSignal()
    theme_toggle_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.logger = self._setup_logger()
        self.init_ui()
        self.apply_styles()

    def _setup_logger(self):
        """Set up logger for the top bar"""
        if config_manager.is_logging_enabled():
            return logging.getLogger(self.__class__.__name__)
        return None

    def init_ui(self):
        """Initialize the top bar UI"""
        self.setFrameStyle(QFrame.NoFrame)
        height = config_manager.get_topbar_height()
        self.setFixedHeight(height)
        self.setObjectName("topBar")

        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(30, 0, 30, 0)
        layout.setSpacing(20)

        # App title and logo section
        title_widget = QWidget()
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(15)

        # Logo
        logo_label = QLabel()
        logo_label.setFixedSize(QSize(40, 40))
        logo_label.setScaledContents(True)

        # Try to load logo
        icons_path = config_manager.get_icons_path()
        logo_path = os.path.join(icons_path, "app_icon.png")
        logo_pixmap = QPixmap(logo_path)

        if not logo_pixmap.isNull():
            logo_label.setPixmap(logo_pixmap)
        else:
            logo_label.setText("🤖")
            logo_label.setAlignment(Qt.AlignCenter)
            logo_label.setStyleSheet("font-size: 24px;")

        # App title with version
        app_name = config_manager.get_app_name()
        app_version = config_manager.get_app_version()
        title_label = QLabel(f"{app_name}")
        title_label.setObjectName("appTitle")

        # Version label
        version_label = QLabel(f"v{app_version}")
        version_label.setObjectName("versionLabel")

        title_layout.addWidget(logo_label)
        title_layout.addWidget(title_label)
        title_layout.addWidget(version_label)
        title_layout.addStretch()

        # Control buttons section
        controls_widget = QWidget()
        controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(10)

        # Theme toggle button
        self.theme_button = QPushButton()
        self.theme_button.setObjectName("themeButton")
        self.theme_button.setFixedSize(QSize(36, 36))
        self.theme_button.setToolTip("Toggle Theme")
        self.theme_button.clicked.connect(self.theme_toggle_requested.emit)

        # Set theme icon based on current theme
        current_theme = config_manager.get_theme()
        self.theme_button.setText("🌙" if current_theme == "dark" else "☀️")

        # Settings button
        self.settings_button = QPushButton()
        self.settings_button.setObjectName("settingsButton")
        self.settings_button.setFixedSize(QSize(36, 36))
        self.settings_button.setToolTip("Settings")
        self.settings_button.clicked.connect(self.settings_requested.emit)

        # Try to load settings icon
        settings_icon_path = os.path.join(icons_path, "settings.icon.png")
        settings_pixmap = QPixmap(settings_icon_path)

        if not settings_pixmap.isNull():
            self.settings_button.setIcon(QIcon(settings_pixmap))
            self.settings_button.setIconSize(QSize(20, 20))
        else:
            self.settings_button.setText("⚙️")

        controls_layout.addWidget(self.theme_button)
        controls_layout.addWidget(self.settings_button)

        # Add widgets to main layout
        layout.addWidget(title_widget, 1)
        layout.addWidget(controls_widget)

    def update_theme_button(self, theme):
        """Update theme button icon based on current theme"""
        self.theme_button.setText("🌙" if theme == "dark" else "☀️")

    def apply_styles(self):
        """Apply styles to the top bar"""
        theme = config_manager.get_theme()
        font_size = config_manager.get_font_size()
        border_color = config_manager.get_border_color()

        if theme == 'dark':
            bg_color = "#1e2329"
            text_color = config_manager.get_text_primary_color()
            text_secondary = config_manager.get_text_secondary_color()
            button_bg = "rgba(255, 255, 255, 0.05)"
            button_hover = "rgba(255, 255, 255, 0.1)"
        else:
            bg_color = "#f8f9fa"
            text_color = "#333333"
            text_secondary = "rgba(0, 0, 0, 0.6)"
            button_bg = "rgba(0, 0, 0, 0.05)"
            button_hover = "rgba(0, 0, 0, 0.1)"

        self.setStyleSheet(f"""
            QFrame#topBar {{
                background-color: {bg_color};
                border-bottom: 1px solid {border_color};
            }}
            
            QLabel#appTitle {{
                color: {text_color};
                font-size: {font_size + 8}px;
                font-weight: 700;
                letter-spacing: 1px;
            }}
            
            QLabel#versionLabel {{
                color: {text_secondary};
                font-size: {font_size}px;
                font-weight: 400;
                padding: 2px 8px;
                background-color: rgba(128, 128, 128, 0.2);
                border-radius: 10px;
            }}
            
            QPushButton#settingsButton, QPushButton#themeButton {{
                background-color: {button_bg};
                border: 1px solid {border_color};
                border-radius: 18px;
                color: {text_color};
                font-size: {font_size + 4}px;
            }}
            
            QPushButton#settingsButton:hover, QPushButton#themeButton:hover {{
                background-color: {button_hover};
                border: 1px solid rgba(255, 255, 255, 0.2);
            }}
            
            QPushButton#settingsButton:pressed, QPushButton#themeButton:pressed {{
                background-color: rgba(255, 255, 255, 0.05);
            }}
        """)


class MainWindow(QMainWindow):
    """Enhanced main application window with improved features"""

    def __init__(self):
        super().__init__()
        self.logger = self._setup_logger()
        self.animations = []
        self.current_page = "home"
        self.init_ui()
        self.apply_styles()
        self.setup_animations()
        self.setup_connections()

    def _setup_logger(self):
        """Set up logger for the main window"""
        if config_manager.is_logging_enabled():
            return logging.getLogger(self.__class__.__name__)
        return None

    def init_ui(self):
        """Initialize the user interface"""
        # Set window title from config
        app_name = config_manager.get_app_name()
        app_version = config_manager.get_app_version()
        self.setWindowTitle(f"{app_name} v{app_version}")

        # Set window size from config
        width, height = config_manager.get_window_size()
        min_width, min_height = config_manager.get_min_window_size()

        self.setMinimumSize(QSize(min_width, min_height))
        self.resize(width, height)

        # Set resizable property from config
        if not config_manager.is_resizable():
            self.setFixedSize(width, height)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create sidebar
        self.sidebar = Sidebar()
        main_layout.addWidget(self.sidebar)

        # Create right side layout for top bar and content
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Create and add top bar
        self.top_bar = TopBar()
        right_layout.addWidget(self.top_bar)

        # Create and add content area
        self.content_area = ContentArea()
        right_layout.addWidget(self.content_area, 1)  # Give content area most space

        # Create right widget and add to main layout
        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        main_layout.addWidget(right_widget, 1)

        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.setObjectName("statusBar")

        # Add ready message
        username = config_manager.get_username()
        self.status_bar.showMessage(f"Ready - Welcome {username}!")

        # Center the window on screen
        self.center_on_screen()

        # Set window icon
        self.set_window_icon()

        # Set initial navigation
        self.sidebar.set_active_navigation("home")

        if self.logger:
            self.logger.info("Main window initialized successfully")

    def setup_connections(self):
        """Set up signal connections between components"""
        try:
            # Connect sidebar navigation
            self.sidebar.navigation_requested.connect(self.handle_navigation)

            # Connect top bar signals
            self.top_bar.settings_requested.connect(self.open_settings)
            self.top_bar.theme_toggle_requested.connect(self.toggle_theme)

            # Connect content area signals
            self.content_area.message_sent.connect(self.handle_message)
            self.content_area.voice_triggered.connect(self.handle_voice_input)
            self.content_area.translation_requested.connect(self.handle_translation)
            self.content_area.task_requested.connect(self.handle_task_automation)

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error setting up connections: {e}")

    def handle_navigation(self, page_id):
        """Handle navigation requests"""
        if self.logger:
            self.logger.info(f"Navigation requested: {page_id}")

        self.current_page = page_id
        self.sidebar.set_active_navigation(page_id)

        # Update status bar
        page_names = {
            "home": "Home",
            "history": "Conversation History",
            "settings": "Settings",
            "help": "Help & Support"
        }

        page_name = page_names.get(page_id, page_id.title())
        self.status_bar.showMessage(f"Current page: {page_name}")

    def handle_message(self, message):
        """Handle sent messages"""
        if self.logger:
            self.logger.info(f"Message sent: {message[:50]}...")

        self.status_bar.showMessage("Processing message...", 3000)

        # Here you would integrate with your AI backend
        # For now, just show confirmation
        QTimer.singleShot(1500, lambda: self.status_bar.showMessage("Message processed!", 2000))

    def handle_voice_input(self):
        """Handle voice input requests"""
        if self.logger:
            self.logger.info("Voice input requested")

        self.status_bar.showMessage("Listening...", 2000)

    def handle_translation(self):
        """Handle translation requests"""
        if self.logger:
            self.logger.info("Translation requested")

        self.status_bar.showMessage("Opening translation assistant...", 2000)

    def handle_task_automation(self):
        """Handle task automation requests"""
        if self.logger:
            self.logger.info("Task automation requested")

        self.status_bar.showMessage("Opening task automation...", 2000)

    def toggle_theme(self):
        """Toggle between light and dark themes"""
        current_theme = config_manager.get_theme()
        new_theme = "light" if current_theme == "dark" else "dark"

        config_manager.set('UI', 'theme', new_theme)
        config_manager.save_config()

        if self.logger:
            self.logger.info(f"Theme changed from {current_theme} to {new_theme}")

        # Update UI with new theme
        self.apply_styles()
        self.sidebar.apply_styles()
        self.top_bar.apply_styles()
        self.top_bar.update_theme_button(new_theme)
        self.content_area.apply_styles()

        self.status_bar.showMessage(f"Theme changed to {new_theme} mode", 2000)

    def open_settings(self):
        """Open settings dialog"""
        if self.logger:
            self.logger.info("Settings requested")

        self.status_bar.showMessage("Settings dialog (not implemented yet)", 3000)

    def set_window_icon(self):
        """Set the window icon"""
        try:
            icons_path = config_manager.get_icons_path()
            icon_path = os.path.join(icons_path, "app_icon.png")

            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
            else:
                # Create a simple default icon
                pixmap = QPixmap(32, 32)
                pixmap.fill(QColor(config_manager.get_primary_color()))
                self.setWindowIcon(QIcon(pixmap))

        except Exception as e:
            if self.logger:
                self.logger.warning(f"Could not set window icon: {e}")

    def center_on_screen(self):
        """Center the window on the screen"""
        try:
            screen = self.screen().availableGeometry()
            window_geometry = self.frameGeometry()
            window_geometry.moveCenter(screen.center())
            self.move(window_geometry.topLeft())
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Could not center window: {e}")

    def setup_animations(self):
        """Set up window animations if enabled"""
        if config_manager.get_bool('UI', 'enable_transitions', True):
            # Fade-in animation for window
            self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
            self.fade_animation.setDuration(config_manager.get_animation_duration())
            self.fade_animation.setStartValue(0.0)
            self.fade_animation.setEndValue(1.0)
            self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)

            self.animations.append(self.fade_animation)

    def showEvent(self, event):
        """Handle window show event with animation"""
        super().showEvent(event)

        if hasattr(self, 'fade_animation'):
            self.fade_animation.start()

    def apply_styles(self):
        """Apply custom styles to the main window"""
        theme = config_manager.get_theme()
        background_color = config_manager.get_background_color()
        text_color = config_manager.get_text_primary_color()
        border_radius = config_manager.get_border_radius()
        border_color = config_manager.get_border_color()

        # Apply global window styling
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {background_color};
                color: {text_color};
                border-radius: {border_radius}px;
            }}
            
            QWidget {{
                font-family: "{config_manager.get_font_family()}";
            }}
            
            QStatusBar#statusBar {{
                background-color: rgba(0, 0, 0, 0.1);
                border-top: 1px solid {border_color};
                color: {text_color};
                font-size: {config_manager.get_font_size()}px;
                padding: 4px;
            }}
            
            QToolTip {{
                background-color: rgba(0, 0, 0, 0.8);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                padding: 8px;
                font-size: {config_manager.get_font_size()}px;
            }}
        """)

        if self.logger:
            self.logger.debug(f"Applied {theme} theme styles")

    def closeEvent(self, event):
        """Handle window close event"""
        if self.logger:
            self.logger.info("Application closing...")

        # Save current page
        config_manager.set('User', 'last_opened_page', self.current_page)

        # Save any pending configuration changes
        config_manager.save_config()

        # Clean up animations
        for animation in self.animations:
            if animation.state() == QPropertyAnimation.Running:
                animation.stop()

        event.accept()

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        try:
            # Handle global shortcuts
            if event.matches(QKeySequence("Ctrl+Q")):
                self.close()
            elif event.matches(QKeySequence("Ctrl+N")):
                self.new_conversation()
            elif event.matches(QKeySequence("Ctrl+,")):
                self.open_settings()
            elif event.matches(QKeySequence("Ctrl+H")):
                self.handle_navigation("home")
            elif event.matches(QKeySequence("Ctrl+Shift+H")):
                self.handle_navigation("history")
            else:
                super().keyPressEvent(event)

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error handling keyboard shortcut: {e}")
            super().keyPressEvent(event)

    def new_conversation(self):
        """Start a new conversation"""
        if hasattr(self.content_area, 'clear_input'):
            self.content_area.clear_input()

        self.status_bar.showMessage("New conversation started", 2000)

        if self.logger:
            self.logger.info("New conversation started")


