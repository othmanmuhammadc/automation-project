import json
import os
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from modules.utils import log, retry


@retry(max_attempts=3)
def upload_video(video_path, script_path, youtube_config):
    with open(script_path, 'r') as f:
        script_data = json.load(f)

    try:
        # Authenticate with YouTube API
        youtube = build('youtube', 'v3', developerKey=youtube_config['api_key'])

        # Create video metadata
        body = {
            'snippet': {
                'title': script_data['TITLE'],
                'description': script_data['DESCRIPTION'],
                'tags': script_data['KEYWORDS'],
                'categoryId': youtube_config['category_id']
            },
            'status': {
                'privacyStatus': youtube_config['privacy']
            }
        }

        # Upload video
        insert_request = youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=video_path
        )

        response = insert_request.execute()
        log.info(f"Video uploaded successfully: {response}")

    except HttpError as e:
        log.error(f"Error uploading video: {e}")
        raise







    