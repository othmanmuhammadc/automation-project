#!/usr/bin/env python3
"""
Smart Automation Tool - Complete YouTube Content Creation Pipeline
Author: AI Assistant
Version: 1.0
Description: Automated text generation, video creation, and YouTube upload tool
"""

import os
import sys
import json
import time
import random
import logging
import argparse
import configparser
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any # Ensure Any is imported
import requests
import threading # Ensure threading is imported
from dataclasses import dataclass

# Required imports with error handling
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
    print("❌ Error: Selenium not installed. Run: pip install selenium")
    sys.exit(1)

try:
    import openai
except ImportError:
    print("⚠️ Warning: OpenAI not installed. AI text generation will be limited.")
    openai = None

try:
    import google.generativeai as genai
except ImportError:
    print("⚠️ Warning: Google Generative AI SDK not installed. Gemini functionality will be unavailable. Run: pip install google-generativeai")
    genai = None


@dataclass
class WorkflowConfig:
    """Configuration for workflow execution"""
    mode: str
    ai_provider: str
    video_style: str
    upload_schedule: str
    max_retries: int
    headless: bool


class Logger:
    """Basic file and console logger."""
    _instance = None

    def __new__(cls, log_file_name="automation_debug.log", log_level=logging.DEBUG):
        # Test comment to check diff tool functionality
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance.logger = logging.getLogger(__name__) # Use __name__ for unique logger name
            cls._instance.logger.setLevel(log_level)
            
            # Prevent duplicate handlers if Logger is instantiated multiple times
            if not cls._instance.logger.handlers:
                # Determine log directory relative to this file's location (AUTOMATION/logs)
                # Path(__file__) is the path to automation_tool.py
                # .resolve().parent gives the AUTOMATION directory
                # then append 'logs'
                log_dir = Path(__file__).resolve().parent / "logs"
                log_dir.mkdir(parents=True, exist_ok=True)
                
                file_handler = logging.FileHandler(log_dir / log_file_name, encoding='utf-8')
                file_handler.setLevel(log_level)
                
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setLevel(log_level)
                
                formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')
                file_handler.setFormatter(formatter)
                console_handler.setFormatter(formatter)
                
                cls._instance.logger.addHandler(file_handler)
                cls._instance.logger.addHandler(console_handler)
        return cls._instance

    def get_logger(self): # This method provides access to the configured logger instance
        return self.logger


class ConfigManager:
    """Manages configuration files with staged default creation."""

    def __init__(self):
        self.main_logger = Logger().get_logger() # Use the new Logger
        # self.config_dir is the directory where customisation.ini should reside.
        # Path(__file__).resolve().parent points to AUTOMATION directory
        self.config_dir = Path(__file__).resolve().parent 
        self.customisation_file = self.config_dir / "customisation.ini"
        
        self.config = configparser.ConfigParser()
        
        # Initialize paths to None; they will be set in _create_default_configs
        self.data_dir: Optional[Path] = None
        self.selectors_file: Optional[Path] = None
        self.api_file: Optional[Path] = None
        self.token_file: Optional[Path] = None
        self.plan_state_file: Optional[Path] = None
        self.uploaded_videos_file: Optional[Path] = None

        self._create_default_configs()

    def _get_default_customisation_ini_content(self) -> str:
        """Returns the full default INI content for customisation.ini."""
        return ("[PATHS]\n"
                "data_base_path = Data/\n"
                "video_output_path = videos/\n"
                "script_output_path = Scripts/\n"
                "log_output_path = logs/\n\n"
                "[AI_SETTINGS]\n"
                "provider = gemini\n"
                "openai_api_key = your_openai_api_key_here\n"
                "grok_api_key = your_grok_api_key_here\n"
                "gemini_api_key = your_gemini_api_key_here\n"
                "default_prompt = Generate an engaging YouTube video script about modern AI advancements\n"
                "max_words = 300\n"
                "language = English\n\n"
                "[VIDEO_METADATA]\n"
                "title = My Awesome AI Video\n"
                "description = This video explores the fascinating world of AI. Created using automation!\n"
                "tags = AI, Artificial Intelligence, Tech, Automation, YouTube\n\n"
                "[VIDEO_SETTINGS]\n"
                "style = anime\n"
                "resolution = 1080p\n"
                "voice_type = female\n"
                "duration = 60\n"
                "background_music = true\n"
                "captions = true\n\n"
                "[YOUTUBE_SETTINGS]\n"
                "privacy = public\n"
                "schedule_upload = false\n"
                "upload_time = 18:00\n\n"
                "[BROWSER_SETTINGS]\n"
                "headless_mode = false\n"
                "primary_browser = chrome\n"
                "secondary_browser = edge\n"
                "wait_timeout = 30\n"
                "retry_attempts = 3\n"
                "page_load_timeout = 60\n"
                "browser_user_data_path = /path/to/your/browser/profile\n\n"
                "[PLATFORM_URLS]\n"
                "chatgpt_url = https://chat.openai.com\n"
                "grok_url = https://grok.com/\n"
                "capcut_url = https://www.capcut.com/ai-creator/start\n\n"
                "[WORKFLOW_SETTINGS]\n"
                "execution_mode = full_auto\n"
                "auto_retry = true\n"
                "save_progress = true\n" # For plan_state.json
                "notification_enabled = true\n\n"
                "[ADVANCED_SETTINGS]\n"
                "action_delay = 2\n"
                "max_processes = 1\n"
                "debug_mode = false\n"
                "screenshot_on_error = true\n")

    def _get_default_selectors_content(self) -> str:
        """Returns full content for selectors.json."""
        selectors = {
            "capcut": {"login_button": ["//button[contains(text(), 'Log in')]", "//a[contains(text(), 'Sign in')]", "#login-button", ".login-btn"],"email_input": ["//input[@type='email']", "//input[@name='email']", "#email", ".email-input"],"password_input": ["//input[@type='password']", "//input[@name='password']", "#password", ".password-input"],"create_video_button": ["//button[contains(text(), 'Create')]", "//div[contains(text(), 'New Project')]", ".create-button", "#new-project"],"upload_media": ["//button[contains(text(), 'Upload')]", "//input[@type='file']", ".upload-btn", "#media-upload"],"text_tool": ["//div[contains(text(), 'Text')]", "//button[@title='Text']", ".text-tool", "#text-button"],"voice_settings": ["//div[contains(text(), 'Voice')]", "//button[contains(text(), 'TTS')]", ".voice-option", "#voice-settings"],"export_button": ["//button[contains(text(), 'Export')]", "//div[contains(text(), 'Download')]", ".export-btn", "#export-video"]},
            "youtube": {"upload_button": ["//button[@aria-label='Create']", "//ytd-topbar-menu-button-renderer[@id='upload-icon']//button", "#upload-icon", ".upload-button"],"select_file": ["//input[@type='file']", "//div[contains(text(), 'SELECT FILES')]", ".file-selector", "#file-upload"],"title_input": ["//div[@id='textbox']", "//textarea[@aria-label='Title']", "#title-input", ".title-field"],"description_input": ["//div[@aria-label='Description']", "//textarea[@aria-label='Description']", "#description-input", ".description-field"],"next_button": ["//button[contains(text(), 'NEXT')]", "//ytd-button-renderer[@id='next-button']//button", "#next-button", ".next-btn"],"publish_button": ["//button[contains(text(), 'PUBLISH')]", "//ytd-button-renderer[@id='done-button']//button", "#publish-button", ".publish-btn"]}
        }
        return json.dumps(selectors, indent=2)

    def _get_default_api_content(self) -> str:
        """Returns content for api.json."""
        return json.dumps({"youtube_api_key": "YOUR_YOUTUBE_API_KEY", "gemini_api_key": "YOUR_GEMINI_API_KEY"}, indent=2)

    def _get_default_uploaded_videos_content(self) -> str:
        """Returns minimal content for uploaded_videos.ini."""
        return "[UPLOADED_VIDEOS]\n"

    def _ensure_default_data_file_exists(self, file_path: Optional[Path], content_func) -> None:
        if file_path is None:
            self.main_logger.error("File path is None in _ensure_default_data_file_exists. Cannot create file.")
            return
        if not file_path.exists():
            try:
                file_path.parent.mkdir(parents=True, exist_ok=True)
                content = content_func()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.main_logger.info(f"Created default data file: '{file_path}'")
            except IOError as e:
                self.main_logger.error(f"IOError writing default data file '{file_path}': {e}")
            except Exception as e:
                self.main_logger.error(f"Unexpected error creating default file '{file_path}': {e}")
    
    def _create_default_configs(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        customisation_ini_was_missing = not self.customisation_file.is_file()
        if customisation_ini_was_missing:
            try:
                content = self._get_default_customisation_ini_content()
                with open(self.customisation_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.main_logger.info(f"Created default customisation.ini at '{self.customisation_file}'")
            except IOError as e:
                self.main_logger.error(f"Failed to write default customisation.ini '{self.customisation_file}': {e}")

        if self.customisation_file.is_file():
            try:
                self.config.read(self.customisation_file, encoding='utf-8')
                if not self.config.sections() and self.customisation_file.stat().st_size > 0:
                    self.main_logger.warning(f"'{self.customisation_file}' is non-empty but unparseable. Defaults may be used.")
            except configparser.Error as e:
                self.main_logger.error(f"Error parsing '{self.customisation_file}': {e}. Defaults may be used.")
        else:
            self.main_logger.warning(f"'{self.customisation_file}' not found. Defaults will be used.")
            if not self.config.has_section('PATHS'): self.config.add_section('PATHS')
            if not self.config.has_option('PATHS', 'data_base_path'): self.config.set('PATHS', 'data_base_path', 'Data/')

        data_base_path_str = self.config.get('PATHS', 'data_base_path', fallback='Data/')
        self.data_dir = self.config_dir / data_base_path_str
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
        except IOError as e:
            self.main_logger.error(f"Failed to create data directory '{self.data_dir}': {e}")
            return 

        self.selectors_file = self.data_dir / "selectors.json"
        self.api_file = self.data_dir / "api.json"
        self.token_file = self.data_dir / "token.json"
        self.plan_state_file = self.data_dir / "plan_state.json"
        self.uploaded_videos_file = self.data_dir / "uploaded_videos.ini"

        self._ensure_default_data_file_exists(self.selectors_file, self._get_default_selectors_content)
        self._ensure_default_data_file_exists(self.api_file, self._get_default_api_content)
        self._ensure_default_data_file_exists(self.token_file, lambda: json.dumps({}))
        self._ensure_default_data_file_exists(self.plan_state_file, lambda: json.dumps({}))
        self._ensure_default_data_file_exists(self.uploaded_videos_file, self._get_default_uploaded_videos_content)

    def load_config(self) -> configparser.ConfigParser:
        return self.config

    def load_selectors(self) -> Dict:
        if self.selectors_file is None or not self.selectors_file.is_file():
            self.main_logger.warning(f"Selectors file path not set or file does not exist: '{self.selectors_file}'. Returning empty dict.")
            return {}
        try:
            with open(self.selectors_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            self.main_logger.error(f"Error decoding JSON from '{self.selectors_file}': {e}. Returning empty dict.")
            return {}
        except Exception as e:
            self.main_logger.error(f"Unexpected error loading '{self.selectors_file}': {e}. Returning empty dict.")
            return {}

    def log_uploaded_video(self, title: str, video_path: str, upload_time: str):
        if self.uploaded_videos_file is None:
            self.main_logger.error("Uploaded videos file path is not set. Cannot log video.")
            return
        if not self.uploaded_videos_file.parent.exists():
            self.main_logger.error(f"Parent directory for uploaded videos file does not exist: '{self.uploaded_videos_file.parent}'. Cannot log video.")
            return

        uploaded_videos_config = configparser.ConfigParser()
        try:
            if self.uploaded_videos_file.is_file() and self.uploaded_videos_file.stat().st_size > 0:
                uploaded_videos_config.read(self.uploaded_videos_file, encoding='utf-8')
        except configparser.Error as e:
            self.main_logger.error(f"Error reading '{self.uploaded_videos_file}' for logging: {e}.")
        
        if not uploaded_videos_config.has_section('UPLOADED_VIDEOS'):
            uploaded_videos_config.add_section('UPLOADED_VIDEOS')
            
        video_id = f"video_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        uploaded_videos_config.set('UPLOADED_VIDEOS', video_id, f"Title: {title} | Path: {str(video_path)} | Time: {upload_time}")

        try:
            with open(self.uploaded_videos_file, 'w', encoding='utf-8') as f:
                uploaded_videos_config.write(f)
        except IOError as e:
            self.main_logger.error(f"Failed to write log to '{self.uploaded_videos_file}': {e}")

    def get_platform_url(self, service_name: str) -> Optional[str]:
        return self.config.get('PLATFORM_URLS', f'{service_name.lower()}_url', fallback=None)

    def get_path(self, path_key: str) -> Optional[str]:
        return self.config.get('PATHS', path_key, fallback=None)
        
    def get_absolute_path(self, path_key: str) -> Optional[Path]:
        relative_path_str = self.config.get('PATHS', path_key, fallback=None)
        if relative_path_str:
            return self.config_dir / relative_path_str
        return None

    def get_video_metadata(self, metadata_key: str) -> Optional[str]:
        return self.config.get('VIDEO_METADATA', metadata_key, fallback=None)

    def get_browser_setting(self, setting_key: str, fallback: Any = None) -> Optional[str]:
        return self.config.get('BROWSER_SETTINGS', setting_key, fallback=fallback)


class ScriptGenerator:
    """AI-powered text generation for video scripts"""

    def __init__(self, config: configparser.ConfigParser, selectors: Dict, browser_manager: 'BrowserManager'):
        self.config = config
        self.logger = Logger().get_logger()
        self.ai_provider = config.get('AI_SETTINGS', 'provider', fallback='openai').lower()
        self.selectors = selectors # Store selectors for browser interaction
        self.browser_manager = browser_manager # Store browser_manager for browser interaction
        self.element_finder: Optional[ElementFinder] = None # Will be initialized when driver is active

        if self.ai_provider == 'openai' and openai: # This 'openai' refers to the library
            openai_api_key = self.config.get('AI_SETTINGS', 'openai_api_key', fallback='')
            if not openai_api_key:
                self.logger.warning("OpenAI provider selected, but API key is missing for direct API calls.")
            openai.api_key = openai_api_key
        # No specific error for library missing here, as 'openai' provider will now use browser

    def generate_script(self, topic: str, max_words: int = None) -> str:
        """
        Generate a video script based on the topic (which is the prompt).
        Returns the generated script text as a string.
        """
        if not max_words:
            try:
                max_words = self.config.getint('AI_SETTINGS', 'max_words', fallback=300)
            except ValueError:
                self.logger.warning("Invalid max_words value in config, using default 300.")
                max_words = 300
        
        self.logger.info(f"🤖 Generating script with {self.ai_provider} for prompt (topic): '{topic[:100]}...' (max_words: {max_words})")

        script_text = ""
        try:
            if self.ai_provider == 'openai': # Now means ChatGPT via browser
                script_text = self._generate_chatgpt_browser_script(topic, max_words)
            elif self.ai_provider == 'grok':
                script_text = self._generate_grok_script(topic, max_words)
            elif self.ai_provider == 'gemini': # Assuming Gemini might still use an API or future browser method
                script_text = self._generate_gemini_script(topic, max_words)
            else: # Fallback for any other configured provider
                self.logger.warning(f"Unknown or unsupported AI provider '{self.ai_provider}'. Using fallback script generator.")
                script_text = self._generate_fallback_script(topic, max_words)
        except NotImplementedError as nie:
            self.logger.error(f"Script generation error for {self.ai_provider}: {nie}")
            script_text = self._generate_fallback_script(topic, max_words)
        except Exception as e:
            self.logger.error(f"Script generation failed for provider {self.ai_provider}: {str(e)}", exc_info=True)
            self.logger.info("Using fallback script generation due to error.")
            script_text = self._generate_fallback_script(topic, max_words)
        
        if not script_text.strip():
            self.logger.warning("Generated script is empty or only whitespace. Using fallback.")
            script_text = self._generate_fallback_script(topic, max_words)
            
        return script_text

    def _generate_chatgpt_browser_script(self, prompt_text: str, max_words: int) -> str:
        """Generates script using ChatGPT via browser automation."""
        chatgpt_url = self.config.get('PLATFORM_URLS', 'chatgpt_url', fallback='https://chat.openai.com')
        self.logger.info(f"Attempting ChatGPT script generation via browser at {chatgpt_url} using prompt: '{prompt_text[:100]}...'")

        driver = None # Ensure driver is defined for the finally block
        script_text = ""

        try:
            driver = self.browser_manager.get_driver()
            if not driver:
                self.logger.error("Failed to get browser driver for ChatGPT.")
                return ""
            
            self.element_finder = ElementFinder(driver, self.selectors) # Initialize ElementFinder with active driver

            driver.get(chatgpt_url)
            time.sleep(5) # Allow initial page load, more robust waits by ElementFinder

            # --- Handle potential login/welcome popups (highly site-specific) ---
            # Example: If there's a known welcome popup with a 'next' or 'close' button
            # self.element_finder.wait_and_click('chatgpt_welcome_next_button', 'CHATGPT') # Add selector if needed
            # self.element_finder.wait_and_click('chatgpt_welcome_done_button', 'CHATGPT') # Add selector if needed
            # self.logger.info("Attempted to handle initial ChatGPT popups if present.")
            # time.sleep(2) # Give time for popups to clear

            input_field = self.element_finder.find_element_smart('input_field', 'CHATGPT')
            if not input_field:
                self.logger.error("ChatGPT input field not found.")
                return ""
            
            # Constructing a more detailed prompt for ChatGPT
            enhanced_prompt = (
                f"{prompt_text}\n\n"
                f"Please generate a script of approximately {max_words} words. "
                "The script should be engaging and well-structured, suitable for a YouTube video. "
                "Include a hook, main content, and a call to action."
            )
            input_field.send_keys(enhanced_prompt)
            time.sleep(1) # Brief pause after typing

            send_button = self.element_finder.find_element_smart('send_button', 'CHATGPT')
            if not send_button:
                self.logger.error("ChatGPT send button not found.")
                return ""
            send_button.click()
            self.logger.info("Prompt sent to ChatGPT.")

            # Wait for response generation
            # This involves checking if a loading indicator is gone or a response area is populated.
            # Selector for 'response_loading' would be for an element that indicates ChatGPT is typing.
            # Selector for 'response' should target the container of the last AI message.
            
            # Wait for the "stop generating" button to disappear (or similar indicator)
            # Max wait time for response generation
            max_wait_time = self.config.getint('BROWSER_SETTINGS', 'page_load_timeout', fallback=120) # Use page_load_timeout as a long wait
            wait_interval = 3 
            elapsed_time = 0
            
            self.logger.info("Waiting for ChatGPT response generation to complete...")
            while elapsed_time < max_wait_time:
                # Check if a "stop generating" button is present (selector: 'response_generating_indicator')
                # Or check if a "regenerate response" button is present (selector: 'regenerate_button')
                # These selectors need to be defined in selectors.json for 'CHATGPT' section
                still_generating = self.element_finder.find_element_smart('response_generating_indicator', 'CHATGPT') # This is an example selector
                if not still_generating: # If indicator is gone, assume generation is complete or stopped
                    self.logger.info("Response generation indicator no longer visible.")
                    break 
                self.logger.info(f"Still waiting for response... ({elapsed_time}/{max_wait_time}s)")
                time.sleep(wait_interval)
                elapsed_time += wait_interval
            
            if elapsed_time >= max_wait_time:
                self.logger.warning("Timeout reached while waiting for ChatGPT response generation.")

            time.sleep(2) # Give a final brief moment for content to settle

            # Attempt to find the last response element
            # This assumes 'response' selector targets all response blocks and ElementFinder gets the last one
            # Or, more reliably, if 'response' targets a specific container of the latest message.
            # For now, we use the existing find_element_smart which gets the first match.
            # This might need refinement based on actual ChatGPT page structure and selectors.json.
            
            # To get the last response, one might need to use find_elements_smart (if it existed)
            # and then take the last element. Example:
            # response_elements = self.element_finder.find_elements_smart('response_message_text', 'CHATGPT')
            # if response_elements:
            #    script_text = response_elements[-1].text.strip()
            # else:
            #    self.logger.error("ChatGPT response element(s) not found.")
            #    script_text = ""
            
            # Using current find_element_smart (gets first match based on selector order)
            response_element = self.element_finder.find_element_smart('response', 'CHATGPT')
            if response_element:
                script_text = response_element.text.strip()
                self.logger.info(f"ChatGPT response extracted (first 200 chars): {script_text[:200]}...")
            else:
                self.logger.error("ChatGPT response element not found after waiting.")
                script_text = "" # Fallback

        except TimeoutException:
            self.logger.error("Timeout waiting for an element in ChatGPT browser automation.")
        except NoSuchElementException:
            self.logger.error("Element not found during ChatGPT browser automation.")
        except WebDriverException as e:
            self.logger.error(f"WebDriverException during ChatGPT interaction: {e}")
        except Exception as e:
            self.logger.error(f"An unexpected error occurred during ChatGPT browser script generation: {e}", exc_info=True)
        finally:
            if driver: # Ensure driver was initialized before trying to close
                self.browser_manager.close_driver()
            self.element_finder = None # Clear element_finder as driver is closed

        return script_text

    def _generate_openai_script(self, topic_prompt: str, max_words: int) -> str:
        """Generate script using OpenAI GPT (direct API). Returns the script text string."""
        if not openai:
             self.logger.error("OpenAI SDK not available for direct API call.")
             return "" 
        if not openai.api_key:
            self.logger.error("OpenAI API key not set for direct API call.")
            return ""
        
        prompt_template = f"{topic_prompt}\n\nGenerate a script approximately {max_words} words long."
        self.logger.info(f"Sending prompt to OpenAI API (first 100 chars): {prompt_template[:200]}...")
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt_template}],
                max_tokens=int(max_words * 1.5),
                temperature=0.7
            )
            script_text = response.choices[0].message.content.strip()
            self.logger.info("Script successfully generated by OpenAI API.")
            return script_text
        except Exception as e:
            self.logger.error(f"OpenAI API call failed: {e}", exc_info=True)
            return ""

    def _generate_grok_script(self, prompt_text: str, max_words: int) -> str:
        """Generates script using Grok via browser automation."""
        grok_url = self.config.get('PLATFORM_URLS', 'grok_url', fallback='https://x.ai/grok') # Standardized Grok URL
        self.logger.info(f"Attempting Grok script generation via browser at {grok_url} using prompt: '{prompt_text[:100]}...'")

        driver = None
        script_text = ""

        try:
            driver = self.browser_manager.get_driver()
            if not driver:
                self.logger.error("Failed to get browser driver for Grok.")
                return ""
            
            self.element_finder = ElementFinder(driver, self.selectors)

            driver.get(grok_url)
            # Increased initial wait for Grok, as it might have more complex loading/auth checks
            self.logger.info(f"Navigated to Grok URL. Waiting for page elements to become available (up to {self.browser_manager.wait_timeout}s)...")
            time.sleep(5) # Initial sleep, more robust waits should be handled by ElementFinder

            # NOTE: Grok's UI is not publicly known/stable for automation like ChatGPT.
            # The selectors 'input_field', 'send_button', 'response_loading', 'response'
            # under a "GROK" section in selectors.json would be highly speculative.
            # This implementation assumes such selectors *could* exist.
            
            # Example: Handle potential login/welcome popups (highly site-specific)
            # self.logger.info("Attempting to handle initial Grok popups if present.")
            # if self.element_finder.find_element_smart('accept_cookies_button', 'GROK'): # Example selector
            #     self.element_finder.wait_and_click('accept_cookies_button', 'GROK')
            # time.sleep(2)


            input_field = self.element_finder.find_element_smart('input_field', 'GROK')
            if not input_field:
                self.logger.error("Grok input field not found. Ensure selectors are defined for 'GROK' section in selectors.json.")
                return ""
            
            enhanced_prompt = (
                f"{prompt_text}\n\n"
                f"Please generate a script of approximately {max_words} words. "
                "The script should be engaging and well-structured, suitable for a YouTube video. "
                "Include a hook, main content, and a call to action."
            )
            input_field.send_keys(enhanced_prompt)
            time.sleep(1)

            send_button = self.element_finder.find_element_smart('send_button', 'GROK')
            if not send_button:
                self.logger.error("Grok send button not found.")
                return ""
            send_button.click()
            self.logger.info("Prompt sent to Grok.")

            max_wait_time = self.config.getint('BROWSER_SETTINGS', 'page_load_timeout', fallback=180) # Longer timeout for AI generation
            wait_interval = 5 # Check more frequently
            elapsed_time = 0
            
            self.logger.info("Waiting for Grok response generation to complete...")
            while elapsed_time < max_wait_time:
                # Assuming 'response_loading' selector points to an element visible ONLY when Grok is typing/processing
                loading_indicator = self.element_finder.find_element_smart('response_loading', 'GROK')
                if not loading_indicator: 
                    self.logger.info("Grok response loading indicator no longer visible or not found.")
                    break 
                self.logger.info(f"Grok is still generating response... ({elapsed_time}/{max_wait_time}s)")
                time.sleep(wait_interval)
                elapsed_time += wait_interval
            
            if elapsed_time >= max_wait_time:
                self.logger.warning("Timeout reached while waiting for Grok response generation.")

            time.sleep(3) # Allow content to fully render after loading indicator disappears

            response_element = self.element_finder.find_element_smart('response', 'GROK')
            if response_element:
                script_text = response_element.text.strip()
                self.logger.info(f"Grok response extracted (first 200 chars): {script_text[:200]}...")
            else:
                self.logger.error("Grok response element not found after waiting. Ensure 'response' selector is correct for GROK section.")
                script_text = ""

        except TimeoutException:
            self.logger.error("Timeout waiting for an element in Grok browser automation.")
        except NoSuchElementException:
            self.logger.error("Element not found during Grok browser automation. Check selectors for 'GROK'.")
        except WebDriverException as e:
            self.logger.error(f"WebDriverException during Grok interaction: {e}")
        except Exception as e:
            self.logger.error(f"An unexpected error occurred during Grok browser script generation: {e}", exc_info=True)
        finally:
            if driver: 
                self.browser_manager.close_driver()
            self.element_finder = None 

        if not script_text.strip():
             self.logger.warning("Grok script generation resulted in empty text. Check selectors and Grok UI if this is unexpected.")
             # Optionally, return a specific placeholder if Grok fails, rather than relying on the main generate_script's fallback
             # return self._generate_fallback_script(prompt_text, max_words) # Or just return empty string

        return script_text

    def _generate_gemini_script(self, prompt_text: str, max_words: int) -> str:
        """Generate script using Gemini API. Returns the script text string."""
        if not genai:
            self.logger.error("Google Generative AI SDK (genai) not available. Cannot use Gemini.")
            return ""

        gemini_api_key = self.config.get('AI_SETTINGS', 'gemini_api_key', fallback=None)
        if not gemini_api_key or not gemini_api_key.strip():
            self.logger.error("Gemini API key is missing or empty in customisation.ini. Cannot generate script.")
            return ""

        try:
            genai.configure(api_key=gemini_api_key)
        except Exception as e:
            self.logger.error(f"Failed to configure Gemini API key: {e}", exc_info=True)
            if "API key not valid" in str(e):
                 return "Error: Gemini API key not valid. Please check your configuration."
            return "Error: Failed to configure Gemini API."

        model_name = self.config.get('AI_SETTINGS', 'gemini_model_name', fallback='gemini-pro')
        self.logger.info(f"Initializing Gemini model: {model_name}")
        model = genai.GenerativeModel(model_name)

        # For controlling length, it's better to include it in the prompt.
        # max_output_tokens is hard to map directly from max_words.
        # An approximation: 1 word ~ 1.33 tokens.
        # For now, we'll rely on the prompt to guide length.
        # generation_config = genai.types.GenerationConfig(
        #     # max_output_tokens=int(max_words * 1.5), # Example: Allow more tokens
        #     # temperature=0.7 # Example temperature
        # )
        # Using default generation_config for now as specific token control can be complex.
        generation_config = genai.types.GenerationConfig()


        self.logger.info(f"Sending prompt to Gemini (first 100 chars): {prompt_text[:100]}...")
        
        try:
            # The prompt_text should ideally already contain instructions about length if precise control is needed.
            # Example: f"{prompt_text}\n\nPlease ensure the script is approximately {max_words} words long."
            response = model.generate_content(prompt_text, generation_config=generation_config)
            
            if response.candidates:
                # Check for content parts
                if response.candidates[0].content and response.candidates[0].content.parts:
                    generated_text = "".join(part.text for part in response.candidates[0].content.parts)
                    
                    # Log finish reason
                    finish_reason_value = response.candidates[0].finish_reason.value
                    finish_reason_name = response.candidates[0].finish_reason.name
                    if finish_reason_name != "STOP": # 1 is STOP
                        self.logger.warning(f"Gemini generation finished due to reason: {finish_reason_name} (value: {finish_reason_value}). This might indicate truncated output or other issues.")
                    
                    # Check for safety ratings / block reason from prompt feedback
                    if response.prompt_feedback and response.prompt_feedback.block_reason:
                        block_reason_msg = response.prompt_feedback.block_reason_message or response.prompt_feedback.block_reason.name
                        self.logger.error(f"Gemini prompt was blocked. Reason: {block_reason_msg}")
                        return f"Error: Gemini prompt blocked. Reason: {block_reason_msg}"
                    
                    # Check safety ratings on candidates (more granular)
                    for candidate in response.candidates:
                        for rating in candidate.safety_ratings:
                            if rating.probability.value > 3 : # HARASSMENT_PROBABILITY_MEDIUM or higher (Scale: 0-5)
                                self.logger.warning(f"Gemini content may have safety concerns: Category '{rating.category.name}', Probability '{rating.probability.name}'.")
                                # Depending on policy, might return error or filter content here.

                    self.logger.info("Script successfully generated by Gemini.")
                    return generated_text.strip()
                else: # No content parts in the first candidate
                    self.logger.warning("Gemini response candidate had no content parts.")
                    if response.prompt_feedback and response.prompt_feedback.block_reason:
                        block_reason_msg = response.prompt_feedback.block_reason_message or response.prompt_feedback.block_reason.name
                        self.logger.error(f"Gemini prompt blocked. Reason: {block_reason_msg}")
                        return f"Error: Gemini prompt blocked. Reason: {block_reason_msg}"
                    return "Error: Gemini response was empty or malformed (no content parts in candidate)."
            else: # No candidates in response
                if response.prompt_feedback and response.prompt_feedback.block_reason:
                     block_reason_msg = response.prompt_feedback.block_reason_message or response.prompt_feedback.block_reason.name
                     self.logger.error(f"Gemini prompt blocked. Reason: {block_reason_msg}")
                     return f"Error: Gemini prompt blocked. Reason: {block_reason_msg}"
                self.logger.error("Gemini API call failed: No candidates in response and no explicit prompt block.")
                return "Error: Gemini API call failed (no candidates returned)."

        except Exception as e:
            error_message = str(e)
            self.logger.error(f"Error during Gemini API call: {error_message}", exc_info=True)
            if "API key not valid" in error_message or "API_KEY_INVALID" in error_message:
                 return "Error: Gemini API key not valid. Please check your configuration."
            # Check for other common errors if the SDK provides specific exception types
            # For example, if ResourceExhausted or a specific permission error.
            return f"Error: Exception during Gemini API call - {error_message}"

    def _generate_fallback_script(self, topic_prompt: str, max_words: int) -> str:
        """Fallback script generation. Returns the script text string."""
        self.logger.info(f"Using fallback script generation for prompt: {topic_prompt[:50]}...")
        templates = [
            f"Welcome to our amazing video about '{topic_prompt}'! Today we'll explore the fascinating world of this topic and discover incredible insights that will blow your mind. We will cover everything you need to know. Don't forget to like and subscribe for more amazing content!",
            f"Hey everyone! Ready to dive deep into '{topic_prompt}'? This video will transform your understanding with expert insights and practical tips. Whether you're a beginner or expert, you'll find valuable information here. Let's get started on this incredible journey!",
            f"What if I told you that '{topic_prompt}' could change everything? In today's video, we're uncovering the secrets that most people don't know. Get ready for mind-blowing facts and actionable advice that you can use right away. Stay tuned!"
        ]
        script = random.choice(templates)
        words = script.split()
        if len(words) > max_words:
            script = " ".join(words[:max_words])
        return script


class BrowserManager:
    """Smart browser management with automatic switching"""

    def __init__(self, config: configparser.ConfigParser):
        self.config = config
        self.logger = Logger().get_logger() # Use the new Logger
        self.headless = config.getboolean('BROWSER_SETTINGS', 'headless_mode', fallback=False)
        self.primary_browser = config.get('BROWSER_SETTINGS', 'primary_browser', fallback='chrome')
        self.secondary_browser = config.get('BROWSER_SETTINGS', 'secondary_browser', fallback='edge')
        self.wait_timeout = config.getint('BROWSER_SETTINGS', 'wait_timeout', fallback=30)
        self.browser_user_data_path = self.config.get('BROWSER_SETTINGS', 'browser_user_data_path', fallback=None)
        self.current_driver = None
        self.current_browser = None

    def get_driver(self, browser_type: str = None):
        """Get browser driver with automatic fallback"""
        if not browser_type:
            browser_type = self.primary_browser.lower()

        try:
            if browser_type == 'chrome':
                return self._get_chrome_driver()
            elif browser_type == 'edge':
                return self._get_edge_driver()
            else:
                raise ValueError(f"Unsupported browser: {browser_type}")
        except Exception as e:
            self.logger.warning(f"Failed to initialize {browser_type}: {str(e)}")
            if browser_type != self.secondary_browser.lower(): # Avoid infinite loop if secondary also fails
                self.logger.info(f"Trying alternative browser: {self.secondary_browser}")
                return self.get_driver(self.secondary_browser.lower())
            self.logger.error("All configured browsers failed to initialize.")
            raise # Re-raise the last exception if all fail

    def _get_chrome_driver(self):
        """Initialize Chrome driver"""
        options = ChromeOptions()
        if self.headless: options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        if self.browser_user_data_path and self.browser_user_data_path.strip():
            options.add_argument(f"user-data-dir={self.browser_user_data_path.strip()}")
            self.logger.info(f"Using Chrome user data directory: {self.browser_user_data_path.strip()}")

        driver = webdriver.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.current_driver = driver
        self.current_browser = 'chrome'
        self.logger.info("Chrome driver initialized.")
        return driver

    def _get_edge_driver(self):
        """Initialize Edge driver"""
        options = EdgeOptions()
        if self.headless: options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0')

        if self.browser_user_data_path and self.browser_user_data_path.strip():
            options.add_argument(f"user-data-dir={self.browser_user_data_path.strip()}")
            self.logger.info(f"Using Edge user data directory: {self.browser_user_data_path.strip()}")

        driver = webdriver.Edge(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.current_driver = driver
        self.current_browser = 'edge'
        self.logger.info("Edge driver initialized.")
        return driver

    def close_driver(self):
        """Close current driver"""
        if self.current_driver:
            try:
                self.current_driver.quit()
                self.logger.info(f"{self.current_browser.capitalize()} driver closed.")
            except Exception as e:
                self.logger.error(f"Error closing {self.current_browser} driver: {e}")
            finally:
                self.current_driver = None
                self.current_browser = None


class ElementFinder:
    """Smart element finder with multiple selector strategies"""

    def __init__(self, driver, selectors: Dict, wait_timeout: int = 30):
        self.driver = driver
        self.selectors = selectors
        self.wait = WebDriverWait(driver, wait_timeout)
        self.logger = Logger().get_logger() # Use the new Logger

    def find_element_smart(self, element_key: str, section: str = None) -> Optional[Any]:
        """Find element using multiple selector strategies"""
        selector_options = []
        if section and section in self.selectors:
            selector_options = self.selectors[section].get(element_key, [])
        elif not section: # Search in all sections if no specific section provided
            for sect_values in self.selectors.values():
                if isinstance(sect_values, dict) and element_key in sect_values:
                    selector_options.extend(sect_values[element_key])
        
        if not selector_options: # If still no options, try to find element_key directly if it's a top-level key
             if element_key in self.selectors and isinstance(self.selectors[element_key], list):
                 selector_options = self.selectors[element_key]

        if not selector_options:
            self.logger.warning(f"No selectors found for key '{element_key}' in section '{section if section else 'any'}'.")
            return None

        for selector in selector_options:
            try:
                by_method = None
                if selector.startswith('//') or selector.startswith('./') or selector.startswith('(') : by_method = By.XPATH
                elif selector.startswith('#'): by_method = By.ID; selector = selector[1:]
                elif selector.startswith('.'): by_method = By.CLASS_NAME; selector = selector[1:]
                else: by_method = By.CSS_SELECTOR
                
                element = self.wait.until(EC.element_to_be_clickable((by_method, selector)))
                self.logger.info(f"✅ Found element '{element_key}' using {by_method} selector: {selector}")
                return element
            except (TimeoutException, NoSuchElementException):
                self.logger.debug(f"Element '{element_key}' not found with {by_method} selector: {selector}")
                continue
            except Exception as e:
                self.logger.error(f"Unexpected error finding '{element_key}' with selector '{selector}': {e}")
                continue
        
        self.logger.warning(f"❌ Could not find element '{element_key}' with any provided selector(s).")
        return None

    def wait_and_click(self, element_key: str, section: str = None, retry_count: int = 3) -> bool:
        """Wait for element and click with retry logic"""
        for attempt in range(retry_count):
            try:
                element = self.find_element_smart(element_key, section)
                if element:
                    self.driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", element)
                    time.sleep(0.5) # Brief pause for scroll
                    element.click()
                    self.logger.info(f"Clicked element '{element_key}'.")
                    return True
            except Exception as e:
                self.logger.warning(f"Click attempt {attempt + 1}/{retry_count} failed for '{element_key}': {str(e)}")
                if attempt < retry_count - 1: time.sleep(1) # Wait before retrying
        self.logger.error(f"Failed to click element '{element_key}' after {retry_count} attempts.")
        return False


class CapcutCreator:
    """CapCut video creation automation"""

    def __init__(self, config: configparser.ConfigParser, selectors: Dict):
        self.config = config
        self.selectors = selectors
        self.logger = Logger().get_logger() 
        self.browser_manager = BrowserManager(config) 
        self.capcut_url = config.get('PLATFORM_URLS', 'capcut_url', fallback="https://www.capcut.com/ai-creator/start")
        self.config_dir = Path(__file__).resolve().parent # Assuming this file is in AUTOMATION directory
        self.driver = None
        self.element_finder = None

    def create_video(self, script_text: str, video_title_from_config: str) -> Optional[str]:
        """Create video using CapCut AI, using provided script text and title."""
        self.logger.info(f"🎬 Starting CapCut video creation for title: '{video_title_from_config}'")
        
        try:
            self.driver = self.browser_manager.get_driver()
            if not self.driver:
                self.logger.error("Failed to get browser driver for CapCut.")
                return None
            self.element_finder = ElementFinder(self.driver, self.selectors)

            self.driver.get(self.capcut_url) 
            time.sleep(5) 

            if not self._login(): return None
            if not self._create_project(): return None
            if not self._add_content(script_text): return None
            if not self._configure_video_settings(): return None
            
            video_output_dir_str = self.config.get('PATHS', 'video_output_path', fallback='videos')
            safe_title = "".join(c if c.isalnum() else "_" for c in video_title_from_config)
            video_file_name = f"{safe_title}_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp4"
            
            # Construct full_video_path relative to the AUTOMATION directory (self.config_dir)
            full_video_path = (self.config_dir / video_output_dir_str / video_file_name).resolve()
            
            # Ensure the parent directory of the target file exists
            full_video_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Call _export_video with the fully resolved path
            exported_video_file = self._export_video(full_video_path) 
            return exported_video_file

        except Exception as e:
            self.logger.error(f"CapCut video creation failed: {str(e)}", exc_info=True)
            return None
        finally:
            self.browser_manager.close_driver()

    def _login(self) -> bool:
        self.logger.info("Attempting CapCut login...")
        self.logger.info("CapCut 'login' step placeholder passed. Assuming manual login if needed.")
        return True

    def _create_project(self) -> bool:
        self.logger.info("Attempting to create a new project in CapCut...")
        self.logger.info("CapCut 'create project' step placeholder passed.")
        return True

    def _add_content(self, script_text: str) -> bool:
        self.logger.info(f"Adding script content (first 50 chars: '{script_text[:50]}...') to CapCut project.")
        self.logger.info("CapCut 'add content' step placeholder passed.")
        return True

    def _configure_video_settings(self) -> bool:
        self.logger.info("Configuring video settings in CapCut...")
        self.logger.info("CapCut 'configure video settings' step placeholder passed.")
        return True

    def _export_video(self, video_title: str, output_dir: Path) -> Optional[str]: 
        """
        Exports the video. In this simulated version, it creates a dummy file
        in the specified output_dir.
        The output_dir path is now constructed and passed by AutomationRunner.
        """
        self.logger.info(f"Exporting video '{video_title}' to directory '{output_dir}'...")
        
        safe_title = "".join(c if c.isalnum() else "_" for c in video_title)
        simulated_video_filename = f"{safe_title}_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp4"
        # output_dir is already an absolute path to the configured video output directory
        simulated_video_path = output_dir / simulated_video_filename
        
        try:
            # Ensure the specific output directory (e.g., videos/subdirectory_if_any) exists
            simulated_video_path.parent.mkdir(parents=True, exist_ok=True)
            with open(simulated_video_path, 'w') as f:
                f.write(f"This is a simulated video file for title: {video_title}") 
            self.logger.success(f"Simulated video exported to: '{simulated_video_path}'")
            return str(simulated_video_path)
        except IOError as e:
            self.logger.error(f"Failed to create simulated video file at '{simulated_video_path}': {e}")
            return None
# The YouTubeUploader class was deleted in a previous subtask.
# If it were still here, its __init__ would be:
# class YouTubeUploader:
#    def __init__(self, config_manager: ConfigManager): # Updated signature
#        self.logger = Logger().get_logger()
#        self.config_manager = config_manager
#        self.config = config_manager.load_config()
#        # ... rest of the API client setup ...
#
#    def upload_video(self, video_path_str: str, metadata: dict) -> bool:
#        # ... API upload logic ...
#        pass


class AutomationRunner:
    """Main automation orchestrator"""

    def __init__(self):
        self.logger = Logger().get_logger()
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config() 
        self.selectors = self.config_manager.load_selectors()
        
        self.browser_manager = BrowserManager(self.config) 
        self.script_generator = ScriptGenerator(self.config, self.selectors, self.browser_manager)
        self.capcut_creator = CapcutCreator(self.config, self.selectors)
        # self.youtube_uploader = YouTubeUploader(self.config_manager) # YouTubeUploader class was deleted.
        self.youtube_uploader = None # Set to None as the class is deleted
        self.logger.info("YouTubeUploader is currently disabled/deleted.")


    def run_workflow(self, mode: str, topic: str = None, video_path: str = None) -> bool:
        """Execute workflow based on mode"""
        self.logger.info(f"🚀 Starting workflow: {mode}")
        
        script_text: str = ""
        
        # Fetch metadata from config. These will be used consistently.
        video_title_from_config: str = self.config_manager.get_video_metadata('title')
        if not video_title_from_config and mode in ['full_auto', 'video_only', 'script_and_video', 'video_and_upload', 'script_only']:
            self.logger.error("Video title not found in config (VIDEO_METADATA -> title) and is required for this mode. Please set it in customisation.ini.")
            return False
        video_title_from_config = video_title_from_config or f"AI Video on {topic or 'Untitled Topic'}" # Fallback if not strictly required by mode
        
        video_description_from_config: str = self.config_manager.get_video_metadata('description') or "An AI-generated video."
        video_tags_from_config: str = self.config_manager.get_video_metadata('tags') or "ai, automation, tech"
        
        # Output directories from config
        script_output_dir_config = self.config_manager.get_absolute_path('script_output_path')
        video_output_dir_config = self.config_manager.get_absolute_path('video_output_path')

        if not script_output_dir_config:
            self.logger.warning("Script output path not defined in config, defaulting to AUTOMATION/Scripts/")
            script_output_dir_config = self.config_manager.config_dir / "Scripts"
        script_output_dir_config.mkdir(parents=True, exist_ok=True)

        if not video_output_dir_config:
            self.logger.warning("Video output path not defined in config, defaulting to AUTOMATION/videos/")
            video_output_dir_config = self.config_manager.config_dir / "videos"
        video_output_dir_config.mkdir(parents=True, exist_ok=True)


        default_prompt_template = self.config.get('AI_SETTINGS', 'default_prompt', 
                                                  fallback="Generate an engaging YouTube video script about {topic}.")
        full_topic_prompt = "" 

        if topic: 
            full_topic_prompt = default_prompt_template.replace("{topic}", topic)
        elif mode not in ['upload_only']: 
            self.logger.error(f"Topic is required for mode '{mode}'.")
            return False

        try:
            # --- Script Generation Stage ---
            if mode in ['full_auto', 'script_only', 'video_only', 'script_and_video', 'video_and_upload']:
                if not full_topic_prompt:
                    self.logger.error(f"Internal error: Full topic prompt is empty for script generation mode '{mode}'.")
                    return False
                
                self.logger.info(f"Processing prompt for script generation: {full_topic_prompt[:150]}...")
                max_words_for_script = self.config.getint('AI_SETTINGS', 'max_words', fallback=300)
                script_text = self.script_generator.generate_script(full_topic_prompt, max_words_for_script)
                
                if not script_text: 
                    self.logger.error("Script generation failed or returned an empty script.")
                    return False
                self.logger.success(f"Script text generated successfully for prompt starting with: '{full_topic_prompt[:50]}...'")
                
                if mode == 'script_only':
                    safe_title_for_filename = "".join(c if c.isalnum() else "_" for c in video_title_from_config)
                    script_file_name = f"script_{safe_title_for_filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                    script_file_path = script_output_dir_config / script_file_name # Use configured path
                    try:
                        with open(script_file_path, 'w', encoding='utf-8') as f:
                            f.write(f"--- Video Title (from config): {video_title_from_config} ---\n")
                            f.write(f"--- Prompt Used: {full_topic_prompt} ---\n\n")
                            f.write(script_text)
                        self.logger.info(f"Script text saved to: '{script_file_path}'")
                    except IOError as e:
                        self.logger.error(f"Failed to save script text to '{script_file_path}': {e}")
                    return True 

            # --- Video Creation Stage ---
            current_video_path = video_path 

            if mode in ['full_auto', 'video_only', 'script_and_video', 'video_and_upload']:
                if not script_text: 
                    self.logger.error("Script text is missing for video creation modes (should have been generated).")
                    return False
                self.logger.info(f"Starting video creation for title: '{video_title_from_config}'.")
                # CapcutCreator's _export_video method should use the video_output_dir_config
                # The create_video method of CapcutCreator already handles passing the correct output dir to _export_video
                current_video_path = self.capcut_creator.create_video(script_text, video_title_from_config)
                if not current_video_path:
                    self.logger.error("Video creation failed.")
                    return False
                self.logger.success(f"Video created: '{current_video_path}'")

            if mode == 'video_only' or mode == 'script_and_video': return True
            
            # --- Video Upload Stage ---
            if mode in ['full_auto', 'upload_only', 'video_and_upload']:
                if not self.youtube_uploader:
                    self.logger.warning("YouTubeUploader is not available (likely deleted or not initialized). Skipping upload.")
                    # Depending on strictness, could return False here. For now, just log and "succeed" for the parts that ran.
                    return mode != 'full_auto' and mode != 'video_and_upload' # Fails if upload was essential
                
                if not current_video_path:
                    self.logger.error(f"Video path is missing for upload mode '{mode}'.")
                    return False
                if not Path(current_video_path).is_file():
                    self.logger.error(f"Video file not found at '{current_video_path}' for upload.")
                    return False
                
                youtube_metadata = {
                    'title': video_title_from_config,
                    'description': video_description_from_config,
                    'tags': video_tags_from_config,
                    'script': script_text 
                }
                if mode == 'upload_only': 
                    youtube_metadata['title'] = f"Uploaded Video - {Path(current_video_path).stem}"
                    youtube_metadata['description'] = f"This video ({Path(current_video_path).name}) was uploaded using the automation tool."
                
                self.logger.info(f"Starting YouTube upload for video: '{current_video_path}'.")
                upload_success = self.youtube_uploader.upload_video(current_video_path, youtube_metadata)
                if not upload_success:
                    self.logger.error("YouTube upload failed.")
                    return False
                
                # Logging of uploaded video is now handled within YouTubeUploader itself
                self.logger.success("🎉 Workflow completed successfully (including upload)!")
                return True
            
            self.logger.error(f"Unknown workflow state or mode reached: {mode}")
            return False

        except Exception as e:
            self.logger.error(f"Workflow execution for mode '{mode}' failed: {str(e)}", exc_info=True)
            return False


def main():
    """Main function for non-interactive execution based on customisation.ini."""
    logger = Logger().get_logger()
    logger.info("🚀 Starting Smart Automation Tool in non-interactive mode.")

    try:
        config_manager = ConfigManager()
        config = config_manager.load_config() # Config is loaded during ConfigManager init

        execution_mode = config.get('WORKFLOW_SETTINGS', 'execution_mode', fallback='full_auto')
        # The 'default_prompt' from config is now the primary topic for non-interactive runs
        default_topic = config.get('AI_SETTINGS', 'default_prompt', fallback='AI in everyday life')
        
        # Video path for 'upload_only' mode would need to be specified in customisation.ini
        # or this mode would need to be adapted/restricted in non-interactive runs.
        # For now, we assume modes requiring a video_path upfront are not the default
        # for non-interactive execution unless explicitly configured.
        video_path_for_upload = config.get('PATHS', 'upload_video_file_path', fallback=None) # Example new config option

        logger.info(f"Configuration loaded. Execution mode: '{execution_mode}'")
        logger.info(f"Default topic/prompt from config: '{default_topic[:100]}...'")
        if execution_mode == 'upload_only' and video_path_for_upload:
            logger.info(f"Video path for upload_only mode: '{video_path_for_upload}'")

        automation_runner = AutomationRunner()
        
        # Prepare arguments for run_workflow based on execution_mode
        topic_for_workflow = default_topic
        video_path_for_workflow = None

        if execution_mode == 'upload_only':
            if video_path_for_upload and Path(video_path_for_upload).is_file():
                video_path_for_workflow = video_path_for_upload
                topic_for_workflow = None # Topic is not used by upload_only if video_path is set
            else:
                logger.error(f"Execution mode is 'upload_only' but 'upload_video_file_path' is not set or invalid in customisation.ini.")
                logger.error("Please set 'upload_video_file_path' in the [PATHS] section of customisation.ini for this mode.")
                return # Exit if necessary configuration for upload_only is missing
        
        # For modes requiring a topic, full_topic_prompt is constructed inside AutomationRunner.run_workflow
        # So, AutomationRunner.run_workflow will use the 'topic' argument to build the full prompt.
        success = automation_runner.run_workflow(mode=execution_mode, topic=topic_for_workflow, video_path=video_path_for_workflow)

        if success:
            logger.info("✅ Non-interactive workflow completed successfully!")
        else:
            logger.error("❌ Non-interactive workflow failed. Check logs for details.")

    except configparser.Error as e:
        logger.critical(f"Error reading or parsing configuration file: {e}", exc_info=True)
        print(f"❌ CRITICAL CONFIGURATION ERROR: {e}. Please check 'AUTOMATION/customisation.ini'.")
    except Exception as e:
        logger.critical(f"An unexpected error occurred in main: {e}", exc_info=True)
        print(f"❌ An unexpected error occurred: {e}. Check logs for details.")

if __name__ == "__main__":
    main()
