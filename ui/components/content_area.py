"""
Content Area Component for STARK AI Desktop Application
Contains the main interface with input field and action buttons.
"""

import os
import logging
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
                              QPushButton, QLabel, QFrame, QSpacerItem,
                              QSizePolicy, QGraphicsOpacityEffect, QApplication,
                              QTextEdit, QScrollArea)
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QTimer, pyqtSignal
from PySide6.QtGui import QPixmap, QFont, QIcon, QKeySequence, QShortcut, QTextCursor
import json
from datetime import datetime

from config_manager import config_manager


class ConversationWidget(QScrollArea):
    """Widget to display conversation history"""

    def __init__(self):
        super().__init__()
        self.messages = []
        self.init_ui()
        self.apply_styles()

    def init_ui(self):
        """Initialize the conversation display"""
        self.setObjectName("conversationArea")
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Container widget
        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)
        self.layout.setAlignment(Qt.AlignTop)

        self.setWidget(self.container)

    def add_message(self, text, sender="user", timestamp=None):
        """Add a message to the conversation"""
        if timestamp is None:
            timestamp = datetime.now()

        message_widget = QFrame()
        message_widget.setObjectName(f"message_{sender}")
        message_layout = QVBoxLayout(message_widget)
        message_layout.setContentsMargins(15, 10, 15, 10)
        message_layout.setSpacing(5)

        # Sender label
        sender_label = QLabel(f"{sender.title()}:")
        sender_label.setObjectName(f"senderLabel_{sender}")

        # Message text
        message_label = QLabel(text)
        message_label.setObjectName(f"messageText_{sender}")
        message_label.setWordWrap(True)

        # Timestamp
        time_label = QLabel(timestamp.strftime("%H:%M"))
        time_label.setObjectName("timestampLabel")
        time_label.setAlignment(Qt.AlignRight)

        message_layout.addWidget(sender_label)
        message_layout.addWidget(message_label)
        message_layout.addWidget(time_label)

        # Add to layout with alignment
        if sender == "user":
            container = QHBoxLayout()
            container.addStretch()
            container.addWidget(message_widget)
            container.setContentsMargins(40, 0, 0, 0)
        else:
            container = QHBoxLayout()
            container.addWidget(message_widget)
            container.addStretch()
            container.setContentsMargins(0, 0, 40, 0)

        container_widget = QWidget()
        container_widget.setLayout(container)

        self.layout.addWidget(container_widget)
        self.messages.append({"text": text, "sender": sender, "timestamp": timestamp})

        # Scroll to bottom
        QTimer.singleShot(100, self.scroll_to_bottom)

    def scroll_to_bottom(self):
        """Scroll to the bottom of the conversation"""
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear_conversation(self):
        """Clear all messages"""
        for i in reversed(range(self.layout.count())):
            child = self.layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        self.messages.clear()

    def apply_styles(self):
        """Apply styles to the conversation area"""
        theme = config_manager.get_theme()
        font_size = config_manager.get_font_size()
        border_radius = config_manager.get_border_radius()

        if theme == 'dark':
            bg_color = "#1a1f2e"
            user_bg = config_manager.get_primary_color()
            assistant_bg = "#2a3441"
            text_color = "#ffffff"
            timestamp_color = "rgba(255, 255, 255, 0.5)"
        else:
            bg_color = "#ffffff"
            user_bg = config_manager.get_primary_color()
            assistant_bg = "#f0f0f0"
            text_color = "#333333"
            timestamp_color = "rgba(0, 0, 0, 0.5)"

        self.setStyleSheet(f"""
            QScrollArea#conversationArea {{
                background-color: {bg_color};
                border: none;
            }}
            
            QFrame#message_user {{
                background-color: {user_bg};
                border-radius: {border_radius}px;
                margin: 2px;
            }}
            
            QFrame#message_assistant {{
                background-color: {assistant_bg};
                border-radius: {border_radius}px;
                margin: 2px;
            }}
            
            QLabel#senderLabel_user, QLabel#senderLabel_assistant {{
                font-weight: 600;
                font-size: {font_size}px;
                color: {text_color};
            }}
            
            QLabel#messageText_user, QLabel#messageText_assistant {{
                font-size: {font_size + 2}px;
                color: {text_color};
                line-height: 1.4;
            }}
            
            QLabel#timestampLabel {{
                font-size: {font_size - 2}px;
                color: {timestamp_color};
            }}
        """)


class ContentArea(QFrame):
    """Enhanced main content area with conversation display and improved input"""

    # Signals
    message_sent = pyqtSignal(str)
    voice_triggered = pyqtSignal()
    translation_requested = pyqtSignal()
    task_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.logger = self._setup_logger()
        self.animations = []
        self.typing_timer = QTimer()
        self.typing_timer.setSingleShot(True)
        self.typing_timer.timeout.connect(self.on_typing_stopped)
        self.init_ui()
        self.apply_styles()
        self.setup_shortcuts()
        self.setup_animations()

    def _setup_logger(self):
        """Set up logger for the content area"""
        if config_manager.is_logging_enabled():
            return logging.getLogger(self.__class__.__name__)
        return None

    def init_ui(self):
        """Initialize the content area UI"""
        self.setFrameStyle(QFrame.NoFrame)
        self.setObjectName("contentArea")

        # Main layout
        main_layout = QVBoxLayout(self)
        padding = config_manager.get_padding()
        main_layout.setContentsMargins(padding, padding//2, padding, padding//2)
        main_layout.setSpacing(0)

        # Show welcome section only for first-time users or when no conversation exists
        if config_manager.is_first_time_launch() or not self.has_conversation_history():
            welcome_section = self.create_welcome_section()
            main_layout.addWidget(welcome_section, 0, Qt.AlignCenter)

            # Add conversation area but keep it hidden initially
            self.conversation_area = ConversationWidget()
            self.conversation_area.hide()
            main_layout.addWidget(self.conversation_area, 1)
        else:
            # Show conversation area directly
            self.conversation_area = ConversationWidget()
            main_layout.addWidget(self.conversation_area, 1)
            self.load_conversation_history()

        # Input section (always at bottom)
        input_section = self.create_input_section()
        main_layout.addWidget(input_section, 0, Qt.AlignCenter)

        # Spacing between input and actions
        spacing = config_manager.get_spacing()
        main_layout.addSpacing(spacing)

        # Action buttons section (only if features are enabled)
        if self.should_show_actions():
            actions_section = self.create_actions_section()
            main_layout.addWidget(actions_section, 0, Qt.AlignCenter)

        # Status section for feedback
        status_section = self.create_status_section()
        main_layout.addWidget(status_section, 0, Qt.AlignCenter)

    def has_conversation_history(self):
        """Check if there's existing conversation history"""
        try:
            history_file = config_manager.get('Paths', 'history_file', './data/history.json')
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return len(data.get('conversations', [])) > 0
        except:
            pass
        return False

    def load_conversation_history(self):
        """Load and display recent conversation history"""
        try:
            history_file = config_manager.get('Paths', 'history_file', './data/history.json')
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    recent_conversations = data.get('conversations', [])[-5:]  # Last 5 messages

                    for conv in recent_conversations:
                        timestamp = datetime.fromisoformat(conv.get('timestamp', datetime.now().isoformat()))
                        self.conversation_area.add_message(
                            conv.get('message', ''),
                            conv.get('sender', 'user'),
                            timestamp
                        )
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Could not load conversation history: {e}")

    def save_message_to_history(self, message, sender="user"):
        """Save a message to conversation history"""
        try:
            history_file = config_manager.get('Paths', 'history_file', './data/history.json')

            # Ensure data directory exists
            os.makedirs(os.path.dirname(history_file), exist_ok=True)

            # Load existing history
            history_data = {"conversations": []}
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)

            # Add new message
            history_data['conversations'].append({
                'message': message,
                'sender': sender,
                'timestamp': datetime.now().isoformat()
            })

            # Keep only last 100 messages to prevent file from growing too large
            max_history = config_manager.get_max_history_items()
            if len(history_data['conversations']) > max_history:
                history_data['conversations'] = history_data['conversations'][-max_history:]

            # Save back to file
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            if self.logger:
                self.logger.error(f"Could not save message to history: {e}")

    def create_welcome_section(self):
        """Create welcome message for first-time users"""
        welcome_widget = QWidget()
        welcome_layout = QVBoxLayout(welcome_widget)
        welcome_layout.setContentsMargins(0, 0, 0, 0)
        welcome_layout.setSpacing(15)
        welcome_layout.setAlignment(Qt.AlignCenter)

        # Welcome title
        app_name = config_manager.get_app_name()
        welcome_title = QLabel(f"Welcome to {app_name}")
        welcome_title.setObjectName("welcomeTitle")
        welcome_title.setAlignment(Qt.AlignCenter)

        # Welcome subtitle
        username = config_manager.get_username()
        welcome_subtitle = QLabel(f"Hello {username}! How can I assist you today?")
        welcome_subtitle.setObjectName("welcomeSubtitle")
        welcome_subtitle.setAlignment(Qt.AlignCenter)

        # Feature highlights
        features_text = "✨ Voice Input • 🌐 Translation • ⚙️ Task Automation • 📝 Smart Conversations"
        features_label = QLabel(features_text)
        features_label.setObjectName("featuresLabel")
        features_label.setAlignment(Qt.AlignCenter)

        welcome_layout.addWidget(welcome_title)
        welcome_layout.addWidget(welcome_subtitle)
        welcome_layout.addSpacing(10)
        welcome_layout.addWidget(features_label)

        return welcome_widget

    def should_show_actions(self):
        """Check if action buttons should be shown based on enabled features"""
        return (config_manager.is_translation_enabled() or
                config_manager.is_task_automation_enabled())

    def create_input_section(self):
        """Create the enhanced input field section"""
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

        # Voice input button (only if enabled)
        if config_manager.is_voice_input_enabled():
            self.mic_button = QPushButton()
            self.mic_button.setObjectName("micButton")
            self.mic_button.setFixedSize(QSize(32, 32))
            self.mic_button.setToolTip("Voice input (Ctrl+M)")
            self.mic_button.clicked.connect(self.voice_triggered.emit)

            # Try to load microphone icon
            mic_icon = self.load_icon("microphone.icon.png", "🎤")
            if isinstance(mic_icon, QIcon):
                self.mic_button.setIcon(mic_icon)
                self.mic_button.setIconSize(QSize(20, 20))
            else:
                self.mic_button.setText(mic_icon)

        # Enhanced input field with placeholder from config
        self.input_field = QLineEdit()
        self.input_field.setObjectName("mainInput")
        placeholder_text = config_manager.get_placeholder_text()
        self.input_field.setPlaceholderText(placeholder_text)
        self.input_field.setFixedHeight(60)
        self.input_field.setMinimumWidth(600)
        self.input_field.setAttribute(Qt.WA_MacShowFocusRect, False)

        # Connect input events
        self.input_field.returnPressed.connect(self.send_message)
        self.input_field.textChanged.connect(self.on_text_changed)

        # Language/settings button
        self.settings_button = QPushButton()
        self.settings_button.setObjectName("settingsButton")
        self.settings_button.setFixedSize(QSize(32, 32))
        self.settings_button.setToolTip("Language & Settings")

        settings_icon = self.load_icon("globe.icon.png", "🌐")
        if isinstance(settings_icon, QIcon):
            self.settings_button.setIcon(settings_icon)
            self.settings_button.setIconSize(QSize(20, 20))
        else:
            self.settings_button.setText(settings_icon)

        # Enhanced send button
        self.send_button = QPushButton()
        self.send_button.setObjectName("sendButton")
        self.send_button.setFixedSize(QSize(80, 40))
        self.send_button.setToolTip("Send message (Enter)")
        self.send_button.clicked.connect(self.send_message)
        self.send_button.setEnabled(False)  # Initially disabled

        # Try to load send icon
        send_icon = self.load_icon("send.button.png", "Send")
        if isinstance(send_icon, QIcon):
            self.send_button.setIcon(send_icon)
            self.send_button.setIconSize(QSize(20, 20))
        else:
            self.send_button.setText(send_icon)

        # Add widgets to container
        if config_manager.is_voice_input_enabled():
            input_container_layout.addWidget(self.mic_button)

        input_container_layout.addWidget(self.input_field, 1)
        input_container_layout.addWidget(self.settings_button)
        input_container_layout.addWidget(self.send_button)

        input_layout.addWidget(input_container)
        return input_widget

    def create_actions_section(self):
        """Create the enhanced action buttons section"""
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(config_manager.get_spacing() * 4)

        # Create action buttons based on enabled features
        actions = []

        if config_manager.is_translation_enabled():
            actions.append(('translation.icon.png', 'Translate', self.translation_requested.emit, '🌐'))

        if config_manager.is_task_automation_enabled():
            actions.append(('tasks.icon.png', 'Automate', self.task_requested.emit, '⚙️'))

        for icon_name, text, callback, fallback_emoji in actions:
            button_widget = self.create_action_button(icon_name, text, callback, fallback_emoji)
            actions_layout.addWidget(button_widget)

        return actions_widget

    def create_action_button(self, icon_name, text, callback, fallback_emoji):
        """Create an enhanced action button with icon and text"""
        button_widget = QWidget()
        button_layout = QVBoxLayout(button_widget)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(15)
        button_layout.setAlignment(Qt.AlignCenter)

        # Icon button
        icon_button = QPushButton()
        icon_button.setObjectName(f"actionButton_{text.lower()}")
        icon_button.setFixedSize(QSize(80, 80))
        icon_button.setToolTip(f"{text} Assistant")
        icon_button.clicked.connect(callback)

        # Try to load icon
        icon = self.load_icon(icon_name, fallback_emoji)
        if isinstance(icon, QIcon):
            icon_size = config_manager.get_icon_size()
            icon_button.setIcon(icon)
            icon_button.setIconSize(QSize(icon_size, icon_size))
        else:
            icon_button.setText(icon)
            icon_button.setStyleSheet(f"""
                QPushButton {{
                    font-size: {config_manager.get_icon_size()}px;
                }}
            """)

        # Text label
        text_label = QLabel(text)
        text_label.setObjectName("actionLabel")
        text_label.setAlignment(Qt.AlignCenter)

        button_layout.addWidget(icon_button)
        button_layout.addWidget(text_label)

        return button_widget

    def create_status_section(self):
        """Create a status section for user feedback"""
        self.status_widget = QWidget()
        status_layout = QVBoxLayout(self.status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(10)
        status_layout.setAlignment(Qt.AlignCenter)

        # Status label (initially hidden)
        self.status_label = QLabel()
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.hide()

        # Typing indicator (initially hidden)
        self.typing_label = QLabel("AI is typing...")
        self.typing_label.setObjectName("typingLabel")
        self.typing_label.setAlignment(Qt.AlignCenter)
        self.typing_label.hide()

        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.typing_label)
        return self.status_widget

    def load_icon(self, icon_name, fallback):
        """Load an icon from the icons directory"""
        try:
            icons_path = config_manager.get_icons_path()
            icon_path = os.path.join(icons_path, icon_name)

            if os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                if not pixmap.isNull():
                    return QIcon(pixmap)

            return fallback

        except Exception as e:
            if self.logger:
                self.logger.warning(f"Could not load icon {icon_name}: {e}")
            return fallback

    def setup_shortcuts(self):
        """Set up keyboard shortcuts"""
        try:
            # Clear input shortcut
            clear_shortcut = QShortcut(QKeySequence("Ctrl+L"), self)
            clear_shortcut.activated.connect(self.clear_input)

            # Voice input shortcut
            if config_manager.is_voice_input_enabled():
                voice_shortcut = QShortcut(QKeySequence("Ctrl+M"), self)
                voice_shortcut.activated.connect(self.voice_triggered.emit)

            # New conversation shortcut
            new_conv_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
            new_conv_shortcut.activated.connect(self.new_conversation)

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error setting up shortcuts: {e}")

    def setup_animations(self):
        """Set up UI animations"""
        if config_manager.get_bool('UI', 'enable_transitions', True):
            duration = config_manager.get_animation_duration()

            # Send button animation
            self.send_button_animation = QPropertyAnimation(self.send_button, b"geometry")
            self.send_button_animation.setDuration(duration)
            self.send_button_animation.setEasingCurve(QEasingCurve.OutCubic)

            self.animations.append(self.send_button_animation)

    def on_text_changed(self, text):
        """Handle input text changes"""
        # Enable/disable send button based on input
        has_text = bool(text.strip())
        self.send_button.setEnabled(has_text)

        # Update send button appearance
        if has_text:
            self.send_button.setObjectName("sendButtonActive")
        else:
            self.send_button.setObjectName("sendButton")

        # Reapply styles
        self.send_button.style().unpolish(self.send_button)
        self.send_button.style().polish(self.send_button)

        # Handle typing indicator
        if text and hasattr(self, 'typing_timer'):
            self.typing_timer.start(1000)  # 1 second delay

    def on_typing_stopped(self):
        """Handle when user stops typing"""
        # Could be used for auto-suggestions or other features
        pass

    def send_message(self):
        """Send the current message"""
        message = self.input_field.text().strip()
        if message:
            if self.logger:
                self.logger.info(f"Sending message: {message[:50]}...")

            # Hide welcome section if it's visible
            if hasattr(self, 'conversation_area') and self.conversation_area.isHidden():
                # Find and hide welcome section
                for i in range(self.layout().count()):
                    item = self.layout().itemAt(i)
                    if item and item.widget():
                        widget = item.widget()
                        if hasattr(widget, 'findChild') and widget.findChild(QLabel, 'welcomeTitle'):
                            widget.hide()
                            break

                # Show conversation area
                self.conversation_area.show()

            # Add message to conversation
            self.conversation_area.add_message(message, "user")

            # Save to history
            self.save_message_to_history(message, "user")

            # Emit signal with message
            self.message_sent.emit(message)

            # Clear input
            self.clear_input()

            # Show processing status
            self.show_status("Processing message...", "info")
            self.show_typing_indicator()

            # Simulate AI response (replace with actual AI integration)
            QTimer.singleShot(2000, self.simulate_ai_response)

    def simulate_ai_response(self):
        """Simulate an AI response (replace with actual AI integration)"""
        responses = [
            "I understand your request. How can I help you further?",
            "That's an interesting question. Let me think about it...",
            "I'd be happy to assist you with that task.",
            "Here's what I found based on your query..."
        ]

        import random
        response = random.choice(responses)

        # Add AI response to conversation
        self.conversation_area.add_message(response, "assistant")
        self.save_message_to_history(response, "assistant")

        # Hide indicators
        self.hide_typing_indicator()
        self.hide_status()

    def show_typing_indicator(self):
        """Show typing indicator"""
        self.typing_label.show()

    def hide_typing_indicator(self):
        """Hide typing indicator"""
        self.typing_label.hide()

    def clear_input(self):
        """Clear the input field"""
        self.input_field.clear()
        self.input_field.setFocus()

    def new_conversation(self):
        """Start a new conversation"""
        self.conversation_area.clear_conversation()
        self.clear_input()
        self.hide_status()
        self.hide_typing_indicator()

    def show_status(self, message, status_type="info"):
        """Show a status message"""
        self.status_label.setText(message)
        self.status_label.setProperty("statusType", status_type)

        # Reapply styles based on status type
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

        self.status_label.show()

    def hide_status(self):
        """Hide the status message"""
        self.status_label.hide()

    def set_focus_to_input(self):
        """Set focus to the input field"""
        self.input_field.setFocus()

    def apply_styles(self):
        """Apply enhanced custom styles to the content area"""
        try:
            font_size = config_manager.get_font_size()
            theme = config_manager.get_theme()
            border_radius = config_manager.get_border_radius()
            primary_color = config_manager.get_primary_color()
            secondary_color = config_manager.get_secondary_color()

            # Adjust colors based on theme
            if theme == 'dark':
                input_bg = "#2a3441"
                border_color = config_manager.get_border_color()
                text_color = config_manager.get_text_primary_color()
                text_secondary = config_manager.get_text_secondary_color()
                placeholder_color = "rgba(255, 255, 255, 0.5)"
                button_bg = "rgba(255, 255, 255, 0.05)"
                button_hover = "rgba(255, 255, 255, 0.1)"
            else:
                input_bg = "#f8f9fa"
                border_color = "rgba(0, 0, 0, 0.1)"
                text_color = "#333333"
                text_secondary = "rgba(0, 0, 0, 0.7)"
                placeholder_color = "rgba(0, 0, 0, 0.5)"
                button_bg = "rgba(0, 0, 0, 0.05)"
                button_hover = "rgba(0, 0, 0, 0.1)"

            self.setStyleSheet(f"""
                QFrame#contentArea {{
                    background: transparent;
                }}
                
                QLabel#welcomeTitle {{
                    color: {text_color};
                    font-size: {font_size + 16}px;
                    font-weight: 700;
                    margin-bottom: 10px;
                }}
                
                QLabel#welcomeSubtitle {{
                    color: {text_secondary};
                    font-size: {font_size + 4}px;
                    font-weight: 400;
                    margin-bottom: 5px;
                }}
                
                QLabel#featuresLabel {{
                    color: {text_secondary};
                    font-size: {font_size + 1}px;
                    font-weight: 400;
                    padding: 10px 20px;
                    background-color: rgba(128, 128, 128, 0.1);
                    border-radius: {border_radius}px;
                }}
                
                QWidget#inputContainer {{
                    background-color: {input_bg};
                    border: 1px solid {border_color};
                    border-radius: {border_radius * 2}px;
                    min-height: 60px;
                }}
                
                QLineEdit#mainInput {{
                    background-color: transparent;
                    border: none;
                    color: {text_color};
                    font-size: {font_size + 4}px;
                    padding: 0;
                    selection-background-color: {primary_color};
                }}
                
                QLineEdit#mainInput::placeholder {{
                    color: {placeholder_color};
                }}
                
                QLineEdit#mainInput:focus {{
                    outline: none;
                    border: none;
                }}
                
                QPushButton#micButton, QPushButton#settingsButton {{
                    background-color: transparent;
                    border: none;
                    color: {text_secondary};
                    font-size: {font_size + 4}px;
                    border-radius: 16px;
                }}
                
                QPushButton#micButton:hover, QPushButton#settingsButton:hover {{
                    background-color: {button_hover};
                    color: {text_color};
                }}
                
                QPushButton#sendButton {{
                    background-color: rgba(128, 128, 128, 0.3);
                    border: none;
                    border-radius: 20px;
                    color: rgba(255, 255, 255, 0.6);
                    font-weight: 600;
                    font-size: {font_size + 1}px;
                }}
                
                QPushButton#sendButtonActive {{
                    background-color: {primary_color};
                    border: none;
                    border-radius: 20px;
                    color: #ffffff;
                    font-weight: 600;
                    font-size: {font_size + 1}px;
                }}
                
                QPushButton#sendButtonActive:hover {{
                    background-color: {secondary_color};
                    transform: scale(1.02);
                }}
                
                QPushButton#sendButtonActive:pressed {{
                    background-color: {primary_color};
                    transform: scale(0.98);
                }}
                
                QPushButton[objectName^="actionButton"] {{
                    background-color: {button_bg};
                    border: 1px solid {border_color};
                    border-radius: {border_radius * 3}px;
                    color: {text_color};
                    font-size: {font_size + 12}px;
                }}
                
                QPushButton[objectName^="actionButton"]:hover {{
                    background-color: {button_hover};
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    transform: translateY(-2px);
                }}
                
                QPushButton[objectName^="actionButton"]:pressed {{
                    background-color: {button_bg};
                    transform: translateY(0px);
                }}
                
                QLabel#actionLabel {{
                    color: {text_secondary};
                    font-size: {font_size + 2}px;
                    font-weight: 500;
                }}
                
                QLabel#statusLabel {{
                    color: {text_secondary};
                    font-size: {font_size}px;
                    padding: 8px 16px;
                    border-radius: {border_radius}px;
                }}
                
                QLabel#statusLabel[statusType="info"] {{
                    background-color: rgba(74, 144, 226, 0.1);
                    color: {primary_color};
                }}
                
                QLabel#statusLabel[statusType="success"] {{
                    background-color: rgba(76, 175, 80, 0.1);
                    color: #4CAF50;
                }}
                
                QLabel#statusLabel[statusType="error"] {{
                    background-color: rgba(244, 67, 54, 0.1);
                    color: #F44336;
                }}
                
                QLabel#typingLabel {{
                    color: {text_secondary};
                    font-size: {font_size}px;
                    font-style: italic;
                    padding: 4px 12px;
                }}
            """)

            if self.logger:
                self.logger.debug("Content area styles applied successfully")

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error applying styles: {e}")



