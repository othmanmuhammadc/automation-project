"""
Configuration Manager for STARK AI Desktop Application
Handles reading and writing configuration from config.ini file.
"""

import configparser
import os
from typing import Any, Dict, Optional


class ConfigManager:
    """Manages application configuration from config.ini file"""

    def __init__(self, config_path: str = "./config/config.ini"):
        self.config_path = config_path
        self.config = configparser.ConfigParser()
        self.load_config()

    def load_config(self):
        """Load configuration from the config.ini file"""
        try:
            if os.path.exists(self.config_path):
                self.config.read(self.config_path, encoding='utf-8')
            else:
                self.create_default_config()
        except Exception as e:
            print(f"Error loading config: {e}")
            self.create_default_config()

    def create_default_config(self):
        """Create default configuration if file doesn't exist"""
        # Ensure config directory exists
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

        # Set default values
        self.config['Default'] = {
            'The_tool_name': 'STARK AI',
            'The_send_bar_message': 'Type a message...',
            'Default_language': 'en',
            'Default_mode': 'assistant',
            'Enable_notifications': 'true',
            'Auto_check_updates': 'true'
        }

        self.config['Paths'] = {
            'ui_folder': './ui/',
            'assets_folder': './assets/',
            'icons_folder': './assets/icons/',
            'fonts_folder': './assets/fonts/',
            'data_folder': './data/',
            'sites_file': './data/sites.json',
            'history_file': './data/history.json',
            'selectors_file': './data/selectors.json'
        }

        self.config['UI'] = {
            'Sidebar_width': '80',
            'Topbar_height': '80',
            'Icon_size': '32',
            'Window_width': '1400',
            'Window_height': '900',
            'Resizable': 'yes',
            'Theme': 'dark',
            'Font_family': 'Arial',
            'Font_size': '12',
            'Enable_transitions': 'true',
            'Rounded_corners': 'true',
            'Language_direction': 'ltr'
        }

        self.config['User'] = {
            'Username': 'user',
            'Preferred_language': 'en',
            'First_time_launch': 'true',
            'Last_opened_page': 'home',
            'Theme_mode': 'auto'
        }

        self.config['Debug'] = {
            'Show_fps': 'false',
            'Enable_logging': 'true'
        }

        self.save_config()

    def get(self, section: str, key: str, fallback: Any = None) -> str:
        """Get a configuration value"""
        try:
            return self.config.get(section, key, fallback=str(fallback) if fallback is not None else None)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return str(fallback) if fallback is not None else ""

    def get_int(self, section: str, key: str, fallback: int = 0) -> int:
        """Get a configuration value as integer"""
        try:
            return self.config.getint(section, key, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback

    def get_bool(self, section: str, key: str, fallback: bool = False) -> bool:
        """Get a configuration value as boolean"""
        try:
            return self.config.getboolean(section, key, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback

    def get_float(self, section: str, key: str, fallback: float = 0.0) -> float:
        """Get a configuration value as float"""
        try:
            return self.config.getfloat(section, key, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback

    def set(self, section: str, key: str, value: Any):
        """Set a configuration value"""
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, str(value))

    def save_config(self):
        """Save configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as configfile:
                self.config.write(configfile)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get_all_sections(self) -> Dict[str, Dict[str, str]]:
        """Get all configuration sections as a dictionary"""
        result = {}
        for section_name in self.config.sections():
            result[section_name] = dict(self.config.items(section_name))
        return result

    def reload(self):
        """Reload configuration from file"""
        self.load_config()

    # Convenience methods for common configurations
    def get_app_name(self) -> str:
        """Get application name"""
        return self.get('Default', 'The_tool_name', 'STARK AI')

    def get_placeholder_text(self) -> str:
        """Get input placeholder text"""
        return self.get('Default', 'The_send_bar_message', 'Type a message...')

    def get_window_size(self) -> tuple:
        """Get window size as (width, height)"""
        width = self.get_int('UI', 'Window_width', 1400)
        height = self.get_int('UI', 'Window_height', 900)
        return (width, height)

    def get_topbar_height(self) -> int:
        """Get topbar height"""
        return self.get_int('UI', 'Topbar_height', 80)

    def get_icon_size(self) -> int:
        """Get icon size"""
        return self.get_int('UI', 'Icon_size', 32)

    def get_font_family(self) -> str:
        """Get font family"""
        return self.get('UI', 'Font_family', 'Arial')

    def get_font_size(self) -> int:
        """Get font size"""
        return self.get_int('UI', 'Font_size', 12)

    def is_resizable(self) -> bool:
        """Check if window is resizable"""
        return self.get('UI', 'Resizable', 'yes').lower() in ['yes', 'true', '1']

    def get_theme(self) -> str:
        """Get theme"""
        return self.get('UI', 'Theme', 'dark')

    def get_username(self) -> str:
        """Get username"""
        return self.get('User', 'Username', 'user')

    def is_first_time_launch(self) -> bool:
        """Check if this is first time launch"""
        return self.get_bool('User', 'First_time_launch', True)

    def set_first_time_launch(self, value: bool):
        """Set first time launch flag"""
        self.set('User', 'First_time_launch', value)
        self.save_config()

    def get_icons_path(self) -> str:
        """Get icons folder path"""
        return self.get('Paths', 'icons_folder', './assets/icons/')

    def get_fonts_path(self) -> str:
        """Get fonts folder path"""
        return self.get('Paths', 'fonts_folder', './assets/fonts/')

    def is_logging_enabled(self) -> bool:
        """Check if logging is enabled"""
        return self.get_bool('Debug', 'Enable_logging', True)


# Global config manager instance
config_manager = ConfigManager()



