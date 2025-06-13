"""
STARK AI - Enhanced Main Application
Modern ChatGPT-style GUI with advanced features and F11 fullscreen support
"""

import customtkinter as ctk
import tkinter as tk
import configparser
import os
from pathlib import Path
from sidebar import Sidebar
from content_area import ContentArea

class StarkAI:
    def __init__(self):
        """Initialize STARK AI application"""
        self.root = ctk.CTk()
        self.is_fullscreen = False
        self.is_maximized = False
        self.normal_geometry = None
        self.mouse_timer = None
        self.controls_visible = False
        self.fade_alpha = 0.0

        # Load configuration
        self.load_config()

        # Setup window
        self.setup_window()

        # Create UI
        self.create_interface()

        # Bind events
        self.bind_events()

    def load_config(self):
        """Load configuration from config.ini"""
        self.config = configparser.ConfigParser()
        config_path = Path("config/config.ini")

        if config_path.exists():
            self.config.read(config_path)
        else:
            # Default configuration
            self.config['Window'] = {
                'Window_width': '1280',
                'Window_height': '720',
                'Sidebar_width': '280',
                'Corner_radius': '12'
            }
            self.config['Fonts'] = {
                'Font_family': 'Segoe UI',
                'Font_size': '14'
            }
            self.config['Theme'] = {
                'Mode': 'dark'
            }
            self.config['Default'] = {
                'the_tool_name': 'STARK AI',
                'the_send_bar_message': 'Message STARK AI...'
            }

        # Enhanced color scheme inspired by ChatGPT and modern design
        self.colors = {
            'bg_primary': '#0d1117',        # GitHub dark background
            'bg_secondary': '#161b22',      # Sidebar background
            'bg_tertiary': '#21262d',       # Input/card background
            'bg_quaternary': '#30363d',     # Elevated surfaces
            'bg_hover': '#262c36',          # Hover states
            'accent_primary': '#238636',    # GitHub green
            'accent_secondary': '#1f6feb',  # GitHub blue
            'accent_hover': '#2ea043',      # Hover green
            'text_primary': '#f0f6fc',      # Primary text
            'text_secondary': '#8b949e',    # Secondary text
            'text_muted': '#6e7681',        # Muted text
            'border': '#30363d',            # Border color
            'border_muted': '#21262d',      # Subtle borders
            'success': '#238636',           # Success color
            'warning': '#d29922',           # Warning color
            'error': '#f85149',             # Error color
            'shadow': 'rgba(0, 0, 0, 0.3)'  # Shadow color
        }

    def setup_window(self):
        """Configure main window properties"""
        # Set appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Window properties
        width = int(self.config['Window'].get('Window_width', 1280))
        height = int(self.config['Window'].get('Window_height', 720))

        self.root.geometry(f"{width}x{height}")
        self.root.title(self.config['Default'].get('the_tool_name', 'STARK AI'))
        self.root.configure(fg_color=self.colors['bg_primary'])

        # Remove default title bar
        self.root.overrideredirect(True)

        # Center window
        self.center_window(width, height)

        # Store normal geometry
        self.normal_geometry = f"{width}x{height}"

    def center_window(self, width, height):
        """Center window on screen"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def create_interface(self):
        """Create the main interface"""
        # Main container
        self.main_container = ctk.CTkFrame(
            self.root,
            fg_color=self.colors['bg_primary'],
            corner_radius=0
        )
        self.main_container.pack(fill="both", expand=True)

        # Configure grid
        self.main_container.grid_columnconfigure(1, weight=1)
        self.main_container.grid_rowconfigure(1, weight=1)

        # Create title bar
        self.create_title_bar()

        # Create sidebar
        self.create_sidebar()

        # Create content area
        self.create_content_area()

        # Create window controls (initially hidden)
        self.create_window_controls()

    def create_title_bar(self):
        """Create custom title bar"""
        self.title_bar = ctk.CTkFrame(
            self.main_container,
            height=50,
            fg_color=self.colors['bg_secondary'],
            corner_radius=0
        )
        self.title_bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.title_bar.grid_propagate(False)
        self.title_bar.grid_columnconfigure(1, weight=1)

        # Left section - App branding
        left_frame = ctk.CTkFrame(self.title_bar, fg_color="transparent")
        left_frame.grid(row=0, column=0, sticky="w", padx=20, pady=12)

        # App icon
        icon_label = ctk.CTkLabel(
            left_frame,
            text="⚡",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=self.colors['accent_primary']
        )
        icon_label.pack(side="left", padx=(0, 12))

        # App name
        app_label = ctk.CTkLabel(
            left_frame,
            text=self.config['Default'].get('the_tool_name', 'STARK AI'),
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors['text_primary']
        )
        app_label.pack(side="left")

        # Center section - Status
        center_frame = ctk.CTkFrame(self.title_bar, fg_color="transparent")
        center_frame.grid(row=0, column=1, sticky="", padx=10, pady=12)

        self.status_indicator = ctk.CTkLabel(
            center_frame,
            text="●",
            font=ctk.CTkFont(size=14),
            text_color=self.colors['success']
        )
        self.status_indicator.pack(side="left", padx=(0, 8))

        self.status_label = ctk.CTkLabel(
            center_frame,
            text="Ready",
            font=ctk.CTkFont(size=12),
            text_color=self.colors['text_secondary']
        )
        self.status_label.pack(side="left")

        # Enable dragging
        self.enable_title_bar_dragging()

    def create_sidebar(self):
        """Create sidebar"""
        sidebar_width = int(self.config['Window'].get('Sidebar_width', 280))

        self.sidebar_frame = ctk.CTkFrame(
            self.main_container,
            width=sidebar_width,
            fg_color=self.colors['bg_secondary'],
            corner_radius=0
        )
        self.sidebar_frame.grid(row=1, column=0, sticky="nsw")
        self.sidebar_frame.grid_propagate(False)

        # Initialize sidebar component
        self.sidebar = Sidebar(
            self.sidebar_frame,
            self.colors,
            self.config['Window'],
            self.on_sidebar_action
        )

    def create_content_area(self):
        """Create content area"""
        self.content_frame = ctk.CTkFrame(
            self.main_container,
            fg_color=self.colors['bg_primary'],
            corner_radius=0
        )
        self.content_frame.grid(row=1, column=1, sticky="nsew")

        # Initialize content area component
        self.content_area = ContentArea(
            self.content_frame,
            self.colors,
            self.config['Window'],
            self.config['Default'].get('the_send_bar_message', 'Message STARK AI...')
        )

    def create_window_controls(self):
        """Create window control buttons"""
        self.controls_frame = ctk.CTkFrame(
            self.title_bar,
            fg_color="transparent"
        )
        self.controls_frame.grid(row=0, column=2, sticky="e", padx=15, pady=12)

        # Minimize button
        self.minimize_btn = ctk.CTkButton(
            self.controls_frame,
            text="−",
            width=32,
            height=28,
            corner_radius=6,
            fg_color="transparent",
            hover_color=self.colors['bg_hover'],
            font=ctk.CTkFont(size=16),
            text_color=self.colors['text_secondary'],
            command=self.minimize_window
        )
        self.minimize_btn.pack(side="left", padx=2)

        # Maximize button
        self.maximize_btn = ctk.CTkButton(
            self.controls_frame,
            text="□",
            width=32,
            height=28,
            corner_radius=6,
            fg_color="transparent",
            hover_color=self.colors['bg_hover'],
            font=ctk.CTkFont(size=14),
            text_color=self.colors['text_secondary'],
            command=self.toggle_maximize
        )
        self.maximize_btn.pack(side="left", padx=2)

        # Close button
        self.close_btn = ctk.CTkButton(
            self.controls_frame,
            text="×",
            width=32,
            height=28,
            corner_radius=6,
            fg_color="transparent",
            hover_color=self.colors['error'],
            font=ctk.CTkFont(size=18),
            text_color=self.colors['text_secondary'],
            command=self.close_window
        )
        self.close_btn.pack(side="left", padx=2)

        # Initially hide controls
        self.hide_window_controls()

    def enable_title_bar_dragging(self):
        """Enable window dragging via title bar"""
        def start_drag(event):
            self.drag_data = {"x": event.x_root, "y": event.y_root}

        def do_drag(event):
            if not self.is_fullscreen:
                x = event.x_root - self.drag_data["x"]
                y = event.y_root - self.drag_data["y"]
                new_x = self.root.winfo_x() + x
                new_y = self.root.winfo_y() + y
                self.root.geometry(f"+{new_x}+{new_y}")
                self.drag_data = {"x": event.x_root, "y": event.y_root}

        self.title_bar.bind("<Button-1>", start_drag)
        self.title_bar.bind("<B1-Motion>", do_drag)

    def bind_events(self):
        """Bind keyboard and mouse events"""
        # F11 for fullscreen toggle
        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<KeyPress-F11>", self.toggle_fullscreen)

        # Mouse motion for showing/hiding controls
        self.root.bind("<Motion>", self.on_mouse_motion)

        # Focus events
        self.root.focus_set()

    def toggle_fullscreen(self, event=None):
        """Toggle fullscreen mode"""
        if self.is_fullscreen:
            self.exit_fullscreen()
        else:
            self.enter_fullscreen()

    def enter_fullscreen(self):
        """Enter fullscreen mode"""
        if not self.is_fullscreen:
            # Store current geometry
            self.normal_geometry = self.root.geometry()

            # Get screen dimensions
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()

            # Set fullscreen
            self.root.geometry(f"{screen_width}x{screen_height}+0+0")
            self.is_fullscreen = True

            # Hide window controls permanently in fullscreen
            self.hide_window_controls()

            # Update status
            self.update_status("Fullscreen Mode - Press F11 to exit")

    def exit_fullscreen(self):
        """Exit fullscreen mode"""
        if self.is_fullscreen:
            # Restore normal geometry
            if self.normal_geometry:
                self.root.geometry(self.normal_geometry)
            else:
                width = int(self.config['Window'].get('Window_width', 1280))
                height = int(self.config['Window'].get('Window_height', 720))
                self.center_window(width, height)

            self.is_fullscreen = False

            # Update status
            self.update_status("Ready")

    def on_mouse_motion(self, event):
        """Handle mouse motion for showing/hiding controls"""
        if not self.is_fullscreen:
            # Get mouse position relative to window
            x, y = event.x_root - self.root.winfo_rootx(), event.y_root - self.root.winfo_rooty()

            # Show controls if mouse is in top-right corner
            if x > self.root.winfo_width() - 150 and y < 50:
                self.show_window_controls()
                self.schedule_hide_controls()
            elif y > 50:  # Hide if mouse moves away from title bar area
                self.schedule_hide_controls()

    def schedule_hide_controls(self):
        """Schedule hiding of window controls"""
        if self.mouse_timer:
            self.root.after_cancel(self.mouse_timer)

        self.mouse_timer = self.root.after(2000, self.hide_window_controls)

    def show_window_controls(self):
        """Show window controls with smooth animation"""
        if not self.controls_visible and not self.is_fullscreen:
            self.controls_visible = True
            self.controls_frame.grid()
            self.animate_controls_fade_in()

    def hide_window_controls(self):
        """Hide window controls with smooth animation"""
        if self.controls_visible:
            self.controls_visible = False
            self.animate_controls_fade_out()

    def animate_controls_fade_in(self):
        """Animate controls fade in"""
        if self.fade_alpha < 1.0:
            self.fade_alpha = min(1.0, self.fade_alpha + 0.1)
            # Simple opacity simulation by adjusting colors
            self.root.after(20, self.animate_controls_fade_in)

    def animate_controls_fade_out(self):
        """Animate controls fade out"""
        if self.fade_alpha > 0.0:
            self.fade_alpha = max(0.0, self.fade_alpha - 0.1)
            self.root.after(20, self.animate_controls_fade_out)
        else:
            self.controls_frame.grid_remove()

    def minimize_window(self):
        """Minimize window"""
        self.root.iconify()

    def toggle_maximize(self):
        """Toggle maximize window"""
        if not self.is_fullscreen:
            if self.is_maximized:
                # Restore
                if self.normal_geometry:
                    self.root.geometry(self.normal_geometry)
                self.is_maximized = False
                self.maximize_btn.configure(text="□")
            else:
                # Maximize
                self.normal_geometry = self.root.geometry()
                screen_width = self.root.winfo_screenwidth()
                screen_height = self.root.winfo_screenheight()
                self.root.geometry(f"{screen_width}x{screen_height-40}+0+0")  # Leave space for taskbar
                self.is_maximized = True
                self.maximize_btn.configure(text="❐")

    def close_window(self):
        """Close application"""
        self.root.quit()
        self.root.destroy()

    def on_sidebar_action(self, action):
        """Handle sidebar actions"""
        if hasattr(self.content_area, 'set_mode'):
            self.content_area.set_mode(action)

        # Update status based on action
        action_names = {
            "chat": "Chat Mode",
            "translate": "Translation Mode",
            "search": "Search Mode",
            "automation": "Automation Mode",
            "new_chat": "New Chat Started"
        }

        status = action_names.get(action, "Ready")
        self.update_status(status)

    def update_status(self, status_text):
        """Update status display"""
        self.status_label.configure(text=status_text)

    def run(self):
        """Start the application"""
        self.root.mainloop()


def main():
    """Main entry point"""
    app = StarkAI()
    app.run()


if __name__ == "__main__":
    main()


