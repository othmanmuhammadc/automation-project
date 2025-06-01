# SMART-AUTOMATION Tool

**Version:** 5.3

## Overview

SMART-AUTOMATION is a Python-based tool designed to fully automate a YouTube content creation pipeline. It handles text generation (using AI APIs or browser automation), video creation (currently via CapCut browser automation), and uploading the final video to YouTube (using the YouTube Data API v3).

The tool is designed for unattended operation, reading all necessary configurations from external files (`.ini` and `.json`). It incorporates robust error handling, configuration validation, and automatic browser driver management.

This version includes significant improvements in browser handling, utilizing `webdriver-manager` for automatic ChromeDriver/EdgeDriver installation and management, resolving previous browser initialization issues.

## Features

*   **Automated Script Generation:**
    *   Supports Google Gemini API (`gemini`).
    *   Supports browser automation for ChatGPT (`chatgpt_browser`) and Grok (`grok_browser`).
    *   Uses configurable prompts (`customisation.ini`).
    *   Parses generated text for script, title, description, and keywords.
*   **Automated Video Creation:**
    *   Supports CapCut web interface (`capcut_browser`) via Selenium.
    *   Automates style selection, voice selection, script input, generation, captioning, and export.
    *   Configurable export settings (resolution, framerate) via `customisation.ini`.
    *   Handles video download automatically.
*   **Automated YouTube Upload:**
    *   Uses YouTube Data API v3 for uploading.
    *   Handles OAuth 2.0 authentication (requires initial manual setup for credentials).
    *   Uses metadata (title, description, tags) parsed from the generated script.
    *   Configurable privacy status, category ID, and subscriber notification via `customisation.ini`.
    *   Logs uploaded videos to `uploaded_videos.ini`.
*   **Configuration Driven:**
    *   All settings managed through external files (`customisation.ini`, `api.json`, `selectors.json`).
    *   Strict configuration validation on startup.
*   **Robust Browser Management:**
    *   Uses `webdriver-manager` to automatically download and manage appropriate WebDriver executables (ChromeDriver, EdgeDriver).
    *   Supports connecting to an existing browser instance via remote debugging port (optional).
    *   Includes fallback mechanisms and retries for browser operations.
    *   Supports headless mode.
*   **Logging:**
    *   Detailed logging to both console and a file (`log_file` path configured in `customisation.ini`).
    *   Includes timestamps, log levels, and informative messages.
    *   Takes screenshots on specific browser errors.

## Prerequisites

*   Python 3.x
*   Google Chrome or Microsoft Edge browser installed.
*   Access to the AI provider (API key for Gemini, or logged-in browser session for ChatGPT/Grok).
*   Access to CapCut web interface (potentially requires login).
*   Google Cloud Project with YouTube Data API v3 enabled.
*   OAuth 2.0 Client ID credentials (for Desktop application type) downloaded as a JSON file (required for YouTube upload).

## Installation

1.  **Clone or Download:** Obtain the project files.
    ```bash
    # If using Git (replace with actual repository URL if available)
    # git clone <repository_url>
    # cd SMART-AUTOMATION/smart_automation_project

    # If using the provided ZIP, navigate into the extracted folder:
    cd /path/to/SMART-AUTOMATION/smart_automation_project
    ```
2.  **Install Dependencies:** Install the required Python packages using pip.
    ```bash
    pip install -r requirements.txt
    ```
    This will install `selenium`, `webdriver-manager`, `google-generativeai`, `google-auth-oauthlib`, `google-api-python-client`, and `configparser`.

## Configuration

All configuration is managed through files within the project directory, primarily in the `Data` sub-directory.

**IMPORTANT:** Replace ALL placeholder values (like `"YOUR_API_KEY"`, `"YOUR_URL"`, etc.) with your actual information.

1.  **`customisation.ini`:** Main configuration file.
    *   `[PATHS]`: Define absolute or relative paths for scripts, videos, downloads, logs, and the uploaded videos log.
    *   `[AI_SETTINGS]`: Set the `provider` (e.g., `gemini`, `chatgpt_browser`), `ai_prompt`, and provider-specific URLs if using browser automation.
    *   `[VIDEO_SETTINGS]`: Set the `provider` (`capcut_browser`), `capcut_url`, and desired CapCut style, voice, resolution, format, and framerate.
    *   `[YOUTUBE_SETTINGS]`: Configure video `privacy_status` (`public`, `private`, `unlisted`), `category_id` (numeric ID from YouTube), and `notify_subscribers` (`true` or `false`).
    *   `[BROWSER_SETTINGS]`: Set `primary_browser` (`chrome` or `edge`), `user_data_dir` (optional, path to browser profile), `wait_timeout`, `retry_attempts`, `page_load_timeout`, `headless_mode` (`true` or `false`), and `debugger_port` (optional, for connecting to an existing browser).

2.  **`Data/api.json`:** API keys and YouTube credentials configuration.
    *   `gemini`: Contains `api_key` if using the Gemini provider.
    *   `youtube`: Contains paths to `credentials_file` (the token file generated after first auth, e.g., `token.json`) and either:
        *   `client_secrets_file`: Path to your downloaded Google OAuth 2.0 client secrets JSON file.
        *   `client_secrets_config`: The *entire content* of your client secrets JSON file embedded directly.
        *(Note: Use only one of `client_secrets_file` or `client_secrets_config`)*

3.  **`Data/selectors.json`:** CSS or XPath selectors for browser automation.
    *   Contains sections for `chatgpt`, `grok`, and `capcut`.
    *   These selectors identify elements on the respective websites (input fields, buttons, response areas, etc.).
    *   **These may need frequent updates** if the target websites change their layout.

4.  **`Data/token.json` (Generated):** Stores the YouTube API OAuth 2.0 credentials after the first successful authentication. You need to generate this initially.

5.  **`Data/uploaded_videos.ini` (Generated):** Logs details of successfully uploaded videos.

### Initial YouTube Authentication

The tool requires pre-authorized credentials to upload videos non-interactively. You need to run a one-time manual authentication process:

1.  Ensure your `Data/api.json` is configured with your `client_secrets_file` path or `client_secrets_config`.
2. Create a small Python script (e.g., `authenticate_youtube.py`) in the same directory as `automation_tool.py` with the following content (adjust paths if needed):

   ```python
   import json
   from pathlib import Path
   from google_auth_oauthlib.flow import InstalledAppFlow

   # --- Configuration ---
   API_CONFIG_PATH = Path("api.json")
   SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
   # --- End Configuration ---

   def get_client_config():
       if not API_CONFIG_PATH.is_file():
           print(f"Error: API config file not found at {API_CONFIG_PATH}")
           return None
       try:
           with open(API_CONFIG_PATH, 'r') as f:
               api_conf = json.load(f)
           youtube_conf = api_conf.get("youtube", {})
           embedded_secrets = youtube_conf.get("client_secrets_config")
           secrets_file_path_str = youtube_conf.get("client_secrets_file")

           if embedded_secrets and isinstance(embedded_secrets, dict):
               print("Using embedded client secrets.")
               return embedded_secrets
           elif secrets_file_path_str:
               # Resolve relative path if needed (assuming script runs from project root)
               secrets_file_path = Path(secrets_file_path_str)
               if not secrets_file_path.is_absolute():
                    # Assumes Data/api.json is relative to script dir if path is relative
                    base_dir = Path(__file__).parent
                    secrets_file_path = (base_dir / secrets_file_path).resolve()

               if secrets_file_path.is_file():
                   print(f"Using client secrets file: {secrets_file_path}")
                   return str(secrets_file_path)
               else:
                   print(f"Error: Client secrets file not found at {secrets_file_path}")
                   return None
           else:
               print("Error: No client secrets configuration found in api.json")
               return None
       except Exception as e:
           print(f"Error reading API config: {e}")
           return None

   client_config = get_client_config()
   if not client_config:
       exit(1)

   try:
       if isinstance(client_config, dict):
           flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
       else: # It's a path string
           flow = InstalledAppFlow.from_client_secrets_file(client_config, SCOPES)

       print("Starting local server for authentication...")
       creds = flow.run_local_server(port=0)
       print("Authentication successful!")

       # Save the credentials
       creds_path_str = None
       try:
           with open(API_CONFIG_PATH, 'r') as f:
               api_conf = json.load(f)
           creds_path_str = api_conf.get("youtube", {}).get("credentials_file")
       except Exception:
           pass # Ignore errors reading path here

       if not creds_path_str:
            creds_path_str = "Data/token.json" # Default if not specified
            print(f"Warning: 'credentials_file' not found in api.json, saving to default: {creds_path_str}")

       creds_path = Path(creds_path_str)
       if not creds_path.is_absolute():
            base_dir = Path(__file__).parent
            creds_path = (base_dir / creds_path).resolve()

       creds_path.parent.mkdir(parents=True, exist_ok=True)
       with open(creds_path, 'w') as token_file:
           token_file.write(creds.to_json())
       print(f"Credentials saved to: {creds_path}")

   except Exception as e:
       print(f"An error occurred during authentication: {e}")

   ```
3.  Run this script from your terminal within the `smart_automation_project` directory:
    ```bash
    python authenticate_youtube.py
    ```
4.  Follow the instructions in your browser to authorize the application.
5.  Once complete, a `token.json` file (or the name specified in `api.json` under `youtube.credentials_file`) will be created containing your credentials. The main `automation_tool.py` can now use this file.

## Usage

Once configured, run the main script from the `smart_automation_project` directory:

```bash
python automation_tool.py
```

The tool will execute the following steps based on your configuration:

1.  **Load & Validate Config:** Reads `.ini` and `.json` files, validates settings, and resolves paths.
2.  **Initialize Browser (if needed):** Sets up Selenium WebDriver using `webdriver-manager` or connects via debugger port.
3.  **Generate Script:** Uses the configured AI provider (API or Browser) to generate text containing the script, title, description, and keywords.
4.  **Save & Parse Script:** Saves the generated text and parses out the metadata.
5.  **Create Video:** Uses the configured video provider (CapCut Browser) to generate a video based on the script text.
6.  **Upload Video:** Uploads the generated video to YouTube using the parsed metadata and API credentials.
7.  **Cleanup:** Closes the browser (if launched by the script).

Monitor the console output and the log file (specified in `customisation.ini`) for progress and potential errors.

## Troubleshooting

*   **Configuration Errors:** The tool performs strict validation on startup. Check the log file for specific error messages indicating missing files, sections, keys, or placeholder values.
*   **Browser Automation Issues:**
    *   **Selectors:** Websites change frequently. If browser automation fails (e.g., cannot find buttons, input fields), the selectors in `Data/selectors.json` likely need updating. Use browser developer tools (Inspect Element) to find the new CSS selectors or XPaths.
    *   **WebDriver:** `webdriver-manager` should handle driver compatibility. If you encounter `SessionNotCreated` errors, ensure your Chrome/Edge browser is up-to-date. Check `webdriver-manager` logs (usually in `~/.wdm/`) for download issues.
    *   **Login/CAPTCHA:** Browser automation may fail if the target website requires login or presents CAPTCHAs. Consider using the `user_data_dir` setting in `customisation.ini` to point to a browser profile where you are already logged in. Alternatively, use the `debugger_port` option to connect to a browser you manually prepared.
*   **API Errors:**
    *   **Gemini:** Ensure your API key is correct and has not expired. Check for billing issues or quota limits in your Google Cloud project.
    *   **YouTube:** Ensure the YouTube Data API v3 is enabled. Verify your OAuth credentials (`client_secrets` and `token.json`) are correct and valid. Refresh the `token.json` if you encounter authorization errors (run `authenticate_youtube.py` again).
*   **CapCut Issues:** CapCut automation can be brittle. Ensure the URL is correct and selectors match the current interface. Generation and export can take time; check timeouts in `customisation.ini` (`wait_timeout`, `page_load_timeout`) and potentially increase them if needed.

## Contributing

(Optional: Add guidelines if you intend for others to contribute).

## License

(Optional: Specify the license, e.g., MIT License, Apache 2.0, etc.).


