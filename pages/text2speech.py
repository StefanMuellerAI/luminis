from pathlib import Path
import openai
import random
import os
from dotenv import load_dotenv
import streamlit as st
from home import add_menu

load_dotenv()

# Setze hier deinen OpenAI API-Key
openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(
    page_title="Luminis - KI-Labor und Lernplattform",
    page_icon="🥼",
    layout="wide",
    initial_sidebar_state="expanded"
)


def create_speech_from_text(text, voice):
    try:
        speech_file = random.randint(100000, 999999)
        speech_file_path = Path(__file__).parent / f"speech/{speech_file}.mp3"
        response = openai.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )
        response.stream_to_file(speech_file_path)
        return speech_file_path, None  # Rückgabe des Pfades und None für den Fehler
    except Exception as e:
        # Gib bei einem Fehler None und die Fehlermeldung zurück
        return None, str(e)

def clear_speech_directory(directory="/speech"):
    if os.path.exists(directory) and os.path.isdir(directory):
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Fehler beim Löschen der Datei {file_path}. Grund: {e}")

st.title("Text2Speech")
st.subheader("Konvertieren Sie Ihren Text in eine Sprachausgabe.")
col1, col2 = st.columns([1, 1])
with col1:
    user_input = st.text_area("Geben Sie hier Ihren Text ein:", "Hallo Welt!")
    voice = st.selectbox("Wählen Sie eine Stimme:", ["alloy", "echo", "fable", "onyx", "nova", "shimmer"])
    if st.button("Sprachausgabe generieren!"):
        with col2:
            with st.spinner('Generiere Sprachausgabe...'):
                speech_path, error = create_speech_from_text(user_input, voice)
                if speech_path and speech_path.is_file():
                    # Lösche den Inhalt des Verzeichnisses `speech` direkt nach der Erstellung der Datei
                    clear_speech_directory()
                    st.audio(str(speech_path), format='audio/mp3')
                elif error:
                    st.error(f"Ein Fehler ist aufgetreten: {error}")
                else:
                    st.error("Ein unbekannter Fehler ist aufgetreten.")

# Fügen Sie Ihre Funktion zum Hinzufügen des Menüs hier ein
add_menu()
