from openai import OpenAI
from dotenv import load_dotenv
import requests
import os
import base64
import random

load_dotenv()

client_openai = OpenAI()
stability_api_key = os.getenv("STABILITY_API_KEY")

def create_dalle_image(description, size):

    try:
        response = client_openai.images.generate(
            model="dall-e-3",
            prompt=f"{description}",
            size=f"{size}",
            quality="standard",
            n=1
        )
        image_url = response.data[0].url
    except Exception as e:
        print(e)
        image_url = None
    return image_url


import os
import random
import requests
import base64
from dotenv import load_dotenv

# Lade Variablen aus der .env-Datei
load_dotenv()

# Der API-Schlüssel wird hier geladen
stability_api_key = os.getenv("STABILITY_API_KEY")

def create_stability_image(description, anti_description, steps, style_preset, size, cfg_scale):
    if not os.path.exists("./images"):
        os.makedirs("./images")
    image_id = random.randint(100000, 999999)

    parts = size.split("x")
    size_width = int(parts[0])
    size_height = int(parts[1])

    try:
        url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
        body = {
            "steps": steps,
            "style_preset": style_preset,
            "width": size_width,
            "height": size_height,
            "seed": 0,
            "cfg_scale": cfg_scale,
            "samples": 1,
            "text_prompts": [
                {"text": description, "weight": 1},
                {"text": anti_description, "weight": -1}
            ],
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {stability_api_key}",
        }

        response = requests.post(url, headers=headers, json=body)

        if response.status_code != 200:
            print(f"Error: {response.status_code}, {response.text}")
            return None
        else:
            data = response.json()
            images = []
            for image in data["artifacts"]:
                image_path = f'./images/{image_id}_{len(images)}.png'  # Update naming to prevent overwrite
                with open(image_path, "wb") as f:
                    f.write(base64.b64decode(image["base64"]))
                images.append(image_path)
            return {"images": images}
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def clear_images_directory(directory="./images"):
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
