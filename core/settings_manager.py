"""
Settings Manager for STARK AI Desktop Application
Handles application settings and preferences using the config system.
"""

from utils.config_manager import config_manager
from typing import Dict, Any


class SettingsManager:
    """Manages application settings and preferences"""

    def __init__(self):
        self.config = config_manager

    def get_user_settings(self) -> Dict[str, Any]:
        """Get all user settings"""
        return {
            'username': self.config.get_username(),
            'preferred_language': self.config.get('User', 'Preferred_language', 'en'),
            'theme_mode': self.config.get('User', 'Theme_mode', 'auto'),
            'last_opened_page': self.config.get('User', 'Last_opened_page', 'home'),
            'notifications_enabled': self.config.get_bool('Default', 'Enable_notifications', True),
            'auto_check_updates': self.config.get_bool('Default', 'Auto_check_updates', True)
        }

    def update_user_setting(self, key: str, value: Any):
        """Update a user setting"""
        self.config.set('User', key, value)
        self.config.save_config()

    def get_ui_settings(self) -> Dict[str, Any]:
        """Get all UI settings"""
        return {
            'window_width': self.config.get_int('UI', 'Window_width', 1400),
            'window_height': self.config.get_int('UI', 'Window_height', 900),
            'topbar_height': self.config.get_int('UI', 'Topbar_height', 80),
            'sidebar_width': self.config.get_int('UI', 'Sidebar_width', 80),
            'icon_size': self.config.get_int('UI', 'Icon_size', 32),
            'font_family': self.config.get('UI', 'Font_family', 'Arial'),
            'font_size': self.config.get_int('UI', 'Font_size', 12),
            'theme': self.config.get('UI', 'Theme', 'dark'),
            'resizable': self.config.is_resizable(),
            'enable_transitions': self.config.get_bool('UI', 'Enable_transitions', True),
            'rounded_corners': self.config.get_bool('UI', 'Rounded_corners', True),
            'language_direction': self.config.get('UI', 'Language_direction', 'ltr')
        }

    def update_ui_setting(self, key: str, value: Any):
        """Update a UI setting"""
        self.config.set('UI', key, value)
        self.config.save_config()

    def get_debug_settings(self) -> Dict[str, Any]:
        """Get debug settings"""
        return {
            'show_fps': self.config.get_bool('Debug', 'Show_fps', False),
            'enable_logging': self.config.get_bool('Debug', 'Enable_logging', True)
        }

    def update_debug_setting(self, key: str, value: Any):
        """Update a debug setting"""
        self.config.set('Debug', key, value)
        self.config.save_config()

    def reset_to_defaults(self):
        """Reset all settings to default values"""
        self.config.create_default_config()

    def export_settings(self) -> Dict[str, Dict[str, str]]:
        """Export all settings"""
        return self.config.get_all_sections()

    def get_paths(self) -> Dict[str, str]:
        """Get all configured paths"""
        return {
            'ui_folder': self.config.get('Paths', 'ui_folder', './ui/'),
            'assets_folder': self.config.get('Paths', 'assets_folder', './assets/'),
            'icons_folder': self.config.get('Paths', 'icons_folder', './assets/icons/'),
            'fonts_folder': self.config.get('Paths', 'fonts_folder', './assets/fonts/'),
            'data_folder': self.config.get('Paths', 'data_folder', './data/'),
            'sites_file': self.config.get('Paths', 'sites_file', './data/sites.json'),
            'history_file': self.config.get('Paths', 'history_file', './data/history.json'),
            'selectors_file': self.config.get('Paths', 'selectors_file', './data/selectors.json')
        }


# Global settings manager instance
settings_manager = SettingsManager()





