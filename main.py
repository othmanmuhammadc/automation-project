#!/usr/bin/env python3
"""
STARK AI - Advanced Desktop Automation Tool
Main Application Entry Point
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import os
import sys
import configparser
from pathlib import Path

# Import custom modules
from ui.main_window import MainWindow
from ui.components.sidebar import Sidebar
from ui.components.topbar import Topbar
from ui.components.content_area import ContentArea


class StarkAI:
    def __init__(self):
        """Initialize STARK AI Application"""
        self.config = self.load_config()
        self.setup_directories()
        self.setup_theme()

        # Initialize main window
        self.root = ctk.CTk()
        self.setup_window()

        # Initialize UI components
        self.main_window = MainWindow(self.root, self.config)

    def load_config(self):
        """Load configuration from config.ini"""
        config = configparser.ConfigParser()
        config_path = Path("config.ini")

        if config_path.exists():
            config.read(config_path)
        else:
            # Create default config if not exists
            self.create_default_config(config)

        return config

    def create_default_config(self, config):
        """Create default configuration file"""
        config['GUI'] = {
            'Sidebar_width': '80',
            'Topbar_height': '60',
            'Icon_size': '32',
            'Window_width': '1280',
            'Window_height': '720',
            'Resizable': 'yes',
            'Theme': 'dark',
            'Font_family': 'Arial',
            'Font_size': '12'
        }

        config['Paths'] = {
            'ui_folder': './ui/',
            'assets_folder': './assets/',
            'Icons_folder': './assets/icons/',
            'Fonts_folder': './assets/fonts/',
            'Data_folder': './data/',
            'sites_folder': './data/sites.json',
            'history_folder': './data/history.json',
            'selectors_folder': './data/selectors.json'
        }

        config['Languages'] = {
            'default': 'en',
            'supported': 'en,ar,de'
        }

        with open('config.ini', 'w') as configfile:
            config.write(configfile)

    def setup_directories(self):
        """Create necessary directories if they don't exist"""
        directories = [
            './ui/',
            './ui/components/',
            './assets/',
            './assets/icons/',
            './assets/fonts/',
            './data/'
        ]

        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

    def setup_theme(self):
        """Setup CustomTkinter theme"""
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

    def setup_window(self):
        """Setup main window properties"""
        gui_config = self.config['GUI']

        self.root.title("STARK AI - Advanced Desktop Automation")
        self.root.geometry(f"{gui_config.get('Window_width', '1280')}x{gui_config.get('Window_height', '720')}")

        if gui_config.get('Resizable', 'yes').lower() == 'yes':
            self.root.resizable(True, True)
        else:
            self.root.resizable(False, False)

        # Center window on screen
        self.center_window()

        # Set minimum size
        self.root.minsize(800, 600)

    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def run(self):
        """Start the application"""
        try:
            print("🚀 Starting STARK AI...")
            print(f"📊 Window Size: {self.config['GUI'].get('Window_width')}x{self.config['GUI'].get('Window_height')}")
            print(f"🎨 Theme: {self.config['GUI'].get('Theme')}")
            print("✅ STARK AI is ready!")

            self.root.mainloop()

        except KeyboardInterrupt:
            print("\n👋 STARK AI shutting down gracefully...")
            self.root.quit()
        except Exception as e:
            print(f"❌ Error starting STARK AI: {e}")
            sys.exit(1)


def main():
    """Main entry point"""
    try:
        app = StarkAI()
        app.run()
    except Exception as e:
        print(f"❌ Failed to start STARK AI: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


