# 🚀 Smart Automation Tool - YouTube Content Creator

A powerful Python automation tool that creates complete YouTube content pipelines from a single script file. Generate AI-powered scripts, create videos with CapCut, and upload to YouTube automatically.

## ✨ Features

- **🤖 AI-Powered Script Generation** - OpenAI, Grok, Gemini support
- **🎬 Automated Video Creation** - CapCut integration with anime-style videos
- **📤 YouTube Upload Automation** - Complete upload pipeline with scheduling
- **🔄 Flexible Workflows** - 6 different execution modes
- **🧠 Smart Element Finding** - Multiple selector strategies with auto-fallback
- **🌐 Multi-Browser Support** - Chrome/Edge with automatic switching
- **📊 Batch Processing** - Process multiple topics from files
- **📝 Comprehensive Logging** - Detailed logs and progress tracking

## 🛠️ Requirements

### System Requirements
- **OS**: Windows 10/11
- **Python**: 3.10+
- **Browsers**: Chrome and/or Edge installed

### Python Dependencies
```bash
pip install selenium openai requests configparser pathlib
```

### Browser Drivers
Download and add to PATH:
- [ChromeDriver](https://chromedriver.chromium.org/)
- [EdgeDriver](https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/)

## 📁 File Structure

```
project_folder/
├── automation_tool.py      # Main script (single file)
├── customisation.ini       # User configuration
├── selectors.json         # Element selectors
├── uploaded_videos.ini    # Upload log (auto-generated)
├── automation.log         # Execution log (auto-generated)
└── videos/               # Generated videos folder
```

## 🚀 Quick Start

### 1. Initial Setup
```bash
# Create configuration files
python automation_tool.py --setup

# Check configuration locations
python automation_tool.py --config
```

### 2. Configure Settings
Edit `customisation.ini`:
```ini
[AI_SETTINGS]
provider = openai
openai_api_key = your_actual_api_key_here

[YOUTUBE_SETTINGS]
channel_email = your_youtube_email@gmail.com
channel_password = your_youtube_password
```

### 3. Run Interactive Mode
```bash
python automation_tool.py --interactive
```

## 🔄 Workflow Modes

| Mode | Description | Usage |
|------|-------------|-------|
| `full_auto` | Complete pipeline: Script → Video → Upload | `--mode full_auto --topic "AI Facts"` |
| `script_only` | Generate script only | `--mode script_only --topic "Coding Tips"` |
| `video_only` | Generate script + create video | `--mode video_only --topic "Tech News"` |
| `upload_only` | Upload existing video | `--mode upload_only --video-path "./video.mp4"` |
| `script_and_video` | Generate script + create video | `--mode script_and_video --topic "Tutorial"` |
| `video_and_upload` | Create video + upload | `--mode video_and_upload --topic "Review"` |

## 💻 Command Line Usage

### Interactive Mode
```bash
python automation_tool.py --interactive
python automation_tool.py -i
```

### Direct Execution
```bash
# Full automation
python automation_tool.py --mode full_auto --topic "Amazing AI Facts"

# Script generation only
python automation_tool.py --mode script_only --topic "Python Tutorial"

# Upload existing video
python automation_tool.py --mode upload_only --video-path "./my_video.mp4"
```

### Batch Processing
```bash
# Create topics.txt with one topic per line
echo "AI in Healthcare" > topics.txt
echo "Future of Technology" >> topics.txt
echo "Programming Best Practices" >> topics.txt

# Run batch processing
python automation_tool.py --batch topics.txt --mode full_auto
```

## ⚙️ Configuration Guide

### AI Settings (`customisation.ini`)
```ini
[AI_SETTINGS]
provider = openai                    # AI provider: openai, grok, gemini
openai_api_key = sk-your-key-here   # Your OpenAI API key
max_words = 300                     # Script length limit
language = English                  # Content language
```

### Video Settings
```ini
[VIDEO_SETTINGS]
style = anime                       # Video style: anime, realistic, cartoon
resolution = 1080p                  # Resolution: 720p, 1080p, 4k
voice_type = female                 # Voice: male, female, child, robot
duration = 60                       # Video duration (seconds)
background_music = true             # Add background music
captions = true                     # Add captions
```

### YouTube Settings
```ini
[YOUTUBE_SETTINGS]
channel_email = your@email.com      # YouTube account email
channel_password = your_password    # YouTube account password
privacy = public                    # Privacy: public, unlisted, private
default_tags = AI, automation       # Default video tags
```

### Browser Settings
```ini
[BROWSER_SETTINGS]
headless_mode = false              # Run browser in background
primary_browser = chrome           # Primary: chrome, edge
wait_timeout = 30                  # Element wait timeout (seconds)
retry_attempts = 3                 # Retry count for failed operations
```

## 🧠 Smart Features

### Flexible Element Finding
The tool uses multiple strategies to find web elements:
- XPath selectors
- CSS selectors  
- ID selectors
- Class selectors
- Multiple fallback options per element

### Automatic Browser Switching
- Starts with primary browser (Chrome)
- Automatically switches to Edge if Chrome fails
- Handles browser crashes and connection issues

### Robust Error Handling
- Automatic retries with exponential backoff
- Screenshot capture on errors (when debug enabled)
- Detailed logging with timestamps
-