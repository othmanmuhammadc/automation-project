#!/usr/bin/env python3
"""
Smart Automation Tool - Fully Automated YouTube Content Creation Pipeline
Author: AI Assistant (Revised by Manus)
Version: 5.3 (Integrated webdriver-manager)
Description: Fully automated text generation (via API/Browser), video creation (via Browser),
             and YouTube upload (via API) tool. Reads ALL configuration from external
             files (INI/JSON) and requires no user interaction during runtime.
             Supports YouTube client secrets embedded directly in api.json or via a separate file.
             Supports connecting to an existing browser via remote debugging port with fallback.
             Uses webdriver-manager for automatic driver handling.
             Fails critically if any required configuration is missing.
             Includes robustness improvements for browser initialization and config validation.
"""

import os
import sys
import json
import time
import random
import logging
import configparser
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union

# --- Dependency Imports ---
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.edge.options import Options as EdgeOptions
    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.webdriver.edge.service import Service as EdgeService
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
except ImportError:
    print("❌ Error: Selenium is required but not installed. Run: pip install selenium")
    sys.exit(1)

try:
    from webdriver_manager.chrome import ChromeDriverManager
    from webdriver_manager.microsoft import EdgeChromiumDriverManager
except ImportError:
    print("❌ Error: webdriver-manager is required but not installed. Run: pip install webdriver-manager")
    sys.exit(1)

try:
    import google.generativeai as genai
except ImportError:
    # We won't print a warning here; the config validation will handle it if Gemini is selected.
    genai = None

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload
except ImportError:
    # Config validation will handle this if YouTube upload is implicitly needed.
    InstalledAppFlow = None
    Credentials = None
    build = None
    HttpError = None
    MediaFileUpload = None

# --- Constants ---
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'
YOUTUBE_SCOPES = ['https://www.googleapis.com/auth/youtube.upload']


# --- Logger Class ---
class Logger:
    """Basic file and console logging.

    Requires log file path to be passed during initialization.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            # Initialization logic only runs once
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, log_file_path: Optional[str] = None):
        if self._initialized:
            return
        if log_file_path is None:
            # Cannot initialize without a path, but don't crash here.
            # ConfigManager should handle this.
            print("Logger Error: Log file path not provided during initialization.")
            self.logger = None  # Set logger to None to indicate failure
            self._initialized = True  # Mark as initialized to prevent re-entry
            return

        self.log_file = Path(log_file_path)
        try:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            # Clear previous log handlers if any (useful for re-runs in same session)
            for handler in logging.root.handlers[:]:
                logging.root.removeHandler(handler)

            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(self.log_file, encoding='utf-8'),
                    logging.StreamHandler(sys.stdout)
                ]
            )
            self.logger = logging.getLogger(__name__)
            print(f"Logger initialized. Logging to: {self.log_file}")  # Initial confirmation
        except Exception as e:
            # Fallback to console if file logging fails
            print(f"Error initializing file logger at {self.log_file}: {e}. Falling back to console logging.")
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[logging.StreamHandler(sys.stdout)]
            )
            self.logger = logging.getLogger(__name__)

        self._initialized = True

    def _log(self, level, message):
        if self.logger:
            self.logger.log(level, message)
        else:
            # Fallback print if logger failed init
            print(f"{logging.getLevelName(level)}: {message}")

    def info(self, message: str):
        self._log(logging.INFO, message)

    def error(self, message: str):
        self._log(logging.ERROR, message)

    def warning(self, message: str):
        self._log(logging.WARNING, message)

    def success(self, message: str):
        self._log(logging.INFO, f"✅ {message}")

    def critical(self, message: str):
        self._log(logging.CRITICAL, message)
        # Consider removing sys.exit(1) here if more graceful failure is desired in main loop
        sys.exit(1)  # Exit on critical errors


# --- Configuration Manager Class ---
class ConfigManager:
    """Loads and validates ALL required configurations from external files.

    Does NOT create default files. Assumes all files and required keys exist.
    Fails critically if any required configuration is missing or invalid.
    Supports YouTube client secrets embedded directly in api.json or via a separate file.
    """

    def __init__(self, base_dir_override: Optional[str] = None):
        # Determine base directory (useful for testing/different structures)
        self.base_dir = Path(base_dir_override) if base_dir_override else Path.cwd()

        # Define expected file paths RELATIVE to the base directory
        self.customisation_file = self.base_dir / "customisation.ini"
        self.data_dir_placeholder = self.base_dir / "Data"  # Used for constructing other paths
        self.selectors_file = self.data_dir_placeholder / "selectors.json"
        self.api_file = self.data_dir_placeholder / "api.json"
        self.uploaded_videos_file = self.data_dir_placeholder / "uploaded_videos.ini"

        # --- Load Files --- (Fail fast if files don't exist)
        self.config = self._load_ini_config(self.customisation_file)
        self.selectors = self._load_json_config(self.selectors_file)
        self.api_config = self._load_json_config(self.api_file)

        # --- Initialize Logger --- (Must happen AFTER loading customisation.ini)
        # Resolve log file path FIRST
        log_file_path_str = self.config.get('PATHS', 'log_file', fallback=None)
        if not log_file_path_str:
            print("CRITICAL ERROR: Missing required configuration key 'log_file' in section '[PATHS]' of customisation.ini")
            sys.exit(1)
        # Resolve relative to base_dir if needed
        if not os.path.isabs(log_file_path_str):
             self.log_file_abs_path = self.base_dir / log_file_path_str
        else:
             self.log_file_abs_path = Path(log_file_path_str)

        self.logger = Logger(str(self.log_file_abs_path))
        self.logger.info(f"Base directory set to: {self.base_dir}")
        self.logger.info(f"Loaded customisation.ini from: {self.customisation_file}")
        self.logger.info(f"Loaded selectors.json from: {self.selectors_file}")
        self.logger.info(f"Loaded api.json from: {self.api_file}")

        # --- Define Required Keys --- (Centralized list for validation)
        self.required_ini_keys = {
            'PATHS': ['scripts_dir', 'videos_dir', 'downloads_dir', 'log_file', 'uploaded_videos_log'],
            'AI_SETTINGS': ['provider', 'ai_prompt'],
            'VIDEO_SETTINGS': ['provider', 'capcut_url', 'capcut_style', 'capcut_voice', 'capcut_export_resolution',
                               'capcut_export_format', 'capcut_export_frame_rate'],
            'YOUTUBE_SETTINGS': ['privacy_status', 'category_id', 'notify_subscribers'],
            'BROWSER_SETTINGS': ['primary_browser', 'user_data_dir', 'wait_timeout', 'retry_attempts',
                                 'page_load_timeout', 'headless_mode']  # debugger_port is optional
        }
        # YouTube API keys validation is now more complex (handled in _validate_configs)
        self.required_api_keys = {
            'gemini': ['api_key']
            # Add other potential AI providers here if they use API keys
        }

        # --- Validate Configurations --- (Strict validation)
        self._validate_configs()

        # --- Resolve Paths --- (Make paths absolute based on base_dir)
        self._resolve_paths()

        self.logger.success("Configuration loaded and validated successfully.")

    def _load_ini_config(self, file_path: Path) -> configparser.ConfigParser:
        """Loads an INI file. Fails critically if file not found or parse error."""
        if not file_path.is_file():
            # Use logger if available, otherwise print
            msg = f"CRITICAL ERROR: Configuration file not found: {file_path}"
            if hasattr(self, 'logger') and self.logger: self.logger.critical(msg)
            else: print(msg)
            sys.exit(1)
        try:
            # Allow empty values for optional keys like debugger_port
            config = configparser.ConfigParser(allow_no_value=True)
            config.read(file_path, encoding='utf-8')
            return config
        except Exception as e:
            msg = f"CRITICAL ERROR: Error reading INI configuration file {file_path}: {e}"
            if hasattr(self, 'logger') and self.logger: self.logger.critical(msg)
            else: print(msg)
            sys.exit(1)

    def _load_json_config(self, file_path: Path) -> Dict:
        """Loads a JSON file. Fails critically if file not found or parse error."""
        if not file_path.is_file():
            msg = f"CRITICAL ERROR: Configuration file not found: {file_path}"
            if hasattr(self, 'logger') and self.logger: self.logger.critical(msg)
            else: print(msg)
            sys.exit(1)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            msg = f"CRITICAL ERROR: Error decoding JSON from {file_path}: {e}"
            if hasattr(self, 'logger') and self.logger: self.logger.critical(msg)
            else: print(msg)
            sys.exit(1)
        except Exception as e:
            msg = f"CRITICAL ERROR: Error reading JSON file {file_path}: {e}"
            if hasattr(self, 'logger') and self.logger: self.logger.critical(msg)
            else: print(msg)
            sys.exit(1)

    def _get_required_config(self, config_obj: Any, section_name_for_log: Optional[str], key: str, filename: Path, section_dict: Optional[Dict] = None) -> str:
        """Helper to get a required key, failing critically if absent or placeholder.
           Handles ConfigParser and Dict objects.
           If section_dict is provided, it checks within that dictionary.
           Allows empty value only for 'user_data_dir' and 'debugger_port'.
        """
        value = None
        location_desc = f"section '[{section_name_for_log}]'" if section_name_for_log else "top level"

        if section_dict is not None and isinstance(section_dict, dict):
            # Primarily for checking within a specific section of a JSON dict (e.g., api_config['youtube'])
            value = section_dict.get(key)
            location_desc = f"section '{section_name_for_log}'" # Use provided name for logging
        elif isinstance(config_obj, configparser.ConfigParser):
            # Handles INI files
            if section_name_for_log and config_obj.has_option(section_name_for_log, key):
                value = config_obj.get(section_name_for_log, key)
            location_desc = f"section '[{section_name_for_log}]'" # Keep original description for INI
        elif isinstance(config_obj, dict):
            # Handles top-level keys in a JSON dict if section_dict wasn't provided
            value = config_obj.get(key)
            location_desc = "top level" # Assume top level if checking the whole dict

        is_optional_empty = key in ['user_data_dir', 'debugger_port'] and value == ''

        if value is None or (value == '' and not is_optional_empty):
            self.logger.critical(
                f"Missing required configuration value for '{key}' in {location_desc} of file: {filename}")
        elif isinstance(value, str) and 'YOUR_' in value:
             self.logger.critical(
                f"Placeholder value found for '{key}' in {location_desc} of file: {filename}. Please replace it.")

        return value if value is not None else '' # Return empty string if optional and missing/empty

    def _validate_configs(self):
        """Perform strict validation of all loaded configurations."""
        self.logger.info("Validating configurations...")
        errors = []

        # 1. Validate customisation.ini structure and required keys
        for section, keys in self.required_ini_keys.items():
            if not self.config.has_section(section):
                errors.append(f"Missing required section '[{section}]' in {self.customisation_file}")
                continue # Skip key checks if section is missing
            for key in keys:
                # Use the helper for INI files
                self._get_required_config(self.config, section, key, self.customisation_file)

        # 1b. Validate optional debugger_port format if present
        debugger_port_str = self.config.get('BROWSER_SETTINGS', 'debugger_port', fallback=None)
        if debugger_port_str:
            try:
                int(debugger_port_str)
            except ValueError:
                errors.append(
                    f"Invalid value for 'debugger_port' in [BROWSER_SETTINGS] of {self.customisation_file}. Must be an integer.")

        # 1c. Validate numeric settings format
        numeric_settings = {
            'BROWSER_SETTINGS': ['wait_timeout', 'retry_attempts', 'page_load_timeout'],
            'YOUTUBE_SETTINGS': ['category_id']
        }
        for section, keys in numeric_settings.items():
            if self.config.has_section(section):
                for key in keys:
                    value_str = self.config.get(section, key, fallback=None)
                    if value_str:
                        try:
                            int(value_str)
                        except ValueError:
                             errors.append(f"Invalid non-integer value for '{key}' in [{section}] of {self.customisation_file}.")
                    # else: handled by _get_required_config

        # 1d. Validate boolean settings format
        boolean_settings = {
            'BROWSER_SETTINGS': ['headless_mode'],
            'YOUTUBE_SETTINGS': ['notify_subscribers']
        }
        for section, keys in boolean_settings.items():
            if self.config.has_section(section):
                for key in keys:
                    value_str = self.config.get(section, key, fallback=None)
                    if value_str and value_str.lower() not in ['true', 'false']:
                         errors.append(f"Invalid non-boolean value for '{key}' in [{section}] of {self.customisation_file}. Use 'true' or 'false'.")
                    # else: handled by _get_required_config

        # 2. Validate api.json structure and required keys based on AI provider
        ai_provider = self.config.get('AI_SETTINGS', 'provider', fallback='').lower()
        if ai_provider == 'gemini':
            gemini_config = self.api_config.get('gemini')
            if not gemini_config or not isinstance(gemini_config, dict):
                errors.append(
                    f"Missing or invalid section 'gemini' in {self.api_file} (required by AI provider '{ai_provider}')")
            else:
                for key in self.required_api_keys['gemini']:
                     # Use helper, passing the specific gemini dict section
                     self._get_required_config(None, 'gemini', key, self.api_file, section_dict=gemini_config)
            # Check if genai library was imported
            if genai is None:
                errors.append(f"AI provider is 'gemini' but 'google-generativeai' library is not installed.")

        # 3. Validate YouTube API configuration (credentials file + secrets file OR embedded secrets)
        youtube_config = self.api_config.get('youtube')
        if not youtube_config or not isinstance(youtube_config, dict):
            errors.append(f"Missing or invalid section 'youtube' in {self.api_file}")
        else:
            # Credentials file is always required
            self._get_required_config(None, 'youtube', 'credentials_file', self.api_file, section_dict=youtube_config)

            # Check for client secrets: either file path OR embedded config
            has_secrets_file = 'client_secrets_file' in youtube_config and youtube_config['client_secrets_file']
            has_embedded_secrets = 'client_secrets_config' in youtube_config and isinstance(
                youtube_config['client_secrets_config'], dict) and youtube_config['client_secrets_config']

            if not has_secrets_file and not has_embedded_secrets:
                errors.append(
                    f"Missing YouTube client secrets configuration in {self.api_file}. Provide either 'client_secrets_file' (path) or 'client_secrets_config' (embedded JSON object) in the 'youtube' section.")
            elif has_secrets_file and has_embedded_secrets:
                self.logger.warning(
                    f"Both 'client_secrets_file' and 'client_secrets_config' found in 'youtube' section of {self.api_file}. Using 'client_secrets_config' (embedded). Remove one to avoid confusion.")
            elif has_secrets_file:
                # Validate the secrets file path exists (relative path checked here, resolved later)
                secrets_path_rel = youtube_config['client_secrets_file']
                # Check for placeholder value first
                if isinstance(secrets_path_rel, str) and 'YOUR_' in secrets_path_rel:
                     errors.append(f"Placeholder value found for 'client_secrets_file' in section 'youtube' of {self.api_file}. Please replace it.")
                elif isinstance(secrets_path_rel, str):
                    # Check path existence after potential resolution
                    secrets_path_abs = self.base_dir / secrets_path_rel if not os.path.isabs(secrets_path_rel) else Path(secrets_path_rel)
                    if not secrets_path_abs.is_file():
                        errors.append(
                            f"YouTube 'client_secrets_file' path specified in {self.api_file} does not exist: {secrets_path_abs}")
                # else: _get_required_config handles missing/empty
            elif has_embedded_secrets:
                # Basic validation of embedded structure (e.g., check for 'web' or 'installed' key)
                if not ('web' in youtube_config['client_secrets_config'] or 'installed' in youtube_config['client_secrets_config']):
                    errors.append(
                        f"Invalid structure for 'client_secrets_config' in {self.api_file}. Expected a standard Google client secrets JSON object.")

            # Check if Google libraries were imported
            if None in [InstalledAppFlow, Credentials, build, HttpError, MediaFileUpload]:
                 errors.append(f"YouTube upload selected, but required Google libraries ('google-auth-oauthlib', 'google-api-python-client') are not installed.")

        # 4. Validate Selectors (Basic check for presence)
        ai_provider = self.config.get('AI_SETTINGS', 'provider', fallback='').lower()
        video_provider = self.config.get('VIDEO_SETTINGS', 'provider', fallback='').lower()

        providers_needing_selectors = []
        if 'browser' in ai_provider: providers_needing_selectors.append(ai_provider.replace('_browser',''))
        if 'browser' in video_provider: providers_needing_selectors.append(video_provider.replace('_browser',''))

        for provider in providers_needing_selectors:
            if provider not in self.selectors or not isinstance(self.selectors[provider], dict) or not self.selectors[provider]:
                errors.append(f"Missing or empty selectors section for '{provider}' in {self.selectors_file}")

        # --- Report Errors and Exit --- #
        if errors:
            for msg in errors:
                self.logger.error(f"Configuration Error: {msg}")
            self.logger.critical(
                "Critical configuration errors found. Please fix the issues in the INI/JSON files and restart.")
        else:
            self.logger.info("Core configuration validation passed.")

    def _resolve_paths(self):
        """Resolve relative paths from config files to absolute paths."""
        self.logger.info("Resolving configuration paths...")
        path_sections = ['PATHS'] # Add other sections with paths if needed

        for section in path_sections:
            if self.config.has_section(section):
                for key, value in self.config.items(section):
                    # Simple check: if it looks like a relative path, make it absolute
                    # Ensure value is not None or empty before checking
                    if value and not os.path.isabs(value) and ('/' in value or '\\' in value):
                        abs_path = (self.base_dir / value).resolve()
                        self.config.set(section, key, str(abs_path))
                        self.logger.info(f"Resolved path [{section}]{key}: {value} -> {abs_path}")
                    elif value:
                        # Ensure existing absolute paths are also resolved to handle '..' etc.
                        self.config.set(section, key, str(Path(value).resolve()))

        # Resolve paths within api.json (specifically for file paths like credentials)
        if 'youtube' in self.api_config:
            youtube_conf = self.api_config['youtube']
            for key in ['credentials_file', 'client_secrets_file']:
                value = youtube_conf.get(key)
                if isinstance(value, str) and value and not os.path.isabs(value):
                    abs_path = (self.base_dir / value).resolve()
                    youtube_conf[key] = str(abs_path)
                    self.logger.info(f"Resolved path api.json[youtube][{key}]: {value} -> {abs_path}")
                elif isinstance(value, str) and value:
                    youtube_conf[key] = str(Path(value).resolve())

    def get_config(self, section: str, key: str, fallback: Optional[Any] = None) -> Any:
        """Get a value from the INI config."""
        # Use fallback mechanism of configparser itself
        return self.config.get(section, key, fallback=fallback)

    def get_selector(self, section: str, key: str) -> Optional[List[str]]:
        """Get a selector list from the JSON config."""
        # Ensure the value is a list of strings
        selector_val = self.selectors.get(section, {}).get(key)
        if isinstance(selector_val, list) and all(isinstance(s, str) for s in selector_val):
            return selector_val
        elif isinstance(selector_val, str): # Allow single string selector
             return [selector_val]
        elif selector_val:
             self.logger.warning(f"Invalid selector format for [{section}]{key} in {self.selectors_file}. Expected list of strings or single string. Got: {type(selector_val)}")
        return None

    def get_api_config(self, section: str, key: Optional[str] = None) -> Any:
        """Get a value or section from the API JSON config."""
        if key:
            return self.api_config.get(section, {}).get(key)
        return self.api_config.get(section)

    def get_path(self, key: str) -> Path:
        """Get a resolved absolute path from the [PATHS] section."""
        path_str = self.config.get('PATHS', key)
        if not path_str:
            self.logger.critical(f"Required path key '{key}' not found or empty in [PATHS] section.")
        # Path should be resolved to absolute already
        return Path(path_str)

    def get_api_path(self, key: str) -> Optional[Path]:
        """Get a resolved absolute path from the api.json (youtube section). Handles potential missing key."""
        path_str = self.api_config.get('youtube', {}).get(key)
        if not path_str:
            # This might be okay if using embedded secrets, let the calling code handle it.
            return None # Return None if path is not found
        # Path should be resolved to absolute already
        return Path(path_str)

    def get_youtube_client_config(self) -> Union[Path, Dict, None]:
        """Gets the YouTube client secrets, preferring embedded config over file path.

        Returns:
            Path: Absolute path to the client_secrets_file if configured and exists.
            Dict: The embedded client_secrets_config dictionary if configured.
            None: If neither is configured correctly.
        """
        youtube_config = self.api_config.get('youtube', {})
        embedded_secrets = youtube_config.get('client_secrets_config')
        secrets_file_path_str = youtube_config.get('client_secrets_file')

        if embedded_secrets and isinstance(embedded_secrets, dict):
            self.logger.info("Using embedded YouTube client secrets from api.json['youtube']['client_secrets_config']")
            return embedded_secrets
        elif secrets_file_path_str:
            # Path should already be resolved to absolute by _resolve_paths
            secrets_file_path = Path(secrets_file_path_str)
            if secrets_file_path.is_file():
                self.logger.info(f"Using YouTube client secrets file: {secrets_file_path}")
                return secrets_file_path
            else:
                # This case should have been caught by validation, but double-check
                self.logger.error(
                    f"YouTube 'client_secrets_file' path configured but file not found: {secrets_file_path}")
                return None
        else:
            # This case should also have been caught by validation
            self.logger.error("No valid YouTube client secrets configuration found in api.json.")
            return None


# --- Browser Manager Class ---
class BrowserManager:
    """Manages the Selenium WebDriver instance.
       Can launch a new browser or connect to an existing one via debugger port.
       Includes fallback logic for connection failures.
       Uses webdriver-manager for automatic driver handling.
    """

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = Logger()
        self.driver = None
        self.wait_timeout = int(config_manager.get_config('BROWSER_SETTINGS', 'wait_timeout', 30))
        self.retry_attempts = int(config_manager.get_config('BROWSER_SETTINGS', 'retry_attempts', 2))
        self.page_load_timeout = int(config_manager.get_config('BROWSER_SETTINGS', 'page_load_timeout', 60))
        self._connected_via_debugger = False # Flag to track connection method
        # Store browser settings locally for easier access in _init_driver
        self.browser_type = config_manager.get_config('BROWSER_SETTINGS', 'primary_browser', 'chrome').lower()
        self.user_data_dir = config_manager.get_config('BROWSER_SETTINGS', 'user_data_dir')
        self.headless = config_manager.get_config('BROWSER_SETTINGS', 'headless_mode', 'true').lower() == 'true'
        self.debugger_port_str = config_manager.get_config('BROWSER_SETTINGS', 'debugger_port', fallback=None)
        self.debugger_port = None
        if self.debugger_port_str:
            try:
                self.debugger_port = int(self.debugger_port_str)
            except ValueError:
                self.logger.warning(f"Invalid debugger_port '{self.debugger_port_str}', ignoring. Will launch new browser.")
                self.debugger_port = None # Ensure it's None if invalid

    def _configure_options(self, use_user_data_dir: bool = True) -> Union[ChromeOptions, EdgeOptions, None]:
        """Creates and configures browser options."""
        options: Union[ChromeOptions, EdgeOptions]
        if self.browser_type == 'chrome':
            options = ChromeOptions()
            # Specify binary location if using Chromium snap (common path)
            # Check if the standard snap path exists
            chromium_snap_path = "/snap/chromium/current/usr/lib/chromium-browser/chrome"
            if Path(chromium_snap_path).is_file():
                 options.binary_location = chromium_snap_path
                 self.logger.info(f"Using Chromium binary location: {chromium_snap_path}")
            # else: rely on webdriver-manager finding it

            options.add_experimental_option('excludeSwitches', ['enable-logging']) # Suppress DevTools messages
        elif self.browser_type == 'edge':
            options = EdgeOptions()
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
        else:
            self.logger.error(f"Unsupported browser type specified: {self.browser_type}")
            return None

        # Common options
        if self.headless: options.add_argument('--headless')
        options.add_argument('--no-sandbox') # Often needed in containerized environments
        options.add_argument('--disable-dev-shm-usage') # Overcomes limited resource problems
        options.add_argument('--disable-gpu') # Applicable to headless
        options.add_argument("--window-size=1920,1080") # Standard window size
        options.add_argument("--lang=en-US") # Set language
        options.add_argument("--disable-extensions") # Disable extensions
        options.add_argument("--disable-popup-blocking") # Disable popup blocking

        # User data directory (only if requested and valid)
        if use_user_data_dir and self.user_data_dir:
            resolved_user_data_dir = Path(self.user_data_dir)
            self.logger.info(f"Attempting to use user data directory: {resolved_user_data_dir}")
            options.add_argument(f"user-data-dir={resolved_user_data_dir}")
        elif not use_user_data_dir and self.user_data_dir:
             self.logger.info("User data directory specified but being skipped for this attempt.")

        return options

    def _init_driver(self):
        """Initializes the WebDriver using webdriver-manager,
           trying debugger port first, then new instance.
           Includes fallbacks for connection failures and user_data_dir issues.
        """
        driver = None
        attempt_debugger = bool(self.debugger_port)

        # --- Attempt 1: Connect via Debugger Port (if configured) ---
        if attempt_debugger:
            debugger_address = f"127.0.0.1:{self.debugger_port}"
            self.logger.info(f"Attempting to connect to existing browser via debugger address: {debugger_address}")
            options = self._configure_options(use_user_data_dir=False) # Don't specify user dir when connecting
            if not options: return None # Unsupported browser type

            options.add_experimental_option("debuggerAddress", debugger_address)

            try:
                if self.browser_type == 'chrome':
                    # Use webdriver-manager to get the correct service for the *potentially running* browser version
                    # This might still fail if the running browser is drastically different, but it's the best guess.
                    service = ChromeService(ChromeDriverManager().install())
                    driver = webdriver.Chrome(service=service, options=options)
                elif self.browser_type == 'edge':
                    service = EdgeService(EdgeChromiumDriverManager().install())
                    driver = webdriver.Edge(service=service, options=options)

                # Verify connection by getting title (might throw exception if connection failed)
                self.logger.info(f"Connected to browser. Current page title: {driver.title}")
                self.logger.success(f"Successfully connected to existing {self.browser_type} browser via debugger port {self.debugger_port}.")
                self._connected_via_debugger = True

            except WebDriverException as e:
                self.logger.warning(f"Failed to connect to browser via debugger port {self.debugger_port}: {e}")
                if "unable to connect" in str(e).lower() or "connection refused" in str(e).lower():
                    self.logger.warning("Ensure the browser was launched with --remote-debugging-port="
                                        f"{self.debugger_port} and is running.")
                driver = None # Ensure driver is None if connection failed
                self._connected_via_debugger = False
            except Exception as e:
                 self.logger.error(f"An unexpected error occurred connecting via debugger port: {e}")
                 driver = None
                 self._connected_via_debugger = False

        # --- Attempt 2: Launch New Browser Instance (if debugger failed or wasn't attempted) ---
        if not driver:
            self.logger.info(f"Launching new {self.browser_type} browser instance...")
            initial_launch_failed = False

            # Try 2a: Launch WITH user_data_dir (if specified)
            options = self._configure_options(use_user_data_dir=True)
            if not options: return None # Unsupported browser type

            try:
                if self.browser_type == 'chrome':
                    self.logger.info("Using webdriver-manager to install/manage ChromeDriver...")
                    service = ChromeService(ChromeDriverManager().install())
                    driver = webdriver.Chrome(service=service, options=options)
                elif self.browser_type == 'edge':
                    self.logger.info("Using webdriver-manager to install/manage EdgeDriver...")
                    service = EdgeService(EdgeChromiumDriverManager().install())
                    driver = webdriver.Edge(service=service, options=options)

                self.logger.success(f"New {self.browser_type.capitalize()} browser initialized successfully.")
                self._connected_via_debugger = False

            except WebDriverException as e:
                self.logger.warning(f"Failed to initialize {self.browser_type} WebDriver: {e}")
                initial_launch_failed = True
                driver = None # Ensure driver is None
                # Specific check if user_data_dir might be the cause
                if self.user_data_dir:
                    self.logger.warning(f"Initial launch failed. Retrying without user_data_dir ('{self.user_data_dir}')...")
                # else: If no user_data_dir was used, the failure is likely due to other reasons (driver version, browser path)

            except Exception as e:
                 self.logger.error(f"An unexpected error occurred during initial browser launch: {e}")
                 initial_launch_failed = True # Treat as failure
                 driver = None # Ensure driver is None

            # Try 2b: Launch WITHOUT user_data_dir (if 2a failed and user_data_dir was used)
            if initial_launch_failed and self.user_data_dir:
                options = self._configure_options(use_user_data_dir=False) # Explicitly disable user_data_dir
                if not options: return None # Unsupported browser type
                try:
                    if self.browser_type == 'chrome':
                        self.logger.info("Using webdriver-manager to install/manage ChromeDriver (retry without user_data_dir)...")
                        service = ChromeService(ChromeDriverManager().install())
                        driver = webdriver.Chrome(service=service, options=options)
                    elif self.browser_type == 'edge':
                        self.logger.info("Using webdriver-manager to install/manage EdgeDriver (retry without user_data_dir)...")
                        service = EdgeService(EdgeChromiumDriverManager().install())
                        driver = webdriver.Edge(service=service, options=options)

                    self.logger.success(f"New {self.browser_type.capitalize()} browser initialized successfully (without user_data_dir).")
                    self._connected_via_debugger = False

                except WebDriverException as e:
                    self.logger.error(f"Failed to initialize {self.browser_type} WebDriver even without user_data_dir: {e}")
                    # Check for common critical errors after retrying
                    if "net::ERR_CONNECTION_REFUSED" in str(e):
                        self.logger.critical(
                            f"Connection refused. Ensure WebDriver service for {self.browser_type} is running or accessible.")
                    elif "session not created" in str(e).lower():
                         # Often indicates driver/browser version mismatch, though webdriver-manager should prevent this.
                         # Could also be permission issues or browser crashing immediately.
                         self.logger.critical(f"'Session not created' error. Check browser compatibility, permissions, or if the browser is crashing on startup. Error: {e}")
                    else:
                         self.logger.critical(f"Failed to initialize {self.browser_type} WebDriver after retries: {e}")
                    driver = None # Ensure driver is None
                except Exception as e:
                     self.logger.critical(f"An unexpected error occurred launching browser (without user_data_dir): {e}")
                     driver = None # Ensure driver is None

        # --- Final Check and Return --- #
        if driver:
            self.driver = driver
            self.driver.set_page_load_timeout(self.page_load_timeout)
            return self.driver
        else:
            # If we reach here, all attempts failed. A critical error should have been logged already.
            # Adding a final critical log just in case logic above missed something.
            self.logger.critical(f"All attempts to initialize or connect to {self.browser_type} browser failed.")
            return None # Should not be reached due to critical logs

    def get_driver(self):
        """Returns the WebDriver instance, initializing if needed."""
        if not self.driver:
            self._init_driver()
            # Check again if driver is still None after init attempt (critical error occurred)
            if not self.driver:
                 # A critical error was logged, but we need to stop execution flow here
                 # Raising an exception might be better than sys.exit within get_driver
                 raise RuntimeError("Browser initialization failed. Check logs for critical errors.")
        return self.driver

    def close_driver(self):
        """Closes the WebDriver if it's running, but only quits if not connected via debugger."""
        if self.driver:
            try:
                if self._connected_via_debugger:
                    self.logger.info("Detaching from browser (connected via debugger port). Browser remains open.")
                    # Don't quit the browser, just release the driver instance
                    # Setting driver to None might be enough, no explicit detach method
                else:
                    self.logger.info("Closing browser...")
                    self.driver.quit()
                    self.logger.info("Browser closed.")
            except WebDriverException as e:
                # Handle case where browser might have already crashed or closed
                if "disconnected" in str(e) or "unable to connect" in str(e):
                    self.logger.warning(f"Browser seems to have already closed or disconnected: {e}")
                else:
                    self.logger.error(f"Error closing/detaching browser: {e}")
            except Exception as e:
                 self.logger.error(f"Unexpected error closing/detaching browser: {e}")
            finally:
                 self.driver = None # Ensure driver is set to None
                 self._connected_via_debugger = False # Reset flag

    def navigate(self, url: str) -> bool:
        """Navigates the browser to a URL with retries."""
        try:
            driver = self.get_driver()
        except RuntimeError as e:
             self.logger.error(f"Cannot navigate: {e}")
             return False

        self.logger.info(f"Navigating to: {url}")
        for attempt in range(self.retry_attempts + 1):
            try:
                driver.get(url)
                # Basic check for page load - more specific checks should be done after navigation
                WebDriverWait(driver, self.wait_timeout).until(
                    lambda d: d.execute_script('return document.readyState') == 'complete'
                )
                self.logger.success(f"Successfully navigated to: {url}")
                return True
            except TimeoutException:
                self.logger.warning(f"Timeout loading page {url} (Attempt {attempt + 1}/{self.retry_attempts + 1})")
            except WebDriverException as e:
                # Check if browser crashed
                if "disconnected" in str(e) or "target crashed" in str(e):
                     self.logger.error(f"Browser crashed or disconnected during navigation to {url}. Attempting to close.")
                     self.close_driver() # Attempt cleanup
                     return False # Cannot continue
                self.logger.warning(
                    f"WebDriverException during navigation to {url}: {e} (Attempt {attempt + 1}/{self.retry_attempts + 1})")
            except Exception as e:
                self.logger.error(
                    f"Unexpected error navigating to {url}: {e} (Attempt {attempt + 1}/{self.retry_attempts + 1})")

            if attempt < self.retry_attempts:
                self.logger.info(f"Retrying navigation in {2 ** attempt} seconds...")
                time.sleep(2 ** attempt) # Exponential backoff
            else:
                self.logger.error(f"Failed to navigate to {url} after {self.retry_attempts + 1} attempts.")
                # Consider taking screenshot self.take_screenshot(f"navigate_fail_{url.split('/')[-1]}")
                return False
        return False # Should not be reached

    def find_element(self, selectors: List[str], timeout: Optional[int] = None, visible: bool = False) -> Optional[Any]:
        """Finds an element using a list of selectors (CSS or XPath).
           Waits for presence by default, optionally waits for visibility.
        """
        try:
            driver = self.get_driver()
        except RuntimeError as e:
             self.logger.error(f"Cannot find element: {e}")
             return None
        if not selectors:
            self.logger.warning("find_element called with empty selectors list.")
            return None

        wait_time = timeout if timeout is not None else self.wait_timeout
        wait = WebDriverWait(driver, wait_time)
        condition = EC.visibility_of_element_located if visible else EC.presence_of_element_located
        condition_desc = "visible" if visible else "present"

        last_exception = None
        for selector in selectors:
            try:
                locator = (By.XPATH, selector) if selector.startswith('/') or selector.startswith('(') else (By.CSS_SELECTOR, selector)
                element = wait.until(condition(locator))
                self.logger.info(f"Found {condition_desc} element using {locator[0]}: {selector}")
                return element
            except TimeoutException:
                # Logged as debug, as trying multiple selectors is expected
                self.logger.info(f"Element not {condition_desc} within {wait_time}s using selector: {selector}")
                last_exception = TimeoutException(f"Timeout waiting for {selector}")
            except NoSuchElementException: # Should be caught by wait, but just in case
                 self.logger.info(f"Element not found using selector: {selector}")
                 last_exception = NoSuchElementException(f"Not found: {selector}")
            except WebDriverException as e:
                 # Check for browser crash
                 if "disconnected" in str(e) or "target crashed" in str(e):
                      self.logger.error(f"Browser crashed or disconnected while finding element: {selector}. Attempting to close.")
                      self.close_driver() # Attempt cleanup
                      raise RuntimeError("Browser crashed while finding element.") from e # Propagate critical failure
                 self.logger.error(f"WebDriver error finding element with selector {selector}: {e}")
                 last_exception = e
            except Exception as e:
                self.logger.error(f"Unexpected error finding element with selector {selector}: {e}")
                last_exception = e

        self.logger.error(f"Element not found or not {condition_desc} using any provided selectors: {selectors}")
        # Optionally re-raise the last exception if needed for control flow
        # if last_exception: raise last_exception
        return None

    def click_element(self, element_or_selectors: Union[Any, List[str]], timeout: Optional[int] = None) -> bool:
        """Clicks an element, finding it first if selectors are provided.
           Waits for the element to be clickable.
        """
        element = None
        if isinstance(element_or_selectors, list):
            # Find the element first (wait for presence/visibility based on need)
            # For clicking, usually presence is enough, then wait for clickable
            try:
                 element = self.find_element(element_or_selectors, timeout, visible=False)
            except RuntimeError as e: # Catch browser crash during find_element
                 self.logger.error(f"Cannot click element: {e}")
                 return False
        else:
            element = element_or_selectors # Assume it's already a WebElement

        if not element:
            self.logger.error("Cannot click element: Element not found or provided.")
            return False

        try:
            driver = self.get_driver()
        except RuntimeError as e:
             self.logger.error(f"Cannot click element: {e}")
             return False

        wait_time = timeout if timeout is not None else self.wait_timeout
        element_text = element.text[:50].replace('\n', ' ') if hasattr(element, 'text') and element.text else "(no text)"
        element_tag = element.tag_name if hasattr(element, 'tag_name') else "(unknown tag)"
        element_desc = f"<{element_tag}> '{element_text}...'"

        for attempt in range(self.retry_attempts + 1):
            try:
                # Wait for element to be clickable
                self.logger.info(f"Waiting for element {element_desc} to be clickable...")
                clickable_element = WebDriverWait(driver, wait_time).until(EC.element_to_be_clickable(element))
                # Use JavaScript click as a fallback for stubborn elements
                # driver.execute_script("arguments[0].click();", clickable_element)
                clickable_element.click()
                self.logger.success(f"Clicked element {element_desc} successfully.")
                return True
            except TimeoutException:
                self.logger.warning(f"Timeout waiting for element {element_desc} to be clickable (Attempt {attempt + 1}/{self.retry_attempts + 1})")
            except WebDriverException as e:
                 # Check for browser crash
                 if "disconnected" in str(e) or "target crashed" in str(e):
                      self.logger.error(f"Browser crashed or disconnected while clicking element {element_desc}. Attempting to close.")
                      self.close_driver() # Attempt cleanup
                      return False # Cannot continue
                 # Handle ElementClickInterceptedException, etc.
                 self.logger.warning(
                     f"WebDriverException clicking element {element_desc}: {e} (Attempt {attempt + 1}/{self.retry_attempts + 1})")
                 # Try scrolling into view? Requires element, not clickable_element
                 try:
                      driver.execute_script("arguments[0].scrollIntoView(true);", element)
                      time.sleep(0.5)
                 except Exception as scroll_err:
                      self.logger.warning(f"Failed to scroll element into view: {scroll_err}")
            except Exception as e:
                self.logger.error(
                    f"Unexpected error clicking element {element_desc}: {e} (Attempt {attempt + 1}/{self.retry_attempts + 1})")

            if attempt < self.retry_attempts:
                self.logger.info(f"Retrying click in {1 + attempt * 0.5} seconds...") # Shorter backoff for clicks
                time.sleep(1 + attempt * 0.5)
            else:
                self.logger.error(f"Failed to click element {element_desc} after {self.retry_attempts + 1} attempts.")
                self.take_screenshot(f"click_fail_{element_tag}")
                return False
        return False # Should not be reached

    def input_text(self, element_or_selectors: Union[Any, List[str]], text: str, clear_first: bool = True, timeout: Optional[int] = None) -> bool:
        """Inputs text into an element, finding it first if selectors are provided.
           Waits for the element to be visible.
        """
        element = None
        if isinstance(element_or_selectors, list):
            try:
                # Wait for visibility before inputting text
                element = self.find_element(element_or_selectors, timeout, visible=True)
            except RuntimeError as e: # Catch browser crash during find_element
                 self.logger.error(f"Cannot input text: {e}")
                 return False
        else:
            element = element_or_selectors # Assume it's already a WebElement

        if not element:
            self.logger.error("Cannot input text: Element not found or provided.")
            return False

        element_text = element.get_attribute('name') or element.get_attribute('id') or element.tag_name
        element_desc = f"<{element.tag_name}> ({element_text})"

        for attempt in range(self.retry_attempts + 1):
            try:
                if clear_first:
                    # Use CTRL+A and Delete for more reliable clearing
                    element.send_keys(Keys.CONTROL + "a")
                    element.send_keys(Keys.DELETE)
                    # element.clear() # clear() can sometimes be unreliable
                    time.sleep(0.2) # Small pause after clearing
                element.send_keys(text)
                self.logger.success(f"Input text into element {element_desc} successfully.")
                return True
            except WebDriverException as e:
                 # Check for browser crash
                 if "disconnected" in str(e) or "target crashed" in str(e):
                      self.logger.error(f"Browser crashed or disconnected while inputting text into {element_desc}. Attempting to close.")
                      self.close_driver() # Attempt cleanup
                      return False # Cannot continue
                 self.logger.warning(
                     f"WebDriverException inputting text into {element_desc}: {e} (Attempt {attempt + 1}/{self.retry_attempts + 1})")
            except Exception as e:
                self.logger.error(
                    f"Unexpected error inputting text into {element_desc}: {e} (Attempt {attempt + 1}/{self.retry_attempts + 1})")

            if attempt < self.retry_attempts:
                self.logger.info(f"Retrying input in {1 + attempt * 0.5} seconds...")
                time.sleep(1 + attempt * 0.5)
                # Try finding the element again in case the page refreshed
                if isinstance(element_or_selectors, list):
                    try:
                        element = self.find_element(element_or_selectors, timeout, visible=True)
                        if not element: break # Stop retrying if element is gone
                    except RuntimeError: # Browser crash
                         return False
                    except Exception:
                         break # Stop retrying if element cannot be found
            else:
                self.logger.error(f"Failed to input text into {element_desc} after {self.retry_attempts + 1} attempts.")
                self.take_screenshot(f"input_fail_{element.tag_name}")
                return False
        return False # Should not be reached

    def take_screenshot(self, filename_prefix: str = "screenshot") -> Optional[Path]:
        """Takes a screenshot and saves it to the logs directory."""
        try:
            driver = self.get_driver()
        except RuntimeError as e:
             self.logger.error(f"Cannot take screenshot: {e}")
             return None

        try:
            # Use the logger's log file path to determine the logs directory
            log_dir = self.config_manager.logger.log_file.parent
        except AttributeError:
             # Fallback if logger or its path isn't set up correctly
             log_dir = self.config_manager.base_dir / "logs"
             self.logger.warning(f"Could not determine log directory from logger, using default: {log_dir}")

        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = log_dir / f"{filename_prefix}_{timestamp}.png"
            if driver.save_screenshot(str(filepath)):
                self.logger.info(f"Screenshot saved to: {filepath}")
                return filepath
            else:
                 self.logger.error(f"Failed to save screenshot to {filepath} (driver returned false).")
                 return None
        except WebDriverException as e:
             # Check for browser crash
             if "disconnected" in str(e) or "target crashed" in str(e):
                  self.logger.error(f"Browser crashed or disconnected before taking screenshot. Attempting to close.")
                  self.close_driver() # Attempt cleanup
             else:
                  self.logger.error(f"WebDriverException taking screenshot: {e}")
        except Exception as e:
            self.logger.error(f"❌ Failed to take screenshot: {e}")
        return None

    def wait_for_download_complete(self, download_dir: Path, initial_files: set, timeout: int = 300) -> Optional[Path]:
        """Waits for a new file to appear and stabilize in the download directory."""
        self.logger.info(f"Waiting up to {timeout} seconds for download to complete in: {download_dir}")
        start_time = time.time()
        last_found_temp_file = None
        last_size = -1
        stable_count = 0

        while time.time() - start_time < timeout:
            try:
                current_files = set(p for p in download_dir.iterdir() if p.is_file())
            except FileNotFoundError:
                self.logger.warning(f"Download directory {download_dir} not found yet. Waiting...")
                time.sleep(5)
                continue
            except Exception as e:
                self.logger.error(f"Error listing files in download directory {download_dir}: {e}")
                return None # Cannot proceed if directory is inaccessible

            new_files = current_files - initial_files
            potential_file = None

            if new_files:
                # Prioritize non-temporary files
                non_temp_files = [f for f in new_files if not str(f).endswith(('.tmp', '.crdownload', '.part'))]
                if non_temp_files:
                    potential_file = non_temp_files[0] # Assume first non-temp is the one
                    if last_found_temp_file and last_found_temp_file.stem == potential_file.stem:
                         self.logger.info(f"Temporary file {last_found_temp_file.name} likely completed as {potential_file.name}")
                         last_found_temp_file = None # Reset temp file tracking
                else:
                    # If only temp files are new, track the first one
                    temp_files = list(new_files)
                    if not last_found_temp_file or last_found_temp_file.name != temp_files[0].name:
                        last_found_temp_file = temp_files[0]
                        self.logger.info(f"Detected temporary download file: {last_found_temp_file.name}. Waiting...")
                    # Keep waiting if only temp file found
                    potential_file = None

            if potential_file:
                # Check if file size is stable
                try:
                    current_size = potential_file.stat().st_size
                    if current_size == last_size and current_size > 0:
                        stable_count += 1
                    else:
                        stable_count = 0 # Reset count if size changes or is zero
                        last_size = current_size

                    if stable_count >= 2: # Require 2 stable checks (e.g., 4 seconds apart)
                        self.logger.success(f"Download detected and appears complete: {potential_file} (Size: {current_size} bytes)")
                        return potential_file
                    else:
                        self.logger.info(
                            f"Detected new file {potential_file.name}, size {current_size} bytes. Checking stability (Stable count: {stable_count})...")

                except FileNotFoundError:
                    # File might have been quickly renamed or deleted, reset and continue
                    self.logger.warning(f"Detected file {potential_file.name} disappeared. Resetting search...")
                    initial_files = current_files # Update baseline
                    last_found_temp_file = None
                    last_size = -1
                    stable_count = 0
                    continue
                except Exception as e:
                    self.logger.error(f"Error checking file {potential_file.name} status: {e}")
                    # Continue waiting, maybe it's a transient issue

            # Wait before next check
            time.sleep(2)

        self.logger.error(f"Timeout waiting for download to complete in {download_dir}.")
        if last_found_temp_file:
             self.logger.error(f"Last detected temporary file was: {last_found_temp_file.name}")
        return None


# --- Script Generator Class ---
class ScriptGenerator:
    """Generates script text using the configured AI provider (API or Browser)."""

    def __init__(self, config_manager: ConfigManager, browser_manager: Optional[BrowserManager] = None):
        self.config_manager = config_manager
        self.browser_manager = browser_manager # Only needed for browser-based AI
        self.logger = Logger()
        self.ai_provider = config_manager.get_config('AI_SETTINGS', 'provider').lower()
        self.prompt = config_manager.get_config('AI_SETTINGS', 'ai_prompt')

    def generate_script(self) -> Optional[str]:
        """Generates the script using the appropriate method based on provider."""
        self.logger.info(f"Generating script using AI provider: {self.ai_provider}")

        if self.ai_provider == 'gemini':
            return self._generate_with_gemini()
        elif self.ai_provider in ['chatgpt_browser', 'grok_browser']:
            if not self.browser_manager:
                self.logger.critical("BrowserManager is required for browser-based AI providers but was not provided.")
            return self._generate_with_browser()
        # Add other providers here
        # elif self.ai_provider == 'some_other_api':
        #     return self._generate_with_some_other_api()
        else:
            self.logger.critical(f"Unsupported AI provider configured: {self.ai_provider}")
            return None

    def _generate_with_gemini(self) -> Optional[str]:
        """Generates script using the Gemini API."""
        if not genai:
            self.logger.critical("Gemini provider selected, but 'google-generativeai' library is not installed.")

        api_key = self.config_manager.get_api_config('gemini', 'api_key')
        if not api_key:
            self.logger.critical("Gemini API key is missing or empty in api.json.")

        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-pro') # Or specify another model if needed
            self.logger.info("Sending prompt to Gemini API...")
            # Add safety settings if needed
            # safety_settings = [...]
            # response = model.generate_content(self.prompt, safety_settings=safety_settings)
            response = model.generate_content(self.prompt)

            # More robust check for response content
            if not response.parts:
                block_reason = getattr(response.prompt_feedback, 'block_reason', None)
                safety_ratings = getattr(response.prompt_feedback, 'safety_ratings', [])
                if block_reason:
                    self.logger.error(f"❌ Gemini API request blocked. Reason: {block_reason}")
                elif safety_ratings:
                     self.logger.error(f"❌ Gemini API response potentially blocked due to safety ratings: {safety_ratings}")
                else:
                    self.logger.error("❌ Gemini API returned an empty response with no specific block reason.")
                # Log candidates if available for debugging
                try:
                     self.logger.info(f"Gemini Candidates (if any): {response.candidates}")
                except Exception:
                     pass # Ignore if candidates attribute doesn't exist or causes error
                return None

            # Access text safely
            try:
                script_text = response.text
            except ValueError as e:
                 # Handle cases where response.text access fails (e.g., function calls in response)
                 self.logger.error(f"❌ Failed to extract text from Gemini response: {e}")
                 self.logger.info(f"Full Gemini Response: {response}")
                 return None

            self.logger.success("Received response from Gemini API.")
            # Perform basic validation of the expected format
            if not self._validate_ai_response_format(script_text):
                self.logger.error("AI response format validation failed. Check log for details.")
                # Log the problematic response for debugging
                self.logger.info(f"Problematic AI Response:\n---\n{script_text}\n---")
                return None
            return script_text
        except Exception as e:
            self.logger.error(f"❌ Error interacting with Gemini API: {e}")
            return None

    def _generate_with_browser(self) -> Optional[str]:
        """Generates script using browser automation (ChatGPT or Grok)."""
        if not self.browser_manager:
            self.logger.critical(
                "Browser interaction required but BrowserManager not available.") # Should be caught earlier

        provider_key = 'chatgpt' if self.ai_provider == 'chatgpt_browser' else 'grok'
        # Get URL from config, fallback to None if missing
        ai_url = self.config_manager.get_config('AI_SETTINGS', f'{provider_key}_url', fallback=None)
        selectors = self.config_manager.selectors.get(provider_key, {})

        if not ai_url:
            self.logger.critical(
                f"URL for {provider_key} ({provider_key}_url) not found or empty in customisation.ini [AI_SETTINGS].")
        if not selectors:
            self.logger.critical(f"Selectors for {provider_key} not found in selectors.json.")

        # --- Define selectors --- (Get required selectors, fail if missing)
        # Use get_selector for robust handling of single/list selectors
        prompt_sel = self.config_manager.get_selector(provider_key, 'prompt_input') or \
                     self.config_manager.get_selector(provider_key, 'prompt_textarea')
        send_sel = self.config_manager.get_selector(provider_key, 'send_button') or \
                   self.config_manager.get_selector(provider_key, 'submit_button')
        response_sel = self.config_manager.get_selector(provider_key, 'response_area_last') or \
                       self.config_manager.get_selector(provider_key, 'response_output_last')
        # Optional: Selector to detect when generation is complete (e.g., regenerate button appears)
        completion_indicator_sel = self.config_manager.get_selector(provider_key, 'response_regenerate_button')
        # Optional: Selector for potential login/cookie consent elements
        login_popup_close_sel = self.config_manager.get_selector(provider_key, 'login_popup_close_button')
        cookie_accept_sel = self.config_manager.get_selector(provider_key, 'cookie_accept_button')

        if not all([prompt_sel, send_sel, response_sel]):
            self.logger.critical(
                f"Missing required selectors for {provider_key} in selectors.json. Need prompt input, send button, and response area selectors.")

        # --- Browser Automation ---
        try:
            if not self.browser_manager.navigate(ai_url):
                return None

            # Handle potential overlays (login popups, cookie banners)
            time.sleep(2) # Allow overlays to appear
            if login_popup_close_sel:
                 if self.browser_manager.click_element(login_popup_close_sel, timeout=5):
                      self.logger.info("Closed login/signup popup.")
                      time.sleep(1)
                 else:
                      self.logger.info("Login/signup popup not found or could not be closed.")
            if cookie_accept_sel:
                 if self.browser_manager.click_element(cookie_accept_sel, timeout=5):
                      self.logger.info("Accepted cookies.")
                      time.sleep(1)
                 else:
                      self.logger.info("Cookie banner not found or could not be accepted.")

            # Input prompt
            if not self.browser_manager.input_text(prompt_sel, self.prompt):
                self.logger.error(f"Failed to input prompt into {provider_key}.")
                self.browser_manager.take_screenshot(f"{provider_key}_input_fail")
                return None
            time.sleep(1) # Brief pause after input

            # Send prompt
            if not self.browser_manager.click_element(send_sel):
                self.logger.error(f"Failed to click send button for {provider_key}.")
                self.browser_manager.take_screenshot(f"{provider_key}_send_fail")
                return None

            self.logger.info(f"Prompt sent to {provider_key}. Waiting for response...")

            # Wait for response generation to complete
            generation_timeout = 180 # Increased timeout for AI generation
            wait_start_time = time.time()
            response_text = None

            # Strategy 1: Wait for a specific indicator element (more reliable)
            if completion_indicator_sel:
                self.logger.info(f"Waiting for completion indicator: {completion_indicator_sel}")
                indicator_element = self.browser_manager.find_element(completion_indicator_sel, timeout=generation_timeout)
                if not indicator_element:
                    self.logger.error(
                        f"Timeout waiting for response completion indicator ({completion_indicator_sel}) from {provider_key}.")
                    self.browser_manager.take_screenshot(f"{provider_key}_completion_timeout")
                    # Try to grab text anyway if indicator fails
                    response_element = self.browser_manager.find_element(response_sel, timeout=5)
                    if response_element and response_element.text:
                        self.logger.warning("Completion indicator timeout, but found response text. Proceeding cautiously.")
                        response_text = response_element.text
                    else:
                        return None # Fail if indicator doesn't appear and no text found
                else:
                    self.logger.info(f"Response generation appears complete (indicator found).")
                    # Add a small delay AFTER indicator appears, sometimes needed for text to fully render
                    time.sleep(2)
                    # Get the final response text now
                    response_element = self.browser_manager.find_element(response_sel, timeout=5)
                    if response_element:
                         response_text = response_element.text
                    else:
                         self.logger.error(f"Found completion indicator, but failed to find response element ({response_sel}).")
                         return None
            # Strategy 2: Wait for response area text to stabilize (less reliable)
            else:
                self.logger.warning(
                    "No completion indicator selector found. Using text stabilization check (less reliable).")
                last_text = ""
                stable_count = 0
                while time.time() - wait_start_time < generation_timeout:
                    response_element = self.browser_manager.find_element(response_sel, timeout=5)
                    current_text = response_element.text if response_element else ""

                    if current_text and current_text == last_text:
                        stable_count += 1
                    else:
                        stable_count = 0
                        last_text = current_text

                    if stable_count >= 3: # Require 3 stable checks (e.g., 6 seconds)
                        self.logger.info(f"Response text appears stable after {int(time.time() - wait_start_time)} seconds.")
                        response_text = current_text
                        break
                    elif current_text:
                         self.logger.info(f"Waiting for response text to stabilize... (Length: {len(current_text)}, Stable: {stable_count})")
                    else:
                         self.logger.info(f"Waiting for response element/text...")

                    time.sleep(2)
                else: # Loop finished without breaking (timeout)
                    self.logger.error(f"Timeout waiting for response text to stabilize from {provider_key}.")
                    self.browser_manager.take_screenshot(f"{provider_key}_stabilize_timeout")
                    # Use last captured text if available
                    if last_text:
                         self.logger.warning("Using last captured text before timeout.")
                         response_text = last_text
                    else:
                         return None

            # --- Process Response ---
            if not response_text:
                self.logger.error(f"Failed to retrieve response text from {provider_key}.")
                self.browser_manager.take_screenshot(f"{provider_key}_no_response_text")
                return None

            self.logger.success(f"Received response from {provider_key}.")
            # Validate format
            if not self._validate_ai_response_format(response_text):
                self.logger.error(f"AI response format validation failed for {provider_key}. Check log for details.")
                self.logger.info(f"Problematic AI Response from {provider_key}:\n---\n{response_text}\n---")
                return None

            return response_text

        except RuntimeError as e: # Catch browser crash from find/click/input
             self.logger.error(f"❌ Browser crashed during interaction with {provider_key}: {e}")
             return None
        except Exception as e:
            self.logger.error(f"❌ An unexpected error occurred during browser interaction with {provider_key}: {e}")
            self.browser_manager.take_screenshot(f"{provider_key}_error")
            return None

    def _validate_ai_response_format(self, response_text: str) -> bool:
        """Validates if the AI response contains the required sections."""
        required_headers = ["SCRIPT:", "TITLE:", "DESCRIPTION:", "KEYWORDS:"]
        missing = []
        found_any = False
        for header in required_headers:
            # Use regex for case-insensitivity and potential leading/trailing whitespace
            if re.search(rf"^\s*{re.escape(header)}", response_text, re.IGNORECASE | re.MULTILINE):
                 found_any = True
            else:
                 missing.append(header)

        if not found_any:
             self.logger.error("AI response does not contain ANY of the required section headers.")
             return False
        elif missing:
            self.logger.warning(
                f"AI response is missing optional sections (case-insensitive check): {', '.join(missing)}")
            # Allow missing sections for now, but log warning
            # return False # Uncomment this line to make all sections strictly required

        # Optional: Add more checks (e.g., check if sections have content)
        self.logger.info("AI response format validated successfully (or warnings logged).")
        return True

    def save_script(self, script_content: str) -> Optional[Path]:
        """Saves the generated script content to a timestamped file."""
        try:
            scripts_dir = self.config_manager.get_path('scripts_dir')
            scripts_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"generated_script_{timestamp}.txt"
            filepath = scripts_dir / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(script_content)
            self.logger.success(f"Script saved successfully to: {filepath}")
            return filepath
        except Exception as e:
            self.logger.error(f"❌ Failed to save script to {self.config_manager.get_config('PATHS', 'scripts_dir')}: {e}")
            return None

    @staticmethod
    def parse_script_file(script_filepath: Path) -> Optional[Dict[str, Any]]:
        """Parses a saved script file to extract metadata sections.
           Handles case-insensitivity and extracts content accurately.
        """
        logger = Logger() # Get logger instance
        if not script_filepath.is_file():
            logger.error(f"Script file not found for parsing: {script_filepath}")
            return None

        try:
            with open(script_filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            metadata = {}
            # Define headers and their corresponding keys in the output dict
            section_map = {
                "SCRIPT": "script",
                "TITLE": "title",
                "DESCRIPTION": "description",
                "KEYWORDS": "tags" # Map KEYWORDS: to 'tags' key
            }
            # Create regex pattern to find headers (case-insensitive, start of line, optional space after colon)
            # Pattern: ^\s*(SCRIPT|TITLE|DESCRIPTION|KEYWORDS)\s*:(.*)
            header_pattern = re.compile(r"^\s*(" + "|".join(section_map.keys()) + r")\s*:(.*)", re.IGNORECASE | re.MULTILINE)

            last_pos = 0
            current_key = None
            buffer = []

            for match in header_pattern.finditer(content):
                start, end = match.span()
                header_text = match.group(1).upper() # Normalize header to uppercase for map lookup
                value_on_header_line = match.group(2).strip()

                # Add content before this header to the previous section
                if current_key:
                    previous_content = content[last_pos:start].strip()
                    buffer.append(previous_content)
                    metadata[current_key] = "\n".join(filter(None, buffer)).strip() # Join non-empty lines

                # Start new section
                current_key = section_map[header_text]
                buffer = [value_on_header_line] # Start buffer with content on header line
                last_pos = end # Update position

            # Add the content of the last section
            if current_key:
                last_content = content[last_pos:].strip()
                buffer.append(last_content)
                metadata[current_key] = "\n".join(filter(None, buffer)).strip()

            # Validate required keys were found (adjust based on strictness)
            # For now, we check if at least the SCRIPT was found, as others might be optional depending on use case
            # required_keys = list(section_map.values())
            required_keys = ['script', 'title', 'description', 'tags'] # Make all required for YouTube upload
            missing = [k for k in required_keys if k not in metadata or not metadata[k]]

            if missing:
                logger.error(f"Failed to parse required sections or sections are empty in {script_filepath}. Missing/Empty: {missing}")
                # Log content for debugging
                logger.info(f"Content of {script_filepath}:\n---\n{content}\n---")
                return None

            # Special handling for tags (split by comma, remove empty)
            if 'tags' in metadata and isinstance(metadata['tags'], str):
                metadata['tags'] = [tag.strip() for tag in metadata['tags'].split(',') if tag.strip()]
            elif 'tags' not in metadata:
                 metadata['tags'] = [] # Ensure tags key exists even if empty

            logger.success(f"Successfully parsed metadata from {script_filepath}")
            return metadata

        except Exception as e:
            logger.error(f"❌ Error parsing script file {script_filepath}: {e}")
            return None


# --- Video Creator Class ---
class VideoCreator:
    """Creates video using the configured provider (currently CapCut via Browser)."""

    def __init__(self, config_manager: ConfigManager, browser_manager: BrowserManager):
        self.config_manager = config_manager
        self.browser_manager = browser_manager
        self.logger = Logger()
        self.video_provider = config_manager.get_config('VIDEO_SETTINGS', 'provider').lower()
        self.capcut_url = config_manager.get_config('VIDEO_SETTINGS', 'capcut_url')
        # Store other settings
        self.capcut_style = config_manager.get_config('VIDEO_SETTINGS', 'capcut_style')
        self.capcut_voice = config_manager.get_config('VIDEO_SETTINGS', 'capcut_voice')
        self.capcut_resolution = config_manager.get_config('VIDEO_SETTINGS', 'capcut_export_resolution')
        self.capcut_format = config_manager.get_config('VIDEO_SETTINGS', 'capcut_export_format') # Currently unused by selectors
        self.capcut_framerate = config_manager.get_config('VIDEO_SETTINGS', 'capcut_export_frame_rate')

    def create_video(self, script_text: str) -> Optional[Path]:
        """Creates the video using the appropriate method."""
        if self.video_provider == 'capcut_browser':
            return self._create_with_capcut_browser(script_text)
        else:
            self.logger.critical(f"Unsupported video provider configured: {self.video_provider}")
            return None

    def _create_with_capcut_browser(self, script_text: str) -> Optional[Path]:
        """Uses Selenium to automate video creation on CapCut website."""
        self.logger.info(f"Starting video creation using CapCut Browser Automation: {self.capcut_url}")
        selectors = self.config_manager.selectors.get('capcut', {})
        if not selectors:
            self.logger.critical("Selectors for 'capcut' not found in selectors.json.")

        # --- Define Selectors (using get_selector for robustness) ---
        # Use descriptive keys matching the config/purpose
        style_key = self.capcut_style
        voice_key = self.capcut_voice
        resolution_key = self.capcut_resolution
        framerate_key = self.capcut_framerate

        try_it_sel = self.config_manager.get_selector('capcut', 'try_it_button') # Optional
        style_sel = self.config_manager.get_selector('capcut', f'style_{style_key}')
        voice_sel = self.config_manager.get_selector('capcut', f'voice_{voice_key}')
        script_input_sel = self.config_manager.get_selector('capcut', 'script_input_area')
        generate_sel = self.config_manager.get_selector('capcut', 'generate_button')
        # Use a reliable indicator for generation completion if possible
        generation_complete_indicator_sel = self.config_manager.get_selector('capcut', 'generation_complete_indicator')
        export_sel = self.config_manager.get_selector('capcut', 'export_button')
        # Captions selectors (assuming a simple workflow)
        captions_menu_sel = self.config_manager.get_selector('capcut', 'captions_menu_button')
        captions_choice_sel = self.config_manager.get_selector('capcut', 'captions_choice_option') # e.g., first style
        # Export settings selectors
        export_res_dropdown_sel = self.config_manager.get_selector('capcut', 'export_resolution_dropdown')
        export_res_option_sel = self.config_manager.get_selector('capcut', f'export_resolution_{resolution_key}')
        export_fps_dropdown_sel = self.config_manager.get_selector('capcut', 'export_framerate_dropdown')
        export_fps_option_sel = self.config_manager.get_selector('capcut', f'export_framerate_{framerate_key}')
        export_confirm_sel = self.config_manager.get_selector('capcut', 'export_confirm_button')

        # Validate required selectors dynamically based on config
        required_selectors = {
            f'Style ({style_key})': style_sel, f'Voice ({voice_key})': voice_sel,
            'Script Input': script_input_sel, 'Generate Button': generate_sel,
            'Export Button': export_sel,
            'Captions Menu': captions_menu_sel, 'Caption Choice': captions_choice_sel,
            'Resolution Dropdown': export_res_dropdown_sel,
            f'Resolution Option ({resolution_key})': export_res_option_sel,
            'Framerate Dropdown': export_fps_dropdown_sel, f'Framerate Option ({framerate_key})': export_fps_option_sel,
            'Export Confirm': export_confirm_sel
        }
        missing_sels = [name for name, sel in required_selectors.items() if not sel]
        if missing_sels:
            self.logger.critical(f"Missing required CapCut selectors in selectors.json for current settings: {', '.join(missing_sels)}")

        # --- Browser Automation Steps ---
        try:
            if not self.browser_manager.navigate(self.capcut_url):
                return None

            # 1. Click Try It (Optional - if selector exists)
            if try_it_sel:
                self.logger.info("Attempting to click 'Try It' button...")
                # Use longer timeout for initial page elements
                if self.browser_manager.click_element(try_it_sel, timeout=30):
                    self.logger.info("'Try It' button clicked. Waiting for editor load...")
                    # Wait for a key editor element to appear after clicking 'Try It'
                    if not self.browser_manager.find_element(script_input_sel, timeout=90, visible=True):
                        self.logger.error("CapCut editor did not load correctly after clicking 'Try It' (script input not found/visible).")
                        self.browser_manager.take_screenshot("capcut_editor_load_fail")
                        return None
                else:
                    self.logger.warning("Could not find or click 'Try It' button. Assuming already in editor.")
                    # Still wait for editor elements if 'Try It' wasn't clicked
                    if not self.browser_manager.find_element(script_input_sel, timeout=90, visible=True):
                        self.logger.error("CapCut editor did not load correctly (script input not found/visible).")
                        self.browser_manager.take_screenshot("capcut_editor_load_fail_no_tryit")
                        return None
            else:
                self.logger.info("No 'Try It' button selector configured. Assuming already in editor.")
                # Still wait for editor elements
                if not self.browser_manager.find_element(script_input_sel, timeout=90, visible=True):
                    self.logger.error("CapCut editor did not load correctly (script input not found/visible).")
                    self.browser_manager.take_screenshot("capcut_editor_load_fail_direct")
                    return None

            # 2. Choose Style
            self.logger.info(f"Selecting style: {style_key}")
            if not self.browser_manager.click_element(style_sel):
                self.logger.error(f"Failed to select style '{style_key}'.")
                self.browser_manager.take_screenshot(f"capcut_style_fail_{style_key}")
                return None
            time.sleep(1)

            # 3. Choose Voice
            self.logger.info(f"Selecting voice: {voice_key}")
            if not self.browser_manager.click_element(voice_sel):
                self.logger.error(f"Failed to select voice '{voice_key}'.")
                self.browser_manager.take_screenshot(f"capcut_voice_fail_{voice_key}")
                return None
            time.sleep(1)

            # 4. Paste Script
            self.logger.info("Pasting script...")
            if not self.browser_manager.input_text(script_input_sel, script_text):
                self.logger.error("Failed to paste script into CapCut.")
                self.browser_manager.take_screenshot("capcut_paste_fail")
                return None
            time.sleep(1)

            # 5. Click Generate
            self.logger.info("Clicking 'Generate'...")
            if not self.browser_manager.click_element(generate_sel):
                self.logger.error("Failed to click 'Generate' button.")
                self.browser_manager.take_screenshot("capcut_generate_click_fail")
                return None

            # --- Wait for video generation ---
            generation_wait = 300 # Increased timeout further for generation
            self.logger.info(f"Waiting up to {generation_wait} seconds for video generation...")
            # Use a more reliable indicator if available
            wait_target_sel = generation_complete_indicator_sel or export_sel # Prefer specific indicator, fallback to export button
            wait_target_name = "generation complete indicator" if generation_complete_indicator_sel else "export button to be clickable"

            element_to_wait_for = None
            try:
                self.logger.info(f"Waiting for {wait_target_name} using selectors: {wait_target_sel}")
                # Wait for presence first, then check clickability if needed
                present_element = self.browser_manager.find_element(wait_target_sel, timeout=generation_wait, visible=False)
                if not present_element:
                    raise TimeoutException(f"Target element {wait_target_name} not found after waiting {generation_wait}s.")

                # If waiting for export button, ensure it's clickable
                if wait_target_sel == export_sel:
                    self.logger.info("Export button found, waiting for it to be clickable...")
                    element_to_wait_for = WebDriverWait(self.browser_manager.get_driver(), 20).until(
                        EC.element_to_be_clickable(present_element)
                    )
                else:
                    element_to_wait_for = present_element # Use the found indicator element

                self.logger.success(f"Video generation complete ({wait_target_name} found/ready).")
                time.sleep(2) # Small buffer after generation

            except TimeoutException as e:
                self.logger.error(f"Timeout waiting for video generation to complete ({wait_target_name}). {e}")
                self.browser_manager.take_screenshot("capcut_generation_timeout")
                return None
            except RuntimeError as e: # Catch browser crash during find
                 self.logger.error(f"Browser crashed while waiting for video generation: {e}")
                 return None

            # 6. Add Captions (Optional but recommended)
            self.logger.info("Adding captions...")
            if not self.browser_manager.click_element(captions_menu_sel):
                 self.logger.warning("Failed to click captions menu button. Skipping captions.")
            else:
                 time.sleep(1)
                 if not self.browser_manager.click_element(captions_choice_sel):
                      self.logger.warning("Failed to select caption style. Skipping captions.")
                 else:
                      self.logger.info("Captions added successfully.")
                      time.sleep(2) # Wait for captions to apply

            # 7. Click Export
            self.logger.info("Clicking 'Export'...")
            if not self.browser_manager.click_element(export_sel):
                self.logger.error("Failed to click 'Export' button.")
                self.browser_manager.take_screenshot("capcut_export_click_fail")
                return None
            time.sleep(2) # Wait for export modal

            # 8. Configure Export Settings
            self.logger.info(f"Configuring export settings: Resolution={resolution_key}, Framerate={framerate_key}")
            # Resolution
            if not self.browser_manager.click_element(export_res_dropdown_sel):
                self.logger.error("Failed to click resolution dropdown.")
                self.browser_manager.take_screenshot("capcut_res_dropdown_fail")
                return None
            time.sleep(0.5)
            if not self.browser_manager.click_element(export_res_option_sel):
                self.logger.error(f"Failed to select resolution '{resolution_key}'.")
                self.browser_manager.take_screenshot(f"capcut_res_option_fail_{resolution_key}")
                return None
            time.sleep(1)
            # Framerate
            if not self.browser_manager.click_element(export_fps_dropdown_sel):
                self.logger.error("Failed to click framerate dropdown.")
                self.browser_manager.take_screenshot("capcut_fps_dropdown_fail")
                return None
            time.sleep(0.5)
            if not self.browser_manager.click_element(export_fps_option_sel):
                self.logger.error(f"Failed to select framerate '{framerate_key}'.")
                self.browser_manager.take_screenshot(f"capcut_fps_option_fail_{framerate_key}")
                return None
            time.sleep(1)

            # 9. Confirm Export and Wait for Download
            download_dir = self.config_manager.get_path('downloads_dir')
            download_dir.mkdir(parents=True, exist_ok=True)
            # Clear old temp files before starting download wait
            for item in download_dir.iterdir():
                 if item.is_file() and str(item).endswith(('.tmp', '.crdownload', '.part')):
                      try:
                           item.unlink()
                           self.logger.info(f"Removed old temporary file: {item.name}")
                      except OSError as e:
                           self.logger.warning(f"Could not remove old temp file {item.name}: {e}")
            initial_files = set(p for p in download_dir.iterdir() if p.is_file())

            self.logger.info("Confirming export and starting download...")
            if not self.browser_manager.click_element(export_confirm_sel):
                self.logger.error("Failed to click confirm export button.")
                self.browser_manager.take_screenshot("capcut_export_confirm_fail")
                return None

            downloaded_file_path = self.browser_manager.wait_for_download_complete(download_dir, initial_files,
                                                                                   timeout=600) # Long timeout for export/download

            if not downloaded_file_path:
                self.logger.error("Video download failed or timed out.")
                self.browser_manager.take_screenshot("capcut_download_timeout")
                return None

            # 10. Move downloaded file to videos directory
            videos_dir = self.config_manager.get_path('videos_dir')
            videos_dir.mkdir(parents=True, exist_ok=True)
            # Create a more descriptive filename using script title if possible
            # For now, use timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_suffix = downloaded_file_path.suffix if downloaded_file_path.suffix else '.mp4' # Default suffix
            final_video_filename = f"capcut_video_{timestamp}{safe_suffix}"
            final_video_path = videos_dir / final_video_filename

            try:
                shutil.move(str(downloaded_file_path), str(final_video_path))
                self.logger.success(f"Moved downloaded video to: {final_video_path}")
                return final_video_path
            except Exception as move_err:
                self.logger.error(
                    f"❌ Failed to move downloaded video from {downloaded_file_path} to {final_video_path}: {move_err}")
                # Attempt to leave the file in downloads dir if move fails
                self.logger.warning(f"Leaving downloaded video in downloads directory: {downloaded_file_path}")
                return downloaded_file_path # Return original path as fallback

        except RuntimeError as e: # Catch browser crash
             self.logger.error(f"❌ Browser crashed during CapCut video creation: {e}")
             return None
        except Exception as e:
            self.logger.error(f"❌ An unexpected error occurred during CapCut video creation: {e}")
            self.browser_manager.take_screenshot("capcut_error")
            return None


# --- YouTube Uploader Class ---
class YouTubeUploader:
    """Handles YouTube video upload using the API and metadata from script file."""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = Logger()
        self.credentials_path = config_manager.get_api_path('credentials_file')
        if not self.credentials_path:
             # This should be caught by validation, but handle defensively
             self.logger.error("YouTube credentials file path ('credentials_file') not found in api.json.")
             # Cannot proceed without credentials path
             raise ValueError("Missing YouTube credentials file path in configuration.")

    def _get_credentials(self) -> Optional[Credentials]:
        """Gets existing credentials or initiates OAuth flow using configured secrets."""
        creds = None
        # Check if token file exists
        if self.credentials_path.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(self.credentials_path), YOUTUBE_SCOPES)
                self.logger.info(f"Loaded existing YouTube credentials from: {self.credentials_path}")
            except Exception as e:
                self.logger.warning(
                    f"Error loading existing credentials from {self.credentials_path}: {e}. Will attempt re-authentication if possible, or fail.")
                creds = None # Force re-auth attempt or failure

        # If no valid credentials, try to refresh or fail (no interactive flow allowed)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    self.logger.info("Refreshing YouTube API credentials...")
                    creds.refresh(Request())
                    self.logger.info("Credentials refreshed successfully.")
                    # Save the refreshed credentials
                    try:
                        with open(self.credentials_path, 'w') as token:
                            token.write(creds.to_json())
                        self.logger.info(f"Refreshed YouTube credentials saved to: {self.credentials_path}")
                    except Exception as e:
                        self.logger.warning(f"Failed to save refreshed credentials to {self.credentials_path}: {e}")
                except Exception as e:
                    self.logger.error(f"❌ Failed to refresh credentials: {e}. Need manual re-authentication.")
                    # Delete potentially corrupted creds file?
                    try:
                        self.credentials_path.unlink(missing_ok=True)
                    except OSError:
                        pass # Ignore if deletion fails
                    creds = None # Ensure creds is None if refresh failed
            else:
                 # No existing creds or no refresh token
                 self.logger.info("No valid YouTube credentials found and cannot refresh.")
                 creds = None

            # If still no valid creds after potential refresh attempt, fail critically for automation
            if not creds:
                self.logger.error("❌ YouTube credentials not found, invalid, or refresh failed.")
                self.logger.error(
                    f"Please run an initial authentication flow manually to generate a valid '{self.credentials_path.name}' file.")
                # Log guidance on how manual flow would work
                client_config = self.config_manager.get_youtube_client_config()
                if client_config:
                     self.logger.error("Manual flow example (run this separately):")
                     if isinstance(client_config, Path):
                          self.logger.error(
                              f"# from google_auth_oauthlib.flow import InstalledAppFlow")
                          self.logger.error(
                              f"# flow = InstalledAppFlow.from_client_secrets_file(str('{client_config}'), {YOUTUBE_SCOPES})")
                          self.logger.error(f"# creds = flow.run_local_server(port=0)")
                          self.logger.error(f"# with open('{self.credentials_path}', 'w') as token:")
                          self.logger.error(f"#     token.write(creds.to_json())")
                     else: # It's a dict
                          self.logger.error(
                              f"# from google_auth_oauthlib.flow import InstalledAppFlow")
                          # Use json.dumps for cleaner representation of the dict in the log message
                          client_config_str = json.dumps(client_config)
                          self.logger.error(
                              f"# flow = InstalledAppFlow.from_client_config({client_config_str}, {YOUTUBE_SCOPES})")
                          self.logger.error(f"# creds = flow.run_local_server(port=0)")
                          self.logger.error(f"# with open('{self.credentials_path}', 'w') as token:")
                          self.logger.error(f"#     token.write(creds.to_json())")
                else:
                     self.logger.error("Cannot provide manual flow example: Client secrets configuration missing or invalid.")
                return None # Cannot proceed without valid creds in full auto mode

        # If we have valid creds (loaded or refreshed)
        return creds

    def upload_video(self, video_filepath: Path, metadata: Dict[str, Any]) -> Optional[str]:
        """Uploads the video file to YouTube with the provided metadata."""
        self.logger.info(f"🚀 Starting YouTube upload for: {video_filepath}")

        if not video_filepath.is_file():
            self.logger.error(f"Video file not found: {video_filepath}")
            return None

        # Validate required metadata
        required_meta = ['title', 'description', 'tags']
        missing_meta = [key for key in required_meta if key not in metadata or not metadata[key]]
        if missing_meta:
            self.logger.error(
                f"Missing required metadata for YouTube upload. Need non-empty: {required_meta}. Missing/Empty: {missing_meta}")
            return None

        credentials = self._get_credentials()
        if not credentials:
            self.logger.error("Failed to obtain valid YouTube API credentials. Cannot upload.")
            return None

        try:
            youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=credentials)

            # Ensure tags are a list of strings
            tags_list = metadata.get('tags', [])
            if isinstance(tags_list, str): # Should be list from parser, but handle just in case
                tags_list = [tag.strip() for tag in tags_list.split(',') if tag.strip()]
            elif not isinstance(tags_list, list):
                self.logger.warning(f"Metadata 'tags' is not a list, ignoring. Value: {tags_list}")
                tags_list = []

            # Truncate tags if total length exceeds YouTube limit (approx 500 chars)
            truncated_tags = []
            current_length = 0
            for tag in tags_list:
                # Add 1 for comma if not the first tag
                tag_len_with_comma = len(tag) + (1 if truncated_tags else 0)
                if current_length + tag_len_with_comma <= 500:
                    truncated_tags.append(tag)
                    current_length += tag_len_with_comma
                else:
                    self.logger.warning(f"Tag list truncated due to length limit (500 chars). Stopped at tag: '{tag}'")
                    break

            # Prepare request body
            privacy_status = self.config_manager.get_config('YOUTUBE_SETTINGS', 'privacy_status', 'private')
            notify_subs_str = self.config_manager.get_config('YOUTUBE_SETTINGS', 'notify_subscribers', 'false')
            notify_subs = notify_subs_str.lower() == 'true'
            category_id = self.config_manager.get_config('YOUTUBE_SETTINGS', 'category_id')

            body = {
                'snippet': {
                    'title': metadata['title'][:100], # Max 100 chars
                    'description': metadata['description'][:5000], # Max 5000 chars
                    'tags': truncated_tags,
                    'categoryId': category_id
                },
                'status': {
                    'privacyStatus': privacy_status,
                    'selfDeclaredMadeForKids': False # Assume not made for kids unless specified otherwise
                }
            }

            self.logger.info("Uploading video file to YouTube...")
            insert_request = youtube.videos().insert(
                part=",".join(body.keys()),
                body=body,
                # Use notifySubscribers parameter here
                notifySubscribers=notify_subs,
                media_body=MediaFileUpload(str(video_filepath), chunksize=-1, resumable=True)
            )

            # --- Resumable Upload --- #
            response = None
            upload_success = False
            retries = 0
            max_retries = 3
            while response is None and retries <= max_retries:
                try:
                    status, response = insert_request.next_chunk()
                    if status:
                        self.logger.info(f"Upload progress: {int(status.progress() * 100)}%")
                    if response:
                        video_id = response.get('id')
                        self.logger.success(f"✅ Video uploaded successfully! Video ID: {video_id}")
                        upload_success = True
                        # Optionally log to uploaded_videos.ini
                        self._log_uploaded_video(video_filepath, video_id, metadata['title'])
                        return video_id
                except HttpError as e:
                    if e.resp.status in [500, 502, 503, 504]:
                        self.logger.warning(f"YouTube API server error ({e.resp.status}): {e}. Retrying ({retries+1}/{max_retries})...")
                        time.sleep((2 ** retries) + random.random()) # Exponential backoff with jitter
                        retries += 1
                    else:
                        self.logger.error(f"❌ YouTube API Error during upload: {e}")
                        return None # Non-retriable API error
                except Exception as e:
                     # Catch other potential errors during upload (network issues?)
                     self.logger.error(f"❌ Unexpected error during YouTube upload chunk: {e}")
                     # Decide if retry is appropriate based on error type? For now, treat as non-retriable.
                     return None

            if not upload_success:
                 self.logger.error(f"❌ YouTube upload failed after {max_retries} retries.")
                 return None

        except HttpError as e:
            self.logger.error(f"❌ YouTube API Error (initial request): {e}")
            return None
        except Exception as e:
            self.logger.error(f"❌ An unexpected error occurred during YouTube upload setup: {e}")
            return None

    def _log_uploaded_video(self, video_filepath: Path, video_id: str, title: str):
        """Logs the uploaded video details to the specified INI file."""
        try:
            log_file_path_str = self.config_manager.get_config('PATHS', 'uploaded_videos_log')
            if not log_file_path_str:
                 self.logger.warning("uploaded_videos_log path not configured in [PATHS]. Skipping log.")
                 return

            log_file_path = Path(log_file_path_str)
            log_file_path.parent.mkdir(parents=True, exist_ok=True)

            uploaded_log = configparser.ConfigParser()
            # Read existing log if it exists
            if log_file_path.is_file():
                uploaded_log.read(log_file_path, encoding='utf-8')

            # Use timestamp as section header for uniqueness
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            section_name = f"Upload_{timestamp}"
            uploaded_log[section_name] = {
                'timestamp': datetime.now().isoformat(),
                'video_id': video_id,
                'title': title,
                'original_file': str(video_filepath)
            }

            # Write back to the log file
            with open(log_file_path, 'w', encoding='utf-8') as configfile:
                uploaded_log.write(configfile)
            self.logger.info(f"Logged uploaded video details to: {log_file_path}")

        except Exception as e:
            self.logger.error(f"❌ Failed to log uploaded video details: {e}")


# --- Main Orchestration --- #
def main():
    """Main function to orchestrate the automation pipeline."""
    # --- Initialization ---
    # Use the directory containing this script as the base directory
    script_dir = Path(__file__).parent.resolve()
    config_manager = ConfigManager(base_dir_override=str(script_dir))
    logger = Logger() # Get initialized logger instance
    browser_manager = None # Initialize later only if needed

    try:
        # Determine if browser is needed for any step
        ai_provider = config_manager.get_config('AI_SETTINGS', 'provider').lower()
        video_provider = config_manager.get_config('VIDEO_SETTINGS', 'provider').lower()
        needs_browser = 'browser' in ai_provider or 'browser' in video_provider

        if needs_browser:
            logger.info("Browser interaction required for AI or Video generation.")
            browser_manager = BrowserManager(config_manager)
            # Initialize driver early to catch issues
            try:
                 driver_instance = browser_manager.get_driver()
                 if not driver_instance:
                      # Critical error already logged by get_driver/init_driver
                      # No need to log again, just exit gracefully if possible
                      return # Exit main function
                 logger.info("Browser initialized successfully for upcoming tasks.")
            except RuntimeError as e:
                 logger.error(f"Exiting due to browser initialization failure: {e}")
                 return # Exit main function
        else:
            logger.info("No browser interaction required for configured providers.")

        # --- Step 1: Generate Script ---
        logger.info("--- Starting Step 1: Script Generation ---")
        script_generator = ScriptGenerator(config_manager, browser_manager)
        script_content = script_generator.generate_script()

        if not script_content:
            logger.critical("Script generation failed. Cannot proceed.")
            # No need to exit here, critical should handle it

        # Save the raw script content
        script_filepath = script_generator.save_script(script_content)
        if not script_filepath:
            logger.critical("Failed to save generated script. Cannot proceed.")
            # No need to exit here, critical should handle it

        logger.success("Step 1: Script Generation Completed.")

        # --- Step 2: Parse Script Metadata ---
        logger.info("--- Starting Step 2: Parse Script Metadata ---")
        metadata = ScriptGenerator.parse_script_file(script_filepath)
        if not metadata:
            logger.critical(f"Failed to parse metadata from script file: {script_filepath}. Cannot proceed.")
            # No need to exit here, critical should handle it

        # Extract script text needed for video creation
        script_text_for_video = metadata.get('script')
        if not script_text_for_video:
             logger.critical("Parsed metadata is missing the 'script' content. Cannot proceed with video creation.")

        logger.success("Step 2: Parse Script Metadata Completed.")

        # --- Step 3: Create Video ---
        logger.info("--- Starting Step 3: Video Creation ---")
        if not browser_manager and 'browser' in video_provider:
            # This case should ideally not happen due to early check, but safeguard
            logger.critical("Video creation requires a browser, but BrowserManager was not initialized.")

        video_creator = VideoCreator(config_manager, browser_manager)
        video_filepath = video_creator.create_video(script_text_for_video)

        if not video_filepath:
            logger.critical("Video creation failed. Cannot proceed.")
            # No need to exit here, critical should handle it

        logger.success(f"Step 3: Video Creation Completed. Video saved at: {video_filepath}")

        # --- Step 4: Upload to YouTube ---
        logger.info("--- Starting Step 4: Upload to YouTube ---")
        uploader = YouTubeUploader(config_manager)
        video_id = uploader.upload_video(video_filepath, metadata)

        if not video_id:
            logger.error("YouTube upload failed.")
            # Don't make this critical, the video file still exists locally
        else:
            logger.success(f"Step 4: YouTube Upload Completed. Video URL: https://www.youtube.com/watch?v={video_id}")

        # --- Pipeline Complete ---
        logger.success("🎉 Smart Automation Pipeline finished successfully! 🎉")

    except Exception as e:
        # Catch any unexpected errors during the main flow
        logger.critical(f"An unexpected critical error occurred in the main pipeline: {e}", exc_info=True)

    finally:
        # --- Cleanup ---
        if browser_manager:
            browser_manager.close_driver()
        logger.info("Automation tool finished.")


if __name__ == "__main__":
    main()

