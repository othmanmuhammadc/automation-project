"""
STARK AI - Main Application Entry Point
Professional Desktop Automation Tool
"""

import configparser
import os
import sys
from pathlib import Path

import customtkinter as ctk

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ui.main_window import MainWindow


class StarkAI:
    def __init__(self):
        """Initialize STARK AI application"""
        self.config = self.load_config()
        self.root = ctk.CTk()
        self.main_window = None

    def load_config(self):
        """Load configuration from config.ini"""
        config = configparser.ConfigParser()
        config_path = os.path.join(os.path.dirname(__file__), 'config.ini')

        if os.path.exists(config_path):
            config.read(config_path)
        else:
            # Create default config if not exists
            self.create_default_config(config)

        return config

    def create_default_config(self, config):
        """Create default configuration"""
        config['Default'] = {
            'the_tool_name': 'STARK AI',
            'the_send_bar_message': 'Ask STARK AI anything...',
            'default_language': 'en',
            'default_mode': 'assistant',
            'enable_notifications': 'true',
            'auto_check_updates': 'true',
            'app_version': '2.0.0'
        }

        config['Paths'] = {
            'ui_folder': './ui/',
            'assets_folder': './assets/',
            'Icons_folder': './assets/icons/',
            'Fonts_folder': './assets/fonts/',
            'Data_folder': './data/',
            'sites_folder': './data/sites.json',
            'history_folder': './data/history.json',
            'selectors_folder': './data/selectors.json',
            'logs_folder': './logs/'
        }

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

        # Save default config
        config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
        with open(config_path, 'w') as configfile:
            config.write(configfile)

    def run(self):
        """Run the application"""
        try:
            # Initialize main window
            self.main_window = MainWindow(self.root, self.config)

            # Start the application
            self.root.mainloop()

        except Exception as e:
            print(f"Error running STARK AI: {e}")
            import traceback
            traceback.print_exc()

    def shutdown(self):
        """Shutdown the application"""
        if self.root:
            self.root.quit()


def main():
    """Main entry point"""
    app = StarkAI()
    app.run()


if __name__ == "__main__":
    main()






