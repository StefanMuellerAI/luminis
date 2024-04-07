import os
from openai import OpenAI
from PIL import Image
from dotenv import load_dotenv
import streamlit as st
import random
import base64
import requests
from home import add_menu


load_dotenv()

client_openai = OpenAI()
stability_api_key = os.getenv("STABILITY_API_KEY")

st.set_page_config(
    page_title="Luminis - KI-Labor und Lernplattform",
    page_icon="🥼",
    layout="wide",
    initial_sidebar_state="expanded"
)
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
        return image_url
    except Exception as e:
        return None


def create_stability_image(description, anti_description, steps, style_preset, size, cfg_scale):
    if not os.path.exists("../images"):
        os.makedirs("../images")
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

st.title('Text2Image')
st.subheader('Bilderstellung mit Dall-E 3')
col1, col2 = st.columns([1, 1])
with col1:
    dalle_description = st.text_area('Bildbeschreibung DALL-e 3:', "Ein sonniger Tag am Strand")
    dalle_size = st.selectbox('Bildauflösung wählen:', ['1024x1024', '1024x1792', '1792x1024'])
    if st.button('Bild generieren!'):
        with col2:
            with st.spinner('Bild wird generiert...'):
                try:
                    image_url = create_dalle_image(dalle_description, dalle_size)
                    with st.container(border=True):
                        if 'image_url' in locals():
                            st.image(image_url, caption=f'Symbolbild: {dalle_description}', use_column_width=True)
                except Exception as e:
                    st.error(f'Sorry, die Content-Filterung von Openai.com hat die Bildbeschreibung abgelehnt. Vermutlich weil sie anstößig ist.')

    # Streamlit UI
st.subheader('Bilderstellung mit Stability AI')
col1, col2 = st.columns([1, 1])
with col1:
    stability_description = st.text_area("Bildbeschreibung Stability AI:", "Ein sonniger Tag am Strand")
    stability_anti_description = st.text_input("Was nicht im Bild sein soll:", "None")
    stability_steps = st.slider("Arbeitsschritte:", 1, 40, 20)
    stability_style_preset = st.selectbox("Bildart wählen:", ["analog-film", "anime", "cinematic", "comic-book", "digital-art", "enhance", "fantasy-art", "isometric", "line-art", "low-poly", "modeling-compound", "neon-punk", "origami", "photographic", "pixel-art", "tile-texture"])
    stability_size = st.selectbox("Bildauflösung wählen:", ["1024x1024", "1152x896", "1216x832", "1344x768", "1536x640", "640x1536", "768x1344", "832x1216", "896x1152"])
    stability_cfg_scale = st.slider("Kreativität:", 1, 8, 7)

    if st.button("Bild generieren"):
           with col2:
               with st.spinner('Bild wird generiert...'):
                   result = create_stability_image(stability_description, stability_anti_description, stability_steps, stability_style_preset, stability_size, stability_cfg_scale)
                   try:
                       images = result.get("images", [])
                       if images:
                           for img_path in images:
                               img = Image.open(img_path)  # Das Bild wird hier direkt gelesen.
                               st.image(img, caption=f"Symbolbild: {stability_description}", use_column_width=True)
                       clear_images_directory()
                   except Exception as e:
                        st.error("Sorry, die Content-Filterung von Stability AI hat die Bildbeschreibung abgelehnt. Vermutlich weil sie anstößig ist.")

add_menu()


