"""
STARK AI - Enhanced Content Area Component
Modern ChatGPT-style content area with beautiful message display and input
"""

import customtkinter as ctk
import tkinter as tk
from datetime import datetime
import re

class ContentArea:
    def __init__(self, parent, colors, gui_config, send_bar_message):
        self.parent = parent
        self.colors = colors
        self.gui_config = gui_config
        self.send_bar_message = send_bar_message
        self.current_mode = "chat"

        self.setup_content_area()

    def setup_content_area(self):
        """Setup modern content area layout"""
        # Configure parent
        self.parent.grid_columnconfigure(0, weight=1)
        self.parent.grid_rowconfigure(0, weight=1)

        # Main container
        self.content_container = ctk.CTkFrame(
            self.parent,
            fg_color=self.colors['bg_primary'],
            corner_radius=0
        )
        self.content_container.grid(row=0, column=0, sticky="nsew")
        self.content_container.grid_columnconfigure(0, weight=1)
        self.content_container.grid_rowconfigure(0, weight=1)

        # Create chat interface
        self.create_chat_interface()
        self.create_input_section()

    def create_chat_interface(self):
        """Create modern chat interface"""
        # Chat container with subtle styling
        self.chat_container = ctk.CTkFrame(
            self.content_container,
            fg_color=self.colors['bg_primary'],
            corner_radius=0
        )
        self.chat_container.grid(row=0, column=0, sticky="nsew", padx=20, pady=(20, 10))
        self.chat_container.grid_columnconfigure(0, weight=1)
        self.chat_container.grid_rowconfigure(0, weight=1)

        # Scrollable chat area
        self.chat_display = ctk.CTkScrollableFrame(
            self.chat_container,
            fg_color=self.colors['bg_primary'],
            corner_radius=12,
            scrollbar_button_color=self.colors['bg_tertiary'],
            scrollbar_button_hover_color=self.colors['bg_hover']
        )
        self.chat_display.grid(row=0, column=0, sticky="nsew")
        self.chat_display.grid_columnconfigure(0, weight=1)

        # Welcome message
        self.add_welcome_message()

    def create_input_section(self):
        """Create modern input section"""
        # Input container
        self.input_container = ctk.CTkFrame(
            self.content_container,
            height=120,
            fg_color=self.colors['bg_primary'],
            corner_radius=0
        )
        self.input_container.grid(row=1, column=0, sticky="ew", padx=20, pady=(10, 20))
        self.input_container.grid_propagate(False)
        self.input_container.grid_columnconfigure(0, weight=1)

        # Input frame with modern styling
        input_frame = ctk.CTkFrame(
            self.input_container,
            fg_color=self.colors['bg_secondary'],
            corner_radius=16,
            border_width=1,
            border_color=self.colors['border']
        )
        input_frame.grid(row=0, column=0, sticky="ew", pady=10)
        input_frame.grid_columnconfigure(0, weight=1)

        # Text input with placeholder styling
        self.text_input = ctk.CTkTextbox(
            input_frame,
            height=60,
            font=ctk.CTkFont(size=14),
            fg_color=self.colors['bg_secondary'],
            text_color=self.colors['text_primary'],
            corner_radius=12,
            border_width=0,
            wrap="word"
        )
        self.text_input.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))

        # Control bar
        control_frame = ctk.CTkFrame(
            input_frame,
            height=40,
            fg_color="transparent"
        )
        control_frame.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 12))
        control_frame.grid_propagate(False)
        control_frame.grid_columnconfigure(1, weight=1)

        # Left controls
        left_controls = ctk.CTkFrame(control_frame, fg_color="transparent")
        left_controls.grid(row=0, column=0, sticky="w")

        # Attachment button
        attach_btn = ctk.CTkButton(
            left_controls,
            text="📎",
            width=32,
            height=32,
            corner_radius=8,
            fg_color="transparent",
            hover_color=self.colors['bg_hover'],
            font=ctk.CTkFont(size=14),
            text_color=self.colors['text_secondary']
        )
        attach_btn.pack(side="left", padx=(0, 8))

        # Voice button
        voice_btn = ctk.CTkButton(
            left_controls,
            text="🎤",
            width=32,
            height=32,
            corner_radius=8,
            fg_color="transparent",
            hover_color=self.colors['bg_hover'],
            font=ctk.CTkFont(size=14),
            text_color=self.colors['text_secondary']
        )
        voice_btn.pack(side="left", padx=(0, 8))

        # Mode indicator
        self.mode_label = ctk.CTkLabel(
            control_frame,
            text="💬 Chat Mode",
            font=ctk.CTkFont(size=11),
            text_color=self.colors['text_muted']
        )
        self.mode_label.grid(row=0, column=1, sticky="")

        # Send button
        self.send_btn = ctk.CTkButton(
            control_frame,
            text="Send ↗",
            width=80,
            height=32,
            corner_radius=8,
            fg_color=self.colors['accent_primary'],
            hover_color=self.colors['accent_hover'],
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors['text_primary'],
            command=self.send_message
        )
        self.send_btn.grid(row=0, column=2, sticky="e")

        # Bind events
        self.text_input.bind("<Control-Return>", self.send_message)
        self.text_input.bind("<KeyRelease>", self.on_text_change)

        # Set placeholder
        self.set_placeholder()

    def set_placeholder(self):
        """Set placeholder text"""
        placeholder_text = self.send_bar_message
        self.text_input.insert("1.0", placeholder_text)
        self.text_input.configure(text_color=self.colors['text_muted'])
        self.is_placeholder = True

        def on_focus_in(event):
            if self.is_placeholder:
                self.text_input.delete("1.0", "end")
                self.text_input.configure(text_color=self.colors['text_primary'])
                self.is_placeholder = False

        def on_focus_out(event):
            if not self.text_input.get("1.0", "end-1c").strip():
                self.text_input.insert("1.0", placeholder_text)
                self.text_input.configure(text_color=self.colors['text_muted'])
                self.is_placeholder = True

        self.text_input.bind("<FocusIn>", on_focus_in)
        self.text_input.bind("<FocusOut>", on_focus_out)

    def on_text_change(self, event):
        """Handle text input changes"""
        text = self.text_input.get("1.0", "end-1c").strip()

        # Update send button state
        if text and not self.is_placeholder:
            self.send_btn.configure(
                fg_color=self.colors['accent_primary'],
                text_color=self.colors['text_primary']
            )
        else:
            self.send_btn.configure(
                fg_color=self.colors['bg_tertiary'],
                text_color=self.colors['text_muted']
            )

    def add_welcome_message(self):
        """Add welcome message with modern styling"""
        welcome_frame = ctk.CTkFrame(
            self.chat_display,
            fg_color=self.colors['bg_secondary'],
            corner_radius=16
        )
        welcome_frame.grid(row=0, column=0, sticky="ew", pady=20, padx=20)
        welcome_frame.grid_columnconfigure(0, weight=1)

        # Welcome icon
        icon_label = ctk.CTkLabel(
            welcome_frame,
            text="⚡",
            font=ctk.CTkFont(size=32),
            text_color=self.colors['accent_primary']
        )
        icon_label.grid(row=0, column=0, pady=(20, 10))

        # Welcome title
        title_label = ctk.CTkLabel(
            welcome_frame,
            text="Welcome to STARK AI",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.colors['text_primary']
        )
        title_label.grid(row=1, column=0, pady=(0, 8))

        # Welcome description
        desc_label = ctk.CTkLabel(
            welcome_frame,
            text="Your intelligent assistant is ready to help with coding, research, writing, and more.\nStart a conversation below or choose a mode from the sidebar.",
            font=ctk.CTkFont(size=14),
            text_color=self.colors['text_secondary'],
            justify="center"
        )
        desc_label.grid(row=2, column=0, pady=(0, 20), padx=20)

    def send_message(self, event=None):
        """Send message with modern styling"""
        if self.is_placeholder:
            return

        message = self.text_input.get("1.0", "end-1c").strip()
        if not message:
            return

        # Add user message
        self.add_user_message(message)

        # Clear input
        self.text_input.delete("1.0", "end")
        self.set_placeholder()

        # Process message
        self.process_message(message)

    def add_user_message(self, message):
        """Add user message with modern bubble design"""
        row = len(self.chat_display.winfo_children())

        # Message container
        msg_container = ctk.CTkFrame(
            self.chat_display,
            fg_color="transparent"
        )
        msg_container.grid(row=row, column=0, sticky="ew", pady=(10, 5), padx=20)
        msg_container.grid_columnconfigure(1, weight=1)

        # User avatar
        avatar_frame = ctk.CTkFrame(
            msg_container,
            width=36,
            height=36,
            corner_radius=18,
            fg_color=self.colors['accent_primary']
        )
        avatar_frame.grid(row=0, column=0, sticky="ne", padx=(0, 12))
        avatar_frame.grid_propagate(False)

        avatar_label = ctk.CTkLabel(
            avatar_frame,
            text="👤",
            font=ctk.CTkFont(size=16),
            text_color=self.colors['text_primary']
        )
        avatar_label.place(relx=0.5, rely=0.5, anchor="center")

        # Message bubble
        bubble_frame = ctk.CTkFrame(
            msg_container,
            fg_color=self.colors['bg_tertiary'],
            corner_radius=16
        )
        bubble_frame.grid(row=0, column=1, sticky="ew")
        bubble_frame.grid_columnconfigure(0, weight=1)

        # Message text
        msg_label = ctk.CTkLabel(
            bubble_frame,
            text=message,
            font=ctk.CTkFont(size=14),
            text_color=self.colors['text_primary'],
            anchor="w",
            justify="left",
            wraplength=500
        )
        msg_label.grid(row=0, column=0, sticky="ew", padx=16, pady=12)

        # Timestamp
        time_label = ctk.CTkLabel(
            msg_container,
            text=datetime.now().strftime("%H:%M"),
            font=ctk.CTkFont(size=10),
            text_color=self.colors['text_muted']
        )
        time_label.grid(row=1, column=1, sticky="e", pady=(2, 0))

    def add_ai_message(self, message):
        """Add AI message with modern bubble design"""
        row = len(self.chat_display.winfo_children())

        # Message container
        msg_container = ctk.CTkFrame(
            self.chat_display,
            fg_color="transparent"
        )
        msg_container.grid(row=row, column=0, sticky="ew", pady=(5, 10), padx=20)
        msg_container.grid_columnconfigure(0, weight=1)

        # AI avatar
        avatar_frame = ctk.CTkFrame(
            msg_container,
            width=36,
            height=36,
            corner_radius=18,
            fg_color=self.colors['accent_secondary']
        )
        avatar_frame.grid(row=0, column=1, sticky="nw", padx=(12, 0))
        avatar_frame.grid_propagate(False)

        avatar_label = ctk.CTkLabel(
            avatar_frame,
            text="⚡",
            font=ctk.CTkFont(size=16),
            text_color=self.colors['text_primary']
        )
        avatar_label.place(relx=0.5, rely=0.5, anchor="center")

        # Message bubble
        bubble_frame = ctk.CTkFrame(
            msg_container,
            fg_color=self.colors['bg_secondary'],
            corner_radius=16
        )
        bubble_frame.grid(row=0, column=0, sticky="ew")
        bubble_frame.grid_columnconfigure(0, weight=1)

        # Message text
        msg_label = ctk.CTkLabel(
            bubble_frame,
            text=message,
            font=ctk.CTkFont(size=14),
            text_color=self.colors['text_primary'],
            anchor="w",
            justify="left",
            wraplength=500
        )
        msg_label.grid(row=0, column=0, sticky="ew", padx=16, pady=12)

        # Timestamp
        time_label = ctk.CTkLabel(
            msg_container,
            text=datetime.now().strftime("%H:%M"),
            font=ctk.CTkFont(size=10),
            text_color=self.colors['text_muted']
        )
        time_label.grid(row=1, column=0, sticky="w", pady=(2, 0))

        # Scroll to bottom
        self.chat_display._parent_canvas.yview_moveto(1.0)

    def process_message(self, message):
        """Process user message and generate AI response"""
        # Simulate AI processing delay
        self.root.after(1000, lambda: self.generate_ai_response(message))

    def generate_ai_response(self, user_message):
        """Generate contextual AI response based on current mode"""
        responses = {
            "chat": f"I understand you're asking about: '{user_message}'. As your AI assistant, I'm here to help with any questions or tasks you have. How can I assist you further?",
            "translate": f"Translation mode activated. I can help translate '{user_message}' to your desired language. Which language would you like me to translate this to?",
            "search": f"Searching for information about: '{user_message}'. Here are some relevant results and insights I found...",
            "automation": f"I can help you automate tasks related to: '{user_message}'. Let me suggest some automation workflows that might be useful."
        }

        response = responses.get(self.current_mode, responses["chat"])
        self.add_ai_message(response)

    def set_mode(self, mode):
        """Set current mode and update interface"""
        self.current_mode = mode

        mode_info = {
            "chat": {"icon": "💬", "name": "Chat Mode", "desc": "AI Assistant"},
            "translate": {"icon": "🌐", "name": "Translation Mode", "desc": "Language Translation"},
            "search": {"icon": "🔍", "name": "Search Mode", "desc": "Smart Search"},
            "automation": {"icon": "🤖", "name": "Automation Mode", "desc": "Task Automation"},
            "settings": {"icon": "⚙️", "name": "Settings", "desc": "Preferences"}
        }

        info = mode_info.get(mode, mode_info["chat"])
        self.mode_label.configure(text=f"{info['icon']} {info['name']}")

        # Update placeholder
        placeholders = {
            "chat": "Ask STARK AI anything...",
            "translate": "Enter text to translate...",
            "search": "What would you like to search for?",
            "automation": "Describe your automation task...",
            "settings": "Settings command..."
        }

        self.send_bar_message = placeholders.get(mode, "Message STARK AI...")
        if hasattr(self, 'is_placeholder') and self.is_placeholder:
            self.text_input.delete("1.0", "end")
            self.set_placeholder()

    @property
    def root(self):
        """Get root window for after() calls"""
        widget = self.parent
        while widget.master:
            widget = widget.master
        return widget










