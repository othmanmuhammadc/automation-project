#!/usr/bin/env python3
"""
Smart Automation Tool - Fully Automated YouTube Content Creation Pipeline
Author: AI Assistant (Revised by Manus)
Version: 5.6 (Refactored ScriptGenerator, enhanced comments and docstrings)
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

# --- Custom Exceptions ---
class ConfigurationError(Exception):
    """Custom exception for configuration-related errors."""
    pass

class BrowserInitializationError(Exception):
    """Custom exception for errors during browser setup."""
    pass

# --- Dependency Imports (Ensure these are handled if missing) ---
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
    print("❌ Error: Selenium is required. Run: pip install selenium")
    sys.exit(1)

try:
    from webdriver_manager.chrome import ChromeDriverManager
    from webdriver_manager.microsoft import EdgeChromiumDriverManager
except ImportError:
    print("❌ Error: webdriver-manager is required. Run: pip install webdriver-manager")
    sys.exit(1)

try:
    import google.generativeai as genai
    from google.generativeai.types import generation_types
    from google.api_core import exceptions as google_api_exceptions
except ImportError:
    genai = None; generation_types = None; google_api_exceptions = None

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload
except ImportError:
    InstalledAppFlow = None; Credentials = None; build = None; HttpError = None; MediaFileUpload = None

# --- Constants ---
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'
YOUTUBE_SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
MAX_GEMINI_RETRIES = 3


# --- Logger Class ---
class Logger:
    """Basic file and console logging singleton."""
    _instance = None
    def __new__(cls, *args, **kwargs):
        if cls._instance is None: cls._instance = super(Logger, cls).__new__(cls); cls._instance._initialized = False
        return cls._instance
    def __init__(self, log_file_path: Optional[str] = None):
        if self._initialized: return
        if log_file_path is None: print("Logger Error: Path not provided."); self.logger = None; self._initialized = True; return
        self.log_file = Path(log_file_path)
        try:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            for handler in logging.root.handlers[:]: logging.root.removeHandler(handler) # Clear existing handlers
            logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler(self.log_file, encoding='utf-8'), logging.StreamHandler(sys.stdout)])
            self.logger = logging.getLogger(__name__); print(f"Logger initialized: {self.log_file}")
        except Exception as e:
            print(f"Error logger init: {e}. Fallback to console."); logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler(sys.stdout)]); self.logger = logging.getLogger(__name__)
        self._initialized = True
    def _log(self, level, message):
        if self.logger: self.logger.log(level, message)
        else: print(f"{logging.getLevelName(level)}: {message}") # Fallback if logger object not created
    def info(self, message: str): self._log(logging.INFO, message)
    def error(self, message: str): self._log(logging.ERROR, message)
    def warning(self, message: str): self._log(logging.WARNING, message)
    def success(self, message: str): self._log(logging.INFO, f"✅ {message}")
    def critical(self, message: str): self._log(logging.CRITICAL, message)


# --- ConfigManager (Refactored _validate_configs) ---
class ConfigManager:
    """Manages loading, validation, and access to configuration files (INI, JSON)."""
    # ... (init and helper methods for loading and validation as per previous step, condensed for brevity) ...
    def __init__(self, base_dir_override: Optional[str] = None):
        self.base_dir = Path(base_dir_override) if base_dir_override else Path.cwd()
        self.customisation_file = self.base_dir / "customisation.ini"
        self.data_dir_placeholder = self.base_dir / "Data"
        self.selectors_file = self.data_dir_placeholder / "selectors.json"
        self.api_file = self.data_dir_placeholder / "api.json"
        try:
            pre_config = configparser.ConfigParser(allow_no_value=True)
            if not self.customisation_file.is_file(): raise ConfigurationError(f"Config file not found: {self.customisation_file}")
            pre_config.read(self.customisation_file, encoding='utf-8')
            log_file_path_str = pre_config.get('PATHS', 'log_file', fallback=None)
            if not log_file_path_str: raise ConfigurationError("Missing 'log_file' in [PATHS] of customisation.ini")
            self.log_file_abs_path = self.base_dir / log_file_path_str if not os.path.isabs(log_file_path_str) else Path(log_file_path_str)
            self.logger = Logger(str(self.log_file_abs_path))
        except (configparser.Error, ConfigurationError) as e: raise ConfigurationError(f"Failed to initialize logger due to config issue: {e}")
        self.config = self._load_ini_config(self.customisation_file)
        self.selectors = self._load_json_config(self.selectors_file)
        self.api_config = self._load_json_config(self.api_file)
        self.logger.info(f"Base directory: {self.base_dir}")
        self.required_ini_keys = {
            'PATHS': ['scripts_dir', 'videos_dir', 'downloads_dir', 'log_file', 'uploaded_videos_log'],
            'AI_SETTINGS': ['provider', 'ai_prompt'],
            'VIDEO_SETTINGS': ['provider', 'capcut_url', 'capcut_style', 'capcut_voice', 'capcut_export_resolution', 'capcut_export_format', 'capcut_export_frame_rate'],
            'YOUTUBE_SETTINGS': ['privacy_status', 'category_id', 'notify_subscribers'],
            'BROWSER_SETTINGS': ['primary_browser', 'user_data_dir', 'wait_timeout', 'retry_attempts', 'page_load_timeout', 'headless_mode']
        }
        self.required_api_keys = {'gemini': ['api_key']}
        self._validate_configs(); self._resolve_paths(); self.logger.success("Config loaded & validated.")
    def _load_ini_config(self, fp: Path) -> configparser.ConfigParser: # Same
        if not fp.is_file(): msg=f"INI file not found: {fp}"; self.logger.critical(msg); raise ConfigurationError(msg)
        try: conf = configparser.ConfigParser(allow_no_value=True); conf.read(fp, encoding='utf-8'); return conf
        except Exception as e: msg=f"Error reading INI {fp}: {e}"; self.logger.critical(msg); raise ConfigurationError(msg)
    def _load_json_config(self, fp: Path) -> Dict: # Same
        if not fp.is_file(): msg=f"JSON file not found: {fp}"; self.logger.critical(msg); raise ConfigurationError(msg)
        try:
            with open(fp, 'r', encoding='utf-8') as f: return json.load(f)
        except Exception as e: msg=f"Error reading JSON {fp}: {e}"; self.logger.critical(msg); raise ConfigurationError(msg)
    def _get_required_config(self, cfg, section, key, filename, section_dict=None) -> str: # Same
        val=None; loc_desc=f"section '[{section}]'" if section else "top level"
        if section_dict is not None: val=section_dict.get(key); loc_desc=f"section '{section}'"
        elif isinstance(cfg,configparser.ConfigParser):
            if section and cfg.has_option(section,key):val=cfg.get(section,key)
        elif isinstance(cfg,dict):val=cfg.get(key);loc_desc="top level"
        is_opt_empty = key in ['user_data_dir','debugger_port'] and val==''
        if val is None or (val=='' and not is_opt_empty):msg=f"Missing value for '{key}' in {loc_desc} of {filename}";self.logger.critical(msg);raise ConfigurationError(msg)
        if isinstance(val,str)and'YOUR_'in val:msg=f"Placeholder for '{key}' in {loc_desc} of {filename}";self.logger.critical(msg);raise ConfigurationError(msg)
        return val if val is not None else ''
    def _validate_ini_sections_and_keys(self, errors: list): # Same
        for section, keys in self.required_ini_keys.items():
            if not self.config.has_section(section): errors.append(f"Missing section '[{section}]' in {self.customisation_file}"); continue
            for key in keys:
                try: self._get_required_config(self.config, section, key, self.customisation_file)
                except ConfigurationError as e: errors.append(str(e))
        if self.config.get('BROWSER_SETTINGS','debugger_port',fallback=None)and not self.config.get('BROWSER_SETTINGS','debugger_port').isdigit():
            errors.append(f"Invalid 'debugger_port' in {self.customisation_file}. Must be integer.")
    def _validate_numeric_ini_values(self, errors: list): # Same
        sets={'BROWSER_SETTINGS':['wait_timeout','retry_attempts','page_load_timeout'],'YOUTUBE_SETTINGS':['category_id']}
        for section,keys in sets.items():
            if self.config.has_section(section):
                for key in keys:
                    val=self.config.get(section,key,fallback=None)
                    if val and not val.isdigit():errors.append(f"Non-integer for '{key}' in [{section}] of {self.customisation_file}.")
    def _validate_boolean_ini_values(self, errors: list): # Same
        sets={'BROWSER_SETTINGS':['headless_mode'],'YOUTUBE_SETTINGS':['notify_subscribers']}
        for section,keys in sets.items():
            if self.config.has_section(section):
                for key in keys:
                    val=self.config.get(section,key,fallback=None)
                    if val and val.lower()not in['true','false']:errors.append(f"Non-boolean for '{key}' in [{section}] of {self.customisation_file}.")
    def _validate_ai_provider_config(self, errors: list): # Same
        provider=self.config.get('AI_SETTINGS','provider',fallback='').lower()
        if provider=='gemini':
            if genai is None:errors.append("AI 'gemini' selected, but google-generativeai lib not installed.")
            cfg_sec=self.api_config.get('gemini')
            if not cfg_sec or not isinstance(cfg_sec,dict):errors.append(f"Missing/invalid 'gemini' section in {self.api_file}.")
            else:
                for key in self.required_api_keys.get('gemini',[]):
                    try:self._get_required_config(None,'gemini',key,self.api_file,section_dict=cfg_sec)
                    except ConfigurationError as e:errors.append(str(e))
    def _validate_youtube_api_config(self, errors: list): # Same
        if InstalledAppFlow is None:errors.append("Google auth libs not installed.");return
        yt_cfg=self.api_config.get('youtube')
        if not yt_cfg or not isinstance(yt_cfg,dict):errors.append(f"Missing/invalid 'youtube' section in {self.api_file}.");return
        try:self._get_required_config(None,'youtube','credentials_file',self.api_file,section_dict=yt_cfg)
        except ConfigurationError as e:errors.append(str(e))
        has_file='client_secrets_file'in yt_cfg and yt_cfg['client_secrets_file']
        has_embed='client_secrets_config'in yt_cfg and isinstance(yt_cfg['client_secrets_config'],dict)and yt_cfg['client_secrets_config']
        if not has_file and not has_embed:errors.append(f"Missing YouTube client secrets in {self.api_file}.")
        elif has_file:
            sf_rel=yt_cfg['client_secrets_file']
            if isinstance(sf_rel,str)and'YOUR_'in sf_rel:errors.append(f"Placeholder 'client_secrets_file' in {self.api_file}.")
            elif isinstance(sf_rel,str):
                sf_abs=self.base_dir/sf_rel if not os.path.isabs(sf_rel)else Path(sf_rel)
                if not sf_abs.is_file():errors.append(f"YouTube 'client_secrets_file' not exist: {sf_abs}")
        elif has_embed and not('web'in yt_cfg['client_secrets_config']or'installed'in yt_cfg['client_secrets_config']):errors.append(f"Invalid 'client_secrets_config' in {self.api_file}.")
    def _validate_selector_configs(self, errors: list): # Same
        ai_provider=self.config.get('AI_SETTINGS','provider',fallback='').lower()
        vid_provider=self.config.get('VIDEO_SETTINGS','provider',fallback='').lower()
        needed_sel_providers=set()
        if'browser'in ai_provider:needed_sel_providers.add(ai_provider.replace('_browser',''))
        if'browser'in vid_provider:needed_sel_providers.add(vid_provider.replace('_browser',''))
        for prov in needed_sel_providers:
            if prov not in self.selectors or not isinstance(self.selectors[prov],dict)or not self.selectors[prov]:errors.append(f"Missing/empty selectors for '{prov}' in {self.selectors_file}")
    def _validate_configs(self): # Same
        self.logger.info("Validating configurations...")
        errors:List[str]=[]
        self._validate_ini_sections_and_keys(errors); self._validate_numeric_ini_values(errors); self._validate_boolean_ini_values(errors)
        self._validate_ai_provider_config(errors); self._validate_youtube_api_config(errors); self._validate_selector_configs(errors)
        if errors:full_msg="Critical config errors:\n- "+"\n- ".join(errors);self.logger.critical(full_msg);raise ConfigurationError(full_msg)
        self.logger.info("Core configuration validation passed.")
    def _resolve_paths(self): # Same
        self.logger.info("Resolving paths...")
        for section in ['PATHS']:
            if self.config.has_section(section):
                for key, value in self.config.items(section):
                    if value and not os.path.isabs(value) and ('/' in value or '\\' in value): self.config.set(section, key, str((self.base_dir / value).resolve()))
                    elif value: self.config.set(section, key, str(Path(value).resolve()))
        if 'youtube' in self.api_config and isinstance(self.api_config['youtube'], dict):
            for key in ['credentials_file', 'client_secrets_file']:
                value = self.api_config['youtube'].get(key)
                if isinstance(value, str) and value and not os.path.isabs(value): self.api_config['youtube'][key] = str((self.base_dir / value).resolve())
                elif isinstance(value, str) and value: self.api_config['youtube'][key] = str(Path(value).resolve())
    def get_config(self,s:str,k:str,fb:Any=None)->Any:return self.config.get(s,k,fallback=fb)
    def get_selector(self,s:str,k:str)->Optional[List[str]]: # Same
        ps=self.selectors.get(s,{});
        if not ps:return None
        parts=k.split('.');cl=ps
        for i,p in enumerate(parts):
            if isinstance(cl,dict):cl=cl.get(p)
            elif isinstance(cl,list)and i<len(parts)-1:self.logger.warning(f"Sel path err: {p} in {k} for {s} list mid-path.");return None
            elif not isinstance(cl,dict)and i<len(parts)-1:self.logger.warning(f"Sel path err: {p} in {k} for {s} not dict ({type(cl)}).");return None
            if cl is None:return None
        if isinstance(cl,list)and all(isinstance(x,str)for x in cl):return cl
        if isinstance(cl,str):return[cl]
        if cl is not None:self.logger.warning(f"Invalid sel format [{s}].{k}: Expected list/str, got {type(cl)}.")
        return None
    def get_api_config(self,s:str,k:Optional[str]=None)->Any:return self.api_config.get(s,{}).get(k)if k else self.api_config.get(s)
    def get_path(self,k:str)->Path:path_str=self.config.get('PATHS',k);if not path_str:msg=f"Path key '{k}' not in [PATHS].";self.logger.critical(msg);raise ConfigurationError(msg);return Path(path_str)
    def get_api_path(self,k:str)->Optional[Path]:path_str=self.api_config.get('youtube',{}).get(k);return Path(path_str)if path_str else None
    def get_youtube_client_config(self)->Union[Path,Dict,None]: # Same
        yt_cfg=self.api_config.get('youtube',{});embed_sec=yt_cfg.get('client_secrets_config');sf_path_str=yt_cfg.get('client_secrets_file')
        if embed_sec and isinstance(embed_sec,dict):self.logger.info("Using embedded YT client secrets.");return embed_sec
        elif sf_path_str:
            sf_path=Path(sf_path_str)
            if sf_path.is_file():self.logger.info(f"Using YT client secrets file: {sf_path}");return sf_path
            else:msg=f"YT 'client_secrets_file' not found: {sf_path}";self.logger.error(msg);raise ConfigurationError(msg)
        else:msg="No valid YT client secrets found.";self.logger.error(msg);raise ConfigurationError(msg)

# --- BrowserManager (Enhanced Docstrings and Comments) ---
class BrowserManager:
    """
    Manages Selenium WebDriver instances, including setup, connection, and basic operations.
    Supports launching new browsers or connecting to existing ones via a debugger port.
    Includes retry logic and fallback mechanisms for robustness.
    """
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = Logger()
        self.driver: Optional[webdriver.remote.webdriver.WebDriver] = None # More specific type hint
        self.wait_timeout: int = int(config_manager.get_config('BROWSER_SETTINGS', 'wait_timeout', 30))
        self.retry_attempts: int = int(config_manager.get_config('BROWSER_SETTINGS', 'retry_attempts', 2))
        self.page_load_timeout: int = int(config_manager.get_config('BROWSER_SETTINGS', 'page_load_timeout', 60))
        self._connected_via_debugger: bool = False
        self.browser_type: str = config_manager.get_config('BROWSER_SETTINGS', 'primary_browser', 'chrome').lower()
        self.user_data_dir: Optional[str] = config_manager.get_config('BROWSER_SETTINGS', 'user_data_dir', fallback=None) # Allow None
        self.headless: bool = config_manager.get_config('BROWSER_SETTINGS', 'headless_mode', 'true').lower() == 'true'
        self.debugger_port_str: Optional[str] = config_manager.get_config('BROWSER_SETTINGS', 'debugger_port', fallback=None)
        self.debugger_port: Optional[int] = None
        if self.debugger_port_str:
            try: self.debugger_port = int(self.debugger_port_str)
            except ValueError: self.logger.warning(f"Invalid debugger_port '{self.debugger_port_str}', ignoring."); self.debugger_port = None

    def _configure_options(self, use_user_data_dir: bool = True) -> Union[ChromeOptions, EdgeOptions]:
        """Creates and configures browser options based on settings."""
        options: Union[ChromeOptions, EdgeOptions]
        if self.browser_type == 'chrome': options = ChromeOptions()
        elif self.browser_type == 'edge': options = EdgeOptions()
        else:
            msg = f"Unsupported browser type specified: {self.browser_type}"
            self.logger.error(msg); raise BrowserInitializationError(msg)

        options.add_experimental_option('excludeSwitches', ['enable-logging']) # Suppress DevTools messages
        if self.headless: options.add_argument('--headless')
        # Common arguments for stability in various environments
        common_args = ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--window-size=1920,1080", "--lang=en-US", "--disable-extensions", "--disable-popup-blocking"]
        for arg in common_args: options.add_argument(arg)

        if use_user_data_dir and self.user_data_dir: # Apply user data directory if specified and requested
            resolved_user_data_dir = Path(self.user_data_dir).resolve()
            self.logger.info(f"Attempting to use user data directory: {resolved_user_data_dir}")
            options.add_argument(f"user-data-dir={resolved_user_data_dir}")
        elif not use_user_data_dir and self.user_data_dir:
             self.logger.info("User data directory specified but being skipped for this connection attempt (e.g. debugger connection).")
        return options

    def _init_driver(self):
        """
        Initializes or connects to a WebDriver instance.
        Tries connecting via debugger port first if configured.
        Falls back to launching a new browser instance, with or without user_data_dir.
        Raises:
            BrowserInitializationError: If all attempts to initialize or connect fail.
        """
        driver = None
        attempt_debugger = bool(self.debugger_port)

        # Configure options once, deciding on user_data_dir based on debugger attempt
        # If connecting via debugger, user_data_dir is typically not set on the options for the new driver object,
        # as it's assumed the running browser already uses it.
        current_options = self._configure_options(use_user_data_dir=not attempt_debugger)

        if attempt_debugger:
            debugger_address = f"127.0.0.1:{self.debugger_port}"
            self.logger.info(f"Attempting to connect to existing browser via debugger: {debugger_address}")
            # For debugger connection, options usually include debuggerAddress but NOT user-data-dir
            # as the running browser instance is already using its user data directory.
            debug_options = self._configure_options(use_user_data_dir=False) # Ensure no user-data-dir for debugger connection
            debug_options.add_experimental_option("debuggerAddress", debugger_address)
            try:
                if self.browser_type == 'chrome': service = ChromeService(ChromeDriverManager().install()); driver = webdriver.Chrome(service=service, options=debug_options)
                elif self.browser_type == 'edge': service = EdgeService(EdgeChromiumDriverManager().install()); driver = webdriver.Edge(service=service, options=debug_options)
                self.logger.info(f"Successfully connected via debugger. Current URL: {driver.current_url}") # type: ignore
                self._connected_via_debugger = True
            except WebDriverException as e: self.logger.warning(f"Debugger connection failed: {e}. Will try launching new instance."); driver = None; self._connected_via_debugger = False
            except Exception as e: self.logger.error(f"Unexpected error connecting via debugger: {e}"); driver = None; self._connected_via_debugger = False

        if not driver: # Fallback to new instance if debugger connection failed or wasn't attempted
            self.logger.info(f"Launching new {self.browser_type} browser instance...")
            try_with_user_data = True
            if self._connected_via_debugger: try_with_user_data = False # Should not happen if driver is None

            for attempt_num in range(2): # Max 2 attempts: 1. (maybe with user_data_dir), 2. (maybe without user_data_dir)
                if attempt_num == 1 and self.user_data_dir: # Second attempt, and user_data_dir was tried
                    self.logger.info("Retrying new instance without user_data_dir...")
                    try_with_user_data = False
                elif attempt_num == 1 and not self.user_data_dir: # No user_data_dir to remove, so no point in retrying same config
                    break

                current_launch_options = self._configure_options(use_user_data_dir=try_with_user_data)
                try:
                    if self.browser_type == 'chrome': service = ChromeService(ChromeDriverManager().install()); driver = webdriver.Chrome(service=service, options=current_launch_options)
                    elif self.browser_type == 'edge': service = EdgeService(EdgeChromiumDriverManager().install()); driver = webdriver.Edge(service=service, options=current_launch_options)
                    self.logger.success(f"New {self.browser_type} browser initialized {'with user_data_dir' if try_with_user_data and self.user_data_dir else '(no user_data_dir or not specified)'}.")
                    self._connected_via_debugger = False; break # Success, exit loop
                except WebDriverException as e:
                    log_msg = f"Failed to initialize {self.browser_type} WebDriver {'with user_data_dir' if try_with_user_data and self.user_data_dir else '(no user_data_dir or not specified)'}: {e}"
                    if try_with_user_data and self.user_data_dir : self.logger.warning(log_msg) # Log as warning if we can retry without user_data_dir
                    else: self.logger.error(log_msg); raise BrowserInitializationError(log_msg) from e # Raise if no more fallbacks
                except Exception as e_init: # Catch other errors
                    msg = f"Unexpected error during browser launch: {e_init}"
                    self.logger.error(msg); raise BrowserInitializationError(msg) from e_init

                if driver: break # Successfully launched

        if driver: self.driver = driver; self.driver.set_page_load_timeout(self.page_load_timeout)
        else: msg = f"All attempts to initialize or connect to {self.browser_type} browser failed."; self.logger.error(msg); raise BrowserInitializationError(msg)

    def get_driver(self) -> webdriver.remote.webdriver.WebDriver: # More specific return type
        """
        Returns the WebDriver instance, initializing if needed.
        Raises:
            BrowserInitializationError: If driver initialization fails.
        Returns:
            webdriver.remote.webdriver.WebDriver: The initialized WebDriver instance.
        """
        if not self.driver:
            try: self._init_driver()
            except BrowserInitializationError: raise # Propagate
            if not self.driver: raise BrowserInitializationError("Browser driver is None after init attempts.") # Should be caught by _init_driver
        return self.driver

    def close_driver(self): # Docstring added
        """Closes the WebDriver if running. If connected via debugger, it detaches without closing the browser."""
        if self.driver:
            try:
                if self._connected_via_debugger: self.logger.info("Detaching from browser (connected via debugger port). Browser remains open.")
                else: self.logger.info("Closing browser..."); self.driver.quit(); self.logger.info("Browser closed.")
            except WebDriverException as e:
                if "disconnected" in str(e) or "unable to connect" in str(e): self.logger.warning(f"Browser seems to have already closed or disconnected: {e}")
                else: self.logger.error(f"Error closing/detaching browser: {e}")
            except Exception as e: self.logger.error(f"Unexpected error closing/detaching browser: {e}")
            finally: self.driver = None; self._connected_via_debugger = False

    # ... (navigate, find_element, click_element, input_text, take_screenshot, wait_for_download_complete with improved comments/docstrings if needed) ...
    # (These methods already have decent error handling and logging from previous steps)
    # Example for find_element docstring:
    def find_element(self, selectors: List[str], timeout: Optional[int]=None, visible: bool=False) -> Optional[Any]:
        """
        Finds an element using a list of selectors (CSS or XPath).
        Waits for presence by default, optionally waits for visibility.
        Args:
            selectors: A list of selector strings. XPath if starts with '/' or '(', CSS otherwise.
            timeout: Optional custom timeout in seconds. Defaults to self.wait_timeout.
            visible: If True, waits for element visibility. Default is False (presence).
        Returns:
            The WebElement if found, otherwise None.
        Raises:
            RuntimeError: If the browser crashes during the find operation.
            BrowserInitializationError: If get_driver() fails.
        """
        # ... (implementation as before) ...
        try: driver = self.get_driver()
        except BrowserInitializationError as e: self.logger.error(f"Cannot find element: {e}"); return None
        if not selectors: self.logger.warning("find_element called with empty selectors."); return None
        wait_time = timeout if timeout is not None else self.wait_timeout; wait = WebDriverWait(driver, wait_time)
        condition = EC.visibility_of_element_located if visible else EC.presence_of_element_located; condition_desc = "visible" if visible else "present"
        for selector in selectors:
            try:
                locator = (By.XPATH, selector) if selector.startswith('/') or selector.startswith('(') else (By.CSS_SELECTOR, selector)
                element = wait.until(condition(locator)); self.logger.info(f"Found {condition_desc} element: {selector}"); return element
            except TimeoutException: self.logger.info(f"Element not {condition_desc} (timeout): {selector}")
            except NoSuchElementException: self.logger.info(f"Element not found: {selector}")
            except WebDriverException as e:
                 if "disconnected" in str(e) or "target crashed" in str(e): self.logger.error(f"Browser crashed finding: {selector}."); self.close_driver(); raise RuntimeError("Browser crashed while finding element.") from e
                 self.logger.error(f"WebDriver error finding {selector}: {e}")
            except Exception as e: self.logger.error(f"Unexpected error finding {selector}: {e}")
        self.logger.error(f"Element not {condition_desc} with any selectors: {selectors}"); return None


# --- ScriptGenerator (Refactored _generate_with_browser) ---
class ScriptGenerator:
    """Generates script text using AI (API or Browser), with error handling and retries."""
    def __init__(self, config_manager: ConfigManager, browser_manager: Optional[BrowserManager] = None):
        self.config_manager = config_manager; self.browser_manager = browser_manager; self.logger = Logger()
        self.ai_provider = config_manager.get_config('AI_SETTINGS', 'provider').lower()
        self.prompt = config_manager.get_config('AI_SETTINGS', 'ai_prompt')
        self.max_retries = int(config_manager.get_config('BROWSER_SETTINGS', 'retry_attempts', 3))

    def generate_script(self) -> Optional[str]: # Same
        self.logger.info(f"Generating script using AI provider: {self.ai_provider}")
        if self.ai_provider == 'gemini': return self._generate_with_gemini()
        elif self.ai_provider in ['chatgpt_browser', 'grok_browser']:
            if not self.browser_manager: self.logger.error("BrowserManager needed for browser AI."); return None
            return self._generate_with_browser()
        else: self.logger.error(f"Unsupported AI provider: {self.ai_provider}"); return None

    def _generate_with_gemini(self) -> Optional[str]: # Same
        if not genai or not generation_types or not google_api_exceptions: self.logger.error("Gemini lib not fully installed."); return None
        api_key = self.config_manager.get_api_config('gemini', 'api_key')
        if not api_key: self.logger.error("Gemini API key missing."); return None
        try: genai.configure(api_key=api_key); model = genai.GenerativeModel('gemini-pro')
        except Exception as e: self.logger.error(f"Failed to configure Gemini: {e}"); return None
        self.logger.info("Sending prompt to Gemini API...")
        for attempt in range(self.max_retries + 1):
            try:
                response = model.generate_content(self.prompt)
                if not response.parts:
                    block_reason = getattr(response.prompt_feedback, 'block_reason', None); safety_ratings = getattr(response.prompt_feedback, 'safety_ratings', [])
                    if block_reason: self.logger.error(f"❌ Gemini API blocked. Reason: {block_reason}")
                    elif safety_ratings: self.logger.error(f"❌ Gemini API response potentially blocked: {safety_ratings}")
                    else: self.logger.error("❌ Gemini API empty response.")
                    try: self.logger.info(f"Gemini Candidates: {response.candidates}")
                    except Exception: pass
                    return None
                script_text = response.text; self.logger.success("Received response from Gemini API.")
                if not self._validate_ai_response_format(script_text): self.logger.error("AI response format validation failed."); self.logger.info(f"Problematic AI Response:\n---\n{script_text}\n---"); return None
                return script_text
            except (google_api_exceptions.PermissionDenied, google_api_exceptions.InvalidArgument, generation_types.BlockedPromptException, generation_types.StopCandidateException) as e:
                self.logger.error(f"❌ Non-retriable Gemini API error: {type(e).__name__} - {e}"); return None
            except Exception as e:
                self.logger.warning(f"Error Gemini API (Attempt {attempt + 1}/{self.max_retries + 1}): {e}")
                if attempt < self.max_retries: time.sleep((2 ** attempt) + random.uniform(0, 1)); self.logger.info(f"Retrying Gemini...")
                else: self.logger.error(f"❌ Failed Gemini API after retries."); return None
        return None

    def _browser_ai_get_selectors(self, provider_key: str) -> Optional[Dict[str, Any]]:
        """Fetches and validates required selectors for a browser-based AI provider."""
        self.logger.info(f"Fetching selectors for AI provider: {provider_key}")
        selectors = {
            "prompt": self.config_manager.get_selector(provider_key, 'prompt_input') or \
                      self.config_manager.get_selector(provider_key, 'prompt_textarea'),
            "send": self.config_manager.get_selector(provider_key, 'send_button') or \
                    self.config_manager.get_selector(provider_key, 'submit_button'),
            "response": self.config_manager.get_selector(provider_key, 'response_area_last') or \
                        self.config_manager.get_selector(provider_key, 'response_output_last'),
            "completion_indicator": self.config_manager.get_selector(provider_key, 'response_regenerate_button'), # Optional
            "login_popup_close": self.config_manager.get_selector(provider_key, 'login_popup_close_button'), # Optional
            "cookie_accept": self.config_manager.get_selector(provider_key, 'cookie_accept_button') # Optional
        }
        if not all(selectors[k] for k in ["prompt", "send", "response"]):
            self.logger.error(f"Missing one or more critical selectors (prompt, send, response) for {provider_key}. Check selectors.json.")
            return None
        return selectors

    def _browser_ai_navigate_and_prepare(self, url: str, sels: Dict[str, Any]) -> bool:
        """Navigates to AI URL and handles initial popups."""
        if not self.browser_manager or not self.browser_manager.navigate(url): return False # type: ignore
        time.sleep(2) # Allow overlays to appear
        if sels.get("login_popup_close") and not self.browser_manager.click_element(sels["login_popup_close"], timeout=5): # type: ignore
            self.logger.warning("Login/signup popup not found or could not be closed.")
        if sels.get("cookie_accept") and not self.browser_manager.click_element(sels["cookie_accept"], timeout=5): # type: ignore
            self.logger.warning("Cookie banner not found or could not be accepted.")
        return True

    def _browser_ai_submit_prompt(self, prompt_text: str, sels: Dict[str, Any], provider_key: str) -> bool:
        """Inputs prompt and clicks send."""
        if not self.browser_manager or not self.browser_manager.input_text(sels["prompt"], prompt_text): # type: ignore
            self.logger.error(f"Failed to input prompt into {provider_key}. Selector: {sels['prompt']}"); return False
        time.sleep(1)
        if not self.browser_manager.click_element(sels["send"]): # type: ignore
            self.logger.error(f"Failed to click send button for {provider_key}. Selector: {sels['send']}"); return False
        self.logger.info(f"Prompt sent to {provider_key}. Waiting for response..."); return True

    def _browser_ai_wait_for_response(self, sels: Dict[str, Any], provider_key: str, timeout: int = 180) -> Optional[str]:
        """Waits for AI response, using indicator or text stabilization."""
        if not self.browser_manager: return None
        wait_start_time = time.time()

        if sels.get("completion_indicator"):
            self.logger.info(f"Waiting for completion indicator: {sels['completion_indicator']}")
            if not self.browser_manager.find_element(sels["completion_indicator"], timeout=timeout): # type: ignore
                self.logger.error(f"Timeout waiting for response completion indicator from {provider_key}.")
                self.browser_manager.take_screenshot(f"{provider_key}_completion_timeout")
                # Attempt to grab text anyway if indicator fails but response area has content
                return self._browser_ai_extract_response_text(sels["response"], provider_key, is_fallback=True) # type: ignore
            self.logger.info("Response generation appears complete (indicator found).")
            time.sleep(2) # Buffer for text to render
            return self._browser_ai_extract_response_text(sels["response"], provider_key) # type: ignore
        else: # Text stabilization logic
            self.logger.warning("No completion indicator selector. Using text stabilization (less reliable).")
            last_text = ""; stable_count = 0
            while time.time() - wait_start_time < timeout:
                current_text = self._browser_ai_extract_response_text(sels["response"], provider_key, is_fallback=True) # type: ignore
                if current_text is not None and current_text == last_text and current_text: # Ensure not None and not empty
                    stable_count += 1
                else: stable_count = 0; last_text = current_text if current_text is not None else ""
                if stable_count >= 3: self.logger.info(f"Response text appears stable after {int(time.time() - wait_start_time)}s."); return current_text
                self.logger.info(f"Waiting for text to stabilize... (Length: {len(last_text)}, Stable: {stable_count})")
                time.sleep(2)
            self.logger.error(f"Timeout waiting for response text to stabilize from {provider_key}.")
            self.browser_manager.take_screenshot(f"{provider_key}_stabilize_timeout")
            return last_text if last_text else None # Return last captured text if any

    def _browser_ai_extract_response_text(self, response_sel: List[str], provider_key: str, is_fallback: bool = False) -> Optional[str]:
        """Extracts text from the AI response element."""
        if not self.browser_manager: return None
        response_element = self.browser_manager.find_element(response_sel, timeout=10 if is_fallback else 5) # Shorter timeout for final extraction
        if response_element and hasattr(response_element, 'text') and response_element.text:
            return response_element.text
        else:
            if not is_fallback: # Only log error if it's not a fallback attempt during stabilization
                 self.logger.error(f"Failed to find or get text from response element for {provider_key} using {response_sel}.")
                 self.browser_manager.take_screenshot(f"{provider_key}_extract_response_fail")
            return None

    def _generate_with_browser(self) -> Optional[str]:
        """Generates script using browser automation, calling helper methods."""
        if not self.browser_manager: self.logger.error("BrowserManager not available for browser-based AI."); return None

        provider_key = 'chatgpt' if self.ai_provider == 'chatgpt_browser' else 'grok'
        ai_url = self.config_manager.get_config('AI_SETTINGS', f'{provider_key}_url', fallback=None)
        if not ai_url: self.logger.error(f"URL for {provider_key} not found in customisation.ini."); return None

        sels = self._browser_ai_get_selectors(provider_key)
        if not sels: return None # Error already logged by helper

        try:
            if not self._browser_ai_navigate_and_prepare(ai_url, sels): return None
            if not self._browser_ai_submit_prompt(self.prompt, sels, provider_key): return None

            response_text = self._browser_ai_wait_for_response(sels, provider_key)
            if response_text is None: # Handles cases where even fallback text is not found
                self.logger.error(f"Failed to retrieve any response text from {provider_key}.")
                # Screenshot might have been taken by _browser_ai_wait_for_response or _browser_ai_extract_response_text
                return None

            self.logger.success(f"Received response from {provider_key}.")
            if not self._validate_ai_response_format(response_text):
                self.logger.error(f"AI response format validation failed for {provider_key}."); self.logger.info(f"Problematic Response:\n{response_text}"); return None
            return response_text

        except RuntimeError as e: self.logger.error(f"❌ Browser crashed during {provider_key}: {e}"); return None
        except Exception as e:
            self.logger.error(f"❌ Unexpected error with {provider_key}: {e}", exc_info=True)
            if self.browser_manager: self.browser_manager.take_screenshot(f"{provider_key}_unexpected_error")
            return None

    def _validate_ai_response_format(self,response_text:str)->bool: # Same
        required_headers=["SCRIPT:","TITLE:","DESCRIPTION:","KEYWORDS:"];missing=[];found_any=False
        for header in required_headers:
            if re.search(rf"^\s*{re.escape(header)}",response_text,re.IGNORECASE|re.MULTILINE):found_any=True
            else:missing.append(header)
        if not found_any:self.logger.error("AI response lacks ANY required headers.");return False
        elif missing:self.logger.warning(f"AI response missing optional sections: {', '.join(missing)}")
        self.logger.info("AI response format validated.");return True
    def save_script(self,script_content:str)->Optional[Path]: # Same
        try:
            scripts_dir=self.config_manager.get_path('scripts_dir');scripts_dir.mkdir(parents=True,exist_ok=True)
            filepath=scripts_dir/f"generated_script_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filepath,'w',encoding='utf-8')as f:f.write(script_content)
            self.logger.success(f"Script saved to: {filepath}");return filepath
        except Exception as e:self.logger.error(f"❌ Failed to save script: {e}");return None
    @staticmethod
    def parse_script_file(script_filepath:Path)->Optional[Dict[str,Any]]: # Same
        logger=Logger()
        if not script_filepath.is_file():logger.error(f"Script file not found: {script_filepath}");return None
        try:
            with open(script_filepath,'r',encoding='utf-8')as f:content=f.read()
            metadata={};section_map={"SCRIPT":"script","TITLE":"title","DESCRIPTION":"description","KEYWORDS":"tags"}
            header_pattern=re.compile(r"^\s*("+"|".join(section_map.keys())+r")\s*:(.*)",re.IGNORECASE|re.MULTILINE)
            last_pos=0;current_key=None;buffer=[]
            for match in header_pattern.finditer(content):
                start,end=match.span();header_text=match.group(1).upper();value_on_header_line=match.group(2).strip()
                if current_key:buffer.append(content[last_pos:start].strip());metadata[current_key]="\n".join(filter(None,buffer)).strip()
                current_key=section_map[header_text];buffer=[value_on_header_line];last_pos=end
            if current_key:buffer.append(content[last_pos:].strip());metadata[current_key]="\n".join(filter(None,buffer)).strip()
            required_keys=['script','title','description','tags']
            missing=[k for k in required_keys if k not in metadata or not metadata[k]]
            if missing:logger.error(f"Failed to parse/empty sections in {script_filepath}. Missing/Empty: {missing}");return None
            if'tags'in metadata and isinstance(metadata['tags'],str):metadata['tags']=[tag.strip()for tag in metadata['tags'].split(',')if tag.strip()]
            elif'tags'not in metadata:metadata['tags']=[]
            logger.success(f"Successfully parsed metadata from {script_filepath}");return metadata
        except Exception as e:logger.error(f"❌ Error parsing script file {script_filepath}: {e}");return None

# --- VideoCreator (Refactored _create_with_capcut_browser from previous step) ---
class VideoCreator: # Assumes refactoring from previous step is applied
    def __init__(self, config_manager: ConfigManager, browser_manager: BrowserManager):
        self.config_manager = config_manager; self.browser_manager = browser_manager; self.logger = Logger()
        self.video_provider = config_manager.get_config('VIDEO_SETTINGS', 'provider').lower()
        self.capcut_url = config_manager.get_config('VIDEO_SETTINGS', 'capcut_url')
        self.capcut_style = config_manager.get_config('VIDEO_SETTINGS', 'capcut_style')
        self.capcut_voice = config_manager.get_config('VIDEO_SETTINGS', 'capcut_voice')
        self.capcut_resolution = config_manager.get_config('VIDEO_SETTINGS', 'capcut_export_resolution')
        self.capcut_framerate = config_manager.get_config('VIDEO_SETTINGS', 'capcut_export_frame_rate')
    def create_video(self, script_text: str) -> Optional[Path]:
        if self.video_provider == 'capcut_browser': return self._create_with_capcut_browser(script_text)
        else: self.logger.error(f"Unsupported video provider: {self.video_provider}"); return None
    def _capcut_get_and_validate_selectors(self) -> Optional[Dict[str, Any]]: # Same
        self.logger.info("Fetching and validating CapCut selectors...")
        selectors = {
            "style": self.config_manager.get_selector('capcut', f'styles.{self.capcut_style}'),
            "voice": self.config_manager.get_selector('capcut', f'voices.{self.capcut_voice}'),
            "script_input": self.config_manager.get_selector('capcut', 'script_input_area'),
            "generate": self.config_manager.get_selector('capcut', 'generate_button'),
            "export_open_dialog": self.config_manager.get_selector('capcut', 'export_button'),
            "res_dropdown": self.config_manager.get_selector('capcut', 'export_options.resolution_dropdown'),
            "resolution_option": self.config_manager.get_selector('capcut', f'export_options.resolution.{self.capcut_resolution}'),
            "fps_dropdown": self.config_manager.get_selector('capcut', 'export_options.frame_rate_dropdown'),
            "framerate_option": self.config_manager.get_selector('capcut', f'export_options.frame_rate.{self.capcut_framerate}'),
            "export_confirm": self.config_manager.get_selector('capcut', 'export_options.confirm_button') or self.config_manager.get_selector('capcut', 'export_confirm_button'),
            "try_it": self.config_manager.get_selector('capcut', 'try_it_button'),
            "gen_complete_indicator": self.config_manager.get_selector('capcut', 'generation_complete_indicator'),
            "captions_menu": self.config_manager.get_selector('capcut', 'captions_menu_button'),
            "captions_choice": self.config_manager.get_selector('capcut', 'captions_choice_option'),
        }
        critical_selector_keys = ["style", "voice", "script_input", "generate", "export_open_dialog", "resolution_option", "framerate_option", "export_confirm"]
        if selectors["resolution_option"]: critical_selector_keys.append("res_dropdown")
        if selectors["framerate_option"]: critical_selector_keys.append("fps_dropdown")
        missing_critical = [key for key in critical_selector_keys if not selectors.get(key)]
        if missing_critical: self.logger.error(f"Missing critical CapCut selectors: {', '.join(missing_critical)}."); return None
        self.logger.success("All critical CapCut selectors found."); return selectors
    def _capcut_navigate_and_prepare(self, sels: Dict[str, Any]) -> bool: # Same
        self.logger.info(f"Navigating to CapCut URL: {self.capcut_url}")
        if not self.browser_manager.navigate(self.capcut_url): return False
        if sels.get("try_it"):
            if not self.browser_manager.click_element(sels["try_it"], timeout=30): self.logger.warning("Could not click 'Try It'.") # type: ignore
        else: self.logger.info("No 'Try It' selector configured.")
        if not self.browser_manager.find_element(sels["script_input"], timeout=90, visible=True): self.logger.error(f"CapCut editor not loaded."); self.browser_manager.take_screenshot("capcut_editor_load_fail"); return False # type: ignore
        self.logger.success("CapCut editor loaded."); return True
    def _capcut_select_style_and_voice(self, sels: Dict[str, Any]) -> bool: # Same
        self.logger.info(f"Selecting style and voice...")
        if not self.browser_manager.click_element(sels["style"]): self.logger.error(f"Failed style select."); self.browser_manager.take_screenshot("capcut_style_fail"); return False; time.sleep(1) # type: ignore
        if not self.browser_manager.click_element(sels["voice"]): self.logger.error(f"Failed voice select."); self.browser_manager.take_screenshot("capcut_voice_fail"); return False; time.sleep(1) # type: ignore
        self.logger.success("Style and voice selected."); return True
    def _capcut_input_script_and_generate(self, script_text: str, sels: Dict[str, Any]) -> bool: # Same
        self.logger.info(f"Inputting script and starting generation...")
        if not self.browser_manager.input_text(sels["script_input"], script_text): self.logger.error(f"Failed script input."); self.browser_manager.take_screenshot("capcut_paste_fail"); return False; time.sleep(1) # type: ignore
        if not self.browser_manager.click_element(sels["generate"]): self.logger.error(f"Failed generate click."); self.browser_manager.take_screenshot("capcut_generate_click_fail"); return False # type: ignore
        wait_indicator = sels.get("gen_complete_indicator") or sels["export_open_dialog"]; wait_indicator_name = "generation indicator" if sels.get("gen_complete_indicator") else "export button" # type: ignore
        self.logger.info(f"Waiting for generation (indicator: {wait_indicator_name})...")
        element_to_wait = self.browser_manager.find_element(wait_indicator, timeout=300, visible=True) # type: ignore
        if not element_to_wait: self.logger.error(f"Timeout on generation ({wait_indicator_name})."); self.browser_manager.take_screenshot("capcut_generation_timeout"); return False
        if wait_indicator == sels["export_open_dialog"]: # type: ignore
            if not WebDriverWait(self.browser_manager.get_driver(), 20).until(EC.element_to_be_clickable(element_to_wait)): self.logger.error("Export button not clickable."); self.browser_manager.take_screenshot("capcut_export_not_clickable"); return False # type: ignore
        self.logger.success("Generation complete."); time.sleep(2); return True
    def _capcut_add_captions(self, sels: Dict[str, Any]) -> bool: # Same
        captions_menu_sel, captions_choice_sel = sels.get("captions_menu"), sels.get("captions_choice")
        if not captions_menu_sel or not captions_choice_sel: self.logger.info("Caption selectors not set, skipping."); return True
        self.logger.info("Adding captions...")
        if not self.browser_manager.click_element(captions_menu_sel): self.logger.warning(f"Failed captions menu. Skipping."); return True
        time.sleep(1)
        if not self.browser_manager.click_element(captions_choice_sel): self.logger.warning(f"Failed caption choice. Skipping."); return True
        self.logger.info("Captions added (or skipped)."); time.sleep(2); return True
    def _capcut_configure_export_settings(self, sels: Dict[str, Any]) -> bool: # Same
        self.logger.info("Configuring export settings...")
        if not self.browser_manager.click_element(sels["export_open_dialog"]): self.logger.error(f"Failed export dialog open."); self.browser_manager.take_screenshot("capcut_export_dialog_fail"); return False; time.sleep(2) # type: ignore
        if not self.browser_manager.click_element(sels["res_dropdown"]): self.logger.error(f"Failed res dropdown."); return False; time.sleep(0.5) # type: ignore
        if not self.browser_manager.click_element(sels["resolution_option"]): self.logger.error(f"Failed res option."); return False; time.sleep(1) # type: ignore
        if not self.browser_manager.click_element(sels["fps_dropdown"]): self.logger.error(f"Failed fps dropdown."); return False; time.sleep(0.5) # type: ignore
        if not self.browser_manager.click_element(sels["framerate_option"]): self.logger.error(f"Failed fps option."); return False; time.sleep(1) # type: ignore
        self.logger.success("Export settings configured."); return True
    def _capcut_export_and_download(self, sels: Dict[str, Any]) -> Optional[Path]: # Changed to take full sels
        self.logger.info(f"Confirming export to start download...")
        download_dir = self.config_manager.get_path('downloads_dir'); download_dir.mkdir(parents=True, exist_ok=True)
        initial_files = set(p for p in download_dir.iterdir() if p.is_file())
        if not self.browser_manager.click_element(sels["export_confirm"]): self.logger.error(f"Failed confirm export."); self.browser_manager.take_screenshot("capcut_export_confirm_fail"); return None # type: ignore
        dl_path = self.browser_manager.wait_for_download_complete(download_dir, initial_files, timeout=600)
        if not dl_path: self.logger.error("Download failed/timed out."); self.browser_manager.take_screenshot("capcut_download_timeout"); return None
        videos_dir = self.config_manager.get_path('videos_dir'); videos_dir.mkdir(parents=True, exist_ok=True)
        final_path = videos_dir / f"capcut_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}{dl_path.suffix or '.mp4'}"
        try: shutil.move(str(dl_path), str(final_path)); self.logger.success(f"Moved video to: {final_path}"); return final_path
        except Exception as e: self.logger.error(f"Failed to move video: {e}"); return dl_path
    def _create_with_capcut_browser(self, script_text: str) -> Optional[Path]: # Refactored
        self.logger.info(f"Starting CapCut video creation: {self.capcut_url}")
        sels = self._capcut_get_and_validate_selectors()
        if not sels: return None
        try:
            if not self._capcut_navigate_and_prepare(sels): return None
            if not self._capcut_select_style_and_voice(sels): return None
            if not self._capcut_input_script_and_generate(script_text, sels): return None
            self._capcut_add_captions(sels)
            if not self._capcut_configure_export_settings(sels): return None
            return self._capcut_export_and_download(sels) # Pass full sels dict
        except RuntimeError as e: self.logger.error(f"❌ Browser crashed in CapCut: {e}"); return None
        except WebDriverException as e: self.logger.error(f"❌ Selenium error in CapCut: {e}"); if self.browser_manager: self.browser_manager.take_screenshot("capcut_webdriver_error"); return None
        except Exception as e: self.logger.error(f"❌ Unexpected error in CapCut: {e}", exc_info=True); if self.browser_manager: self.browser_manager.take_screenshot("capcut_unexpected_error"); return None

# --- YouTubeUploader (Condensed) ---
class YouTubeUploader: # Same as prev step
    def __init__(self, config_manager: ConfigManager): self.config_manager = config_manager; self.logger = Logger(); self.credentials_path = config_manager.get_api_path('credentials_file');
    def _get_credentials(self) -> Optional[Credentials]: # Same
        creds = None
        if not self.credentials_path or not self.credentials_path.exists(): self.logger.error(f"YouTube credentials file not found: {self.credentials_path}."); return None
        try: creds = Credentials.from_authorized_user_file(str(self.credentials_path), YOUTUBE_SCOPES)
        except ValueError as e: self.logger.error(f"Error loading YouTube creds from {self.credentials_path}: {e}. Corrupted? Re-auth."); return None
        except Exception as e: self.logger.error(f"Unexpected error loading YouTube creds from {self.credentials_path}: {e}"); return None
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                self.logger.info("Refreshing YouTube API credentials...")
                try:
                    creds.refresh(Request())
                    with open(self.credentials_path, 'w') as token: token.write(creds.to_json())
                    self.logger.info(f"Refreshed credentials saved to: {self.credentials_path}")
                except Exception as e: self.logger.error(f"❌ Failed to refresh credentials: {e}. Delete '{self.credentials_path.name}' and re-auth."); return None
            else: self.logger.error(f"No valid YouTube creds at {self.credentials_path} & cannot refresh. Run initial auth."); return None
        return creds
    def upload_video(self, video_filepath: Path, metadata: Dict[str, Any]) -> Optional[str]: # Same
        self.logger.info(f"🚀 Starting YouTube upload for: {video_filepath}")
        if not video_filepath.is_file(): self.logger.error(f"Video file not found: {video_filepath}"); return None
        required_meta = ['title', 'description', 'tags']
        if any(key not in metadata or not metadata[key] for key in required_meta): self.logger.error(f"Missing metadata for upload. Need: {required_meta}."); return None
        credentials = self._get_credentials();
        if not credentials: self.logger.error("Failed to get valid YouTube API credentials."); return None
        if HttpError is None or MediaFileUpload is None or build is None: self.logger.error("Google API libs not available for YouTube upload."); return None
        try:
            youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=credentials)
            tags_list = metadata.get('tags', []); # ... tag processing (truncation) ...
            body = { 'snippet': { 'title': metadata['title'][:100], 'description': metadata['description'][:5000], 'tags': tags_list, 'categoryId': self.config_manager.get_config('YOUTUBE_SETTINGS', 'category_id')},
                     'status': {'privacyStatus': self.config_manager.get_config('YOUTUBE_SETTINGS', 'privacy_status', 'private'), 'selfDeclaredMadeForKids': False}}
            notify_subs = self.config_manager.get_config('YOUTUBE_SETTINGS', 'notify_subscribers', 'false').lower() == 'true'
            insert_request = None
            for attempt in range(MAX_GEMINI_RETRIES + 1): # Using same retry count for initial request
                try:
                    insert_request = youtube.videos().insert(part=",".join(body.keys()), body=body, notifySubscribers=notify_subs, media_body=MediaFileUpload(str(video_filepath), chunksize=-1, resumable=True))
                    self.logger.info("YouTube API insert request created."); break
                except HttpError as e:
                    self.logger.warning(f"HttpError creating YouTube insert request (Attempt {attempt+1}): {e.resp.status} - {e.reason if hasattr(e, 'reason') else e.content}")
                    if e.resp.status in [500, 502, 503, 504] and attempt < MAX_GEMINI_RETRIES: time.sleep((2**attempt) + random.uniform(0,1)); continue
                    else: self.logger.error(f"Non-retriable HttpError or max retries for insert request: {e}"); return None
                except Exception as e: self.logger.error(f"Unexpected error creating insert request (Attempt {attempt+1}): {e}"); return None
            if not insert_request: self.logger.error("Failed to create YouTube insert_request."); return None
            response = None; retries = 0
            while response is None and retries <= MAX_GEMINI_RETRIES:
                try:
                    status, response = insert_request.next_chunk()
                    if status: self.logger.info(f"Upload progress: {int(status.progress() * 100)}%")
                    if response: video_id = response.get('id'); self.logger.success(f"✅ Video uploaded! ID: {video_id}"); self._log_uploaded_video(video_filepath, video_id, metadata['title']); return video_id
                except HttpError as e:
                    if e.resp.status in [500, 502, 503, 504] and retries < MAX_GEMINI_RETRIES: self.logger.warning(f"YouTube API server error ({e.resp.status}) during chunk. Retrying ({retries+1})..."); time.sleep((2**retries) + random.uniform(0,1)); retries += 1
                    else: self.logger.error(f"❌ YouTube API Error (chunk): {e.resp.status} - {e.reason if hasattr(e, 'reason') else e.content}"); return None
                except Exception as e: self.logger.error(f"❌ Unexpected error during upload chunk: {e}"); return None
            if not response: self.logger.error("❌ YouTube upload failed (no response)."); return None
        except Exception as e: self.logger.error(f"❌ Unexpected error in YouTube upload setup: {e}"); return None
        return None
    def _log_uploaded_video(self, video_filepath: Path, video_id: str, title: str): # Same
        try:
            log_file_path_str = self.config_manager.get_config('PATHS', 'uploaded_videos_log', fallback=None)
            if not log_file_path_str: self.logger.warning("uploaded_videos_log path not set. Skipping log."); return
            log_file_path = Path(log_file_path_str); log_file_path.parent.mkdir(parents=True, exist_ok=True)
            uploaded_log = configparser.ConfigParser();
            if log_file_path.is_file(): uploaded_log.read(log_file_path, encoding='utf-8')
            section_name = f"Upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            uploaded_log[section_name] = {'timestamp': datetime.now().isoformat(), 'video_id': video_id, 'title': title, 'original_file': str(video_filepath)}
            with open(log_file_path, 'w', encoding='utf-8') as cf: uploaded_log.write(cf)
            self.logger.info(f"Logged uploaded video to: {log_file_path}")
        except Exception as e: self.logger.warning(f"⚠️ Failed to log uploaded video: {e}")

def main(): # Same as previous step
    logger_for_main = None
    try:
        script_dir = Path(__file__).parent.resolve()
        config_manager = ConfigManager(base_dir_override=str(script_dir))
        logger_for_main = Logger()
        browser_manager = None
        ai_provider = config_manager.get_config('AI_SETTINGS', 'provider').lower()
        video_provider = config_manager.get_config('VIDEO_SETTINGS', 'provider').lower()
        needs_browser = 'browser' in ai_provider or 'browser' in video_provider
        if needs_browser:
            logger_for_main.info("Browser interaction required.")
            try:
                browser_manager = BrowserManager(config_manager)
                browser_manager.get_driver()
                logger_for_main.info("Browser initialized successfully.")
            except (BrowserInitializationError, RuntimeError) as e:
                 logger_for_main.error(f"CRITICAL: Browser initialization failed: {e}"); sys.exit(1)
        else: logger_for_main.info("No browser interaction required.")
        logger_for_main.info("--- Step 1: Script Generation ---")
        script_generator = ScriptGenerator(config_manager, browser_manager)
        script_content = script_generator.generate_script()
        if not script_content: logger_for_main.error("Script generation failed. Pipeline cannot proceed."); return
        script_filepath = script_generator.save_script(script_content)
        if not script_filepath: logger_for_main.error("Failed to save generated script. Pipeline cannot proceed."); return
        logger_for_main.success("Step 1: Script Generation Completed.")
        logger_for_main.info("--- Step 2: Parse Script Metadata ---")
        metadata = ScriptGenerator.parse_script_file(script_filepath)
        if not metadata: logger_for_main.error(f"Failed to parse metadata from {script_filepath}. Pipeline cannot proceed."); return
        script_text_for_video = metadata.get('script')
        if not script_text_for_video: logger_for_main.error("Parsed metadata missing 'script' content. Pipeline cannot proceed."); return
        logger_for_main.success("Step 2: Parse Script Metadata Completed.")
        logger_for_main.info("--- Step 3: Video Creation ---")
        if 'browser' in video_provider and not browser_manager :
            logger_for_main.error("Video creation needs browser, but not initialized/failed. Pipeline cannot proceed."); return
        video_creator = VideoCreator(config_manager, browser_manager) # type: ignore
        video_filepath = video_creator.create_video(script_text_for_video)
        if not video_filepath: logger_for_main.error("Video creation failed. Pipeline cannot proceed."); return
        logger_for_main.success(f"Step 3: Video Creation Completed. Video: {video_filepath}")
        logger_for_main.info("--- Step 4: Upload to YouTube ---")
        uploader = YouTubeUploader(config_manager)
        video_id = uploader.upload_video(video_filepath, metadata)
        if not video_id: logger_for_main.error("YouTube upload failed.")
        else: logger_for_main.success(f"Step 4: YouTube Upload Completed. URL: https://www.youtube.com/watch?v={video_id}")
        logger_for_main.success("🎉 Smart Automation Pipeline finished! 🎉")
    except ConfigurationError as e:
        msg = f"CRITICAL CONFIGURATION ERROR: {e}"
        if logger_for_main and logger_for_main.logger: logger_for_main.critical(msg)
        else: print(msg)
        sys.exit(1)
    except Exception as e:
        msg = f"UNEXPECTED CRITICAL ERROR in main pipeline: {e}"
        if logger_for_main and logger_for_main.logger: logger_for_main.critical(msg)
        else: print(msg)
        sys.exit(1)
    finally:
        if browser_manager: browser_manager.close_driver()
        if logger_for_main and logger_for_main.logger : logger_for_main.info("Automation tool finished.")
        elif logger_for_main: print("Automation tool finished (logger might have had issues).")
        else: print("Automation tool finished (logger was not initialized).")

if __name__ == "__main__":
    main()

[end of automation_tool.py]
