"""
STARK AI - Sidebar Component
Professional sidebar with icons and smooth animations
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import os
from PIL import Image, ImageTk
from pathlib import Path

class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, width, colors, config):
        """Initialize sidebar component"""
        super().__init__(
            parent,
            width=width,
            fg_color=colors['bg_secondary'],
            corner_radius=0
        )

        self.parent = parent
        self.width = width
        self.colors = colors
        self.config = config
        self.gui_config = config['GUI']

        # Sidebar state
        self.expanded = False
        self.expanded_width = 250
        self.collapsed_width = width

        # Icon configuration
        self.icon_size = int(self.gui_config.get('Icon_size', '32'))

        # Active button tracking
        self.active_button = None
        self.buttons = {}

        self.setup_sidebar()

    def setup_sidebar(self):
        """Setup sidebar layout and components"""
        # Configure grid
        self.grid_rowconfigure(0, weight=1)  # Main buttons area
        self.grid_rowconfigure(1, weight=0)  # Bottom area

        # Create main buttons frame
        self.buttons_frame = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        self.buttons_frame.grid(row=0, column=0, sticky="new", padx=5, pady=5)

        # Create bottom frame for settings
        self.bottom_frame = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        self.bottom_frame.grid(row=1, column=0, sticky="sew", padx=5, pady=5)

        # Create sidebar buttons
        self.create_buttons()

        # Create expand/collapse toggle
        self.create_toggle_button()

    def create_buttons(self):
        """Create main sidebar buttons"""
        button_configs = [
            {
                'name': 'chat',
                'icon': 'chat.icon.png',
                'tooltip': 'AI Chat Assistant',
                'action': 'show_chat'
            },
            {
                'name': 'translate',
                'icon': 'translate.icon.png',
                'tooltip': 'Language Translation',
                'action': 'show_translate'
            },
            {
                'name': 'code',
                'icon': 'code.icon.png',
                'tooltip': 'Code Assistant',
                'action': 'show_code'
            },
            {
                'name': 'automation',
                'icon': 'automation.icon.png',
                'tooltip': 'Browser Automation',
                'action': 'show_automation'
            },
            {
                'name': 'search',
                'icon': 'search.icon.png',
                'tooltip': 'Web Search',
                'action': 'show_search'
            },
            {
                'name': 'tasks',
                'icon': 'tasks.icon.png',
                'tooltip': 'Task Manager',
                'action': 'show_tasks'
            }
        ]

        for i, btn_config in enumerate(button_configs):
            button = self.create_sidebar_button(
                btn_config['name'],
                btn_config['icon'],
                btn_config['tooltip'],
                btn_config['action'],
                row=i
            )
            self.buttons[btn_config['name']] = button

        # Set chat as default active
        if 'chat' in self.buttons:
            self.set_active_button('chat')

    def create_sidebar_button(self, name, icon_name, tooltip, action, row):
        """Create individual sidebar button"""
        # Create button frame
        button_frame = ctk.CTkFrame(
            self.buttons_frame,
            height=50,
            fg_color="transparent"
        )
        button_frame.grid(row=row, column=0, sticky="ew", pady=2)
        button_frame.grid_columnconfigure(0, weight=1)

        # Create the button
        button = ctk.CTkButton(
            button_frame,
            text="",
            width=self.collapsed_width - 10,
            height=45,
            fg_color="transparent",
            hover_color=self.colors['hover'],
            corner_radius=8,
            command=lambda: self.button_clicked(name, action)
        )
        button.grid(row=0, column=0, sticky="ew", padx=2)

        # Try to load icon
        icon_path = self.get_icon_path(icon_name)
        if os.path.exists(icon_path):
            try:
                # Load and resize icon
                icon_image = Image.open(icon_path)
                icon_image = icon_image.resize((self.icon_size, self.icon_size), Image.Resampling.LANCZOS)
                icon_photo = ImageTk.PhotoImage(icon_image)

                # Configure button with icon
                button.configure(image=icon_photo)
                button.image = icon_photo  # Keep a reference
            except Exception as e:
                print(f"Warning: Could not load icon {icon_name}: {e}")
                # Fallback to text
                button.configure(text=name.capitalize()[:2])
        else:
            # Fallback to text if icon doesn't exist
            button.configure(text=name.capitalize()[:2])

        # Store button reference with additional properties
        button.name = name
        button.action = action
        button.tooltip = tooltip
        button.is_active = False

        # Add tooltip (simple implementation)
        self.create_tooltip(button, tooltip)

        return button

    def create_toggle_button(self):
        """Create expand/collapse toggle button"""
        self.toggle_btn = ctk.CTkButton(
            self.bottom_frame,
            text="⋮",
            width=self.collapsed_width - 10,
            height=35,
            fg_color="transparent",
            hover_color=self.colors['hover'],
            corner_radius=8,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.toggle_sidebar
        )
        self.toggle_btn.grid(row=0, column=0, sticky="ew", padx=2, pady=2)

        # Settings button
        settings_icon_path = self.get_icon_path('settings.icon.png')
        settings_btn = ctk.CTkButton(
            self.bottom_frame,
            text="⚙",
            width=self.collapsed_width - 10,
            height=35,
            fg_color="transparent",
            hover_color=self.colors['hover'],
            corner_radius=8,
            font=ctk.CTkFont(size=14),
            command=self.show_settings
        )
        settings_btn.grid(row=1, column=0, sticky="ew", padx=2, pady=2)

        if os.path.exists(settings_icon_path):
            try:
                settings_image = Image.open(settings_icon_path)
                settings_image = settings_image.resize((20, 20), Image.Resampling.LANCZOS)
                settings_photo = ImageTk.PhotoImage(settings_image)
                settings_btn.configure(image=settings_photo, text="")
                settings_btn.image = settings_photo
            except Exception as e:
                print(f"Warning: Could not load settings icon: {e}")

    def get_icon_path(self, icon_name):
        """Get full path to icon file"""
        icons_folder = self.config['Paths'].get('Icons_folder', './assets/icons/')
        return os.path.join(icons_folder, icon_name)

    def button_clicked(self, name, action):
        """Handle button click"""
        self.set_active_button(name)

        # Trigger action in content area
        if hasattr(self.parent.master, 'content_area'):
            content_area = self.parent.master.content_area
            if hasattr(content_area, action):
                getattr(content_area, action)()

        print(f"🔘 Sidebar action: {action}")

    def set_active_button(self, name):
        """Set active button state"""
        # Reset all buttons
        for btn_name, button in self.buttons.items():
            if hasattr(button, 'is_active'):
                button.is_active = False
                button.configure(fg_color="transparent")

        # Set active button
        if name in self.buttons:
            button = self.buttons[name]
            button.is_active = True
            button.configure(fg_color=self.colors['accent_blue'])
            self.active_button = name

    def toggle_sidebar(self):
        """Toggle sidebar expanded/collapsed state"""
        if self.expanded:
            self.collapse_sidebar()
        else:
            self.expand_sidebar()

    def expand_sidebar(self):
        """Expand sidebar to show labels"""
        self.expanded = True
        self.configure(width=self.expanded_width)

        # Update button widths and add labels
        for button in self.buttons.values():
            button.configure(width=self.expanded_width - 20)
            # Add text labels when expanded
            if hasattr(button, 'name'):
                if not button.cget('text'):  # Only if no text currently
                    button.configure(text=button.name.capitalize())

        self.toggle_btn.configure(text="◀")

    def collapse_sidebar(self):
        """Collapse sidebar to show only icons"""
        self.expanded = False
        self.configure(width=self.collapsed_width)

        # Update button widths and remove labels
        for button in self.buttons.values():
            button.configure(width=self.collapsed_width - 10)
            # Remove text labels when collapsed (keep only if no icon)
            if hasattr(button, 'image') and button.image:
                button.configure(text="")

        self.toggle_btn.configure(text="⋮")

    def show_settings(self):
        """Show settings dialog"""
        print("⚙️ Opening settings...")
        # This will be implemented later

    def create_tooltip(self, widget, text):
        """Create simple tooltip for widget"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.configure(bg='black')

            label = tk.Label(
                tooltip,
                text=text,
                bg='black',
                fg='white',
                font=('Arial', 10),
                padx=5,
                pady=2
            )
            label.pack()

            # Position tooltip
            x = widget.winfo_rootx() + widget.winfo_width() + 10
            y = widget.winfo_rooty() + widget.winfo_height() // 2
            tooltip.geometry(f"+{x}+{y}")

            widget.tooltip = tooltip

        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def update_colors(self, colors):
        """Update component colors"""
        self.colors = colors
        self.configure(fg_color=colors['bg_secondary'])

        # Update button colors
        for button in self.buttons.values():
            if hasattr(button, 'is_active') and button.is_active:
                button.configure(
                    fg_color=colors['accent_blue'],
                    hover_color=colors['accent_light']
                )
            else:
                button.configure(
                    fg_color="transparent",
                    hover_color=colors['hover']
                )



