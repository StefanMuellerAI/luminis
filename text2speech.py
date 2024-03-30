from pathlib import Path
import openai
import random
import os
from dotenv import load_dotenv

load_dotenv()

# Setze hier deinen OpenAI API-Key
openai.api_key = os.getenv("OPENAI_API_KEY")

if not os.path.exists("./speech"):
    os.makedirs("./speech")

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
        return speech_file_path
    except Exception as e:
        # Gib bei einem Fehler den Pfad und die Fehlermeldung zurück
        return None, str(e)
def clear_speech_directory(directory="./speech"):
    # Überprüfe, ob der angegebene Pfad existiert und ein Verzeichnis ist
    if os.path.exists(directory) and os.path.isdir(directory):
        # Iteriere über alle Dateien im Verzeichnis
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            try:
                # Überprüfe, ob es sich bei dem Pfad um eine Datei handelt (und nicht um ein Unterverzeichnis)
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)  # Entferne die Datei
                elif os.path.isdir(file_path):
                    # Optional: Hier könntest du eine rekursive Löschfunktion für Unterverzeichnisse aufrufen
                    pass
            except Exception as e:
                print(f"Fehler beim Löschen der Datei {file_path}. Grund: {e}")
