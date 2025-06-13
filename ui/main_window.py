"""
STARK AI - Main Window Layout
Professional GUI with Sidebar, Topbar, and Content Area
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import os
from pathlib import Path

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
            'hover': '#4a4a4a'           # Hover state
        }

        self.setup_layout()

    def setup_layout(self):
        """Setup the main window layout"""
        # Configure root
        self.root.configure(fg_color=self.colors['bg_primary'])

        # Create main container
        self.main_container = ctk.CTkFrame(
            self.root,
            fg_color=self.colors['bg_primary'],
            corner_radius=0
        )
        self.main_container.pack(fill="both", expand=True)

        # Setup grid weights
        self.main_container.grid_rowconfigure(1, weight=1)
        self.main_container.grid_columnconfigure(1, weight=1)

        # Create layout components
        self.create_topbar()
        self.create_sidebar()
        self.create_content_area()

    def create_topbar(self):
        """Create the top bar"""
        topbar_height = int(self.gui_config.get('Topbar_height', '60'))

        self.topbar = Topbar(
            self.main_container,
            height=topbar_height,
            colors=self.colors,
            config=self.config
        )
        self.topbar.grid(row=0, column=0, columnspan=2, sticky="ew")

    def create_sidebar(self):
        """Create the sidebar"""
        sidebar_width = int(self.gui_config.get('Sidebar_width', '80'))

        self.sidebar = Sidebar(
            self.main_container,
            width=sidebar_width,
            colors=self.colors,
            config=self.config
        )
        self.sidebar.grid(row=1, column=0, sticky="nsw")

    def create_content_area(self):
        """Create the main content area"""
        self.content_area = ContentArea(
            self.main_container,
            colors=self.colors,
            config=self.config,
            sidebar=self.sidebar
        )
        self.content_area.grid(row=1, column=1, sticky="nsew", padx=(1, 0))

    def get_icon_path(self, icon_name):
        """Get the full path to an icon"""
        icons_folder = self.config['Paths'].get('Icons_folder', './assets/icons/')
        return os.path.join(icons_folder, icon_name)

    def update_theme(self, theme):
        """Update the application theme"""
        if theme == "light":
            self.colors.update({
                'bg_primary': '#ffffff',
                'bg_secondary': '#f5f5f5',
                'bg_tertiary': '#e8e8e8',
                'text_primary': '#000000',
                'text_secondary': '#666666',
                'border': '#d0d0d0',
                'hover': '#e0e0e0'
            })
        else:
            self.colors.update({
                'bg_primary': '#1a1a1a',
                'bg_secondary': '#2d2d2d',
                'bg_tertiary': '#3d3d3d',
                'text_primary': '#ffffff',
                'text_secondary': '#b3b3b3',
                'border': '#404040',
                'hover': '#4a4a4a'
            })

        # Refresh all components
        self.refresh_components()

    def refresh_components(self):
        """Refresh all UI components with new colors"""
        self.topbar.update_colors(self.colors)
        self.sidebar.update_colors(self.colors)
        self.content_area.update_colors(self.colors)





