import requests
import json
import os
import time
from dotenv import load_dotenv
import streamlit as st
from home import add_menu

load_dotenv()

HEYGEN_API_KEY = os.getenv('HEYGEN_API_KEY')

st.set_page_config(
    page_title="Luminis - KI-Labor und Lernplattform",
    page_icon="🥼",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

st.title('Text2Video')
st.subheader('Generieren Sie Videos aus Textbeschreibungen inkl. Voiceover.')
col1, col2 = st.columns([1, 1])
with col1:
    avatar = st.selectbox('Avatar wählen:', ['Avatar1', 'Avatar2', 'Avatar3'])
    voice = st.selectbox('Stimme wählen:', ['Voice1', 'Voice2', 'Voice3'])
    background = st.color_picker('Hintergrundfarbe:', '#00f900')
    description = st.text_area('Beschreibung des Videos', placeholder='Hier kommt der Text hin, der vorgetragen werden soll.')
    if st.button('Video generieren!'):
        with col2:
            with st.spinner('Video wird erstellt... Bitte warten.'):
                video_id = create_video(description)
                status, video_url = check_video_status(video_id)
                if status == 'completed':
                    st.video(video_url)
                elif status == 'failed':
                    st.error('Videoerstellung fehlgeschlagen.')
    st.divider()
    st.subheader('Video in diverse Sprachen übersetzen!')
    target_url = st.text_input('Ziel-URL:', 'https://www.example.com')
    target_language = st.selectbox('Sprache wählen:', ['Englisch', 'Spanisch', 'Französisch'])
    if st.button('Video übersetzen!'):
        video_id = create_video(description)
        with col2:
            if video_id:
                with st.spinner('Video wird übersetzt... Bitte warten.'):
                    status, video_url = check_video_status(video_id)
                    if status == 'completed':
                        st.video(video_url)
                    elif status == 'failed':
                        st.error('Videübersetzung fehlgeschlagen.')

add_menu()