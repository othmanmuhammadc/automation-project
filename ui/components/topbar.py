"""
STARK AI - Topbar Component
Professional topbar with title, controls, and status indicators
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import os
from PIL import Image, ImageTk
import datetime

class Topbar(ctk.CTkFrame):
    def __init__(self, parent, height, colors, config):
        """Initialize topbar component"""
        super().__init__(
            parent,
            height=height,
            fg_color=colors['bg_secondary'],
            corner_radius=0
        )

        self.parent = parent
        self.height = height
        self.colors = colors
        self.config = config
        self.gui_config = config['GUI']

        # Current status
        self.current_mode = "Chat Assistant"
        self.connection_status = "Connected"

        self.setup_topbar()
        self.start_clock()

    def setup_topbar(self):
        """Setup topbar layout and components"""
        # Configure grid
        self.grid_columnconfigure(1, weight=1)  # Center area expands

        # Left section - Logo and title
        self.create_left_section()

        # Center section - Current mode/status
        self.create_center_section()

        # Right section - Controls and status
        self.create_right_section()

    def create_left_section(self):
        """Create left section with logo and title"""
        self.left_frame = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        self.left_frame.grid(row=0, column=0, sticky="nsw", padx=10, pady=5)

        # STARK AI Logo/Title
        self.title_label = ctk.CTkLabel(
            self.left_frame,
            text="STARK AI",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.colors['accent_blue']
        )
        self.title_label.grid(row=0, column=0, sticky="w")

        # Subtitle
        self.subtitle_label = ctk.CTkLabel(
            self.left_frame,
            text="Advanced Desktop Automation",
            font=ctk.CTkFont(size=10),
            text_color=self.colors['text_secondary']
        )
        self.subtitle_label.grid(row=1, column=0, sticky="w")

    def create_center_section(self):
        """Create center section with current mode"""
        self.center_frame = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        self.center_frame.grid(row=0, column=1, sticky="nsew", padx=20)
        self.center_frame.grid_columnconfigure(0, weight=1)

        # Current mode indicator
        self.mode_frame = ctk.CTkFrame(
            self.center_frame,
            fg_color=self.colors['bg_tertiary'],
            corner_radius=15,
            height=35
        )
        self.mode_frame.grid(row=0, column=0, pady=12)

        # Mode icon and text
        self.mode_icon = ctk.CTkLabel(
            self.mode_frame,
            text="💬",
            font=ctk.CTkFont(size=16)
        )
        self.mode_icon.grid(row=0, column=0, padx=(15, 5), pady=8)

        self.mode_label = ctk.CTkLabel(
            self.mode_frame,
            text=self.current_mode,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors['text_primary']
        )
        self.mode_label.grid(row=0, column=1, padx=(0, 15), pady=8)

    def create_right_section(self):
        """Create right section with controls and status"""
        self.right_frame = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        self.right_frame.grid(row=0, column=2, sticky="nse", padx=10, pady=5)

        # Language selector
        self.language_var = ctk.StringVar(value="EN")
        self.language_selector = ctk.CTkOptionMenu(
            self.right_frame,
            values=["EN", "العربية", "Deutsch"],
            variable=self.language_var,
            width=80,
            height=30,
            fg_color=self.colors['bg_tertiary'],
            button_color=self.colors['accent_blue'],
            button_hover_color=self.colors['accent_light'],
            dropdown_fg_color=self.colors['bg_tertiary'],
            font=ctk.CTkFont(size=10),
            command=self.change_language
        )
        self.language_selector.grid(row=0, column=0, padx=5)

        # Connection status
        self.status_frame = ctk.CTkFrame(
            self.right_frame,
            fg_color="transparent"
        )
        self.status_frame.grid(row=0, column=1, padx=10)

        # Status indicator
        self.status_dot = ctk.CTkLabel(
            self.status_frame,
            text="●",
            font=ctk.CTkFont(size=12),
            text_color="#00ff00"  # Green for connected
        )
        self.status_dot.grid(row=0, column=0)

        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text=self.connection_status,
            font=ctk.CTkFont(size=10),
            text_color=self.colors['text_secondary']
        )
        self.status_label.grid(row=0, column=1, padx=(2, 0))

        # Clock
        self.clock_label = ctk.CTkLabel(
            self.right_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=self.colors['text_secondary']
        )
        self.clock_label.grid(row=0, column=2, padx=10)

        # Window controls (minimize, maximize, close)
        self.create_window_controls()

    def create_window_controls(self):
        """Create window control buttons"""
        self.controls_frame = ctk.CTkFrame(
            self.right_frame,
            fg_color="transparent"
        )
        self.controls_frame.grid(row=0, column=3, padx=5)

        # Minimize button
        self.minimize_btn = ctk.CTkButton(
            self.controls_frame,
            text="−",
            width=30,
            height=25,
            fg_color="transparent",
            hover_color=self.colors['hover'],
            corner_radius=4,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.minimize_window
        )
        self.minimize_btn.grid(row=0, column=0, padx=1)

        # Maximize button
        self.maximize_btn = ctk.CTkButton(
            self.controls_frame,
            text="□",
            width=30,
            height=25,
            fg_color="transparent",
            hover_color=self.colors['hover'],
            corner_radius=4,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.maximize_window
        )
        self.maximize_btn.grid(row=0, column=1, padx=1)

        # Close button
        self.close_btn = ctk.CTkButton(
            self.controls_frame,
            text="×",
            width=30,
            height=25,
            fg_color="transparent",
            hover_color="#ff4444",
            corner_radius=4,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.close_window
        )
        self.close_btn.grid(row=0, column=2, padx=1)

    def update_mode(self, mode, icon="💬"):
        """Update current mode display"""
        self.current_mode = mode
        self.mode_label.configure(text=mode)
        self.mode_icon.configure(text=icon)

        print(f"🔄 Mode changed to: {mode}")

    def change_language(self, language):
        """Handle language change"""
        language_codes = {
            "EN": "en",
            "العربية": "ar",
            "Deutsch": "de"
        }

        code = language_codes.get(language, "en")
        print(f"🌐 Language changed to: {language} ({code})")

        # Update UI text based on language
        self.update_ui_language(code)

    def update_ui_language(self, lang_code):
        """Update UI text based on language"""
        translations = {
            "en": {
                "title": "STARK AI",
                "subtitle": "Advanced Desktop Automation",
                "connected": "Connected",
                "disconnected": "Disconnected"
            },
            "ar": {
                "title": "ستارك الذكي",
                "subtitle": "أتمتة سطح المكتب المتقدمة",
                "connected": "متصل",
                "disconnected": "غير متصل"
            },
            "de": {
                "title": "STARK KI",
                "subtitle": "Erweiterte Desktop-Automatisierung",
                "connected": "Verbunden",
                "disconnected": "Getrennt"
            }
        }

        if lang_code in translations:
            trans = translations[lang_code]
            self.title_label.configure(text=trans["title"])
            self.subtitle_label.configure(text=trans["subtitle"])

            # Update status text
            status_text = trans["connected"] if self.connection_status == "Connected" else trans["disconnected"]
            self.status_label.configure(text=status_text)

    def update_connection_status(self, connected=True):
        """Update connection status"""
        if connected:
            self.connection_status = "Connected"
            self.status_dot.configure(text_color="#00ff00")  # Green
            self.status_label.configure(text="Connected")
        else:
            self.connection_status = "Disconnected"
            self.status_dot.configure(text_color="#ff4444")  # Red
            self.status_label.configure(text="Disconnected")

    def start_clock(self):
        """Start the clock update loop"""
        self.update_clock()

    def update_clock(self):
        """Update the clock display"""
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        self.clock_label.configure(text=current_time)

        # Schedule next update
        self.after(1000, self.update_clock)

    def minimize_window(self):
        """Minimize the application window"""
        self.winfo_toplevel().iconify()

    def maximize_window(self):
        """Toggle maximize/restore window"""
        root = self.winfo_toplevel()
        if root.state() == 'zoomed':
            root.state('normal')
            self.maximize_btn.configure(text="□")
        else:
            root.state('zoomed')
            self.maximize_btn.configure(text="❐")

    def close_window(self):
        """Close the application"""
        self.winfo_toplevel().quit()

    def update_colors(self, colors):
        """Update component colors"""
        self.colors = colors
        self.configure(fg_color=colors['bg_secondary'])

        # Update child components
        self.title_label.configure(text_color=colors['accent_blue'])
        self.subtitle_label.configure(text_color=colors['text_secondary'])
        self.mode_frame.configure(fg_color=colors['bg_tertiary'])
        self.mode_label.configure(text_color=colors['text_primary'])
        self.status_label.configure(text_color=colors['text_secondary'])
        self.clock_label.configure(text_color=colors['text_secondary'])

        # Update buttons
        for btn in [self.minimize_btn, self.maximize_btn]:
            btn.configure(
                fg_color="transparent",
                hover_color=colors['hover']
            )

        self.close_btn.configure(
            fg_color="transparent",
            hover_color="#ff4444"
        )

        # Update language selector
        self.language_selector.configure(
            fg_color=colors['bg_tertiary'],
            button_color=colors['accent_blue'],
            button_hover_color=colors['accent_light'],
            dropdown_fg_color=colors['bg_tertiary']
        )


        