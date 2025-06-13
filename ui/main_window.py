"""
STARK AI - Enhanced Main Window Layout
Modern ChatGPT-style GUI with Sidebar, Header, and Content Area
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
        self.controls_visible = True
        self.fade_job = None

        # Modern color scheme inspired by ChatGPT
        self.colors = {
            'bg_primary': '#0f0f0f',        # Very dark background
            'bg_secondary': '#171717',      # Sidebar background
            'bg_tertiary': '#202020',       # Input/card background
            'bg_hover': '#2a2a2a',         # Hover states
            'accent_primary': '#10a37f',    # Green accent (ChatGPT style)
            'accent_hover': '#0e906f',      # Darker green on hover
            'accent_blue': '#3b82f6',       # Blue accent
            'text_primary': '#ececec',      # Primary text
            'text_secondary': '#8e8ea0',    # Secondary text
            'text_muted': '#676767',        # Muted text
            'border': '#303030',            # Border color
            'border_light': '#404040',      # Light border
            'success': '#10a37f',           # Success color
            'warning': '#f59e0b',           # Warning color
            'error': '#ef4444'              # Error color
        }

        # Window configuration
        self.setup_window()

        # Create main layout
        self.create_layout()

        # Initialize components
        self.create_components()

        # Create window controls
        self.create_window_controls()

    def setup_window(self):
        """Configure main window properties"""
        # Set appearance mode and color theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Window properties
        width = int(self.gui_config.get('Window_width', 1200))
        height = int(self.gui_config.get('Window_height', 800))

        self.root.geometry(f"{width}x{height}")
        self.root.title(self.config['Default']['the_tool_name'])
        self.root.configure(bg=self.colors['bg_primary'])

        # Remove default title bar for custom look
        self.root.overrideredirect(True)

        # Make window resizable if configured
        resizable = self.gui_config.get('Resizable', 'yes').lower() == 'yes'

        # Center window on screen
        self.center_window(width, height)

        # Enable window dragging
        self.enable_window_dragging()

    def center_window(self, width, height):
        """Center the window on screen"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def enable_window_dragging(self):
        """Enable dragging the window"""
        self.drag_data = {"x": 0, "y": 0}

        def start_drag(event):
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y

        def do_drag(event):
            x = self.root.winfo_x() + (event.x - self.drag_data["x"])
            y = self.root.winfo_y() + (event.y - self.drag_data["y"])
            self.root.geometry(f"+{x}+{y}")

        # Bind to the topbar frame for dragging
        self.root.bind("<Button-1>", start_drag)
        self.root.bind("<B1-Motion>", do_drag)

    def create_layout(self):
        """Create main layout structure"""
        # Main container with rounded corners effect
        self.main_container = ctk.CTkFrame(
            self.root,
            fg_color=self.colors['bg_primary'],
            corner_radius=0,
            border_width=1,
            border_color=self.colors['border']
        )
        self.main_container.pack(fill="both", expand=True)

        # Configure grid weights
        self.main_container.grid_columnconfigure(1, weight=1)
        self.main_container.grid_rowconfigure(1, weight=1)

        # Custom title bar
        self.title_bar = ctk.CTkFrame(
            self.main_container,
            height=40,
            fg_color=self.colors['bg_secondary'],
            corner_radius=0
        )
        self.title_bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.title_bar.grid_propagate(False)

        # Sidebar frame - wider for modern look
        sidebar_width = int(self.gui_config.get('Sidebar_width', 240))
        self.sidebar_frame = ctk.CTkFrame(
            self.main_container,
            width=sidebar_width,
            fg_color=self.colors['bg_secondary'],
            corner_radius=0
        )
        self.sidebar_frame.grid(row=1, column=0, sticky="nsw")
        self.sidebar_frame.grid_propagate(False)

        # Content area frame
        self.content_frame = ctk.CTkFrame(
            self.main_container,
            fg_color=self.colors['bg_primary'],
            corner_radius=0
        )
        self.content_frame.grid(row=1, column=1, sticky="nsew")

    def create_components(self):
        """Initialize all UI components"""
        # Create title bar content
        self.create_title_bar()

        # Create sidebar
        self.sidebar = Sidebar(
            self.sidebar_frame,
            self.colors,
            self.gui_config,
            self.on_sidebar_action
        )

        # Create content area
        self.content_area = ContentArea(
            self.content_frame,
            self.colors,
            self.gui_config,
            self.config['Default']['the_send_bar_message']
        )

    def create_title_bar(self):
        """Create custom title bar"""
        # Configure title bar
        self.title_bar.grid_columnconfigure(1, weight=1)

        # App icon and name (left side)
        left_frame = ctk.CTkFrame(self.title_bar, fg_color="transparent")
        left_frame.grid(row=0, column=0, sticky="w", padx=15, pady=8)

        # App icon (placeholder)
        icon_label = ctk.CTkLabel(
            left_frame,
            text="⚡",
            font=ctk.CTkFont(size=16),
            text_color=self.colors['accent_primary']
        )
        icon_label.pack(side="left", padx=(0, 8))

        # App name
        app_label = ctk.CTkLabel(
            left_frame,
            text=self.config['Default']['the_tool_name'],
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors['text_primary']
        )
        app_label.pack(side="left")

        # Status indicator (center)
        center_frame = ctk.CTkFrame(self.title_bar, fg_color="transparent")
        center_frame.grid(row=0, column=1, sticky="", padx=10, pady=8)

        self.status_dot = ctk.CTkLabel(
            center_frame,
            text="●",
            font=ctk.CTkFont(size=12),
            text_color=self.colors['success']
        )
        self.status_dot.pack(side="left", padx=(0, 5))

        self.status_text = ctk.CTkLabel(
            center_frame,
            text="Online",
            font=ctk.CTkFont(size=11),
            text_color=self.colors['text_secondary']
        )
        self.status_text.pack(side="left")

        # Enable dragging on title bar
        def start_drag(event):
            self.drag_data = {"x": event.x_root, "y": event.y_root}

        def do_drag(event):
            x = event.x_root - self.drag_data["x"]
            y = event.y_root - self.drag_data["y"]
            new_x = self.root.winfo_x() + x
            new_y = self.root.winfo_y() + y
            self.root.geometry(f"+{new_x}+{new_y}")
            self.drag_data = {"x": event.x_root, "y": event.y_root}

        self.title_bar.bind("<Button-1>", start_drag)
        self.title_bar.bind("<B1-Motion>", do_drag)
        left_frame.bind("<Button-1>", start_drag)
        left_frame.bind("<B1-Motion>", do_drag)
        center_frame.bind("<Button-1>", start_drag)
        center_frame.bind("<B1-Motion>", do_drag)

    def create_window_controls(self):
        """Create window control buttons (minimize, maximize, close)"""
        self.controls_frame = ctk.CTkFrame(
            self.title_bar,
            fg_color="transparent"
        )
        self.controls_frame.grid(row=0, column=2, sticky="e", padx=10, pady=8)

        # Minimize button
        self.minimize_btn = ctk.CTkButton(
            self.controls_frame,
            text="−",
            width=30,
            height=25,
            corner_radius=4,
            fg_color="transparent",
            hover_color=self.colors['bg_hover'],
            font=ctk.CTkFont(size=14),
            text_color=self.colors['text_secondary'],
            command=self.minimize_window
        )
        self.minimize_btn.pack(side="left", padx=1)

        # Maximize button
        self.maximize_btn = ctk.CTkButton(
            self.controls_frame,
            text="□",
            width=30,
            height=25,
            corner_radius=4,
            fg_color="transparent",
            hover_color=self.colors['bg_hover'],
            font=ctk.CTkFont(size=12),
            text_color=self.colors['text_secondary'],
            command=self.maximize_window
        )
        self.maximize_btn.pack(side="left", padx=1)

        # Close button
        self.close_btn = ctk.CTkButton(
            self.controls_frame,
            text="×",
            width=30,
            height=25,
            corner_radius=4,
            fg_color="transparent",
            hover_color=self.colors['error'],
            font=ctk.CTkFont(size=16),
            text_color=self.colors['text_secondary'],
            command=self.close_window
        )
        self.close_btn.pack(side="left", padx=1)

        # Initially hide controls
        self.hide_window_controls()

    def show_window_controls(self):
        """Show window controls with fade effect"""
        if not self.controls_visible:
            self.controls_visible = True
            self.animate_controls_fade(True)

    def hide_window_controls(self):
        """Hide window controls with fade effect"""
        if self.controls_visible:
            self.controls_visible = False
            self.animate_controls_fade(False)

    def animate_controls_fade(self, show=True):
        """Animate fade in/out of controls"""
        if self.fade_job:
            self.root.after_cancel(self.fade_job)

        if show:
            self.controls_frame.grid()
            # Simple show - could be enhanced with alpha animation
        else:
            # Simple hide - could be enhanced with alpha animation
            self.fade_job = self.root.after(100, lambda: self.controls_frame.grid_remove())

    def on_sidebar_action(self, action):
        """Handle sidebar button clicks"""
        self.content_area.set_mode(action)

    def minimize_window(self):
        """Minimize window"""
        self.root.iconify()

    def maximize_window(self):
        """Toggle maximize window"""
        # Since we're using overrideredirect, we need to handle maximize manually
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        current_width = self.root.winfo_width()
        current_height = self.root.winfo_height()

        if current_width >= screen_width * 0.9 and current_height >= screen_height * 0.9:
            # Restore to normal size
            width = int(self.gui_config.get('Window_width', 1200))
            height = int(self.gui_config.get('Window_height', 800))
            self.center_window(width, height)
        else:
            # Maximize
            self.root.geometry(f"{screen_width}x{screen_height}+0+0")

    def close_window(self):
        """Close window"""
        self.root.quit()

    def update_status(self, status_text, is_online=True):
        """Update connection status"""
        self.status_text.configure(text=status_text)
        if is_online:
            self.status_dot.configure(text_color=self.colors['success'])
        else:
            self.status_dot.configure(text_color=self.colors['error'])







