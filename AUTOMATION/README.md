# AI Content Automation Tool

## Purpose

This tool is designed to automate various aspects of content creation, including script generation using AI language models, video creation (interfacing with CapCut), and potentially video uploading. The goal is to operate in a fully automated mode based on external configuration files, with no interactive user input required during runtime.

## Current Status & Limitations (Important!)

**Due to persistent technical limitations encountered with the development tools, several key components of this script could not be fully implemented or refactored as originally planned. As a result, the script is NOT fully functional according to the complete specification.**

Specifically:
*   **YouTube API Upload (`YouTubeUploader`):** The refactoring of the `YouTubeUploader` class to use the YouTube Data API v3 was **blocked**. The existing Selenium-based uploader may still be present but is not aligned with the new non-interactive, API-first approach, or the class might be non-functional. Automated YouTube uploading is therefore considered **non-operational**.
*   **Orchestration Logic (`AutomationRunner`):** Modifications to the main `AutomationRunner` class to fully align with all new configurations and component changes were **partially blocked**. While some adaptations were made, its ability to manage the end-to-end workflow, particularly regarding video output paths and YouTube uploads, is compromised.
*   **CapCut Video Output Path (`CapcutCreator`):** Attempts to make the video output path in `CapcutCreator` fully configurable and robustly handled were **blocked**. The script may not reliably save CapCut-generated videos to the user-specified directory.

The components related to configuration management (`ConfigManager`), browser profile handling (`BrowserManager`), and script generation via AI (ChatGPT browser, Grok browser, Gemini API - `ScriptGenerator`) have been updated according to the new design. However, without the core orchestration and upload functionalities working as intended, the tool's overall utility is severely limited.

## Setup & Configuration

The tool is configured primarily through `customisation.ini` and files in the `Data/` directory.

### 1. `customisation.ini`

This file, located in the same directory as `automation_tool.py`, controls all major aspects of the tool.

*   **`[AI_SETTINGS]`**:
    *   `provider`: Specifies the AI provider for script generation. Options:
        *   `gemini`: Uses the Gemini API.
        *   `openai`: Uses browser-based automation for ChatGPT.
        *   `grok`: Uses browser-based automation for Grok.
        *   `openai_api` (if API version of OpenAI was to be kept separately)
    *   `openai_api_key`: Your OpenAI API key (if using an API-based OpenAI option).
    *   `grok_api_key`: Your Grok API key (if Grok had an API option; currently browser-based).
    *   `gemini_api_key`: Your Gemini API key. **Required if `provider = gemini`**.
    *   `default_prompt`: The main prompt/topic for script generation.
    *   `max_words`: Target word count for the generated script.
    *   `language`: Language for the script (e.g., `English`).

*   **`[VIDEO_METADATA]`**:
    *   `title`: The title for your video.
    *   `description`: The video description.
    *   `tags`: Comma-separated list of video tags.

*   **`[VIDEO_SETTINGS]`**: (Primarily for CapCut or other video tools)
    *   `style`: Video style (e.g., `anime`, `realistic`).
    *   `resolution`: Video resolution (e.g., `1080p`).
    *   `voice_type`: Voice type for text-to-speech.
    *   `duration`: Target video duration in seconds.
    *   `background_music`: `true` or `false`.
    *   `captions`: `true` or `false`.

*   **`[YOUTUBE_SETTINGS]`**: (Intended for the YouTube API uploader)
    *   `privacy`: Video privacy status (`public`, `private`, `unlisted`).
    *   `schedule_upload`: `true` or `false`.
    *   `upload_time`: Time to schedule upload (e.g., `18:00`), if `schedule_upload = true`.
    *   `upload_date`: Date to schedule upload (e.g., `YYYY-MM-DD`), if `schedule_upload = true`.
    *   `categoryId`: YouTube video category ID (e.g., `22` for People & Blogs).

*   **`[BROWSER_SETTINGS]`**:
    *   `headless_mode`: `true` or `false` for browser automation.
    *   `primary_browser`: Preferred browser (`chrome`, `edge`).
    *   `secondary_browser`: Fallback browser.
    *   `wait_timeout`: Default wait timeout in seconds for Selenium.
    *   `retry_attempts`: Retry attempts for Selenium actions.
    *   `page_load_timeout`: Page load timeout for Selenium.
    *   `browser_user_data_path`: **Crucial for persistent logins.** Absolute path to your browser's user data directory (e.g., `C:/Users/YourUser/AppData/Local/Google/Chrome/User Data` or `/home/user/.config/google-chrome/Default`).

*   **`[PLATFORM_URLS]`**:
    *   `chatgpt_url`: URL for ChatGPT.
    *   `grok_url`: URL for Grok.
    *   `capcut_url`: URL for CapCut AI Creator.

*   **`[PATHS]`**:
    *   `data_base_path`: Path to the `Data/` directory (relative to the script, e.g., `Data/`).
    *   `video_output_path`: Directory to save generated videos (e.g., `videos/`).
    *   `script_output_path`: Directory to save generated scripts (e.g., `Scripts/`).
    *   `log_output_path`: Path for the log file (e.g., `logs/automation.log`).

*   **`[WORKFLOW_SETTINGS]`**:
    *   `execution_mode`: Defines the workflow (e.g., `full_auto`, `script_only`). The script runs this mode automatically.
    *   `auto_retry`: `true` or `false`.
    *   `save_progress`: `true` or `false` (for `plan_state.json`).
    *   `notification_enabled`: `true` or `false`.

*   **`[ADVANCED_SETTINGS]`**:
    *   `action_delay`: Delay in seconds between some browser actions.
    *   `max_processes`: (If applicable for concurrency).
    *   `debug_mode`: `true` or `false`.
    *   `screenshot_on_error`: `true` or `false`.

### 2. `Data/` Directory

This directory, specified by `PATHS.data_base_path` in `customisation.ini`, holds key data files:

*   **`selectors.json`**: Contains CSS/XPath selectors for web page elements used in browser automation (CapCut, ChatGPT, Grok).
*   **`api.json`**:
    *   Stores API keys not suitable for `customisation.ini`.
    *   Crucially, for YouTube API uploads (if they were working), this would store the **OAuth 2.0 client secrets JSON content under the `"web"` key**, obtained from Google Cloud Console.
    *   May also store other API keys like `gemini_api_key`, `openai_api_key`, `grok_api_key` as an alternative to `customisation.ini` (current implementation uses `customisation.ini` for these). The `ConfigManager` was set up to create this with placeholders for various keys.
*   **`token.json`**: Intended to store OAuth 2.0 access and refresh tokens for the YouTube API, allowing persistent authorization.
*   **`plan_state.json`**: For tracking execution state or caching (if `WORKFLOW_SETTINGS.save_progress = true`).
*   **`uploaded_videos.ini`**: A log of videos that have been (or attempted to be) uploaded, to prevent duplicates.

## Running the Tool

Once configured, the tool is intended to be run as a simple Python script:

```bash
python AUTOMATION/automation_tool.py
```

It will read `customisation.ini` and execute the mode specified in `WORKFLOW_SETTINGS.execution_mode`. No command-line arguments are supported.

## Dependencies

The script relies on several Python packages, including:
*   `selenium`
*   `google-api-python-client`
*   `google-auth-oauthlib`
*   `google-generativeai` (for Gemini)
*   `openai` (if OpenAI API client is used)

Ensure these are installed in your Python environment (e.g., via `pip install -r requirements.txt` if a requirements file were provided).

```
