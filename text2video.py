import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

HEYGEN_API_KEY = os.getenv('HEYGEN_API_KEY')
def create_video(text):
    url = 'https://api.heygen.com/v2/video/generate'
    headers = {
        'X-Api-Key': HEYGEN_API_KEY,
        'Content-Type': 'application/json',
    }
    data = {
      "video_inputs": [
        {
          "character": {
            "type": "avatar",
            "avatar_id": "Daisy-inskirt-20220818",
            "avatar_style": "normal"
          },
          "voice": {
            "type": "text",
            "input_text": text,
            "voice_id": "2d5b0e6cf36f460aa7fc47e3eee4ba54"
          },
          "background": {
            "type": "color",
            "value": "#008000"
          }
        }
      ],
      "dimension": {
        "width": 1280,
        "height": 720
      },
      "aspect_ratio": "16:9",
      "test": True
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    print(response.json()["error"]["message"])
    if response.status_code == 200:
        video_id = response.json()["data"]["video_id"]
        return video_id
    return None


def check_video_status(video_id):
    url = f'https://api.heygen.com/v1/video_status.get?video_id={video_id}'
    headers = {'X-Api-Key': HEYGEN_API_KEY}

    while True:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            status = response.json().get('data', {}).get('status', '')
            if status == 'completed':
                video_url = response.json()["data"]["video_url"]
                return status, video_url
            elif status == 'failed':
                return status

        time.sleep(30)  # Warte für 30 Sekunden vor dem nächsten Versuch