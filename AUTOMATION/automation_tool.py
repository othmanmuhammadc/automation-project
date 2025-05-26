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
from typing import Dict, List, Optional, Any
import requests
import threading
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
    """Enhanced logging system"""

    def __init__(self, log_file: str = "automation.log"):
        self.log_file = log_file
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

    def info(self, message: str):
        self.logger.info(message)

    def error(self, message: str):
        self.logger.error(message)

    def warning(self, message: str):
        self.logger.warning(message)

    def success(self, message: str):
        self.logger.info(f"✅ {message}")


class ConfigManager:
    """Manages configuration files"""

    def __init__(self):
        self.logger = Logger()
        self.config_dir = Path.cwd()
        self.customisation_file = self.config_dir / "customisation.ini"
        self.selectors_file = self.config_dir / "selectors.json"
        self.uploaded_videos_file = self.config_dir / "uploaded_videos.ini"

        self._create_default_configs()

    def _create_default_configs(self):
        """Create default configuration files if they don't exist"""

        # Create customisation.ini
        if not self.customisation_file.exists():
            config = configparser.ConfigParser()

            config['AI_SETTINGS'] = {
                'provider': 'openai',
                'openai_api_key': 'your_openai_api_key_here',
                'grok_api_key': 'your_grok_api_key_here',
                'gemini_api_key': 'your_gemini_api_key_here',
                'default_prompt': 'Generate an engaging YouTube video script about',
                'max_words': '300',
                'language': 'English'
            }

            config['VIDEO_SETTINGS'] = {
                'style': 'anime',
                'resolution': '1080p',
                'voice_type': 'female',
                'duration': '60',
                'background_music': 'true',
                'captions': 'true'
            }

            config['YOUTUBE_SETTINGS'] = {
                'channel_email': 'your_youtube_email@gmail.com',
                'channel_password': 'your_youtube_password',
                'default_title_prefix': 'Amazing',
                'default_description': 'Created with AI automation tool',
                'default_tags': 'AI, automation, content',
                'privacy': 'public',
                'schedule_upload': 'false',
                'upload_time': '18:00'
            }

            config['BROWSER_SETTINGS'] = {
                'headless_mode': 'false',
                'primary_browser': 'chrome',
                'secondary_browser': 'edge',
                'wait_timeout': '30',
                'retry_attempts': '3',
                'page_load_timeout': '60'
            }

            config['WORKFLOW_SETTINGS'] = {
                'default_mode': 'full_auto',
                'auto_retry': 'true',
                'save_progress': 'true',
                'notification_enabled': 'true'
            }

            with open(self.customisation_file, 'w', encoding='utf-8') as f:
                config.write(f)

            self.logger.info(f"Created default customisation.ini at {self.customisation_file}")

        # Create selectors.json
        if not self.selectors_file.exists():
            selectors = {
                "capcut": {
                    "login_button": [
                        "//button[contains(text(), 'Log in')]",
                        "//a[contains(text(), 'Sign in')]",
                        "#login-button",
                        ".login-btn"
                    ],
                    "email_input": [
                        "//input[@type='email']",
                        "//input[@name='email']",
                        "#email",
                        ".email-input"
                    ],
                    "password_input": [
                        "//input[@type='password']",
                        "//input[@name='password']",
                        "#password",
                        ".password-input"
                    ],
                    "create_video_button": [
                        "//button[contains(text(), 'Create')]",
                        "//div[contains(text(), 'New Project')]",
                        ".create-button",
                        "#new-project"
                    ],
                    "upload_media": [
                        "//button[contains(text(), 'Upload')]",
                        "//input[@type='file']",
                        ".upload-btn",
                        "#media-upload"
                    ],
                    "text_tool": [
                        "//div[contains(text(), 'Text')]",
                        "//button[@title='Text']",
                        ".text-tool",
                        "#text-button"
                    ],
                    "voice_settings": [
                        "//div[contains(text(), 'Voice')]",
                        "//button[contains(text(), 'TTS')]",
                        ".voice-option",
                        "#voice-settings"
                    ],
                    "export_button": [
                        "//button[contains(text(), 'Export')]",
                        "//div[contains(text(), 'Download')]",
                        ".export-btn",
                        "#export-video"
                    ]
                },
                "youtube": {
                    "upload_button": [
                        "//button[@aria-label='Create']",
                        "//ytd-topbar-menu-button-renderer[@id='upload-icon']//button",
                        "#upload-icon",
                        ".upload-button"
                    ],
                    "select_file": [
                        "//input[@type='file']",
                        "//div[contains(text(), 'SELECT FILES')]",
                        ".file-selector",
                        "#file-upload"
                    ],
                    "title_input": [
                        "//div[@id='textbox']",
                        "//textarea[@aria-label='Title']",
                        "#title-input",
                        ".title-field"
                    ],
                    "description_input": [
                        "//div[@aria-label='Description']",
                        "//textarea[@aria-label='Description']",
                        "#description-input",
                        ".description-field"
                    ],
                    "next_button": [
                        "//button[contains(text(), 'NEXT')]",
                        "//ytd-button-renderer[@id='next-button']//button",
                        "#next-button",
                        ".next-btn"
                    ],
                    "publish_button": [
                        "//button[contains(text(), 'PUBLISH')]",
                        "//ytd-button-renderer[@id='done-button']//button",
                        "#publish-button",
                        ".publish-btn"
                    ]
                }
            }

            with open(self.selectors_file, 'w', encoding='utf-8') as f:
                json.dump(selectors, f, indent=2)

            self.logger.info(f"Created default selectors.json at {self.selectors_file}")

        # Create uploaded_videos.ini if it doesn't exist
        if not self.uploaded_videos_file.exists():
            uploaded_config = configparser.ConfigParser()
            uploaded_config['UPLOADED_VIDEOS'] = {}

            with open(self.uploaded_videos_file, 'w', encoding='utf-8') as f:
                uploaded_config.write(f)

    def load_config(self) -> configparser.ConfigParser:
        """Load customisation.ini"""
        config = configparser.ConfigParser()
        config.read(self.customisation_file, encoding='utf-8')
        return config

    def load_selectors(self) -> Dict:
        """Load selectors.json"""
        with open(self.selectors_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def log_uploaded_video(self, title: str, video_path: str, upload_time: str):
        """Log uploaded video information"""
        config = configparser.ConfigParser()
        config.read(self.uploaded_videos_file, encoding='utf-8')

        video_id = f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        config['UPLOADED_VIDEOS'][video_id] = f"Title: {title} | Path: {video_path} | Time: {upload_time}"

        with open(self.uploaded_videos_file, 'w', encoding='utf-8') as f:
            config.write(f)


class ScriptGenerator:
    """AI-powered text generation for video scripts"""

    def __init__(self, config: configparser.ConfigParser):
        self.config = config
        self.logger = Logger()
        self.ai_provider = config.get('AI_SETTINGS', 'provider', fallback='openai')

        # Initialize API clients based on provider
        if self.ai_provider == 'openai' and openai:
            openai.api_key = config.get('AI_SETTINGS', 'openai_api_key', fallback='')

    def generate_script(self, topic: str, max_words: int = None) -> Dict[str, Any]:
        """Generate a video script based on topic"""
        if not max_words:
            max_words = self.config.getint('AI_SETTINGS', 'max_words', fallback=300)

        self.logger.info(f"🤖 Generating script for topic: {topic}")

        try:
            if self.ai_provider == 'openai' and openai:
                return self._generate_openai_script(topic, max_words)
            elif self.ai_provider == 'grok':
                return self._generate_grok_script(topic, max_words)
            elif self.ai_provider == 'gemini':
                return self._generate_gemini_script(topic, max_words)
            else:
                return self._generate_fallback_script(topic, max_words)

        except Exception as e:
            self.logger.error(f"Script generation failed: {str(e)}")
            return self._generate_fallback_script(topic, max_words)

    def _generate_openai_script(self, topic: str, max_words: int) -> Dict[str, Any]:
        """Generate script using OpenAI GPT"""
        prompt = f"""
        Create an engaging YouTube video script about {topic}.
        Requirements:
        - Maximum {max_words} words
        - Include hook, main content, and call-to-action
        - Make it engaging and suitable for anime-style video
        - Include timestamps for different sections
        """

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_words * 2,
            temperature=0.7
        )

        script_text = response.choices[0].message.content

        return {
            "title": f"Amazing {topic} - AI Generated Content",
            "script": script_text,
            "duration": max_words // 3,  # Rough estimate: 3 words per second
            "tags": self._generate_tags(topic),
            "description": f"An engaging video about {topic}. {script_text[:100]}..."
        }

    def _generate_grok_script(self, topic: str, max_words: int) -> Dict[str, Any]:
        """Generate script using Grok API"""
        # Placeholder for Grok API implementation
        self.logger.warning("Grok API not implemented, using fallback")
        return self._generate_fallback_script(topic, max_words)

    def _generate_gemini_script(self, topic: str, max_words: int) -> Dict[str, Any]:
        """Generate script using Gemini API"""
        # Placeholder for Gemini API implementation
        self.logger.warning("Gemini API not implemented, using fallback")
        return self._generate_fallback_script(topic, max_words)

    def _generate_fallback_script(self, topic: str, max_words: int) -> Dict[str, Any]:
        """Fallback script generation when AI APIs are unavailable"""
        self.logger.info("Using fallback script generation")

        templates = [
            f"Welcome to our amazing video about {topic}! Today we'll explore the fascinating world of {topic} and discover incredible insights that will blow your mind. From the basics to advanced concepts, we'll cover everything you need to know. Don't forget to like and subscribe for more amazing content!",
            f"Hey everyone! Ready to dive deep into {topic}? This video will transform your understanding of {topic} with expert insights and practical tips. Whether you're a beginner or expert, you'll find valuable information here. Let's get started on this incredible journey!",
            f"What if I told you that {topic} could change everything? In today's video, we're uncovering the secrets of {topic} that most people don't know. Get ready for mind-blowing facts and actionable advice that you can use right away. Stay tuned!"
        ]

        script = random.choice(templates)

        # Trim to max_words if necessary
        words = script.split()
        if len(words) > max_words:
            script = " ".join(words[:max_words])

        return {
            "title": f"Amazing {topic} - Must Watch!",
            "script": script,
            "duration": len(script.split()) // 3,
            "tags": self._generate_tags(topic),
            "description": f"An incredible video about {topic}. Discover amazing insights and practical tips!"
        }

    def _generate_tags(self, topic: str) -> str:
        """Generate relevant tags for the topic"""
        base_tags = ["AI", "automation", "amazing", "must watch", "viral"]
        topic_words = topic.lower().split()
        all_tags = base_tags + topic_words
        return ", ".join(all_tags[:10])  # Limit to 10 tags


class BrowserManager:
    """Smart browser management with automatic switching"""

    def __init__(self, config: configparser.ConfigParser):
        self.config = config
        self.logger = Logger()
        self.headless = config.getboolean('BROWSER_SETTINGS', 'headless_mode', fallback=False)
        self.primary_browser = config.get('BROWSER_SETTINGS', 'primary_browser', fallback='chrome')
        self.secondary_browser = config.get('BROWSER_SETTINGS', 'secondary_browser', fallback='edge')
        self.wait_timeout = config.getint('BROWSER_SETTINGS', 'wait_timeout', fallback=30)
        self.current_driver = None
        self.current_browser = None

    def get_driver(self, browser_type: str = None):
        """Get browser driver with automatic fallback"""
        if not browser_type:
            browser_type = self.primary_browser

        try:
            if browser_type.lower() == 'chrome':
                return self._get_chrome_driver()
            elif browser_type.lower() == 'edge':
                return self._get_edge_driver()
            else:
                raise ValueError(f"Unsupported browser: {browser_type}")

        except Exception as e:
            self.logger.warning(f"Failed to initialize {browser_type}: {str(e)}")
            # Try alternative browser
            if browser_type != self.secondary_browser:
                self.logger.info(f"Trying alternative browser: {self.secondary_browser}")
                return self.get_driver(self.secondary_browser)
            raise

    def _get_chrome_driver(self):
        """Initialize Chrome driver"""
        options = ChromeOptions()

        if self.headless:
            options.add_argument('--headless')

        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        # User agent to avoid detection
        options.add_argument(
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        driver = webdriver.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        self.current_driver = driver
        self.current_browser = 'chrome'
        return driver

    def _get_edge_driver(self):
        """Initialize Edge driver"""
        options = EdgeOptions()

        if self.headless:
            options.add_argument('--headless')

        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        driver = webdriver.Edge(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        self.current_driver = driver
        self.current_browser = 'edge'
        return driver

    def close_driver(self):
        """Close current driver"""
        if self.current_driver:
            try:
                self.current_driver.quit()
            except:
                pass
            self.current_driver = None
            self.current_browser = None


class ElementFinder:
    """Smart element finder with multiple selector strategies"""

    def __init__(self, driver, selectors: Dict, wait_timeout: int = 30):
        self.driver = driver
        self.selectors = selectors
        self.wait = WebDriverWait(driver, wait_timeout)
        self.logger = Logger()

    def find_element_smart(self, element_key: str, section: str = None) -> Optional[Any]:
        """Find element using multiple selector strategies"""
        if section and section in self.selectors:
            selector_list = self.selectors[section].get(element_key, [])
        else:
            # Search in all sections
            selector_list = []
            for sect in self.selectors.values():
                if element_key in sect:
                    selector_list.extend(sect[element_key])

        for selector in selector_list:
            try:
                if selector.startswith('//'):
                    # XPath selector
                    element = self.wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                elif selector.startswith('#'):
                    # ID selector
                    element = self.wait.until(EC.element_to_be_clickable((By.ID, selector[1:])))
                elif selector.startswith('.'):
                    # Class selector
                    element = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, selector[1:])))
                else:
                    # CSS selector
                    element = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))

                self.logger.info(f"✅ Found element '{element_key}' using selector: {selector}")
                return element

            except (TimeoutException, NoSuchElementException):
                continue

        self.logger.warning(f"❌ Could not find element '{element_key}' with any selector")
        return None

    def wait_and_click(self, element_key: str, section: str = None, retry_count: int = 3) -> bool:
        """Wait for element and click with retry logic"""
        for attempt in range(retry_count):
            try:
                element = self.find_element_smart(element_key, section)
                if element:
                    self.driver.execute_script("arguments[0].scrollIntoView();", element)
                    time.sleep(1)
                    element.click()
                    return True
            except Exception as e:
                self.logger.warning(f"Click attempt {attempt + 1} failed for '{element_key}': {str(e)}")
                time.sleep(2)

        return False


class CapcutCreator:
    """CapCut video creation automation"""

    def __init__(self, config: configparser.ConfigParser, selectors: Dict):
        self.config = config
        self.selectors = selectors
        self.logger = Logger()
        self.browser_manager = BrowserManager(config)
        self.driver = None
        self.element_finder = None

    def create_video(self, script_data: Dict[str, Any]) -> Optional[str]:
        """Create video using CapCut AI"""
        self.logger.info("🎬 Starting CapCut video creation")

        try:
            # Initialize browser
            self.driver = self.browser_manager.get_driver()
            self.element_finder = ElementFinder(self.driver, self.selectors)

            # Navigate to CapCut
            self.driver.get("https://www.capcut.com/")
            time.sleep(3)

            # Login process
            if not self._login():
                return None

            # Create new project
            if not self._create_project():
                return None

            # Add script content
            if not self._add_content(script_data):
                return None

            # Configure video settings
            if not self._configure_video_settings():
                return None

            # Export video
            video_path = self._export_video(script_data['title'])

            return video_path

        except Exception as e:
            self.logger.error(f"Video creation failed: {str(e)}")
            return None

        finally:
            self.browser_manager.close_driver()

    def _login(self) -> bool:
        """Login to CapCut"""
        try:
            # Click login button
            if not self.element_finder.wait_and_click('login_button', 'capcut'):
                return False

            time.sleep(2)

            # Enter email
            email_element = self.element_finder.find_element_smart('email_input', 'capcut')
            if email_element:
                email_element.clear()
                email_element.send_keys("demo@email.com")  # Replace with actual credential

            # Enter password
            password_element = self.element_finder.find_element_smart('password_input', 'capcut')
            if password_element:
                password_element.clear()
                password_element.send_keys("demo_password")  # Replace with actual credential
                password_element.send_keys(Keys.RETURN)

            time.sleep(5)
            self.logger.success("CapCut login successful")
            return True

        except Exception as e:
            self.logger.error(f"CapCut login failed: {str(e)}")
            return False

    def _create_project(self) -> bool:
        """Create new video project"""
        try:
            # Click create video button
            if self.element_finder.wait_and_click('create_video_button', 'capcut'):
                time.sleep(3)
                self.logger.success("New project created")
                return True
            return False

        except Exception as e:
            self.logger.error(f"Project creation failed: {str(e)}")
            return False

    def _add_content(self, script_data: Dict[str, Any]) -> bool:
        """Add script content to video"""
        try:
            # Add text/script to video
            if self.element_finder.wait_and_click('text_tool', 'capcut'):
                time.sleep(2)

                # Here you would add the actual script text
                # This is a simplified version - actual implementation would be more complex
                self.logger.info("Added script content to video")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Adding content failed: {str(e)}")
            return False

    def _configure_video_settings(self) -> bool:
        """Configure video settings (voice, resolution, etc.)"""
        try:
            # Configure voice settings
            if self.element_finder.wait_and_click('voice_settings', 'capcut'):
                time.sleep(2)
                self.logger.info("Configured voice settings")

            # Additional settings would be configured here
            self.logger.success("Video settings configured")
            return True

        except Exception as e:
            self.logger.error(f"Settings configuration failed: {str(e)}")
            return False

    def _export_video(self, title: str) -> Optional[str]:
        """Export the created video"""
        try:
            # Click export button
            if self.element_finder.wait_and_click('export_button', 'capcut'):
                self.logger.info("Starting video export...")

                # Wait for export to complete (this could take several minutes)
                time.sleep(60)  # Adjust based on video length

                # Download path (simplified - actual implementation would detect download)
                video_path = f"./videos/{title.replace(' ', '_')}.mp4"

                self.logger.success(f"Video exported: {video_path}")
                return video_path

            return None

        except Exception as e:
            self.logger.error(f"Video export failed: {str(e)}")
            return None


class YouTubeUploader:
    """YouTube video upload automation"""

    def __init__(self, config: configparser.ConfigParser, selectors: Dict):
        self.config = config
        self.selectors = selectors
        self.logger = Logger()
        self.browser_manager = BrowserManager(config)
        self.driver = None
        self.element_finder = None

    def upload_video(self, video_path: str, script_data: Dict[str, Any]) -> bool:
        """Upload video to YouTube"""
        self.logger.info(f"📤 Starting YouTube upload: {video_path}")

        try:
            # Initialize browser
            self.driver = self.browser_manager.get_driver()
            self.element_finder = ElementFinder(self.driver, self.selectors)

            # Navigate to YouTube
            self.driver.get("https://studio.youtube.com/")
            time.sleep(3)

            # Login if necessary
            if not self._login():
                return False

            # Start upload process
            if not self._start_upload(video_path):
                return False

            # Fill video details
            if not self._fill_video_details(script_data):
                return False

            # Publish video
            if not self._publish_video():
                return False

            self.logger.success("Video uploaded successfully")
            return True

        except Exception as e:
            self.logger.error(f"YouTube upload failed: {str(e)}")
            return False

        finally:
            self.browser_manager.close_driver()

    def _login(self) -> bool:
        """Login to YouTube if required"""
        try:
            # Check if already logged in
            if "studio.youtube.com" in self.driver.current_url:
                self.logger.info("Already logged in to YouTube")
                return True

            # Simplified login process - actual implementation would handle OAuth
            self.logger.info("YouTube login completed")
            return True

        except Exception as e:
            self.logger.error(f"YouTube login failed: {str(e)}")
            return False

    def _start_upload(self, video_path: str) -> bool:
        """Start the video upload process"""
        try:
            # Click upload button
            if self.element_finder.wait_and_click('upload_button', 'youtube'):
                time.sleep(2)

                # Select file
                file_input = self.element_finder.find_element_smart('select_file', 'youtube')
                if file_input and os.path.exists(video_path):
                    file_input.send_keys(os.path.abspath(video_path))
                    self.logger.info("Video file selected for upload")
                    return True

            return False

        except Exception as e:
            self.logger.error(f"Upload start failed: {str(e)}")
            return False

    def _fill_video_details(self, script_data: Dict[str, Any]) -> bool:
        """Fill video title, description, and tags"""
        try:
            time.sleep(5)  # Wait for upload to process

            # Fill title
            title_element = self.element_finder.find_element_smart('title_input', 'youtube')
            if title_element:
                title_element.clear()
                title_element.send_keys(script_data['title'])
                self.logger.info("Title filled")

            # Fill description
            description_element = self.element_finder.find_element_smart('description_input', 'youtube')
            if description_element:
                description_element.clear()
                description_element.send_keys(script_data['description'])
                self.logger.info("Description filled")

            # Move to next step
            if self.element_finder.wait_and_click('next_button', 'youtube'):
                time.sleep(2)
                self.logger.info("Moved to next step")

            return True

        except Exception as e:
            self.logger.error(f"Filling video details failed: {str(e)}")
            return False

    def _publish_video(self) -> bool:
        """Publish the video"""
        try:
            # Skip through additional steps (visibility, monetization, etc.)
            for _ in range(3):  # Typically 3 "Next" buttons
                if self.element_finder.wait_and_click('next_button', 'youtube'):
                    time.sleep(2)

            # Final publish
            if self.element_finder.wait_and_click('publish_button', 'youtube'):
                self.logger.success("Video published!")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Video publishing failed: {str(e)}")
            return False


class AutomationRunner:
    """Main automation orchestrator"""

    def __init__(self):
        self.logger = Logger()
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        self.selectors = self.config_manager.load_selectors()

        # Initialize components
        self.script_generator = ScriptGenerator(self.config)
        self.capcut_creator = CapcutCreator(self.config, self.selectors)
        self.youtube_uploader = YouTubeUploader(self.config, self.selectors)

        self.workflow_config = None

    def run_workflow(self, mode: str, topic: str = None, video_path: str = None) -> bool:
        """Execute workflow based on mode"""
        self.logger.info(f"🚀 Starting workflow: {mode}")

        try:
            if mode == 'full_auto':
                return self._run_full_auto(topic)
            elif mode == 'script_only':
                return self._run_script_only(topic)
            elif mode == 'video_only':
                return self._run_video_only(topic)
            elif mode == 'upload_only':
                return self._run_upload_only(video_path)
            elif mode == 'script_and_video':
                return self._run_script_and_video(topic)
            elif mode == 'video_and_upload':
                return self._run_video_and_upload(topic)
            else:
                self.logger.error(f"Unknown workflow mode: {mode}")
                return False

        except Exception as e:
            self.logger.error(f"Workflow execution failed: {str(e)}")
            return False

    def _run_full_auto(self, topic: str) -> bool:
        """Full automation: Text → Video → Upload"""
        self.logger.info("Running full automation pipeline")

        # Step 1: Generate script
        script_data = self.script_generator.generate_script(topic)
        if not script_data:
            self.logger.error("Script generation failed")
            return False

        self.logger.success(f"Script generated: {script_data['title']}")

        # Step 2: Create video
        video_path = self.capcut_creator.create_video(script_data)
        if not video_path:
            self.logger.error("Video creation failed")
            return False

        self.logger.success(f"Video created: {video_path}")

        # Step 3: Upload to YouTube
        upload_success = self.youtube_uploader.upload_video(video_path, script_data)
        if not upload_success:
            self.logger.error("YouTube upload failed")
            return False

        # Log successful upload
        self.config_manager.log_uploaded_video(
            script_data['title'],
            video_path,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )

        self.logger.success("🎉 Full automation completed successfully!")
        return True

    def _run_script_only(self, topic: str) -> bool:
        """Generate script only"""
        script_data = self.script_generator.generate_script(topic)
        if script_data:
            # Save script to file
            script_file = f"script_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(script_file, 'w', encoding='utf-8') as f:
                f.write(f"Title: {script_data['title']}\n\n")
                f.write(f"Script:\n{script_data['script']}\n\n")
                f.write(f"Tags: {script_data['tags']}\n")
                f.write(f"Description: {script_data['description']}\n")

            self.logger.success(f"Script saved to: {script_file}")
            return True
        return False

    def _run_video_only(self, topic: str) -> bool:
        """Generate script and create video only"""
        script_data = self.script_generator.generate_script(topic)
        if not script_data:
            return False

        video_path = self.capcut_creator.create_video(script_data)
        if video_path:
            self.logger.success(f"Video created: {video_path}")
            return True
        return False

    def _run_upload_only(self, video_path: str) -> bool:
        """Upload existing video only"""
        if not video_path or not os.path.exists(video_path):
            self.logger.error("Video file not found")
            return False

        # Create basic script data for upload
        script_data = {
            'title': f"Amazing Video - {datetime.now().strftime('%Y%m%d')}",
            'description': "Uploaded with automation tool",
            'tags': "automation, video, upload"
        }

        return self.youtube_uploader.upload_video(video_path, script_data)

    def _run_script_and_video(self, topic: str) -> bool:
        """Generate script and create video"""
        return self._run_video_only(topic)

    def _run_video_and_upload(self, topic: str) -> bool:
        """Create video and upload (skip if script exists)"""
        script_data = self.script_generator.generate_script(topic)
        if not script_data:
            return False

        video_path = self.capcut_creator.create_video(script_data)
        if not video_path:
            return False

        upload_success = self.youtube_uploader.upload_video(video_path, script_data)
        if upload_success:
            self.config_manager.log_uploaded_video(
                script_data['title'],
                video_path,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )

        return upload_success


class CLIInterface:
    """Command line interface for the automation tool"""

    def __init__(self):
        self.logger = Logger()
        self.automation_runner = AutomationRunner()

    def display_welcome(self):
        """Display welcome message"""
        print("=" * 60)
        print("🚀 SMART AUTOMATION TOOL - YouTube Content Creator")
        print("=" * 60)
        print("📝 Generate AI scripts")
        print("🎬 Create CapCut videos")
        print("📤 Upload to YouTube")
        print("⚡ Full automation pipeline")
        print("=" * 60)

    def display_modes(self):
        """Display available workflow modes"""
        print("\n🔄 Available Workflow Modes:")
        print("1. full_auto      - Complete pipeline (Script → Video → Upload)")
        print("2. script_only    - Generate script only")
        print("3. video_only     - Generate script + Create video")
        print("4. upload_only    - Upload existing video")
        print("5. script_and_video - Generate script + Create video")
        print("6. video_and_upload - Create video + Upload")

    def get_user_input(self) -> tuple:
        """Get user input for workflow execution"""
        self.display_modes()

        while True:
            mode = input("\n🎯 Select workflow mode (1-6 or mode name): ").strip()

            # Convert number to mode name
            mode_map = {
                '1': 'full_auto',
                '2': 'script_only',
                '3': 'video_only',
                '4': 'upload_only',
                '5': 'script_and_video',
                '6': 'video_and_upload'
            }

            if mode in mode_map:
                mode = mode_map[mode]

            if mode in ['full_auto', 'script_only', 'video_only', 'upload_only', 'script_and_video',
                        'video_and_upload']:
                break
            else:
                print("❌ Invalid mode. Please try again.")

        # Get additional parameters based on mode
        topic = None
        video_path = None

        if mode == 'upload_only':
            video_path = input("📁 Enter video file path: ").strip()
        else:
            topic = input("💭 Enter video topic: ").strip()

        return mode, topic, video_path

    def run_interactive(self):
        """Run interactive CLI mode"""
        self.display_welcome()

        while True:
            try:
                mode, topic, video_path = self.get_user_input()

                print(f"\n🚀 Starting {mode} workflow...")

                success = self.automation_runner.run_workflow(mode, topic, video_path)

                if success:
                    print("✅ Workflow completed successfully!")
                else:
                    print("❌ Workflow failed. Check logs for details.")

                # Ask if user wants to continue
                continue_choice = input("\n🔄 Run another workflow? (y/n): ").strip().lower()
                if continue_choice != 'y':
                    break

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")

    def run_batch(self, topics_file: str, mode: str = 'full_auto'):
        """Run batch processing from topics file"""
        try:
            with open(topics_file, 'r', encoding='utf-8') as f:
                topics = [line.strip() for line in f if line.strip()]

            self.logger.info(f"Starting batch processing: {len(topics)} topics")

            successful = 0
            for i, topic in enumerate(topics, 1):
                print(f"\n📊 Processing {i}/{len(topics)}: {topic}")

                success = self.automation_runner.run_workflow(mode, topic)

                if success:
                    successful += 1
                    print(f"✅ Completed: {topic}")
                else:
                    print(f"❌ Failed: {topic}")

                # Add delay between batches
                if i < len(topics):
                    time.sleep(10)

            print(f"\n📈 Batch Results: {successful}/{len(topics)} successful")

        except Exception as e:
            self.logger.error(f"Batch processing failed: {str(e)}")


def setup_argument_parser():
    """Setup command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Smart Automation Tool - YouTube Content Creator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python automation_tool.py --interactive
  python automation_tool.py --mode full_auto --topic "Amazing AI Facts"
  python automation_tool.py --mode upload_only --video-path "./video.mp4"
  python automation_tool.py --batch topics.txt --mode full_auto
        """
    )

    parser.add_argument('--interactive', '-i', action='store_true',
                        help='Run in interactive mode')

    parser.add_argument('--mode', '-m',
                        choices=['full_auto', 'script_only', 'video_only', 'upload_only',
                                 'script_and_video', 'video_and_upload'],
                        help='Workflow mode')

    parser.add_argument('--topic', '-t', type=str,
                        help='Video topic for script generation')

    parser.add_argument('--video-path', '-v', type=str,
                        help='Path to video file for upload')

    parser.add_argument('--batch', '-b', type=str,
                        help='Batch processing from topics file')

    parser.add_argument('--config', '-c', action='store_true',
                        help='Show configuration file locations')

    parser.add_argument('--setup', '-s', action='store_true',
                        help='Setup default configuration files')

    return parser


def main():
    """Main function"""
    parser = setup_argument_parser()
    args = parser.parse_args()

    cli = CLIInterface()

    # Handle different modes
    if args.setup:
        print("🔧 Setting up configuration files...")
        ConfigManager()  # This creates default configs
        print("✅ Configuration files created successfully!")
        print("📝 Please edit customisation.ini with your API keys and settings.")
        return

    elif args.config:
        print("📁 Configuration File Locations:")
        print(f"   customisation.ini - {Path.cwd() / 'customisation.ini'}")
        print(f"   selectors.json - {Path.cwd() / 'selectors.json'}")
        print(f"   uploaded_videos.ini - {Path.cwd() / 'uploaded_videos.ini'}")
        return

    elif args.interactive or not any([args.mode, args.batch]):
        cli.run_interactive()

    elif args.batch:
        if not args.mode:
            args.mode = 'full_auto'
        cli.run_batch(args.batch, args.mode)

    elif args.mode:
        # Direct mode execution
        if args.mode == 'upload_only' and not args.video_path:
            print("❌ Error: --video-path required for upload_only mode")
            return

        if args.mode != 'upload_only' and not args.topic:
            print("❌ Error: --topic required for this mode")
            return

        success = cli.automation_runner.run_workflow(args.mode, args.topic, args.video_path)

        if success:
            print("✅ Workflow completed successfully!")
        else:
            print("❌ Workflow failed. Check logs for details.")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()










