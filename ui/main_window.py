"""
STARK AI - Main Window Layout
Professional GUI with Sidebar, Topbar, and Content Area
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import os
from pathlib import Path
import configparser

from .components.sidebar import Sidebar
from .components.topbar import Topbar
from .components.content_area import ContentArea

class MainWindow:
    def __init__(self, root, config):
        """Initialize main window layout"""
        self.root = root
        self.config = config
        self.gui_config = config['GUI']

        # Color scheme
        self.colors = {
            'bg_primary': '#1a1a1a',      # Dark background
            'bg_secondary': '#2d2d2d',    # Sidebar/panel background
            'bg_tertiary': '#3d3d3d',     # Component background
            'accent_blue': '#0078d4',     # Primary blue accent
            'accent_light': '#106ebe',    # Light blue accent
            'text_primary': '#ffffff',    # Primary text
            'text_secondary': '#b3b3b3',  # Secondary text
            'border': '#404040',          # Border color
            'hover': '#404040'            # Hover state
        }

        # Window configuration
        self.setup_window()

        # Create main layout
        self.create_layout()

        # Initialize components
        self.create_components()

    def setup_window(self):
        """Configure main window properties"""
        # Set appearance mode and color theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Window properties
        width = int(self.gui_config.get('Window_width', 1280))
        height = int(self.gui_config.get('Window_height', 720))

        self.root.geometry(f"{width}x{height}")
        self.root.title(self.config['Default']['the_tool_name'])
        self.root.configure(bg=self.colors['bg_primary'])

        # Make window resizable if configured
        resizable = self.gui_config.get('Resizable', 'yes').lower() == 'yes'
        self.root.resizable(resizable, resizable)

        # Center window on screen
        self.center_window(width, height)

    def center_window(self, width, height):
        """Center the window on screen"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def create_layout(self):
        """Create main layout structure"""
        # Main container
        self.main_container = ctk.CTkFrame(
            self.root,
            fg_color=self.colors['bg_primary'],
            corner_radius=0
        )
        self.main_container.pack(fill="both", expand=True)

        # Configure grid weights
        self.main_container.grid_columnconfigure(1, weight=1)
        self.main_container.grid_rowconfigure(1, weight=1)

        # Sidebar frame
        sidebar_width = int(self.gui_config.get('Sidebar_width', 80))
        self.sidebar_frame = ctk.CTkFrame(
            self.main_container,
            width=sidebar_width,
            fg_color=self.colors['bg_secondary'],
            corner_radius=0
        )
        self.sidebar_frame.grid(row=0, column=0, rowspan=2, sticky="nsw")
        self.sidebar_frame.grid_propagate(False)

        # Topbar frame
        topbar_height = int(self.gui_config.get('Topbar_height', 60))
        self.topbar_frame = ctk.CTkFrame(
            self.main_container,
            height=topbar_height,
            fg_color=self.colors['bg_secondary'],
            corner_radius=0
        )
        self.topbar_frame.grid(row=0, column=1, sticky="ew")
        self.topbar_frame.grid_propagate(False)

        # Content area frame
        self.content_frame = ctk.CTkFrame(
            self.main_container,
            fg_color=self.colors['bg_primary'],
            corner_radius=0
        )
        self.content_frame.grid(row=1, column=1, sticky="nsew", padx=1, pady=1)

    def create_components(self):
        """Initialize all UI components"""
        # Create sidebar
        self.sidebar = Sidebar(
            self.sidebar_frame,
            self.colors,
            self.gui_config,
            self.on_sidebar_action
        )

        # Create topbar
        self.topbar = Topbar(
            self.topbar_frame,
            self.colors,
            self.gui_config,
            self.config['Default']['the_tool_name']
        )

        # Create content area
        self.content_area = ContentArea(
            self.content_frame,
            self.colors,
            self.gui_config,
            self.config['Default']['the_send_bar_message']
        )

    def on_sidebar_action(self, action):
        """Handle sidebar button clicks"""
        # This will be implemented to handle different sidebar actions
        # For now, just update the content area
        self.content_area.set_mode(action)

    def get_icon_path(self, icon_name):
        """Get full path to icon file"""
        icons_folder = self.config['Paths']['Icons_folder']
        return os.path.join(icons_folder, icon_name)

    def apply_glassmorphism(self, widget, alpha=0.8):
        """Apply glassmorphism effect to widget (placeholder for future implementation)"""
        # This would require additional libraries or custom implementation
        # For now, we'll use subtle transparency and blur-like effects with colors
        pass







