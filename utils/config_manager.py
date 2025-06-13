"""
Enhanced Configuration Manager for STARK AI Desktop Application
Handles reading and writing configuration from config.ini file with comprehensive features.
"""

import configparser
import logging
import os
from typing import Any, Dict, Tuple, List


class ConfigManager:
    """Enhanced configuration manager with robust error handling and extensive features"""

    def __init__(self, config_path: str = "./config.ini"):
        self.config_path = config_path
        self.config = configparser.ConfigParser()
        self._logger = None
        self._observers = []  # For configuration change notifications
        self.load_config()

    def _get_logger(self):
        """Get logger instance if logging is enabled"""
        if self._logger is None and self.is_logging_enabled():
            self._logger = logging.getLogger(self.__class__.__name__)
        return self._logger

    def add_observer(self, callback):
        """Add a callback to be notified of configuration changes"""
        if callback not in self._observers:
            self._observers.append(callback)

    def remove_observer(self, callback):
        """Remove a configuration change observer"""
        if callback in self._observers:
            self._observers.remove(callback)

    def _notify_observers(self, section, key, old_value, new_value):
        """Notify all observers of configuration changes"""
        for callback in self._observers:
            try:
                callback(section, key, old_value, new_value)
            except Exception as e:
                logger = self._get_logger()
                if logger:
                    logger.error(f"Error notifying observer: {e}")

    def load_config(self):
        """Load configuration from the config.ini file"""
        try:
            if os.path.exists(self.config_path):
                self.config.read(self.config_path, encoding='utf-8')
                logger = self._get_logger()
                if logger:
                    logger.info(f"Configuration loaded from {self.config_path}")
            else:
                self.create_default_config()
        except Exception as e:
            print(f"Error loading config: {e}")
            self.create_default_config()

    def create_default_config(self):
        """Create comprehensive default configuration if file doesn't exist"""
        try:
            # Ensure config directory exists
            config_dir = os.path.dirname(self.config_path)
            if config_dir:
                os.makedirs(config_dir, exist_ok=True)

            # Set default values with comprehensive configuration
            self.config['Default'] = {
                'the_tool_name': 'STARK AI',
                'the_send_bar_message': 'Ask STARK AI anything...',
                'default_language': 'en',
                'default_mode': 'assistant',
                'enable_notifications': 'true',
                'auto_check_updates': 'true',
                'app_version': '2.0.0'
            }

            self.config['Paths'] = {
                'ui_folder': './ui/',
                'assets_folder': './assets/',
                'icons_folder': './assets/icons/',
                'fonts_folder': './assets/fonts/',
                'data_folder': './data/',
                'sites_file': './data/sites.json',
                'history_file': './data/history.json',
                'selectors_file': './data/selectors.json',
                'logs_folder': './logs/'
            }

            self.config['UI'] = {
                'sidebar_width': '80',
                'topbar_height': '80',
                'icon_size': '32',
                'window_width': '1400',
                'window_height': '900',
                'min_window_width': '1200',
                'min_window_height': '800',
                'resizable': 'yes',
                'theme': 'dark',
                'font_family': 'Arial',
                'font_size': '12',
                'enable_transitions': 'true',
                'rounded_corners': 'true',
                'language_direction': 'ltr',
                'animation_duration': '200',
                'border_radius': '12',
                'spacing': '20',
                'padding': '40'
            }

            self.config['User'] = {
                'username': 'user',
                'preferred_language': 'en',
                'first_time_launch': 'true',
                'last_opened_page': 'home',
                'theme_mode': 'auto',
                'save_window_state': 'true',
                'remember_last_input': 'true'
            }

            self.config['Features'] = {
                'voice_input_enabled': 'true',
                'translation_enabled': 'true',
                'task_automation_enabled': 'true',
                'web_search_enabled': 'true',
                'file_operations_enabled': 'true',
                'notifications_enabled': 'true'
            }

            self.config['Performance'] = {
                'animation_fps': '60',
                'cache_size': '100',
                'max_history_items': '1000',
                'auto_save_interval': '300'
            }

            self.config['Debug'] = {
                'show_fps': 'false',
                'enable_logging': 'true',
                'log_level': 'INFO',
                'debug_mode': 'false',
                'show_tooltips': 'true'
            }

            self.config['Shortcuts'] = {
                'send_message': 'Return',
                'clear_input': 'Ctrl+L',
                'toggle_voice': 'Ctrl+M',
                'open_settings': 'Ctrl+Comma',
                'quit_app': 'Ctrl+Q',
                'new_conversation': 'Ctrl+N'
            }

            self.config['Colors'] = {
                'primary_color': '#4A90E2',
                'secondary_color': '#5BA0F2',
                'accent_color': '#7B68EE',
                'success_color': '#4CAF50',
                'warning_color': '#FF9800',
                'error_color': '#F44336',
                'background_dark': '#1a1f2e',
                'background_light': '#ffffff',
                'text_primary': '#ffffff',
                'text_secondary': 'rgba(255, 255, 255, 0.8)',
                'border_color': 'rgba(255, 255, 255, 0.1)'
            }

            self.config['Advanced'] = {
                'startup_check_updates': 'true',
                'auto_backup_config': 'true',
                'crash_reporting': 'true',
                'analytics_enabled': 'false',
                'beta_features': 'false'
            }

            self.save_config()
            print(f"Default configuration created at {self.config_path}")

        except Exception as e:
            print(f"Error creating default config: {e}")

    def backup_config(self):
        """Create a backup of the current configuration"""
        try:
            backup_path = f"{self.config_path}.backup"
            with open(self.config_path, 'r', encoding='utf-8') as original:
                with open(backup_path, 'w', encoding='utf-8') as backup:
                    backup.write(original.read())

            logger = self._get_logger()
            if logger:
                logger.info(f"Configuration backed up to {backup_path}")
            return True
        except Exception as e:
            logger = self._get_logger()
            if logger:
                logger.error(f"Failed to backup configuration: {e}")
            return False

    def restore_config_from_backup(self):
        """Restore configuration from backup"""
        try:
            backup_path = f"{self.config_path}.backup"
            if os.path.exists(backup_path):
                with open(backup_path, 'r', encoding='utf-8') as backup:
                    with open(self.config_path, 'w', encoding='utf-8') as original:
                        original.write(backup.read())

                self.load_config()
                logger = self._get_logger()
                if logger:
                    logger.info("Configuration restored from backup")
                return True
        except Exception as e:
            logger = self._get_logger()
            if logger:
                logger.error(f"Failed to restore configuration from backup: {e}")
        return False

    def get(self, section: str, key: str, fallback: Any = None) -> str:
        """Get a configuration value with enhanced error handling"""
        try:
            return self.config.get(section, key, fallback=str(fallback) if fallback is not None else None)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return str(fallback) if fallback is not None else ""

    def get_int(self, section: str, key: str, fallback: int = 0) -> int:
        """Get a configuration value as integer with validation"""
        try:
            value = self.config.getint(section, key, fallback=fallback)
            # Add basic validation
            if key in ['window_width', 'window_height', 'min_window_width', 'min_window_height']:
                return max(value, 100)  # Minimum window size
            elif key in ['font_size']:
                return max(8, min(value, 72))  # Font size limits
            elif key in ['animation_duration']:
                return max(0, min(value, 5000))  # Animation duration limits
            return value
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback

    def get_bool(self, section: str, key: str, fallback: bool = False) -> bool:
        """Get a configuration value as boolean"""
        try:
            return self.config.getboolean(section, key, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback

    def get_float(self, section: str, key: str, fallback: float = 0.0) -> float:
        """Get a configuration value as float with validation"""
        try:
            value = self.config.getfloat(section, key, fallback=fallback)
            # Add validation for specific keys
            if key in ['opacity']:
                return max(0.0, min(value, 1.0))
            return value
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback

    def get_list(self, section: str, key: str, fallback: List[str] = None) -> List[str]:
        """Get a configuration value as a list (comma-separated)"""
        if fallback is None:
            fallback = []
        try:
            value = self.get(section, key, "")
            if value:
                return [item.strip() for item in value.split(',') if item.strip()]
            return fallback
        except Exception:
            return fallback

    def set(self, section: str, key: str, value: Any):
        """Set a configuration value with change notification"""
        if not self.config.has_section(section):
            self.config.add_section(section)

        old_value = self.get(section, key)
        self.config.set(section, key, str(value))

        # Notify observers of the change
        if str(value) != old_value:
            self._notify_observers(section, key, old_value, str(value))

    def set_list(self, section: str, key: str, value_list: List[str]):
        """Set a configuration value as a comma-separated list"""
        self.set(section, key, ','.join(value_list))

    def save_config(self):
        """Save configuration to file with enhanced error handling"""
        try:
            # Create backup before saving if auto-backup is enabled
            if self.get_bool('Advanced', 'auto_backup_config', True):
                self.backup_config()

            config_dir = os.path.dirname(self.config_path)
            if config_dir:
                os.makedirs(config_dir, exist_ok=True)

            with open(self.config_path, 'w', encoding='utf-8') as configfile:
                self.config.write(configfile)

            logger = self._get_logger()
            if logger:
                logger.info("Configuration saved successfully")

        except Exception as e:
            error_msg = f"Error saving config: {e}"
            logger = self._get_logger()
            if logger:
                logger.error(error_msg)
            else:
                print(error_msg)

    def get_all_sections(self) -> Dict[str, Dict[str, str]]:
        """Get all configuration sections as a dictionary"""
        result = {}
        for section_name in self.config.sections():
            result[section_name] = dict(self.config.items(section_name))
        return result

    def section_exists(self, section: str) -> bool:
        """Check if a configuration section exists"""
        return self.config.has_section(section)

    def key_exists(self, section: str, key: str) -> bool:
        """Check if a configuration key exists"""
        return self.config.has_option(section, key)

    def remove_key(self, section: str, key: str) -> bool:
        """Remove a configuration key"""
        try:
            if self.config.has_option(section, key):
                old_value = self.get(section, key)
                self.config.remove_option(section, key)
                self._notify_observers(section, key, old_value, None)
                return True
        except Exception as e:
            logger = self._get_logger()
            if logger:
                logger.error(f"Error removing key {section}.{key}: {e}")
        return False

    def remove_section(self, section: str) -> bool:
        """Remove an entire configuration section"""
        try:
            if self.config.has_section(section):
                self.config.remove_section(section)
                return True
        except Exception as e:
            logger = self._get_logger()
            if logger:
                logger.error(f"Error removing section {section}: {e}")
        return False

    def reload(self):
        """Reload configuration from file"""
        self.load_config()

    def reset_to_defaults(self):
        """Reset configuration to default values"""
        self.config.clear()
        self.create_default_config()

    def validate_config(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []

        # Check required sections
        required_sections = ['Default', 'Paths', 'UI', 'User', 'Features', 'Debug', 'Colors']
        for section in required_sections:
            if not self.section_exists(section):
                issues.append(f"Missing required section: {section}")

        # Validate specific values
        if self.get_int('UI', 'window_width') < 800:
            issues.append("Window width is too small (minimum 800)")

        if self.get_int('UI', 'window_height') < 600:
            issues.append("Window height is too small (minimum 600)")

        # Check if paths exist
        paths_to_check = ['assets_folder', 'icons_folder', 'fonts_folder', 'data_folder']
        for path_key in paths_to_check:
            path_value = self.get('Paths', path_key)
            if path_value and not os.path.exists(path_value):
                issues.append(f"Path does not exist: {path_key} = {path_value}")

        return issues

    # Enhanced convenience methods for common configurations
    def get_app_name(self) -> str:
        """Get application name"""
        return self.get('Default', 'the_tool_name', 'STARK AI')

    def get_app_version(self) -> str:
        """Get application version"""
        return self.get('Default', 'app_version', '2.0.0')

    def get_placeholder_text(self) -> str:
        """Get input placeholder text"""
        return self.get('Default', 'the_send_bar_message', 'Ask STARK AI anything...')

    def get_window_size(self) -> Tuple[int, int]:
        """Get window size as (width, height)"""
        width = self.get_int('UI', 'window_width', 1400)
        height = self.get_int('UI', 'window_height', 900)
        return (width, height)

    def get_min_window_size(self) -> Tuple[int, int]:
        """Get minimum window size as (width, height)"""
        width = self.get_int('UI', 'min_window_width', 1200)
        height = self.get_int('UI', 'min_window_height', 800)
        return (width, height)

    def get_topbar_height(self) -> int:
        """Get topbar height"""
        return self.get_int('UI', 'topbar_height', 80)

    def get_sidebar_width(self) -> int:
        """Get sidebar width"""
        return self.get_int('UI', 'sidebar_width', 80)

    def get_icon_size(self) -> int:
        """Get icon size"""
        return self.get_int('UI', 'icon_size', 32)

    def get_font_family(self) -> str:
        """Get font family"""
        return self.get('UI', 'font_family', 'Arial')

    def get_font_size(self) -> int:
        """Get font size"""
        return self.get_int('UI', 'font_size', 12)

    def get_animation_duration(self) -> int:
        """Get animation duration in milliseconds"""
        return self.get_int('UI', 'animation_duration', 200)

    def get_border_radius(self) -> int:
        """Get border radius"""
        return self.get_int('UI', 'border_radius', 12)

    def get_spacing(self) -> int:
        """Get default spacing"""
        return self.get_int('UI', 'spacing', 20)

    def get_padding(self) -> int:
        """Get default padding"""
        return self.get_int('UI', 'padding', 40)

    def is_resizable(self) -> bool:
        """Check if window is resizable"""
        return self.get('UI', 'resizable', 'yes').lower() in ['yes', 'true', '1']

    def get_theme(self) -> str:
        """Get theme"""
        return self.get('UI', 'theme', 'dark')

    def get_username(self) -> str:
        """Get username"""
        return self.get('User', 'username', 'user')

    def is_first_time_launch(self) -> bool:
        """Check if this is first time launch"""
        return self.get_bool('User', 'first_time_launch', True)

    def set_first_time_launch(self, value: bool):
        """Set first time launch flag"""
        self.set('User', 'first_time_launch', value)
        self.save_config()

    def get_language_direction(self) -> str:
        """Get language direction"""
        return self.get('UI', 'language_direction', 'ltr')

    # Enhanced path methods
    def get_assets_path(self) -> str:
        """Get assets folder path"""
        return self.get('Paths', 'assets_folder', './assets/')

    def get_icons_path(self) -> str:
        """Get icons folder path"""
        return self.get('Paths', 'icons_folder', './assets/icons/')

    def get_fonts_path(self) -> str:
        """Get fonts folder path"""
        return self.get('Paths', 'fonts_folder', './assets/fonts/')

    def get_data_path(self) -> str:
        """Get data folder path"""
        return self.get('Paths', 'data_folder', './data/')

    def get_ui_path(self) -> str:
        """Get UI folder path"""
        return self.get('Paths', 'ui_folder', './ui/')

    def get_logs_path(self) -> str:
        """Get logs folder path"""
        return self.get('Paths', 'logs_folder', './logs/')

    # Feature flags
    def is_voice_input_enabled(self) -> bool:
        """Check if voice input is enabled"""
        return self.get_bool('Features', 'voice_input_enabled', True)

    def is_translation_enabled(self) -> bool:
        """Check if translation is enabled"""
        return self.get_bool('Features', 'translation_enabled', True)

    def is_task_automation_enabled(self) -> bool:
        """Check if task automation is enabled"""
        return self.get_bool('Features', 'task_automation_enabled', True)

    def is_notifications_enabled(self) -> bool:
        """Check if notifications are enabled"""
        return self.get_bool('Features', 'notifications_enabled', True)

    def is_web_search_enabled(self) -> bool:
        """Check if web search is enabled"""
        return self.get_bool('Features', 'web_search_enabled', True)

    def is_file_operations_enabled(self) -> bool:
        """Check if file operations are enabled"""
        return self.get_bool('Features', 'file_operations_enabled', True)

    # Debug settings
    def is_logging_enabled(self) -> bool:
        """Check if logging is enabled"""
        return self.get_bool('Debug', 'enable_logging', True)

    def get_log_level(self) -> str:
        """Get log level"""
        return self.get('Debug', 'log_level', 'INFO')

    def is_debug_mode(self) -> bool:
        """Check if debug mode is enabled"""
        return self.get_bool('Debug', 'debug_mode', False)

    def show_tooltips(self) -> bool:
        """Check if tooltips should be shown"""
        return self.get_bool('Debug', 'show_tooltips', True)

    def show_fps(self) -> bool:
        """Check if FPS should be shown"""
        return self.get_bool('Debug', 'show_fps', False)

    # Enhanced color methods
    def get_primary_color(self) -> str:
        """Get primary color"""
        return self.get('Colors', 'primary_color', '#4A90E2')

    def get_secondary_color(self) -> str:
        """Get secondary color"""
        return self.get('Colors', 'secondary_color', '#5BA0F2')

    def get_accent_color(self) -> str:
        """Get accent color"""
        return self.get('Colors', 'accent_color', '#7B68EE')

    def get_success_color(self) -> str:
        """Get success color"""
        return self.get('Colors', 'success_color', '#4CAF50')

    def get_warning_color(self) -> str:
        """Get warning color"""
        return self.get('Colors', 'warning_color', '#FF9800')

    def get_error_color(self) -> str:
        """Get error color"""
        return self.get('Colors', 'error_color', '#F44336')

    def get_background_color(self) -> str:
        """Get background color based on theme"""
        theme = self.get_theme()
        if theme == 'dark':
            return self.get('Colors', 'background_dark', '#1a1f2e')
        else:
            return self.get('Colors', 'background_light', '#ffffff')

    def get_text_primary_color(self) -> str:
        """Get primary text color"""
        return self.get('Colors', 'text_primary', '#ffffff')

    def get_text_secondary_color(self) -> str:
        """Get secondary text color"""
        return self.get('Colors', 'text_secondary', 'rgba(255, 255, 255, 0.8)')

    def get_border_color(self) -> str:
        """Get border color"""
        return self.get('Colors', 'border_color', 'rgba(255, 255, 255, 0.1)')

    # Performance settings
    def get_animation_fps(self) -> int:
        """Get animation FPS"""
        return self.get_int('Performance', 'animation_fps', 60)

    def get_cache_size(self) -> int:
        """Get cache size"""
        return self.get_int('Performance', 'cache_size', 100)

    def get_max_history_items(self) -> int:
        """Get maximum history items"""
        return self.get_int('Performance', 'max_history_items', 1000)

    def get_auto_save_interval(self) -> int:
        """Get auto save interval in seconds"""
        return self.get_int('Performance', 'auto_save_interval', 300)

    # Shortcut methods
    def get_shortcut(self, action: str) -> str:
        """Get keyboard shortcut for an action"""
        return self.get('Shortcuts', action, '')

    # Advanced settings
    def is_startup_check_updates(self) -> bool:
        """Check if updates should be checked on startup"""
        return self.get_bool('Advanced', 'startup_check_updates', True)

    def is_auto_backup_enabled(self) -> bool:
        """Check if auto backup is enabled"""
        return self.get_bool('Advanced', 'auto_backup_config', True)

    def is_crash_reporting_enabled(self) -> bool:
        """Check if crash reporting is enabled"""
        return self.get_bool('Advanced', 'crash_reporting', True)

    def is_analytics_enabled(self) -> bool:
        """Check if analytics are enabled"""
        return self.get_bool('Advanced', 'analytics_enabled', False)

    def is_beta_features_enabled(self) -> bool:
        """Check if beta features are enabled"""
        return self.get_bool('Advanced', 'beta_features', False)


# Global config manager instance
config_manager = ConfigManager()



