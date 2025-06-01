import configparser
import json
from datetime import datetime
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
import time
import os
import logging
import asyncio
from typing import Dict, List, Optional
from pathlib import Path
import backoff
import traceback
import argparse # Added argparse


class ErrorLogger:
    def __init__(self, cache_dir: str):
        """Initialize error logger with cache directory."""
        self.cache_dir = cache_dir
        self.error_log_path = os.path.join(cache_dir, 'error_log.txt')
        self.setup_logging()

    def setup_logging(self):
        """Set up logging configuration."""
        os.makedirs(self.cache_dir, exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(self.error_log_path)
            ]
        )
        self.logger = logging.getLogger(__name__)

    def log_error(self, error: Exception, context: str = ""):
        """Log error with stack trace and context."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        error_details = {
            'timestamp': timestamp,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context,
            'stack_trace': traceback.format_exc()
        }

        # Log to file
        with open(self.error_log_path, 'a') as f:
            f.write(f"\n{'=' * 50}\n")
            f.write(f"Error occurred at {timestamp}\n")
            f.write(f"Context: {context}\n")
            f.write(f"Type: {error_details['error_type']}\n")
            f.write(f"Message: {error_details['error_message']}\n")
            f.write(f"Stack Trace:\n{error_details['stack_trace']}\n")

        # Also log to console
        self.logger.error(f"Error in {context}: {str(error)}")
        return error_details


class ScriptGenerator:
    def __init__(self, config_file: str):
        """Initialize the ScriptGenerator with configuration."""
        try:
            # Changed base_dir calculation to be relative to the config file itself
            self.config_file_path = os.path.abspath(config_file)
            self.base_dir = os.path.dirname(self.config_file_path)
            self.config = self._load_config(self.config_file_path)
            # Ensure cache_dir path is resolved correctly before initializing logger
            cache_dir_path = self._get_abs_path(self.config.get('PATHS', 'cache_dir', fallback='./data/cache'))
            self.error_logger = ErrorLogger(cache_dir_path)
            self.validate_config()
            self.selectors = self._load_selectors()
            self.wait_times = self._load_wait_times()
            self.driver = None
            self._setup_directories()
        except Exception as e:
            # Use print for early init errors before logger is ready
            print(f"Initialization Error: {e}\n{traceback.format_exc()}")
            if hasattr(self, 'error_logger'):
                self.error_logger.log_error(e, "Initialization")
            raise

    def _get_abs_path(self, path: str) -> str:
        """Convert relative path to absolute path based on config file location."""
        if os.path.isabs(path):
            return path
        # Resolve relative paths based on the directory containing the config file
        return os.path.normpath(os.path.join(self.base_dir, path))

    def _setup_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        try:
            directories = [
                self._get_abs_path(self.config.get('PATHS', 'scripts_dir')),
                self._get_abs_path(self.config.get('PATHS', 'videos_dir')),
                self._get_abs_path(self.config.get('PATHS', 'cache_dir'))
            ]
            for directory in directories:
                Path(directory).mkdir(parents=True, exist_ok=True)
                self.error_logger.logger.info(f"Ensured directory exists: {directory}")
        except Exception as e:
            self.error_logger.log_error(e, "Directory Setup")
            raise

    @staticmethod
    def _load_config(config_file: str) -> configparser.ConfigParser:
        """Load configuration from file with error handling."""
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Configuration file not found: {config_file}")

        config = configparser.ConfigParser()
        try:
            config.read(config_file)
        except configparser.Error as e:
            raise ValueError(f"Error parsing configuration file {config_file}: {e}")

        # Add cache_dir default if not present under [PATHS]
        if not config.has_section('PATHS'):
             config.add_section('PATHS')
        if not config.has_option('PATHS', 'cache_dir'):
            config.set('PATHS', 'cache_dir', './data/cache')
            print(f"Warning: 'cache_dir' not found in [PATHS], defaulting to './data/cache'")

        return config

    def validate_config(self) -> None:
        """Validate configuration with detailed error messages."""
        try:
            required_sections = {
                'PATHS': ['scripts_dir', 'videos_dir', 'selectors_dir', 'wait_times_file', 'cache_dir'],
                'AI': ['provider', 'mode', 'prompt', 'chatgpt_url'],
                'VIDEO': ['provider', 'capcut_url', 'style', 'voice'],
                'YOUTUBE': ['privacy', 'category_id'],
                'BROWSER': ['type', 'headless', 'wait_timeout', 'page_load_timeout', 'data_browser_dir']
            }

            for section, fields in required_sections.items():
                if not self.config.has_section(section):
                    raise ValueError(f"Missing required section: [{section}]")

                for field in fields:
                    if not self.config.has_option(section, field):
                        # Provide default for data_browser_dir if missing, otherwise raise error
                        if section == 'BROWSER' and field == 'data_browser_dir':
                             default_browser_data_path = os.path.join(self.base_dir, 'browser_data')
                             self.config.set(section, field, default_browser_data_path)
                             self.error_logger.logger.warning(f"Missing field '{field}' in section '[{section}]'. Defaulting to '{default_browser_data_path}'")
                        else:
                             raise ValueError(f"Missing required field '{field}' in section '[{section}]'")

            # Validate browser type
            browser_type = self.config.get('BROWSER', 'type').lower()
            if browser_type not in ['chrome', 'firefox', 'edge']:
                 self.error_logger.logger.warning(f"Unsupported browser type '{browser_type}' specified. Defaulting to 'chrome'.")
                 self.config.set('BROWSER', 'type', 'chrome')

        except Exception as e:
            self.error_logger.log_error(e, "Config Validation")
            raise

    def _load_selectors(self) -> Dict:
        """Load selectors with error handling and validation."""
        try:
            # Construct path relative to config file location
            selectors_rel_path = os.path.join(
                self.config.get('PATHS', 'selectors_dir'),
                'selectors.json'
            )
            selectors_path = self._get_abs_path(selectors_rel_path)
            self.error_logger.logger.info(f"Loading selectors from: {selectors_path}")

            if not os.path.exists(selectors_path):
                raise FileNotFoundError(f"Selectors file not found at: {selectors_path}")

            with open(selectors_path, 'r', encoding='utf-8') as f:
                selectors = json.load(f)
            self._validate_selectors(selectors)
            return selectors
        except json.JSONDecodeError as e:
             self.error_logger.log_error(e, f"Error decoding JSON from {selectors_path}")
             raise ValueError(f"Invalid JSON in selectors file: {selectors_path}") from e
        except Exception as e:
            self.error_logger.log_error(e, "Loading Selectors")
            raise

    def _validate_selectors(self, selectors: Dict) -> None:
        """Validate that all required selectors are present."""
        try:
            # Only validate CHATGPT for now as others are not implemented
            required_providers = ['CHATGPT']
            # required_providers = ['CHATGPT', 'CAPCUT', 'YOUTUBE'] # Original
            for provider in required_providers:
                if provider not in selectors:
                    raise ValueError(f"Missing required provider '{provider}' in selectors")
                # Basic check for essential ChatGPT selectors
                if provider == 'CHATGPT':
                    if 'input_field' not in selectors[provider] or not selectors[provider]['input_field']:
                         raise ValueError(f"Missing 'input_field' selector for CHATGPT")
                    if 'send_button' not in selectors[provider] or not selectors[provider]['send_button']:
                         raise ValueError(f"Missing 'send_button' selector for CHATGPT")
                    if 'response' not in selectors[provider] or not selectors[provider]['response']:
                         raise ValueError(f"Missing 'response' selector for CHATGPT")
        except Exception as e:
            self.error_logger.log_error(e, "Selector Validation")
            raise

    def _load_wait_times(self) -> Dict:
        """Load wait times with validation."""
        try:
            wait_times_rel_path = self.config.get('PATHS', 'wait_times_file')
            wait_times_path = self._get_abs_path(wait_times_rel_path)
            self.error_logger.logger.info(f"Loading wait times from: {wait_times_path}")

            if not os.path.exists(wait_times_path):
                raise FileNotFoundError(f"Wait times file not found at: {wait_times_path}")

            with open(wait_times_path, 'r') as f:
                wait_times = json.load(f)
            self._validate_wait_times(wait_times)
            return wait_times
        except json.JSONDecodeError as e:
             self.error_logger.log_error(e, f"Error decoding JSON from {wait_times_path}")
             raise ValueError(f"Invalid JSON in wait times file: {wait_times_path}") from e
        except Exception as e:
            self.error_logger.log_error(e, "Loading Wait Times")
            raise

    def _validate_wait_times(self, wait_times: Dict) -> None:
        """Validate wait times configuration."""
        try:
            required_times = ['captcha_wait', 'post_captcha_wait']
            for time_key in required_times:
                if time_key not in wait_times:
                    raise ValueError(f"Missing required wait time: {time_key}")
                if not isinstance(wait_times[time_key], (int, float)) or wait_times[time_key] < 0:
                    raise ValueError(f"Invalid wait time value for {time_key}: must be a non-negative number")
        except Exception as e:
            self.error_logger.log_error(e, "Wait Times Validation")
            raise

    @backoff.on_exception(
        backoff.expo,
        (TimeoutException, WebDriverException),
        max_tries=3,
        on_giveup=lambda details: print(f"Browser setup failed after multiple retries: {details['exception']}")
    )
    async def setup_browser(self) -> None:
        """Set up the browser with retry mechanism."""
        try:
            browser_type = self.config.get('BROWSER', 'type').lower()
            self.error_logger.logger.info(f"Setting up browser: {browser_type}")

            options = uc.ChromeOptions()
            # Use absolute path for user data dir
            user_data_dir = self._get_abs_path(self.config.get('BROWSER', 'data_browser_dir'))
            self.error_logger.logger.info(f"Using browser data directory: {user_data_dir}")
            options.add_argument(f"--user-data-dir={user_data_dir}")
            options.add_argument("--start-maximized")
            # Add arguments to potentially improve stability in Docker/sandbox
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu') # Often needed for headless

            # *** Add binary location for Chromium in sandbox ***
            options.binary_location = '/usr/bin/chromium-browser'
            self.error_logger.logger.info(f"Set browser binary location to: {options.binary_location}")

            if self.config.getboolean('BROWSER', 'headless'):
                self.error_logger.logger.info("Running browser in headless mode")
                options.add_argument("--headless=new") # Use new headless mode

            # Ensure the directory exists
            Path(user_data_dir).mkdir(parents=True, exist_ok=True)

            # Specify driver executable path if needed (often automatic with uc)
            # driver_executable_path = '/path/to/chromedriver' # Example
            # self.driver = uc.Chrome(options=options, driver_executable_path=driver_executable_path)
            self.driver = uc.Chrome(options=options)

            page_load_timeout = int(self.config.get('BROWSER', 'page_load_timeout', fallback=30))
            self.driver.set_page_load_timeout(page_load_timeout)
            self.error_logger.logger.info(f"Page load timeout set to {page_load_timeout} seconds")

            self.error_logger.logger.info("Browser setup completed successfully")
        except WebDriverException as e:
             self.error_logger.log_error(e, f"WebDriverException during Browser Setup. Check ChromeDriver/Chrome compatibility and paths. Data dir: {user_data_dir}")
             raise
        except Exception as e:
            self.error_logger.log_error(e, "Browser Setup")
            raise

    async def find_element_by_xpath(self, xpaths: List[str], timeout: int = 10) -> Optional[object]:
        """Try multiple XPath selectors to find an element."""
        last_exception = None
        for xpath in xpaths:
            try:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.XPATH, xpath))
                )
                self.error_logger.logger.info(f"Element found using XPath: {xpath}")
                return element
            except (TimeoutException, NoSuchElementException) as e:
                last_exception = e
                self.error_logger.logger.warning(f"Element not found with XPath: {xpath}. Trying next...")
            except Exception as e:
                self.error_logger.log_error(e, f"Unexpected error finding element with XPath: {xpath}")
                raise # Re-raise unexpected errors

        # If loop finishes without finding element
        if last_exception:
             self.error_logger.log_error(last_exception, f"Element not found using any provided XPaths: {xpaths}")
        return None

    async def generate_script(self) -> Optional[str]:
        """Generate script using configured AI provider (currently only ChatGPT)."""
        try:
            provider = self.config.get('AI', 'provider').upper()
            if provider != 'CHATGPT':
                self.error_logger.logger.error(f"Unsupported AI provider configured: {provider}. Only CHATGPT is implemented.")
                return None

            prompt = self.config.get('AI', 'prompt')
            url = self.config.get('AI', 'chatgpt_url')
            wait_timeout = int(self.config.get('BROWSER', 'wait_timeout', fallback=10))

            self.error_logger.logger.info(f"Navigating to {url}")
            self.driver.get(url)
            # Increased sleep to allow potential Cloudflare checks/redirects
            await asyncio.sleep(self.wait_times.get('post_captcha_wait', 5))

            # Handle potential CAPTCHA or login prompts (basic wait)
            self.error_logger.logger.info("Waiting for potential CAPTCHA/login...")
            await asyncio.sleep(self.wait_times.get('captcha_wait', 10))

            # Find and interact with input field
            self.error_logger.logger.info("Locating input field...")
            input_field = await self.find_element_by_xpath(self.selectors[provider]['input_field'], wait_timeout)
            if not input_field:
                raise TimeoutException(f"Could not locate input field at {url} using selectors: {self.selectors[provider]['input_field']}")

            self.error_logger.logger.info("Sending prompt...")
            input_field.send_keys(prompt)
            await asyncio.sleep(1) # Small delay after typing

            # Find and click send button
            self.error_logger.logger.info("Locating send button...")
            send_button = await self.find_element_by_xpath(self.selectors[provider]['send_button'], wait_timeout)
            if not send_button:
                raise TimeoutException(f"Could not locate send button using selectors: {self.selectors[provider]['send_button']}")

            # Try clicking via JavaScript if direct click fails
            try:
                 send_button.click()
            except Exception as click_err:
                 self.error_logger.logger.warning(f"Direct click failed for send button: {click_err}. Trying JavaScript click.")
                 self.driver.execute_script("arguments[0].click();", send_button)

            self.error_logger.logger.info("Prompt sent. Waiting for response...")
            await asyncio.sleep(2) # Wait for response generation to start

            # Wait for response element to appear
            # Consider adding a check for 'response_loading' selector to wait until generation finishes
            response_element = await self.find_element_by_xpath(self.selectors[provider]['response'], wait_timeout * 3) # Longer timeout for response
            if not response_element:
                raise TimeoutException(f"Could not get response from AI using selectors: {self.selectors[provider]['response']}")

            self.error_logger.logger.info("Response element located. Extracting text...")
            response = response_element.text

            if not response or response.strip() == "":
                 self.error_logger.logger.warning("AI response element found but was empty.")
                 # Potentially add retry logic here or raise a specific error
                 return None

            # Save response
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            filename = f'script_{timestamp}.txt'
            scripts_dir = self._get_abs_path(self.config.get('PATHS', 'scripts_dir'))
            filepath = os.path.join(scripts_dir, filename)

            self.error_logger.logger.info(f"Saving script to: {filepath}")
            with open(filepath, 'w', encoding='utf-8') as file:
                file.write(response)

            self.error_logger.logger.info(f"Script generated and saved successfully.")
            return response

        except TimeoutException as e:
             self.error_logger.log_error(e, "Script Generation Timeout")
             # Capture screenshot on timeout
             self.capture_screenshot("timeout_error")
             raise
        except Exception as e:
            self.error_logger.log_error(e, "Script Generation")
            # Capture screenshot on general error
            self.capture_screenshot("general_error")
            raise

    def capture_screenshot(self, suffix: str = "error") -> None:
        """Captures a screenshot of the current browser window."""
        if not self.driver:
            return
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"screenshot_{suffix}_{timestamp}.png"
            cache_dir = self._get_abs_path(self.config.get('PATHS', 'cache_dir'))
            filepath = os.path.join(cache_dir, filename)
            self.driver.save_screenshot(filepath)
            self.error_logger.logger.info(f"Screenshot saved to {filepath}")
        except Exception as e:
            self.error_logger.log_error(e, "Capture Screenshot")

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.driver:
            try:
                self.driver.quit()
                self.error_logger.logger.info("Browser closed successfully")
            except Exception as e:
                self.error_logger.log_error(e, "Cleanup")


async def main(config_path: str):
    """Main execution function."""
    script_gen = None
    try:
        # Use the provided config_path
        script_gen = ScriptGenerator(config_path)
        await script_gen.setup_browser()
        generated_script = await script_gen.generate_script()
        if generated_script:
             print("\n--- Generated Script ---")
             print(generated_script)
             print("------------------------\n")
        else:
             print("Script generation failed. Check logs for details.")

    except FileNotFoundError as e:
         print(f"Error: Configuration file not found at {config_path}. {e}")
    except ValueError as e:
         print(f"Error: Invalid configuration or selectors. {e}")
    except Exception as e:
        print(f"An unexpected error occurred during main execution: {e}")
        # Log error if logger was initialized
        if script_gen and hasattr(script_gen, 'error_logger'):
            script_gen.error_logger.log_error(e, "Main Execution")
        else:
            # Fallback basic logging if logger failed
            print(f"Fatal error (logger might not be available): {str(e)}\n{traceback.format_exc()}")
    finally:
        if script_gen:
            await script_gen.cleanup()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate script using AI and browser automation.")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_config_path = os.path.join(script_dir, 'config.ini')
    parser.add_argument(
        '--config',
        type=str,
        default=default_config_path,
        help=f"Path to the configuration file (default: {default_config_path})"
    )
    args = parser.parse_args()

    # Run the main async function with the specified or default config path
    asyncio.run(main(args.config))

