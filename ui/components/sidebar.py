"""
STARK AI - Sidebar Component
Professional sidebar with icons and navigation
"""

import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageTk
import os

class Sidebar:
    def __init__(self, parent, colors, gui_config, callback):
        self.parent = parent
        self.colors = colors
        self.gui_config = gui_config
        self.callback = callback
        self.icon_size = int(gui_config.get('Icon_size', 32))

        self.setup_sidebar()

    def setup_sidebar(self):
        """Setup sidebar layout and components"""
        # Configure parent frame
        self.parent.grid_rowconfigure(10, weight=1)  # Spacer at bottom

        # Sidebar buttons data
        self.buttons_data = [
            {"name": "chat", "icon": "chat.icon.png", "tooltip": "Chat"},
            {"name": "translate", "icon": "translate.icon.png", "tooltip": "Translate"},
            {"name": "code", "icon": "code.icon.png", "tooltip": "Code Assistant"},
            {"name": "search", "icon": "search.icon.png", "tooltip": "Search"},
            {"name": "automation", "icon": "automation.icon.png", "tooltip": "Automation"},
            {"name": "files", "icon": "files.icon.png", "tooltip": "Files"},
            {"name": "history", "icon": "history.icon.png", "tooltip": "History"},
        ]

        self.buttons = {}
        self.create_buttons()

        # Settings button at bottom
        self.create_settings_button()

    def create_buttons(self):
        """Create sidebar navigation buttons"""
        for i, button_data in enumerate(self.buttons_data):
            button = self.create_sidebar_button(
                button_data["name"],
                button_data["icon"],
                button_data["tooltip"],
                i
            )
            self.buttons[button_data["name"]] = button

    def create_sidebar_button(self, name, icon_name, tooltip, row):
        """Create individual sidebar button"""
        # Create button frame for better control
        button_frame = ctk.CTkFrame(
            self.parent,
            height=60,
            fg_color="transparent"
        )
        button_frame.grid(row=row, column=0, sticky="ew", padx=5, pady=2)
        button_frame.grid_propagate(False)

        # Create the actual button
        button = ctk.CTkButton(
            button_frame,
            text="",
            width=50,
            height=50,
            corner_radius=8,
            fg_color=self.colors['bg_tertiary'],
            hover_color=self.colors['accent_blue'],
            border_width=1,
            border_color=self.colors['border'],
            command=lambda: self.on_button_click(name)
        )
        button.pack(expand=True)

        # Try to load and set icon (placeholder for now since icons will be added manually)
        self.set_button_icon(button, icon_name)

        # Add tooltip (simple implementation)
        self.create_tooltip(button, tooltip)

        return button

    def set_button_icon(self, button, icon_name):
        """Set icon for button (placeholder implementation)"""
        # For now, we'll use text labels since icons will be added manually
        icon_text = {
            "chat.icon.png": "💬",
            "translate.icon.png": "🌐",
            "code.icon.png": "💻",
            "search.icon.png": "🔍",
            "automation.icon.png": "🤖",
            "files.icon.png": "📁",
            "history.icon.png": "📜",
            "settings.icon.png": "⚙️"
        }

        if icon_name in icon_text:
            button.configure(text=icon_text[icon_name], font=("Arial", 16))
        else:
            # Fallback to first letter of name
            button.configure(text=icon_name[0].upper(), font=("Arial", 14, "bold"))

    def create_settings_button(self):
        """Create settings button at bottom of sidebar"""
        settings_frame = ctk.CTkFrame(
            self.parent,
            height=60,
            fg_color="transparent"
        )
        settings_frame.grid(row=11, column=0, sticky="ew", padx=5, pady=2)
        settings_frame.grid_propagate(False)

        settings_button = ctk.CTkButton(
            settings_frame,
            text="",
            width=50,
            height=50,
            corner_radius=8,
            fg_color=self.colors['bg_tertiary'],
            hover_color=self.colors['accent_blue'],
            border_width=1,
            border_color=self.colors['border'],
            command=lambda: self.on_button_click("settings")
        )
        settings_button.pack(expand=True)

        self.set_button_icon(settings_button, "settings.icon.png")
        self.create_tooltip(settings_button, "Settings")

        self.buttons["settings"] = settings_button

    def create_tooltip(self, widget, text):
        """Create simple tooltip for widget"""
        def on_enter(event):
            # Simple tooltip implementation - could be enhanced
            pass

        def on_leave(event):
            pass

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def on_button_click(self, action):
        """Handle button click"""
        # Update button states
        self.update_button_states(action)

        # Call callback
        if self.callback:
            self.callback(action)

    def update_button_states(self, active_button):
        """Update visual state of buttons"""
        for name, button in self.buttons.items():
            if name == active_button:
                button.configure(fg_color=self.colors['accent_blue'])
            else:
                button.configure(fg_color=self.colors['bg_tertiary'])

    def set_active_button(self, button_name):
        """Set active button programmatically"""
        self.update_button_states(button_name)






