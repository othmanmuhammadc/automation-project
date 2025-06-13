"""
STARK AI - Topbar Component
Professional topbar with app name and controls
"""

import customtkinter as ctk
import tkinter as tk
from datetime import datetime

class Topbar:
    def __init__(self, parent, colors, gui_config, app_name):
        self.parent = parent
        self.colors = colors
        self.gui_config = gui_config
        self.app_name = app_name

        self.setup_topbar()

    def setup_topbar(self):
        """Setup topbar layout and components"""
        # Configure parent frame
        self.parent.grid_columnconfigure(1, weight=1)

        # Left section - App name and logo
        self.left_frame = ctk.CTkFrame(
            self.parent,
            fg_color="transparent"
        )
        self.left_frame.grid(row=0, column=0, sticky="w", padx=15, pady=10)

        # App name label
        self.app_label = ctk.CTkLabel(
            self.left_frame,
            text=self.app_name,
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.colors['text_primary']
        )
        self.app_label.pack(side="left")

        # Center section - Current mode/status
        self.center_frame = ctk.CTkFrame(
            self.parent,
            fg_color="transparent"
        )
        self.center_frame.grid(row=0, column=1, sticky="", padx=10, pady=10)

        self.status_label = ctk.CTkLabel(
            self.center_frame,
            text="Assistant Mode",
            font=ctk.CTkFont(size=12),
            text_color=self.colors['text_secondary']
        )
        self.status_label.pack()

        # Right section - Controls and info
        self.right_frame = ctk.CTkFrame(
            self.parent,
            fg_color="transparent"
        )
        self.right_frame.grid(row=0, column=2, sticky="e", padx=15, pady=10)

        # Connection status indicator
        self.status_indicator = ctk.CTkLabel(
            self.right_frame,
            text="●",
            font=ctk.CTkFont(size=16),
            text_color=self.colors['accent_blue']
        )
        self.status_indicator.pack(side="right", padx=(10, 0))

        # Status text
        self.connection_label = ctk.CTkLabel(
            self.right_frame,
            text="Online",
            font=ctk.CTkFont(size=11),
            text_color=self.colors['text_secondary']
        )
        self.connection_label.pack(side="right")

        # Minimize/Maximize/Close buttons (optional)
        self.create_window_controls()

    def create_window_controls(self):
        """Create window control buttons"""
        controls_frame = ctk.CTkFrame(
            self.right_frame,
            fg_color="transparent"
        )
        controls_frame.pack(side="right", padx=(0, 10))

        # Minimize button
        minimize_btn = ctk.CTkButton(
            controls_frame,
            text="−",
            width=25,
            height=25,
            corner_radius=4,
            fg_color=self.colors['bg_tertiary'],
            hover_color=self.colors['hover'],
            font=ctk.CTkFont(size=12),
            command=self.minimize_window
        )
        minimize_btn.pack(side="left", padx=2)

        # Maximize button
        maximize_btn = ctk.CTkButton(
            controls_frame,
            text="□",
            width=25,
            height=25,
            corner_radius=4,
            fg_color=self.colors['bg_tertiary'],
            hover_color=self.colors['hover'],
            font=ctk.CTkFont(size=10),
            command=self.maximize_window
        )
        maximize_btn.pack(side="left", padx=2)

        # Close button
        close_btn = ctk.CTkButton(
            controls_frame,
            text="×",
            width=25,
            height=25,
            corner_radius=4,
            fg_color="#d13438",
            hover_color="#b12125",
            font=ctk.CTkFont(size=14),
            command=self.close_window
        )
        close_btn.pack(side="left", padx=2)

    def update_status(self, status_text, mode_text=None):
        """Update status and mode text"""
        if mode_text:
            self.status_label.configure(text=mode_text)

        self.connection_label.configure(text=status_text)

    def set_connection_status(self, online=True):
        """Set connection status indicator"""
        if online:
            self.status_indicator.configure(text_color=self.colors['accent_blue'])
            self.connection_label.configure(text="Online")
        else:
            self.status_indicator.configure(text_color="#d13438")
            self.connection_label.configure(text="Offline")

    def minimize_window(self):
        """Minimize window"""
        self.parent.winfo_toplevel().iconify()

    def maximize_window(self):
        """Toggle maximize window"""
        root = self.parent.winfo_toplevel()
        if root.state() == 'zoomed':
            root.state('normal')
        else:
            root.state('zoomed')

    def close_window(self):
        """Close window"""
        self.parent.winfo_toplevel().quit()






