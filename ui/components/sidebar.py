"""
STARK AI - Enhanced Sidebar Component
Modern ChatGPT-style sidebar with smooth interactions and beautiful design
"""

import customtkinter as ctk
import tkinter as tk
import os
from pathlib import Path

class Sidebar:
    def __init__(self, parent, colors, gui_config, callback):
        self.parent = parent
        self.colors = colors
        self.gui_config = gui_config
        self.callback = callback
        self.active_button = "chat"
        self.nav_buttons = {}

        self.setup_sidebar()

    def setup_sidebar(self):
        """Setup modern sidebar layout"""
        # Configure parent
        self.parent.grid_rowconfigure(1, weight=1)
        self.parent.grid_columnconfigure(0, weight=1)

        # Create sections
        self.create_header()
        self.create_chat_history()
        self.create_navigation()
        self.create_footer()

    def create_header(self):
        """Create elegant header with new chat button"""
        header_frame = ctk.CTkFrame(
            self.parent,
            height=70,
            fg_color="transparent"
        )
        header_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        header_frame.grid_propagate(False)
        header_frame.grid_columnconfigure(0, weight=1)

        # New chat button with modern styling
        self.new_chat_btn = ctk.CTkButton(
            header_frame,
            text="✨ New Chat",
            height=44,
            corner_radius=12,
            fg_color=self.colors['bg_tertiary'],
            hover_color=self.colors['bg_hover'],
            border_width=1,
            border_color=self.colors['border'],
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors['text_primary'],
            command=self.new_chat
        )
        self.new_chat_btn.grid(row=0, column=0, sticky="ew")

    def create_chat_history(self):
        """Create chat history section with modern design"""
        history_container = ctk.CTkFrame(
            self.parent,
            fg_color="transparent"
        )
        history_container.grid(row=1, column=0, sticky="nsew", padx=16, pady=8)
        history_container.grid_columnconfigure(0, weight=1)
        history_container.grid_rowconfigure(1, weight=1)

        # Section title
        title_label = ctk.CTkLabel(
            history_container,
            text="Recent Conversations",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=self.colors['text_secondary'],
            anchor="w"
        )
        title_label.grid(row=0, column=0, sticky="ew", pady=(0, 12))

        # Scrollable history with custom styling
        self.history_scroll = ctk.CTkScrollableFrame(
            history_container,
            fg_color=self.colors['bg_secondary'],
            corner_radius=12,
            scrollbar_button_color=self.colors['bg_tertiary'],
            scrollbar_button_hover_color=self.colors['bg_hover']
        )
        self.history_scroll.grid(row=1, column=0, sticky="nsew")
        self.history_scroll.grid_columnconfigure(0, weight=1)

        # Add sample conversations
        self.populate_chat_history()

    def populate_chat_history(self):
        """Add sample chat history with modern styling"""
        conversations = [
            {"title": "Python Web Scraping", "preview": "Help with BeautifulSoup and requests", "time": "2h ago"},
            {"title": "React Component Design", "preview": "Building reusable UI components", "time": "1d ago"},
            {"title": "Database Optimization", "preview": "SQL query performance tuning", "time": "2d ago"},
            {"title": "API Integration Guide", "preview": "RESTful API best practices", "time": "3d ago"},
            {"title": "Machine Learning Basics", "preview": "Introduction to neural networks", "time": "1w ago"},
        ]

        for i, conv in enumerate(conversations):
            self.create_chat_item(conv, i)

    def create_chat_item(self, conversation, row):
        """Create individual chat history item"""
        item_frame = ctk.CTkFrame(
            self.history_scroll,
            height=60,
            fg_color="transparent",
            corner_radius=8
        )
        item_frame.grid(row=row, column=0, sticky="ew", pady=2)
        item_frame.grid_propagate(False)
        item_frame.grid_columnconfigure(0, weight=1)

        # Chat button
        chat_btn = ctk.CTkButton(
            item_frame,
            text="",
            height=60,
            corner_radius=8,
            fg_color="transparent",
            hover_color=self.colors['bg_hover'],
            anchor="w",
            command=lambda: self.load_conversation(conversation['title'])
        )
        chat_btn.grid(row=0, column=0, sticky="ew")

        # Content frame
        content_frame = ctk.CTkFrame(chat_btn, fg_color="transparent")
        content_frame.place(relx=0.05, rely=0.5, anchor="w")

        # Title
        title_label = ctk.CTkLabel(
            content_frame,
            text=conversation['title'],
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors['text_primary'],
            anchor="w"
        )
        title_label.pack(anchor="w")

        # Preview
        preview_label = ctk.CTkLabel(
            content_frame,
            text=conversation['preview'],
            font=ctk.CTkFont(size=10),
            text_color=self.colors['text_muted'],
            anchor="w"
        )
        preview_label.pack(anchor="w", pady=(2, 0))

        # Time
        time_label = ctk.CTkLabel(
            chat_btn,
            text=conversation['time'],
            font=ctk.CTkFont(size=9),
            text_color=self.colors['text_muted']
        )
        time_label.place(relx=0.95, rely=0.2, anchor="e")

    def create_navigation(self):
        """Create modern navigation section"""
        nav_container = ctk.CTkFrame(
            self.parent,
            fg_color="transparent"
        )
        nav_container.grid(row=2, column=0, sticky="ew", padx=16, pady=8)
        nav_container.grid_columnconfigure(0, weight=1)

        # Navigation buttons
        nav_items = [
            {"name": "chat", "icon": "💬", "text": "Chat Assistant", "desc": "AI-powered conversations"},
            {"name": "translate", "icon": "🌐", "text": "Translator", "desc": "Multi-language support"},
            {"name": "search", "icon": "🔍", "text": "Smart Search", "desc": "Intelligent web search"},
            {"name": "automation", "icon": "🤖", "text": "Automation", "desc": "Task automation tools"},
        ]

        for i, item in enumerate(nav_items):
            self.create_nav_button(item, i)

    def create_nav_button(self, item, row):
        """Create individual navigation button with modern design"""
        button = ctk.CTkButton(
            self.parent.children[f'!ctkframe{row+3}'] if f'!ctkframe{row+3}' in self.parent.children else self.parent,
            text=f"{item['icon']} {item['text']}",
            height=48,
            corner_radius=12,
            fg_color="transparent",
            hover_color=self.colors['bg_hover'],
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=self.colors['text_secondary'],
            anchor="w",
            command=lambda: self.on_nav_click(item['name'])
        )

        # Create container for this button
        button_container = ctk.CTkFrame(
            self.parent.children['!ctkframe2'],  # nav_container
            fg_color="transparent"
        )
        button_container.grid(row=row, column=0, sticky="ew", pady=3)
        button_container.grid_columnconfigure(0, weight=1)

        # Recreate button in container
        button = ctk.CTkButton(
            button_container,
            text=f"{item['icon']} {item['text']}",
            height=48,
            corner_radius=12,
            fg_color="transparent",
            hover_color=self.colors['bg_hover'],
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=self.colors['text_secondary'],
            anchor="w",
            command=lambda name=item['name']: self.on_nav_click(name)
        )
        button.grid(row=0, column=0, sticky="ew", padx=4)

        self.nav_buttons[item['name']] = button

        # Set initial active state
        if item['name'] == self.active_button:
            self.set_active_button(item['name'])

    def create_footer(self):
        """Create elegant footer section"""
        footer_frame = ctk.CTkFrame(
            self.parent,
            height=100,
            fg_color="transparent"
        )
        footer_frame.grid(row=3, column=0, sticky="ew", padx=16, pady=(8, 16))
        footer_frame.grid_propagate(False)
        footer_frame.grid_columnconfigure(0, weight=1)

        # Settings button
        settings_btn = ctk.CTkButton(
            footer_frame,
            text="⚙️ Settings & Preferences",
            height=40,
            corner_radius=10,
            fg_color="transparent",
            hover_color=self.colors['bg_hover'],
            font=ctk.CTkFont(size=12),
            text_color=self.colors['text_secondary'],
            anchor="w",
            command=lambda: self.on_nav_click("settings")
        )
        settings_btn.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        # User profile section
        profile_frame = ctk.CTkFrame(
            footer_frame,
            height=44,
            corner_radius=12,
            fg_color=self.colors['bg_tertiary'],
            border_width=1,
            border_color=self.colors['border']
        )
        profile_frame.grid(row=1, column=0, sticky="ew")
        profile_frame.grid_propagate(False)
        profile_frame.grid_columnconfigure(1, weight=1)

        # Avatar
        avatar_label = ctk.CTkLabel(
            profile_frame,
            text="👨‍💻",
            font=ctk.CTkFont(size=16),
            width=40
        )
        avatar_label.grid(row=0, column=0, padx=(12, 8), pady=8)

        # User info
        user_info_frame = ctk.CTkFrame(profile_frame, fg_color="transparent")
        user_info_frame.grid(row=0, column=1, sticky="ew", padx=(0, 12), pady=8)

        user_name = ctk.CTkLabel(
            user_info_frame,
            text="User",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors['text_primary'],
            anchor="w"
        )
        user_name.pack(anchor="w")

        user_status = ctk.CTkLabel(
            user_info_frame,
            text="Free Plan",
            font=ctk.CTkFont(size=10),
            text_color=self.colors['text_muted'],
            anchor="w"
        )
        user_status.pack(anchor="w")

    def on_nav_click(self, action):
        """Handle navigation clicks with smooth transitions"""
        self.set_active_button(action)
        if self.callback:
            self.callback(action)

    def set_active_button(self, button_name):
        """Set active button with visual feedback"""
        self.active_button = button_name

        for name, button in self.nav_buttons.items():
            if name == button_name:
                button.configure(
                    fg_color=self.colors['accent_primary'],
                    text_color=self.colors['text_primary'],
                    hover_color=self.colors['accent_hover']
                )
            else:
                button.configure(
                    fg_color="transparent",
                    text_color=self.colors['text_secondary'],
                    hover_color=self.colors['bg_hover']
                )

    def new_chat(self):
        """Start new chat with animation"""
        if self.callback:
            self.callback("new_chat")

    def load_conversation(self, title):
        """Load specific conversation"""
        if self.callback:
            self.callback(f"load_chat:{title}")


