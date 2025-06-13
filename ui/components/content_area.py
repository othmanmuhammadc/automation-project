"""
STARK AI - Content Area Component
Professional content area with message input/output and different modes
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import scrolledtext
import json
from datetime import datetime

class ContentArea:
    def __init__(self, parent, colors, gui_config, send_bar_message):
        self.parent = parent
        self.colors = colors
        self.gui_config = gui_config
        self.send_bar_message = send_bar_message
        self.current_mode = "chat"

        self.setup_content_area()

    def setup_content_area(self):
        """Setup content area layout"""
        # Configure parent frame
        self.parent.grid_columnconfigure(0, weight=1)
        self.parent.grid_rowconfigure(0, weight=1)

        # Main content container
        self.content_container = ctk.CTkFrame(
            self.parent,
            fg_color=self.colors['bg_primary'],
            corner_radius=8
        )
        self.content_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.content_container.grid_columnconfigure(0, weight=1)
        self.content_container.grid_rowconfigure(0, weight=1)

        # Create different mode interfaces
        self.create_chat_interface()
        self.create_input_area()

    def create_chat_interface(self):
        """Create chat interface with message history"""
        # Chat area frame
        self.chat_frame = ctk.CTkFrame(
            self.content_container,
            fg_color=self.colors['bg_secondary'],
            corner_radius=8
        )
        self.chat_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 5))
        self.chat_frame.grid_columnconfigure(0, weight=1)
        self.chat_frame.grid_rowconfigure(0, weight=1)

        # Scrollable text area for messages
        self.chat_display = ctk.CTkTextbox(
            self.chat_frame,
            fg_color=self.colors['bg_tertiary'],
            text_color=self.colors['text_primary'],
            font=ctk.CTkFont(size=12),
            corner_radius=6,
            wrap="word"
        )
        self.chat_display.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Welcome message
        self.add_system_message("Welcome to STARK AI! How can I assist you today?")

    def create_input_area(self):
        """Create input area with send button"""
        # Input frame
        self.input_frame = ctk.CTkFrame(
            self.content_container,
            height=80,
            fg_color=self.colors['bg_secondary'],
            corner_radius=8
        )
        self.input_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(5, 10))
        self.input_frame.grid_columnconfigure(0, weight=1)
        self.input_frame.grid_propagate(False)

        # Input container
        input_container = ctk.CTkFrame(
            self.input_frame,
            fg_color="transparent"
        )
        input_container.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        input_container.grid_columnconfigure(0, weight=1)

        # Text input
        self.text_input = ctk.CTkEntry(
            input_container,
            placeholder_text=self.send_bar_message,
            height=40,
            font=ctk.CTkFont(size=12),
            fg_color=self.colors['bg_tertiary'],
            border_color=self.colors['border'],
            text_color=self.colors['text_primary']
        )
        self.text_input.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.text_input.bind("<Return>", self.on_send_message)

        # Send button
        self.send_button = ctk.CTkButton(
            input_container,
            text="Send",
            width=80,
            height=40,
            corner_radius=6,
            fg_color=self.colors['accent_blue'],
            hover_color=self.colors['accent_light'],
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.on_send_message
        )
        self.send_button.grid(row=0, column=1, sticky="e")

        # Additional controls frame
        controls_frame = ctk.CTkFrame(
            input_container,
            fg_color="transparent"
        )
        controls_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(5, 0))

        # Language selector
        self.language_var = ctk.StringVar(value="English")
        self.language_selector = ctk.CTkOptionMenu(
            controls_frame,
            values=["English", "العربية", "Deutsch"],
            variable=self.language_var,
            width=100,
            height=25,
            fg_color=self.colors['bg_tertiary'],
            button_color=self.colors['accent_blue'],
            font=ctk.CTkFont(size=10)
        )
        self.language_selector.pack(side="left", padx=(0, 10))

        # Mode indicator
        self.mode_label = ctk.CTkLabel(
            controls_frame,
            text="Chat Mode",
            font=ctk.CTkFont(size=10),
            text_color=self.colors['text_secondary']
        )
        self.mode_label.pack(side="left")

        # Clear chat button
        self.clear_button = ctk.CTkButton(
            controls_frame,
            text="Clear",
            width=60,
            height=25,
            corner_radius=4,
            fg_color=self.colors['bg_tertiary'],
            hover_color=self.colors['hover'],
            font=ctk.CTkFont(size=10),
            command=self.clear_chat
        )
        self.clear_button.pack(side="right")

    def on_send_message(self, event=None):
        """Handle send message action"""
        message = self.text_input.get().strip()
        if not message:
            return

        # Add user message
        self.add_user_message(message)

        # Clear input
        self.text_input.delete(0, tk.END)

        # Process message (placeholder for actual AI processing)
        self.process_message(message)

    def add_user_message(self, message):
        """Add user message to chat display"""
        timestamp = datetime.now().strftime("%H:%M")
        formatted_message = f"[{timestamp}] You: {message}\n\n"

        self.chat_display.insert(tk.END, formatted_message)
        self.chat_display.see(tk.END)

    def add_ai_message(self, message):
        """Add AI response to chat display"""
        timestamp = datetime.now().strftime("%H:%M")
        formatted_message = f"[{timestamp}] STARK AI: {message}\n\n"

        self.chat_display.insert(tk.END, formatted_message)
        self.chat_display.see(tk.END)

    def add_system_message(self, message):
        """Add system message to chat display"""
        timestamp = datetime.now().strftime("%H:%M")
        formatted_message = f"[{timestamp}] System: {message}\n\n"

        self.chat_display.insert(tk.END, formatted_message)
        self.chat_display.see(tk.END)

    def process_message(self, message):
        """Process user message and generate response (placeholder)"""
        # This is a placeholder for actual AI processing
        # In the real implementation, this would connect to the AI backend

        if self.current_mode == "translate":
            response = f"Translation mode: '{message}' -> [Translation would appear here]"
        elif self.current_mode == "code":
            response = f"Code assistance for: {message}\n\n```python\n# Code example would appear here\nprint('Hello, World!')\n```"
        elif self.current_mode == "search":
            response = f"Searching for: {message}\n\nSearch results would appear here..."
        else:
            response = f"I understand you said: '{message}'. This is a placeholder response. The actual AI processing would happen here."

        self.add_ai_message(response)

    def set_mode(self, mode):
        """Set current mode and update interface"""
        self.current_mode = mode

        mode_names = {
            "chat": "Chat Mode",
            "translate": "Translation Mode",
            "code": "Code Assistant Mode",
            "search": "Search Mode",
            "automation": "Automation Mode",
            "files": "File Manager Mode",
            "history": "History Mode",
            "settings": "Settings Mode"
        }

        mode_name = mode_names.get(mode, "Unknown Mode")
        self.mode_label.configure(text=mode_name)

        # Update placeholder text
        placeholders = {
            "chat": "Ask STARK AI anything...",
            "translate": "Enter text to translate...",
            "code": "Describe your coding task...",
            "search": "What would you like to search for?",
            "automation": "Describe the automation task...",
            "files": "File operation command...",
            "history": "Search chat history...",
            "settings": "Settings command..."
        }

        placeholder = placeholders.get(mode, self.send_bar_message)
        self.text_input.configure(placeholder_text=placeholder)

        # Add mode change message
        self.add_system_message(f"Switched to {mode_name}")

    def clear_chat(self):
        """Clear chat history"""
        self.chat_display.delete("1.0", tk.END)
        self.add_system_message("Chat cleared. How can I help you?")

    def get_chat_history(self):
        """Get current chat history"""
        return self.chat_display.get("1.0", tk.END)

    def load_chat_history(self, history):
        """Load chat history from string"""
        self.chat_display.delete("1.0", tk.END)
        self.chat_display.insert("1.0", history)






