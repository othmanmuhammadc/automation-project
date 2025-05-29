#!/usr/bin/env python3
"""
Smart Automation Tool - Fully Automated YouTube Content Creation Pipeline
Author: AI Assistant (Revised by Manus)
Version: 5.0
Description: Fully automated text generation (via API/Browser), video creation (via Browser),
             and YouTube upload (via API) tool. Reads ALL configuration from external
             files (INI/JSON) and requires no user interaction during runtime.
             Supports YouTube client secrets embedded directly in api.json or via a separate file.
             Supports connecting to an existing browser via remote debugging port.
             Fails critically if any required configuration is missing.
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
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
except ImportError:
    print("❌ Error: Selenium is required but not installed. Run: pip install selenium")
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
        log_file_rel_path = self._get_required_config(self.config, 'PATHS', 'log_file', self.customisation_file)
        self.log_file_abs_path = self.base_dir / log_file_rel_path
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
            print(f"CRITICAL ERROR: Configuration file not found: {file_path}")
            sys.exit(1)
        config = configparser.ConfigParser()
        try:
            # Allow empty values for optional keys like debugger_port
            config = configparser.ConfigParser(allow_no_value=True)
            config.read(file_path, encoding='utf-8')
            return config
        except Exception as e:
            print(f"CRITICAL ERROR: Error reading INI configuration file {file_path}: {e}")
            sys.exit(1)

    def _load_json_config(self, file_path: Path) -> Dict:
        """Loads a JSON file. Fails critically if file not found or parse error."""
        if not file_path.is_file():
            print(f"CRITICAL ERROR: Configuration file not found: {file_path}")
            sys.exit(1)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"CRITICAL ERROR: Error decoding JSON from {file_path}: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"CRITICAL ERROR: Error reading JSON file {file_path}: {e}")
            sys.exit(1)

    def _get_required_config(self, config_obj: Any, section: str, key: str, filename: Path) -> str:
        """Helper to get a required key, failing critically if absent."""
        value = None
        if isinstance(config_obj, configparser.ConfigParser):
            if config_obj.has_option(section, key):
                value = config_obj.get(section, key)
        elif isinstance(config_obj, dict):
            value = config_obj.get(section, {}).get(key)

        # Allow empty value only for 'user_data_dir' and 'debugger_port' (optional)
        is_optional_empty = key in ['user_data_dir', 'debugger_port'] and value == ''

        if value is None or (value == '' and not is_optional_empty):
            self.logger.critical(
                f"Missing required configuration key \t'{key}' in section '[{section}]' of file: {filename}")
        return value if value is not None else ''  # Return empty string if optional and missing/empty

    def _validate_configs(self):
        """Perform strict validation of all loaded configurations."""
        self.logger.info("Validating configurations...")
        errors = []

        # 1. Validate customisation.ini structure and required keys
        for section, keys in self.required_ini_keys.items():
            if not self.config.has_section(section):
                errors.append(f"Missing required section '[{section}]' in {self.customisation_file}")
                continue  # Skip key checks if section is missing
            for key in keys:
                # Use the helper which now understands optional empty values
                self._get_required_config(self.config, section, key, self.customisation_file)

        # 1b. Validate optional debugger_port format if present
        debugger_port_str = self.config.get('BROWSER_SETTINGS', 'debugger_port', fallback=None)
        if debugger_port_str:
            try:
                int(debugger_port_str)
            except ValueError:
                errors.append(
                    f"Invalid value for 'debugger_port' in [BROWSER_SETTINGS] of {self.customisation_file}. Must be an integer.")

        # 2. Validate api.json structure and required keys based on AI provider
        ai_provider = self.config.get('AI_SETTINGS', 'provider', fallback='').lower()
        if ai_provider == 'gemini':
            if 'gemini' not in self.api_config:
                errors.append(
                    f"Missing required section 'gemini' in {self.api_file} (required by AI provider '{ai_provider}')")
            else:
                for key in self.required_api_keys['gemini']:
                    if key not in self.api_config['gemini'] or not self.api_config['gemini'][key] or 'YOUR_' in \
                            self.api_config['gemini'][key]:
                        errors.append(
                            f"Missing, empty, or placeholder key \t'{key}' in section 'gemini' of {self.api_file}")
            # Check if genai library was imported
            if genai is None:
                errors.append(f"AI provider is 'gemini' but 'google-generativeai' library is not installed.")

        # 3. Validate YouTube API configuration (credentials file + secrets file OR embedded secrets)
        if 'youtube' not in self.api_config:
            errors.append(f"Missing required section 'youtube' in {self.api_file}")
        else:
            youtube_config = self.api_config['youtube']
            # Credentials file is always required
            if 'credentials_file' not in youtube_config or not youtube_config['credentials_file']:
                errors.append(
                    f"Missing or empty required key \t'credentials_file' in section 'youtube' of {self.api_file}")

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
                if not os.path.isabs(secrets_path_rel):
                    secrets_path_abs = self.base_dir / secrets_path_rel
                    if not secrets_path_abs.is_file():
                        errors.append(
                            f"YouTube 'client_secrets_file' path specified in {self.api_file} does not exist: {secrets_path_abs}")
                elif not Path(secrets_path_rel).is_file():  # Check if absolute path exists
                    errors.append(
                        f"YouTube 'client_secrets_file' absolute path specified in {self.api_file} does not exist: {secrets_path_rel}")
            elif has_embedded_secrets:
                # Basic validation of embedded structure (e.g., check for 'web' or 'installed' key)
                if not ('web' in youtube_config['client_secrets_config'] or 'installed' in youtube_config[
                    'client_secrets_config']):
                    errors.append(
                        f"Invalid structure for embedded 'client_secrets_config' in {self.api_file}. Expected a JSON object with a 'web' or 'installed' key.")

        # Check if Google API libraries were imported
        if None in [InstalledAppFlow, Credentials, build, HttpError, MediaFileUpload]:
            errors.append(
                f"Required Google API client libraries for YouTube upload are not installed (google-api-python-client google-auth-oauthlib google-auth-httplib2).")

        # 4. Validate selectors.json structure (basic)
        if not isinstance(self.selectors, dict) or not self.selectors:
            errors.append(f"Selectors file {self.selectors_file} is empty or not a valid JSON object.")
        else:
            # Check for expected top-level keys based on configured providers
            expected_selector_sections = []
            video_provider = self.config.get('VIDEO_SETTINGS', 'provider', fallback='').lower()
            if video_provider == 'capcut_browser':
                expected_selector_sections.append('capcut')

            ai_provider_sel = self.config.get('AI_SETTINGS', 'provider', fallback='').lower()
            if ai_provider_sel == 'chatgpt_browser':
                expected_selector_sections.append('chatgpt')
            elif ai_provider_sel == 'grok_browser':
                expected_selector_sections.append('grok')

            for section in expected_selector_sections:
                if section not in self.selectors:
                    errors.append(
                        f"Missing required selector section '{section}' in {self.selectors_file} (required by provider '{video_provider or ai_provider_sel}')")
                elif not isinstance(self.selectors[section], dict) or not self.selectors[section]:
                    errors.append(
                        f"Selector section '{section}' in {self.selectors_file} is empty or not a valid JSON object.")

        # 5. Validate specific value formats (example: timeouts must be integers)
        try:
            int(self.config.get('BROWSER_SETTINGS', 'wait_timeout', fallback='-1'))
            int(self.config.get('BROWSER_SETTINGS', 'retry_attempts', fallback='-1'))
            int(self.config.get('BROWSER_SETTINGS', 'page_load_timeout', fallback='-1'))
            # debugger_port already validated above
        except ValueError:
            errors.append(
                f"One or more timeout/retry values in [BROWSER_SETTINGS] of {self.customisation_file} are not valid integers.")

        # --- Final Check ---
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
        path_sections = ['PATHS']  # Add other sections with paths if needed

        for section in path_sections:
            if self.config.has_section(section):
                for key, value in self.config.items(section):
                    # Simple check: if it looks like a relative path, make it absolute
                    if value and not os.path.isabs(value) and ('/' in value or '\\' in value):
                        abs_path = self.base_dir / value
                        self.config.set(section, key, str(abs_path))
                        self.logger.info(f"Resolved path [{section}]{key}: {value} -> {abs_path}")

        # Resolve paths within api.json (specifically for file paths like credentials)
        if 'youtube' in self.api_config:
            youtube_conf = self.api_config['youtube']
            for key in ['credentials_file', 'client_secrets_file']:
                if key in youtube_conf and isinstance(youtube_conf[key], str) and youtube_conf[
                    key] and not os.path.isabs(youtube_conf[key]):
                    abs_path = self.base_dir / youtube_conf[key]
                    youtube_conf[key] = str(abs_path)
                    self.logger.info(f"Resolved path api.json[youtube][{key}]: {abs_path}")

    def get_config(self, section: str, key: str, fallback: Optional[Any] = None) -> Any:
        """Get a value from the INI config."""
        # Use fallback mechanism of configparser itself
        return self.config.get(section, key, fallback=fallback)

    def get_selector(self, section: str, key: str) -> Optional[List[str]]:
        """Get a selector list from the JSON config."""
        return self.selectors.get(section, {}).get(key)

    def get_api_config(self, section: str, key: Optional[str] = None) -> Any:
        """Get a value or section from the API JSON config."""
        if key:
            return self.api_config.get(section, {}).get(key)
        return self.api_config.get(section)

    def get_path(self, key: str) -> Path:
        """Get a resolved absolute path from the [PATHS] section."""
        path_str = self.config.get('PATHS', key)
        if not path_str:
            self.logger.critical(f"Required path key '{key}' not found in [PATHS] section.")
        return Path(path_str)

    def get_api_path(self, key: str) -> Path:
        """Get a resolved absolute path from the api.json (youtube section). Handles potential missing key."""
        path_str = self.api_config.get('youtube', {}).get(key)
        if not path_str:
            # This might be okay if using embedded secrets, let the calling code handle it.
            # self.logger.warning(f"API path key '{key}' not found in api.json[youtube] section.")
            return None  # Return None if path is not found
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
    """

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = Logger()
        self.driver = None
        self.wait_timeout = int(config_manager.get_config('BROWSER_SETTINGS', 'wait_timeout', 30))
        self.retry_attempts = int(config_manager.get_config('BROWSER_SETTINGS', 'retry_attempts', 2))
        self.page_load_timeout = int(config_manager.get_config('BROWSER_SETTINGS', 'page_load_timeout', 60))
        self._connected_via_debugger = False  # Flag to track connection method

    def _init_driver(self):
        """Initializes the WebDriver based on config, connecting via debugger if specified."""
        browser_type = self.config_manager.get_config('BROWSER_SETTINGS', 'primary_browser', 'chrome').lower()
        user_data_dir = self.config_manager.get_config('BROWSER_SETTINGS', 'user_data_dir')
        headless = self.config_manager.get_config('BROWSER_SETTINGS', 'headless_mode', 'true').lower() == 'true'
        debugger_port_str = self.config_manager.get_config('BROWSER_SETTINGS', 'debugger_port', fallback=None)
        debugger_port = None
        if debugger_port_str:
            try:
                debugger_port = int(debugger_port_str)
            except ValueError:
                self.logger.warning(f"Invalid debugger_port '{debugger_port_str}', ignoring. Will launch new browser.")

        options: Union[ChromeOptions, EdgeOptions]
        if browser_type == 'chrome':
            options = ChromeOptions()
            options.add_experimental_option('excludeSwitches', ['enable-logging'])  # Suppress DevTools messages
        elif browser_type == 'edge':
            options = EdgeOptions()
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
        else:
            self.logger.critical(f"Unsupported browser type specified: {browser_type}")
            return None  # Exit handled by logger.critical

        # --- Connection Logic ---
        try:
            if debugger_port:
                debugger_address = f"localhost:{debugger_port}"
                self.logger.info(f"Attempting to connect to existing {browser_type} browser on {debugger_address}...")
                options.add_experimental_option("debuggerAddress", debugger_address)
                # User data dir might still be relevant depending on how the user launched the browser
                if user_data_dir:
                    self.logger.info(f"Assuming externally launched browser uses user data directory: {user_data_dir}")
                    # Note: Selenium doesn't directly use user-data-dir when connecting via debugger,
                    # but it's good practice for the user to launch with the same profile.
                    # options.add_argument(f"user-data-dir={user_data_dir}") # This line has no effect here

                # Initialize driver to connect
                if browser_type == 'chrome':
                    self.driver = webdriver.Chrome(options=options)
                elif browser_type == 'edge':
                    self.driver = webdriver.Edge(options=options)

                # Verify connection by getting current URL (might throw exception if connection failed)
                current_url = self.driver.current_url
                self.logger.success(
                    f"Successfully connected to existing {browser_type} browser at {debugger_address}. Current URL: {current_url}")
                self._connected_via_debugger = True

            else:
                # Launch a new browser instance
                self.logger.info(f"Launching new {browser_type} browser... Headless: {headless}")
                if headless: options.add_argument('--headless')
                options.add_argument('--no-sandbox')  # Often needed in containerized environments
                options.add_argument('--disable-dev-shm-usage')  # Overcomes limited resource problems
                options.add_argument('--disable-gpu')  # Applicable to headless
                options.add_argument("--window-size=1920,1080")  # Standard window size
                if user_data_dir:
                    self.logger.info(f"Using user data directory: {user_data_dir}")
                    options.add_argument(f"user-data-dir={user_data_dir}")

                if browser_type == 'chrome':
                    self.driver = webdriver.Chrome(options=options)
                elif browser_type == 'edge':
                    self.driver = webdriver.Edge(options=options)

                self.logger.success(f"New {browser_type.capitalize()} browser initialized successfully.")
                self._connected_via_debugger = False

            # Set page load timeout for the session
            self.driver.set_page_load_timeout(self.page_load_timeout)
            return self.driver

        except WebDriverException as e:
            if debugger_port and ("cannot connect" in str(e).lower() or "connection refused" in str(e).lower()):
                self.logger.critical(
                    f"Failed to connect to browser on debugger port {debugger_port}. Ensure browser is running with --remote-debugging-port={debugger_port} enabled.")
            elif "net::ERR_CONNECTION_REFUSED" in str(e):
                self.logger.critical(
                    f"Connection refused. Ensure WebDriver service for {browser_type} is running or accessible.")
            elif "executable needs to be in PATH" in str(e):
                self.logger.critical(
                    f"WebDriver executable for {browser_type} not found in PATH. Please install it or provide the path.")
            else:
                self.logger.critical(f"Failed to initialize {browser_type} WebDriver: {e}")
        except Exception as e:
            self.logger.critical(f"An unexpected error occurred during browser initialization: {e}")

        return None  # Return None if initialization failed

    def get_driver(self):
        """Returns the WebDriver instance, initializing if needed."""
        if not self.driver:
            self._init_driver()
        return self.driver

    def close_driver(self):
        """Closes the WebDriver if it's running, but only quits if not connected via debugger."""
        if self.driver:
            try:
                if self._connected_via_debugger:
                    self.logger.info("Detaching from browser (connected via debugger port). Browser remains open.")
                    # Don't quit the browser, just release the driver instance
                    self.driver = None
                else:
                    self.logger.info("Closing browser...")
                    self.driver.quit()
                    self.driver = None
                    self.logger.info("Browser closed.")
            except Exception as e:
                self.logger.error(f"Error closing/detaching browser: {e}")

    def navigate(self, url: str) -> bool:
        """Navigates the browser to a URL with retries."""
        driver = self.get_driver()
        if not driver:
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
                self.logger.warning(
                    f"WebDriverException during navigation to {url}: {e} (Attempt {attempt + 1}/{self.retry_attempts + 1})")
            except Exception as e:
                self.logger.error(
                    f"Unexpected error navigating to {url}: {e} (Attempt {attempt + 1}/{self.retry_attempts + 1})")

            if attempt < self.retry_attempts:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                self.logger.error(f"Failed to navigate to {url} after {self.retry_attempts + 1} attempts.")
                return False
        return False  # Should not be reached

    def find_element(self, selectors: List[str], timeout: Optional[int] = None) -> Optional[Any]:
        """Finds an element using a list of selectors (CSS or XPath)."""
        driver = self.get_driver()
        if not driver or not selectors:
            return None

        wait_time = timeout if timeout is not None else self.wait_timeout
        wait = WebDriverWait(driver, wait_time)

        for selector in selectors:
            try:
                if selector.startswith('/') or selector.startswith('('):
                    # Assume XPath
                    element = wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                    self.logger.info(f"Found element using XPath: {selector}")
                    return element
                else:
                    # Assume CSS Selector
                    element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    self.logger.info(f"Found element using CSS Selector: {selector}")
                    return element
            except TimeoutException:
                self.logger.warning(f"Element not found within {wait_time}s using selector: {selector}")
            except Exception as e:
                self.logger.error(f"Error finding element with selector {selector}: {e}")

        self.logger.error(f"Element not found using any provided selectors: {selectors}")
        return None

    def click_element(self, element_or_selectors: Union[Any, List[str]], timeout: Optional[int] = None) -> bool:
        """Clicks an element, finding it first if selectors are provided."""
        if isinstance(element_or_selectors, list):
            element = self.find_element(element_or_selectors, timeout)
        else:
            element = element_or_selectors

        if not element:
            return False

        driver = self.get_driver()
        if not driver:
            return False

        for attempt in range(self.retry_attempts + 1):
            try:
                # Wait for element to be clickable
                wait_time = timeout if timeout is not None else self.wait_timeout
                WebDriverWait(driver, wait_time).until(EC.element_to_be_clickable(element))
                element.click()
                self.logger.success(f"Clicked element successfully.")
                return True
            except TimeoutException:
                self.logger.warning(
                    f"Element not clickable within {wait_time}s (Attempt {attempt + 1}/{self.retry_attempts + 1})")
            except NoSuchElementException:
                self.logger.warning(
                    f"Element became stale or detached before click (Attempt {attempt + 1}/{self.retry_attempts + 1})")
                # Re-find the element if selectors were provided
                if isinstance(element_or_selectors, list):
                    element = self.find_element(element_or_selectors, timeout)
                    if not element: return False  # Stop if re-find fails
                else:
                    return False  # Cannot re-find if only element was passed
            except Exception as e:
                self.logger.error(f"Error clicking element: {e} (Attempt {attempt + 1}/{self.retry_attempts + 1})")

            if attempt < self.retry_attempts:
                time.sleep(1)  # Short pause before retry
            else:
                self.logger.error(f"Failed to click element after {self.retry_attempts + 1} attempts.")
                return False
        return False

    def input_text(self, element_or_selectors: Union[Any, List[str]], text: str, clear_first: bool = True,
                   timeout: Optional[int] = None) -> bool:
        """Inputs text into an element, finding it first if selectors are provided."""
        if isinstance(element_or_selectors, list):
            element = self.find_element(element_or_selectors, timeout)
        else:
            element = element_or_selectors

        if not element:
            return False

        for attempt in range(self.retry_attempts + 1):
            try:
                if clear_first:
                    element.clear()
                    time.sleep(0.2)  # Small pause after clear
                element.send_keys(text)
                self.logger.success(f"Input text successfully.")  # Avoid logging potentially sensitive text
                return True
            except NoSuchElementException:
                self.logger.warning(
                    f"Element became stale or detached before input (Attempt {attempt + 1}/{self.retry_attempts + 1})")
                if isinstance(element_or_selectors, list):
                    element = self.find_element(element_or_selectors, timeout)
                    if not element: return False
                else:
                    return False
            except Exception as e:
                self.logger.error(f"Error inputting text: {e} (Attempt {attempt + 1}/{self.retry_attempts + 1})")

            if attempt < self.retry_attempts:
                time.sleep(1)
            else:
                self.logger.error(f"Failed to input text after {self.retry_attempts + 1} attempts.")
                return False
        return False

    def wait_for_download_complete(self, download_dir: Path, initial_files: set, timeout: int = 300) -> Optional[Path]:
        """Waits for a new file to appear and finish downloading in a directory."""
        self.logger.info(f"Waiting for download to complete in: {download_dir} (Timeout: {timeout}s)")
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                current_files = set(p for p in download_dir.iterdir() if p.is_file())
            except FileNotFoundError:
                self.logger.warning(f"Download directory {download_dir} not found yet. Waiting...")
                time.sleep(5)
                continue
            except Exception as e:
                self.logger.error(f"Error listing files in download directory {download_dir}: {e}")
                return None  # Cannot proceed if directory is inaccessible

            new_files = current_files - initial_files

            if new_files:
                # Assume the first new file is the download
                potential_file = list(new_files)[0]
                # Check for temporary download extensions (customize as needed)
                if not str(potential_file).endswith(('.tmp', '.crdownload', '.part')):
                    # Check if file size is stable
                    try:
                        size1 = potential_file.stat().st_size
                        time.sleep(1)  # Wait a second
                        size2 = potential_file.stat().st_size
                        if size1 == size2 and size1 > 0:  # File size stable and not empty
                            self.logger.success(f"Download detected and appears complete: {potential_file}")
                            return potential_file
                        else:
                            self.logger.info(
                                f"Detected new file {potential_file}, but size is changing or zero. Still downloading...")
                    except FileNotFoundError:
                        # File might have been quickly renamed or deleted, continue loop
                        self.logger.warning(f"Detected file {potential_file} disappeared. Continuing search...")
                        initial_files = current_files  # Update baseline
                        continue
                    except Exception as e:
                        self.logger.error(f"Error checking file {potential_file} status: {e}")
                else:
                    self.logger.info(f"Detected temporary download file: {potential_file}. Waiting...")

            time.sleep(2)  # Check every 2 seconds

        self.logger.error(f"Timeout waiting for download to complete in {download_dir}.")
        return None


# --- Script Generator Class ---
class ScriptGenerator:
    """Generates script text using the configured AI provider (API or Browser)."""

    def __init__(self, config_manager: ConfigManager, browser_manager: Optional[BrowserManager] = None):
        self.config_manager = config_manager
        self.browser_manager = browser_manager  # Only needed for browser-based AI
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
        if not api_key or 'YOUR_' in api_key:
            self.logger.critical("Gemini API key is missing or is a placeholder in api.json.")

        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-pro')  # Or specify another model if needed
            self.logger.info("Sending prompt to Gemini API...")
            response = model.generate_content(self.prompt)

            # Basic check for safety ratings or blocks
            if not response.parts:
                if response.prompt_feedback.block_reason:
                    self.logger.error(f"❌ Gemini API request blocked. Reason: {response.prompt_feedback.block_reason}")
                else:
                    self.logger.error("❌ Gemini API returned an empty response with no specific block reason.")
                return None

            script_text = response.text
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
                "Browser interaction required but BrowserManager not available.")  # Should be caught earlier

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
        prompt_sel = selectors.get('prompt_input') or selectors.get('prompt_textarea')
        send_sel = selectors.get('send_button') or selectors.get('submit_button')
        response_sel = selectors.get('response_area_last') or selectors.get('response_output_last')
        # Optional: Selector to detect when generation is complete (e.g., regenerate button appears)
        completion_indicator_sel = selectors.get('response_regenerate_button')

        if not all([prompt_sel, send_sel, response_sel]):
            self.logger.critical(
                f"Missing required selectors for {provider_key} in selectors.json. Need prompt input, send button, and response area selectors.")

        # --- Browser Automation ---
        try:
            if not self.browser_manager.navigate(ai_url):
                return None

            # Input prompt
            if not self.browser_manager.input_text(prompt_sel, self.prompt):
                self.logger.error(f"Failed to input prompt into {provider_key}.")
                return None
            time.sleep(1)  # Brief pause after input

            # Send prompt
            if not self.browser_manager.click_element(send_sel):
                self.logger.error(f"Failed to click send button for {provider_key}.")
                return None

            self.logger.info(f"Prompt sent to {provider_key}. Waiting for response...")

            # Wait for response generation to complete
            # Strategy 1: Wait for a specific indicator element (more reliable)
            if completion_indicator_sel:
                if not self.browser_manager.find_element(completion_indicator_sel,
                                                         timeout=120):  # Long timeout for generation
                    self.logger.error(
                        f"Timeout waiting for response completion indicator ({completion_indicator_sel}) from {provider_key}.")
                    # Consider trying to grab text anyway?
                    # response_element = self.browser_manager.find_element(response_sel, timeout=5)
                    # if response_element and response_element.text:
                    #    self.logger.warning("Completion indicator timeout, but found response text. Proceeding cautiously.")
                    #    script_text = response_element.text
                    # else:
                    #    return None
                    return None  # Fail if indicator doesn't appear
                else:
                    self.logger.info(f"Response generation appears complete (indicator found).")
                    # Add a small delay AFTER indicator appears, sometimes needed for text to fully render
                    time.sleep(2)
            # Strategy 2: Wait for response area text to stabilize (less reliable)
            else:
                self.logger.warning(
                    "No completion indicator selector found. Using text stabilization check (less reliable).")
                last_text = ""
                stable_count = 0
                wait_start = time.time()
                while time.time() - wait_start < 120:
                    response_element = self.browser_manager.find_element(response_sel, timeout=5)
                    current_text = response_element.text if response_element else ""
                    if current_text == last_text and current_text != "":
                        stable_count += 1
                    else:
                        stable_count = 0
                    last_text = current_text
                    if stable_count >= 3:  # Assume stable after 3 checks (6 seconds)
                        self.logger.info("Response text appears stable.")
                        break
                    time.sleep(2)
                else:
                    self.logger.error(f"Timeout waiting for response text from {provider_key} to stabilize.")
                    return None

            # Get the final response text
            response_element = self.browser_manager.find_element(response_sel, timeout=5)
            if not response_element:
                self.logger.error(f"Failed to find final response element ({response_sel}) after generation.")
                return None

            script_text = response_element.text
            self.logger.success(f"Received response from {provider_key}.")

            # Validate format
            if not self._validate_ai_response_format(script_text):
                self.logger.error("AI response format validation failed. Check log for details.")
                self.logger.info(f"Problematic AI Response:\n---\n{script_text}\n---")
                return None
            return script_text

        except Exception as e:
            self.logger.error(f"❌ An error occurred during browser interaction with {provider_key}: {e}")
            # Consider taking screenshot self.browser_manager.take_screenshot(f"{provider_key}_error")
            return None

    def _validate_ai_response_format(self, response_text: str) -> bool:
        """Validates if the AI response contains the required sections."""
        required_headers = ["SCRIPT:", "TITLE:", "DESCRIPTION:", "KEYWORDS:"]
        missing = []
        for header in required_headers:
            # Use regex for case-insensitivity and potential leading/trailing whitespace
            if not re.search(rf"^\s*{re.escape(header)}", response_text, re.IGNORECASE | re.MULTILINE):
                missing.append(header)

        if missing:
            self.logger.error(
                f"AI response is missing required sections (case-insensitive check): {', '.join(missing)}")
            return False

        # Optional: Add more checks (e.g., check if sections have content)
        self.logger.info("AI response format validated successfully.")
        return True

    def save_script(self, script_content: str) -> Optional[Path]:
        """Saves the generated script content to a timestamped file."""
        scripts_dir = self.config_manager.get_path('scripts_dir')
        try:
            scripts_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"generated_script_{timestamp}.txt"
            filepath = scripts_dir / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(script_content)
            self.logger.success(f"Script saved successfully to: {filepath}")
            return filepath
        except Exception as e:
            self.logger.error(f"❌ Failed to save script to {scripts_dir}: {e}")
            return None

    @staticmethod
    def parse_script_file(script_filepath: Path) -> Optional[Dict[str, Any]]:
        """Parses a saved script file to extract metadata sections."""
        logger = Logger()  # Get logger instance
        if not script_filepath.is_file():
            logger.error(f"Script file not found for parsing: {script_filepath}")
            return None

        try:
            with open(script_filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            metadata = {}
            sections = {
                "SCRIPT:": "script",
                "TITLE:": "title",
                "DESCRIPTION:": "description",
                "KEYWORDS:": "tags"  # Map KEYWORDS: to 'tags' key
            }
            current_key = None
            buffer = []  # Use list for efficient appending

            lines = content.splitlines()
            i = 0
            while i < len(lines):
                line = lines[i]
                found_header = False
                for header, key in sections.items():
                    # Case-insensitive check, allowing whitespace
                    if re.match(rf"^\s*{re.escape(header)}", line, re.IGNORECASE):
                        # Save previous section's buffer
                        if current_key:
                            metadata[current_key] = "\n".join(buffer).strip()

                        # Start new section
                        current_key = key
                        # Get content after header on the same line, strip leading space
                        after_header = re.sub(rf"^\s*{re.escape(header)}\s*", "", line, flags=re.IGNORECASE)
                        buffer = [after_header]  # Start new buffer
                        found_header = True
                        break

                if not found_header and current_key:
                    buffer.append(line)  # Append line to current section's buffer

                i += 1  # Move to next line

            # Save the last section's buffer
            if current_key:
                metadata[current_key] = "\n".join(buffer).strip()

            # Validate required keys were found
            required_keys = list(sections.values())
            if not all(key in metadata for key in required_keys):
                missing = [k for k in required_keys if k not in metadata]
                logger.error(f"Failed to parse required sections from {script_filepath}. Missing: {missing}")
                # Log content for debugging
                logger.info(f"Content of {script_filepath}:\n---\n{content}\n---")
                return None

            # Special handling for tags (split by comma)
            if 'tags' in metadata and isinstance(metadata['tags'], str):
                metadata['tags'] = [tag.strip() for tag in metadata['tags'].split(',') if tag.strip()]
            elif 'tags' not in metadata:  # Ensure tags key exists even if empty
                metadata['tags'] = []

            logger.info(f"Successfully parsed metadata from: {script_filepath}")
            return metadata

        except Exception as e:
            logger.error(f"❌ Error parsing script file {script_filepath}: {e}")
            return None


# --- Capcut Creator Class ---
class CapcutCreator:
    """Handles video creation using CapCut via browser automation."""

    def __init__(self, config_manager: ConfigManager, browser_manager: BrowserManager):
        self.config_manager = config_manager
        self.browser_manager = browser_manager
        self.logger = Logger()
        self.capcut_url = config_manager.get_config('VIDEO_SETTINGS', 'capcut_url')
        self.selectors = config_manager.selectors.get('capcut', {})

    def create_video(self, script_text: str) -> Optional[Path]:
        """Automates CapCut to create a video from the script."""
        self.logger.info("Starting CapCut video creation...")
        if not self.selectors:
            self.logger.critical("CapCut selectors not found in selectors.json.")

        # --- Get required settings and selectors from config ---
        style_key = self.config_manager.get_config('VIDEO_SETTINGS', 'capcut_style')
        voice_key = self.config_manager.get_config('VIDEO_SETTINGS', 'capcut_voice')
        resolution_key = self.config_manager.get_config('VIDEO_SETTINGS', 'capcut_export_resolution')
        framerate_key = self.config_manager.get_config('VIDEO_SETTINGS', 'capcut_export_frame_rate')
        # Format is currently assumed mp4 by download logic, but could be used for validation
        # format_key = self.config_manager.get_config('VIDEO_SETTINGS', 'capcut_export_format')

        try_it_sel = self.selectors.get('capcut_try_it_button')
        style_sel = self.selectors.get(f'capcut_style_{style_key}')
        voice_sel = self.selectors.get(f'capcut_voice_{voice_key}')
        script_input_sel = self.selectors.get('capcut_script_input')
        generate_sel = self.selectors.get('capcut_generate_button')
        export_sel = self.selectors.get('capcut_export_button')
        captions_menu_sel = self.selectors.get('capcut_captions_menu_button')
        captions_choice_sel = self.selectors.get('capcut_captions_choice_button')
        export_res_dropdown_sel = self.selectors.get('capcut_export_resolution_dropdown')
        export_res_option_sel = self.selectors.get(f'capcut_export_resolution_option_{resolution_key}')
        export_fps_dropdown_sel = self.selectors.get('capcut_export_framerate_dropdown')
        export_fps_option_sel = self.selectors.get(f'capcut_export_framerate_option_{framerate_key}')
        export_confirm_sel = self.selectors.get('capcut_export_confirm_button')
        # Optional: Add selectors for loading indicators if needed
        loading_indicator_sel = self.selectors.get('capcut_loading_indicator')  # Example
        generation_complete_indicator_sel = self.selectors.get(
            'capcut_generation_complete_indicator')  # Example: Export button enabled

        required_selectors = {
            # 'Try It Button': try_it_sel, # Making optional as user might land in editor
            f'Style ({style_key})': style_sel, f'Voice ({voice_key})': voice_sel,
            'Script Input': script_input_sel, 'Generate Button': generate_sel, 'Export Button': export_sel,
            'Captions Menu': captions_menu_sel, 'Caption Choice': captions_choice_sel,
            'Resolution Dropdown': export_res_dropdown_sel,
            f'Resolution Option ({resolution_key})': export_res_option_sel,
            'Framerate Dropdown': export_fps_dropdown_sel, f'Framerate Option ({framerate_key})': export_fps_option_sel,
            'Export Confirm': export_confirm_sel
        }
        missing_sels = [name for name, sel in required_selectors.items() if not sel]
        if missing_sels:
            self.logger.critical(f"Missing required CapCut selectors in selectors.json: {', '.join(missing_sels)}")

        # --- Browser Automation Steps ---
        try:
            if not self.browser_manager.navigate(self.capcut_url):
                return None

            # 1. Click Try It (Optional - if selector exists)
            if try_it_sel:
                self.logger.info("Attempting to click 'Try It' button...")
                if self.browser_manager.click_element(try_it_sel, timeout=20):
                    self.logger.info("'Try It' button clicked. Waiting for editor load...")
                    # Wait for a key editor element to appear after clicking 'Try It'
                    if not self.browser_manager.find_element(script_input_sel, timeout=60):
                        self.logger.error("CapCut editor did not load correctly after clicking 'Try It'.")
                        return None
                else:
                    self.logger.warning("Could not find or click 'Try It' button. Assuming already in editor.")
            else:
                self.logger.info("No 'Try It' button selector configured. Assuming already in editor.")
                # Still wait for editor elements
                if not self.browser_manager.find_element(script_input_sel, timeout=60):
                    self.logger.error("CapCut editor did not load correctly (script input not found).")
                    return None

            # 2. Choose Style
            self.logger.info(f"Selecting style: {style_key}")
            if not self.browser_manager.click_element(style_sel):
                self.logger.error(f"Failed to select style '{style_key}'.")
                return None
            time.sleep(1)

            # 3. Choose Voice
            self.logger.info(f"Selecting voice: {voice_key}")
            if not self.browser_manager.click_element(voice_sel):
                self.logger.error(f"Failed to select voice '{voice_key}'.")
                return None
            time.sleep(1)

            # 4. Paste Script
            self.logger.info("Pasting script...")
            if not self.browser_manager.input_text(script_input_sel, script_text):
                self.logger.error("Failed to paste script into CapCut.")
                return None
            time.sleep(1)

            # 5. Click Generate
            self.logger.info("Clicking 'Generate'...")
            if not self.browser_manager.click_element(generate_sel):
                self.logger.error("Failed to click 'Generate' button.")
                return None

            # --- Wait for video generation ---
            generation_wait = 180  # Increased timeout
            self.logger.info(f"Waiting up to {generation_wait} seconds for video generation...")
            # Use a more reliable indicator if available
            wait_target_sel = generation_complete_indicator_sel or export_sel  # Prefer specific indicator, fallback to export button
            wait_target_name = "generation complete indicator" if generation_complete_indicator_sel else "export button to be clickable"

            try:
                element_to_wait_for = self.browser_manager.find_element(wait_target_sel, timeout=generation_wait)
                if not element_to_wait_for:
                    raise TimeoutException(f"Target element {wait_target_name} not found after waiting.")
                # Optionally wait for clickability if it's the export button
                if wait_target_sel == export_sel:
                    WebDriverWait(self.browser_manager.get_driver(), 10).until(
                        EC.element_to_be_clickable(element_to_wait_for)
                    )
                self.logger.info(f"Video generation appears complete ({wait_target_name} found/ready).")
            except TimeoutException:
                self.logger.error(f"Timeout waiting for video generation to complete (waited for {wait_target_name}).")
                # Consider taking screenshot self.browser_manager.take_screenshot("capcut_generation_timeout")
                return None
            except Exception as wait_err:
                self.logger.error(f"Error waiting for video generation: {wait_err}")
                return None

            # 6. Open Captions Menu & Choose Caption
            self.logger.info("Adding captions...")
            if not self.browser_manager.click_element(captions_menu_sel):
                self.logger.error("Failed to open captions menu.")
                # Continue anyway, maybe captions aren't critical
            else:
                time.sleep(1)
                if not self.browser_manager.click_element(captions_choice_sel):
                    self.logger.error("Failed to choose caption option.")
                else:
                    self.logger.info("Captions added.")
                    time.sleep(2)  # Allow captions to apply

            # 7. Click Export
            self.logger.info("Clicking 'Export'...")
            if not self.browser_manager.click_element(export_sel):
                self.logger.error("Failed to click 'Export' button.")
                return None
            time.sleep(2)  # Wait for export settings modal

            # 8. Select Export Settings
            self.logger.info("Configuring export settings...")
            # Resolution
            if not self.browser_manager.click_element(export_res_dropdown_sel):
                self.logger.error("Failed to click resolution dropdown.")
                return None
            time.sleep(0.5)
            if not self.browser_manager.click_element(export_res_option_sel):
                self.logger.error(f"Failed to select resolution '{resolution_key}'.")
                return None
            time.sleep(0.5)
            # Framerate
            if not self.browser_manager.click_element(export_fps_dropdown_sel):
                self.logger.error("Failed to click framerate dropdown.")
                return None
            time.sleep(0.5)
            if not self.browser_manager.click_element(export_fps_option_sel):
                self.logger.error(f"Failed to select framerate '{framerate_key}'.")
                return None
            time.sleep(1)

            # 9. Confirm Export and Wait for Download
            download_dir = self.config_manager.get_path('downloads_dir')
            download_dir.mkdir(parents=True, exist_ok=True)
            initial_files = set(p for p in download_dir.iterdir() if p.is_file())

            self.logger.info("Confirming export and starting download...")
            if not self.browser_manager.click_element(export_confirm_sel):
                self.logger.error("Failed to click confirm export button.")
                return None

            downloaded_file_path = self.browser_manager.wait_for_download_complete(download_dir, initial_files,
                                                                                   timeout=600)  # Long timeout for export/download

            if not downloaded_file_path:
                self.logger.error("Video download failed or timed out.")
                # Consider taking screenshot self.browser_manager.take_screenshot("capcut_download_timeout")
                return None

            # 10. Move downloaded file to videos directory
            videos_dir = self.config_manager.get_path('videos_dir')
            videos_dir.mkdir(parents=True, exist_ok=True)
            # Create a more descriptive filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_video_filename = f"capcut_video_{timestamp}{downloaded_file_path.suffix}"  # Keep original suffix
            final_video_path = videos_dir / final_video_filename

            try:
                shutil.move(str(downloaded_file_path), str(final_video_path))
                self.logger.success(f"Moved downloaded video to: {final_video_path}")
                return final_video_path
            except Exception as move_err:
                self.logger.error(
                    f"❌ Failed to move downloaded video from {downloaded_file_path} to {final_video_path}: {move_err}")
                # Attempt to leave the file in downloads dir if move fails
                return downloaded_file_path  # Return original path as fallback

        except Exception as e:
            self.logger.error(f"❌ An unexpected error occurred during CapCut video creation: {e}")
            # Consider taking screenshot self.browser_manager.take_screenshot("capcut_error")
            return None


# --- YouTube Uploader Class ---
class YouTubeUploader:
    """Handles YouTube video upload using the API and metadata from script file."""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = Logger()
        # Client secrets are now handled by get_youtube_client_config()
        self.credentials_file = str(config_manager.get_api_path('youtube_credentials'))

    def _get_credentials(self) -> Optional[Credentials]:
        """Gets existing credentials or initiates OAuth flow using configured secrets."""
        creds = None
        # Check if token file exists
        if self.credentials_file and Path(self.credentials_file).exists():
            try:
                creds = Credentials.from_authorized_user_file(self.credentials_file, YOUTUBE_SCOPES)
                self.logger.info(f"Loaded existing YouTube credentials from: {self.credentials_file}")
            except Exception as e:
                self.logger.warning(
                    f"Error loading existing credentials from {self.credentials_file}: {e}. Will attempt re-authentication.")
                creds = None  # Force re-auth
        elif not self.credentials_file:
            self.logger.error("Credentials file path is not configured in api.json.")
            return None

        # If no valid credentials, run the OAuth flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    self.logger.info("Refreshing YouTube API credentials...")
                    creds.refresh(Request())
                    self.logger.info("Credentials refreshed successfully.")
                except Exception as e:
                    self.logger.error(f"❌ Failed to refresh credentials: {e}. Need to re-authenticate.")
                    # Delete potentially corrupted creds file
                    try:
                        Path(self.credentials_file).unlink(missing_ok=True)
                    except OSError:
                        pass  # Ignore if deletion fails (e.g., file not found)
                    creds = None  # Force re-auth

            # If still no valid creds after potential refresh attempt, initiate flow
            if not creds:
                client_config = self.config_manager.get_youtube_client_config()
                if not client_config:
                    self.logger.critical(
                        "Cannot initiate YouTube OAuth flow: Client secrets configuration is missing or invalid in api.json.")
                    return None  # Critical error, validation should prevent this

                # This part requires user interaction in a console/browser, which is NOT allowed in full auto.
                # The script MUST assume valid credentials_file already exists from a prior manual run.
                self.logger.error("❌ YouTube credentials not found or invalid, and refresh failed or not possible.")
                self.logger.error(
                    f"Please run the authentication flow manually first to generate a valid '{Path(self.credentials_file).name}' file.")
                self.logger.error("Manual flow would use client secrets from api.json (embedded or file). Example:")
                if isinstance(client_config, Path):
                    self.logger.error(
                        f"# flow = InstalledAppFlow.from_client_secrets_file(str(client_config), YOUTUBE_SCOPES)")
                else:  # It's a dict
                    self.logger.error(f"# flow = InstalledAppFlow.from_client_config(client_config, YOUTUBE_SCOPES)")
                self.logger.error(f"# creds = flow.run_local_server(port=0)")
                self.logger.error(f"# with open('{self.credentials_file}', 'w') as token:")
                self.logger.error(f"#     token.write(creds.to_json())")
                return None  # Cannot proceed without valid creds in full auto mode

        # Save the credentials (especially if refreshed)
        try:
            with open(self.credentials_file, 'w') as token:
                token.write(creds.to_json())
            self.logger.info(f"YouTube credentials verified and saved/updated: {self.credentials_file}")
        except Exception as e:
            self.logger.warning(f"Failed to save updated credentials to {self.credentials_file}: {e}")

        return creds

    def upload_video(self, video_filepath: Path, metadata: Dict[str, Any]) -> Optional[str]:
        """Uploads the video file to YouTube with the provided metadata."""
        self.logger.info(f"🚀 Starting YouTube upload for: {video_filepath}")

        if not video_filepath.is_file():
            self.logger.error(f"Video file not found: {video_filepath}")
            return None

        # Validate required metadata
        required_meta = ['title', 'description', 'tags']
        if not all(key in metadata for key in required_meta):
            self.logger.error(
                f"Missing required metadata for YouTube upload. Need: {required_meta}. Got: {list(metadata.keys())}")
            return None

        credentials = self._get_credentials()
        if not credentials:
            self.logger.error("Failed to obtain valid YouTube API credentials. Cannot upload.")
            return None

        try:
            youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=credentials)

            # Ensure tags are a list of strings
            tags_list = metadata.get('tags', [])
            if isinstance(tags_list, str):
                tags_list = [tag.strip() for tag in tags_list.split(',') if tag.strip()]
            elif not isinstance(tags_list, list):
                tags_list = []

            # Truncate tags if total length exceeds YouTube limit (approx 500 chars)
            # Simple truncation for now, more sophisticated logic could be added
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

            body = {
                'snippet': {
                    'title': metadata['title'][:100],  # Max 100 chars
                    'description': metadata['description'][:5000],  # Max 5000 chars
                    'tags': truncated_tags,
                    'categoryId': self.config_manager.get_config('YOUTUBE_SETTINGS', 'category_id')
                },
                'status': {
                    'privacyStatus': self.config_manager.get_config('YOUTUBE_SETTINGS', 'privacy_status'),
                    'selfDeclaredMadeForKids': False  # Assume not made for kids unless specified
                }
            }

            # Insert the video
            self.logger.info("Uploading video to YouTube...")
            insert_request = youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=MediaFileUpload(str(video_filepath), chunksize=-1, resumable=True)
            )

            # --- Resumable Upload ---
            response = None
            retries = 0
            max_retries = 5
            while response is None:
                try:
                    status, response = insert_request.next_chunk()
                    if status:
                        self.logger.info(f"Upload progress: {int(status.progress() * 100)}%")
                except HttpError as e:
                    if e.resp.status in [500, 502, 503, 504]:
                        retries += 1
                        if retries > max_retries:
                            self.logger.error("Maximum retries exceeded for YouTube upload.")
                            raise e  # Re-raise after max retries
                        wait_time = (2 ** retries) + random.random()
                        self.logger.warning(
                            f"YouTube API error (Status: {e.resp.status}). Retrying in {wait_time:.2f} seconds...")
                        time.sleep(wait_time)
                    else:
                        self.logger.error(f"Non-retriable YouTube API error: {e}")
                        raise e  # Re-raise non-retriable errors
                except Exception as e:
                    self.logger.error(f"An unexpected error occurred during YouTube upload chunk: {e}")
                    raise e  # Re-raise other unexpected errors

            video_id = response.get('id')
            self.logger.success(f"Video uploaded successfully! Video ID: {video_id}")
            return video_id

        except HttpError as e:
            self.logger.error(f"❌ An HTTP error occurred during YouTube upload: {e}")
            return None
        except Exception as e:
            self.logger.error(f"❌ An unexpected error occurred during YouTube upload process: {e}")
            return None


# --- Upload Tracker Class ---
class UploadTracker:
    """Tracks uploaded videos to prevent duplicates."""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = Logger()
        self.log_filepath = config_manager.get_path('uploaded_videos_log')
        self._ensure_log_file_exists()

    def _ensure_log_file_exists(self):
        """Creates the log file and its directory if they don't exist."""
        try:
            self.log_filepath.parent.mkdir(parents=True, exist_ok=True)
            if not self.log_filepath.exists():
                self.log_filepath.touch()
                self.logger.info(f"Created upload log file: {self.log_filepath}")
        except Exception as e:
            self.logger.error(f"Failed to create or access upload log file {self.log_filepath}: {e}")

    def log_uploaded_video(self, video_title: str):
        """Logs the timestamp and title of an uploaded video."""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"{timestamp} - Title: {video_title}\n"
            with open(self.log_filepath, 'a', encoding='utf-8') as f:
                f.write(log_entry)
            self.logger.info(f"Logged uploaded video: '{video_title}' to {self.log_filepath}")
        except Exception as e:
            self.logger.error(f"Failed to log uploaded video to {self.log_filepath}: {e}")

    def check_if_uploaded(self, video_title: str) -> bool:
        """Checks if a video with the exact title has already been logged."""
        if not self.log_filepath.exists():
            return False  # Cannot check if log doesn't exist
        try:
            search_string = f"Title: {video_title}"
            with open(self.log_filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    # Case-insensitive check for robustness
                    if search_string.lower() in line.lower():
                        self.logger.warning(
                            f"Duplicate upload detected: Video with title '{video_title}' found in log.")
                        return True
            return False
        except Exception as e:
            self.logger.error(f"Error reading upload log file {self.log_filepath}: {e}")
            return False  # Fail safe: assume not uploaded if log is unreadable


# --- Main Orchestration ---
def main():
    logger = None  # Initialize logger variable
    browser_manager = None  # Initialize browser manager
    try:
        # 1. Load Configuration (and initialize logger)
        config_manager = ConfigManager()
        logger = Logger()  # Get the initialized logger instance

        # 2. Initialize Browser Manager (conditionally)
        ai_provider = config_manager.get_config('AI_SETTINGS', 'provider').lower()
        video_provider = config_manager.get_config('VIDEO_SETTINGS', 'provider').lower()
        # Initialize if needed for AI OR Video step
        if ai_provider in ['chatgpt_browser', 'grok_browser'] or video_provider == 'capcut_browser':
            browser_manager = BrowserManager(config_manager)
            # Attempt to get driver instance early to catch connection issues
            driver_instance = browser_manager.get_driver()
            if not driver_instance:
                logger.critical("Failed to initialize or connect to the browser. Exiting.")

        # 3. Generate Script
        logger.info("--- Starting Script Generation Phase ---")
        script_generator = ScriptGenerator(config_manager, browser_manager)
        raw_script_content = script_generator.generate_script()

        if not raw_script_content:
            logger.critical("Failed to generate script content. Exiting.")
            # No need to exit(1) here, logger.critical does it

        # 4. Save Raw Script
        script_filepath = script_generator.save_script(raw_script_content)
        if not script_filepath:
            logger.critical("Failed to save generated script. Exiting.")

        # 5. Parse Script for Metadata and Content
        logger.info("--- Parsing Script File ---")
        parsed_data = ScriptGenerator.parse_script_file(script_filepath)
        if not parsed_data:
            logger.critical(f"Failed to parse metadata from script file: {script_filepath}. Exiting.")

        script_for_video = parsed_data.get('script')
        youtube_metadata = {
            'title': parsed_data.get('title'),
            'description': parsed_data.get('description'),
            'tags': parsed_data.get('tags')  # Already parsed into list or empty list
        }

        # Ensure title exists before checking duplicates
        if not youtube_metadata['title']:
            logger.critical(f"Parsed script file {script_filepath} is missing a TITLE. Exiting.")

        # 6. Check for Duplicate Upload (using Title)
        logger.info("--- Checking Upload History ---")
        upload_tracker = UploadTracker(config_manager)
        if upload_tracker.check_if_uploaded(youtube_metadata['title']):
            logger.warning(
                "This video title has already been uploaded according to the log. Skipping video creation and upload.")
            # Exit gracefully if duplicate
            sys.exit(0)

            # --- Proceed only if not duplicate ---
        # 7. Create Video
        logger.info("--- Starting Video Creation Phase ---")
        video_filepath = None
        if video_provider == 'capcut_browser':
            if not browser_manager:
                # This check should be redundant due to earlier initialization
                logger.critical("CapCut provider selected, but BrowserManager not initialized.")
            capcut_creator = CapcutCreator(config_manager, browser_manager)
            video_filepath = capcut_creator.create_video(script_for_video)
        # Add other video providers here
        # elif video_provider == 'some_other_tool':
        #     # ... video creation logic ...
        else:
            logger.critical(f"Unsupported video provider configured: {video_provider}")

        if not video_filepath:
            logger.critical("Failed to create video file. Exiting.")

        # 8. Upload to YouTube
        logger.info("--- Starting YouTube Upload Phase ---")
        uploader = YouTubeUploader(config_manager)
        video_id = uploader.upload_video(video_filepath, youtube_metadata)

        if video_id:
            # 9. Log Successful Upload
            upload_tracker.log_uploaded_video(youtube_metadata['title'])
            logger.success(f"Automation cycle completed successfully! Video ID: {video_id}")
        else:
            logger.error("YouTube upload failed. Check previous logs for details.")
            # Exit with error code if upload fails
            sys.exit(1)

    except Exception as e:
        # Catch-all for unexpected errors in the main flow
        if logger:
            logger.error(f"❌ An unexpected critical error occurred in the main workflow: {e}", exc_info=True)
        else:
            print(f"❌ An unexpected critical error occurred before logger initialization: {e}")
        sys.exit(1)
    finally:
        # 10. Cleanup
        if browser_manager:
            browser_manager.close_driver()  # close_driver handles not quitting if connected via debugger
        if logger:
            logger.info("--- Automation Script Finished ---")
        else:
            print("--- Automation Script Finished (Logger might have failed) ---")


if __name__ == "__main__":
    main()





