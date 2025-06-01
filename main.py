import os
import json
import logging
from modules.script_generator import generate_script
from modules.video_creator import create_video
from modules.youtube_uploader import upload_video
from modules.utils import setup_logging


def main():
    # Setup logging
    setup_logging()

    # Load configuration
    config = json.load(open('config.ini'))

    # Generate script
    script_path = os.path.join(config['PATHS']['scripts_dir'], 'script.json')
    generate_script(config['AI']['prompt'], config['AI']['chatgpt_url'], config['selectors'], script_path)

    # Create video
    video_path = os.path.join(config['PATHS']['videos_dir'], 'output.mp4')
    create_video(script_path, config['VIDEO']['capcut_url'], config['selectors'], config['VIDEO'], video_path)

    # Upload video to YouTube
    upload_video(video_path, script_path, config['YOUTUBE'])


if __name__ == '__main__':
    main()




