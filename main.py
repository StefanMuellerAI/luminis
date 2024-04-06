import os
from openai import OpenAI
import tiktoken
import database as db
from PIL import Image
from dotenv import load_dotenv
import streamlit as st
import text2image as t2i
import speech2text as s2t
import text2speech as t2s
import fitz
import chromadb
import re
import hashlib
import chromadb.utils.embedding_functions as embedding_functions
import pandas as pd
import anthropic
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage

st.set_page_config(
    page_title="Luminis - KI-Labor und Lernplattform",
    page_icon="🥼🥽",
    layout="wide",
    initial_sidebar_state="expanded")

# Lädt Umgebungsvariablen aus einer .env-Datei
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

openai_client = OpenAI()
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
mistral_client = MistralClient(api_key=MISTRAL_API_KEY)
chroma_client = chromadb.EphemeralClient()


def generate_user_hash(request):
    browser = request.headers.get('User-Agent', '')
    ip = request.remote_addr
    os = request.headers.get('OS', '')

    hash_input = f"{browser}:{ip}:{os}"
    return hashlib.sha256(hash_input.encode()).hexdigest()

def hash_file_content(content):
    """Erzeugt einen SHA-256 Hash des Inhalts."""
    return hashlib.sha256(content.encode()).hexdigest()


def create_embedding(text):
    """Erzeugt einen Text-Embedding mit OpenAI's API."""
    response = openai_client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    embedding_vector = response.data[0].embedding
    return embedding_vector


def extract_text_from_pdf(pdf_file):
    """Extrahiert Text aus einer PDF-Datei."""
    text = ""
    with fitz.open(stream=pdf_file.getvalue()) as doc:
        for page in doc:
            text += page.get_text()
    return text


def tokenize_and_chunk_text(text, max_tokens_per_chunk):
    """
    Zerlegt den Text in Chunks, basierend auf der maximalen Anzahl von Tokens pro Chunk.
    """
    encoding = tiktoken.encoding_for_model("gpt-4-0125-preview")
    tokens = encoding.encode(text)

    # Aufteilen der Token-Liste in Chunks
    chunks = [tokens[i:i + max_tokens_per_chunk] for i in range(0, len(tokens), max_tokens_per_chunk)]

    # Konvertiere die Chunks von Token-Integers zurück in String-Form
    text_chunks = [encoding.decode(chunk) for chunk in chunks]

    return text_chunks


def add_document_to_collection(text, doc_id, hash_value, max_tokens_per_chunk, collection_description):
    """
    Erweiterte Funktion zum Hinzufügen eines Dokuments in Chunks zur Collection.
    """
    # Zuerst teilen wir den Text in Chunks.
    text_chunks = tokenize_and_chunk_text(text, max_tokens_per_chunk)

    # Für jeden Chunk fügen wir ihn zur Collection hinzu.
    for i, chunk in enumerate(text_chunks):
        embedding = create_embedding(chunk)
        chunk_id = f"{doc_id}_{i}"  # Erzeuge eine eindeutige ID für jeden Chunk basierend auf der doc_id und der Reihenfolge.
        collection.upsert(
            embeddings=[embedding],
            documents=[chunk],
            metadatas=[{"source": "user_uploaded_pdf", "hash": hash_value, "describtion": collection_description, "chunk_id": chunk_id}],
            ids=[chunk_id]
        )


def clean_collection_name(name):
    """Bereinigt den Namen der Collection für die Verwendung in einer Datenbank."""
    # Umlaute und das ß umwandeln
    umlaut_mapping = {
        'ä': 'ae',
        'ö': 'oe',
        'ü': 'ue',
        'Ä': 'Ae',
        'Ö': 'Oe',
        'Ü': 'Ue',
        'ß': 'ss'
    }
    for umlaut, replacement in umlaut_mapping.items():
        name = name.replace(umlaut, replacement)

    # Ersetzt alle nicht Wort-Zeichen durch Unterstriche
    cleaned_name = re.sub(r'\W+', '_', name)
    return cleaned_name


def list_collections():
    """Listet alle Collections auf (angepasst für deine ChromaDB-Implementierung)."""
    collections = chroma_client.list_collections()
    return [collection.name for collection in collections]

def collection_exists(collection_name):
    """Überprüft, ob eine bestimmte Collection existiert."""
    existing_collections = list_collections()
    return collection_name in existing_collections

def query_collection(query, collection_name, number_of_results=3):
    """Führt eine Abfrage auf der angegebenen Collection durch."""
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=OPENAI_API_KEY,
        model_name="text-embedding-3-small"
    )

    try:
        collection = chroma_client.get_collection(name=collection_name, embedding_function=openai_ef)
        results = collection.query(
            query_texts=[query],
            n_results=number_of_results,
            include=["embeddings", "documents", "metadatas", "distances"]
        )
    except Exception as e:
        print(f"Ein Fehler ist aufgetreten: {e}")
        results = {"documents": [""]}
    return results

with st.sidebar:
    st.image("luminis_logo.png", width=300)

    sidebar_options1 = [
        "Text2Text",
        "Text2Image",
        "Text2Speech",
        "Speech2Text",
        "Dokumenten-Sammlungen",
        "Experten",
    ]

    page = st.sidebar.selectbox("Navigation zu den Modulen:", sidebar_options1)
    st.divider()
    st.warning("Bitte beachten Sie, dass dies eine Schulungs- und Testumgebung ist, die Verwendung von personenbezogenen Informationen sowie internen Dokumenten ist strengstens untersagt. Arbeitsergebnisse werden nicht gespeichert und sind nicht zur produktiven Nutzung freigegeben. Dieses KI-Labor ist direkt an die amerikanischen Server von openai und stability.ai angeschlossen. Daten werden übermittelt.")
    st.divider()
    st.info("Kontaktdaten: support@stefanai.de bei Fehlern, Fragen und Anregungen. Reaktionszeit: Nächster Werktag. Mo-Fr. 8-18 Uhr")

if page == "Dokumenten-Sammlungen":
    st.title("Dokumenten-Sammlungen erstellen oder löschen.")
    collection_name = st.text_input("Dokumenten-Sammlung benennen:")
    collection_describtion = st.text_area("Dokumenten-Sammlung beschreiben:")
    chunk_size = st.slider('Chunk-Size festlegen:', 256, 2048, 512, help='In wie kleine Stücke soll der Inhalt zur Vektorisierung zerlegt werden? Wenn die Zahl zu klein ist, geht Sinn verloren. Wenn sie zu groß ist, könnte das Context-Fenster des LLM überschritten werden.')
    # PDF-Upload für mehrere Dateien
    uploaded_files = st.file_uploader("PDF-Dateien hochladen:", type=["pdf"], accept_multiple_files=True)

    # Button, um den Prozess zu starten
    if st.button("Zur Sammlung hinzufügen oder hinzufügen!"):
        cleaned_collection_name = clean_collection_name(collection_name)
        collection = chroma_client.get_or_create_collection(name=cleaned_collection_name)

        if uploaded_files and collection_name:
            for doc_id, uploaded_file in enumerate(uploaded_files, start=1):
                text = extract_text_from_pdf(uploaded_file)
                if text:
                    hash_value = hash_file_content(text)
                    add_document_to_collection(text, doc_id, hash_value, chunk_size, collection_describtion)
                    st.success(f"Dokument {doc_id} erfolgreich zur Sammlung hinzugefügt oder ergänzt.")
                else:
                    st.error(f"Die PDF-Datei {doc_id} scheint keinen Text zu enthalten.")
        else:
            st.error(
                "Bitte geben Sie einen Namen für die Sammlung vergeben und laden Sie mindestens eine PDF-Datei hoch.")

    # Abschnitt für das Löschen von Collections
    st.write("## Dokumenten-Sammlung löschen")
    delete_collection_name = st.selectbox("Wählen Sie eine Dokumenten-Sammlung aus:", list_collections())
    if st.button("Bestehende Sammlung löschen!"):
        if delete_collection_name:
            chroma_client.delete_collection(name=delete_collection_name)
            st.success(f"Sammlung '{delete_collection_name}' wurde erfolgreich gelöscht.")

elif page == "Text2Text":
    st.title("Text2Text")
    st.subheader("Interagieren Sie mit der KI und erhalten Sie Antworten auf Ihre Fragen.")

    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

    with col1:
        st.session_state.response_tokens = st.slider('Maximale Ausgabe:', 0, 4000, 1000)
    with col2:
        st.session_state.temperature = st.slider('Kreativität:', 0, 100, 70, help="Gemessen in Tokens, ca. 1,7 Token pro Wort")
        st.session_state.temperature /= 100
    with col3:
        st.session_state.primer = "None"
        st.session_state.role_names = db.get_role_names()
        st.session_state.selected_role_name = st.selectbox(
            "Wählen Sie den Experten:",
            st.session_state.role_names,
            placeholder="Wähle Rollenbeschreibung",
            index=0
        )
        if st.session_state.selected_role_name:
            st.session_state.primer = db.get_description_by_name(st.session_state.selected_role_name)
            st.session_state.aimodel = db.get_aimodel_by_name(st.session_state.selected_role_name)
            st.session_state["ai_model"] = st.session_state.aimodel
    with col4:
        st.session_state.collection_to_talk = st.selectbox(
            "Wählen Sie eine Dokumenten-Sammlung:",
            options=["Keine"]+list_collections(),
            index=0)

    st.divider()

    if "ai_model" not in st.session_state:
        st.session_state["ai_model"] = "gpt-4-0125-preview"

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if prompt := st.chat_input("Stellen Sie eine Frage oder geben Sie eine Anweisung..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            results = query_collection(prompt, st.session_state.collection_to_talk)
            context = "\n".join(results["documents"][0])
            if st.session_state["ai_model"] == "gpt-4-0125-preview":
                st.session_state.messages.append({"role": "system", "content": st.session_state.primer})
                stream = openai_client.chat.completions.create(
                    model="gpt-4-0125-preview",
                    messages=[
                        {"role": m["role"], "content": m["content"] + context}
                        for m in st.session_state.messages
                    ],
                    stream=True,
                    temperature=st.session_state.temperature,
                    max_tokens=st.session_state.response_tokens,
                )
                response = st.write_stream(stream)
            elif st.session_state["ai_model"] == "claude-3-opus-20240229":
                with anthropic_client.messages.stream(
                    model="claude-3-opus-20240229",
                    system=st.session_state.primer,
                    messages=[
                        {"role": m["role"], "content": m["content"] + context}
                        for m in st.session_state.messages if m["role"] != "system"
                    ],
                    temperature=st.session_state.temperature,
                    max_tokens=st.session_state.response_tokens,
                ) as stream:
                    response_container = st.empty()
                    response = ""
                    for text in stream.text_stream:
                        response += text
                        response_container.write(response)
            elif st.session_state["ai_model"] == "mistral-large-latest":
                st.session_state.messages.append({"role": "system", "content": st.session_state.primer})
                stream_response = mistral_client.chat_stream(
                    model="mistral-large-latest",
                    messages=[
                        {"role": m["role"], "content": m["content"] + context}
                        for m in st.session_state.messages
                    ],
                    temperature=st.session_state.temperature,
                    max_tokens=st.session_state.response_tokens,
                )
                response_container = st.empty()
                response = ""
                for text in stream_response:
                    response += text.choices[0].delta.content
                    response_container.write(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

elif page == "Experten":
    # Streamlit UI

    st.title('Experten Verwaltung')
    st.subheader('Gib der KI verschiedene Rollen, um mit ihr besser zu interagieren.')
    # Eingabefelder
    with st.form("role_form", clear_on_submit=True):
        ai_model = st.selectbox('KI-Modell:', ['gpt-4-0125-preview', 'claude-3-opus-20240229', 'mistral-large-latest'],
                                help='Welches KI-Modell soll für diese Rolle verwendet werden?')
        name = st.text_input('Expertenname:', '', help='Wie soll der Experte heißen?')

        description = st.text_area('Beschreibung des Experten:', '', max_chars=1000, help='Beschreibe die Rolle des Experten. Wenn der Chatbot mit Claude-3 läuft, kann diese Beschreibung länger ausfallen.')
        submitted = st.form_submit_button('Experten speichern')
        if submitted:
            if db.role_name_exists(name):
                st.error('Es gibt bereits eine Rolle mit diesem Namen.')
            else:
                if len(description) < 50:
                    st.error('Die Beschreibung muss minimal 50 Zeichen lang sein.')
                db.insert_role(name, description, ai_model)

    # Rollenliste
    st.subheader('Vorhandene Experten')
    roles = db.get_all_roles()
    roles_df = pd.DataFrame(roles, columns=['id', 'Name', 'Beschreibung', 'KI-Modell'])
    st.dataframe(roles_df[['id', 'Name', 'Beschreibung', 'KI-Modell']], hide_index=True)

    # Rolle bearbeiten oder löschen

elif page == "Speech2Text":
    st.title('Speech2Text')
    st.subheader('Transkribieren Sie Podcasts oder Sprachaufnahmen.')
    uploaded_file = st.file_uploader("Laden Sie hier Ihre MP3 hoch:", type="mp3")

    if st.button('Transkription starten!'):
        if uploaded_file is not None:
            file_path = s2t.save_uploaded_file(uploaded_file)
            if file_path:
                with st.spinner('Transkription läuft...'):
                    full_text = s2t.transcribe_podcast_faster(file_path)
                    st.success('Transkription abgeschlossen!')

                st.code(full_text, language="python")
            else:
                st.error("Fehler beim Hochladen der Datei.")
        else:
            st.warning("Bitte lade eine MP3-Datei hoch.")

elif page == "Text2Image":
    st.title('Text2Image')
    st.markdown('Generieren Sie Bilder aus Textbeschreibungen.')
    st.subheader('Möglichkeit: Dall-e 3')
    # Spalten für Layout
    col1, col2 = st.columns([1, 1])
    # Im ersten Spaltenblock
    with col1:
        dalle_description = st.text_area('Bildbeschreibung DALL-e 3:', "Ein sonniger Tag am Strand")
        dalle_size = st.selectbox('Bildauflösung wählen:', ['1024x1024', '1024x1792', '1792x1024'])
        if st.button('Bild generieren!'):
            with col2:
                with st.spinner('Bild wird generiert...'):
                # Aufruf der DALL-E-Funktion
                    try:
                        image_url = t2i.create_dalle_image(dalle_description, dalle_size)
                        with st.container(border=True):
                            if 'image_url' in locals():
                                st.image(image_url, caption=f'Symbolbild: {dalle_description}', use_column_width=True)
                    except Exception as e:
                        st.error(f'Sorry, die Content-Filterung von Openai.com hat die Bildbeschreibung abgelehnt. Vermutlich weil sie anstößig ist.')

    # Streamlit UI
    st.subheader('Möglichkeit 2: Stability AI')
    col1, col2 = st.columns([1, 1])
    # Benutzereingaben
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
                    # Hier nehme ich an, dass `create_stability_image` eine Funktion deiner Klasse oder deines Moduls `t2i` ist.
                    result = t2i.create_stability_image(stability_description, stability_anti_description, stability_steps, stability_style_preset, stability_size, stability_cfg_scale)
                    try:
                        images = result.get("images", [])
                        if images:
                            for img_path in images:
                                img = Image.open(img_path)  # Das Bild wird hier direkt gelesen.
                                st.image(img, caption=f"Symbolbild: {stability_description}", use_column_width=True)  # Und dann an `st.image` übergeben.
                                t2i.clear_images_directory()
                    except Exception as e:
                        st.error("Sorry, die Content-Filterung von Stability AI hat die Bildbeschreibung abgelehnt. Vermutlich weil sie anstößig ist.")

elif page == "Text2Speech":
    # Streamlit UI
    st.title("Text2Speech")
    st.subheader("Konvertieren Sie Ihren Text in eine Sprachausgabe.")

    # Eingabefeld für den Text
    user_input = st.text_area("Geben Sie hier Ihren Text ein:", "Hallo Welt!")
    voice = st.selectbox("Wählen Sie eine Stimme:", ["alloy", "echo", "fable", "onyx", "nova", "shimmer"])

    # Button zur Generierung der Sprachausgabe
    if st.button("Sprachausgabe generieren!"):
        with st.spinner('Generiere Sprachausgabe...'):
            speech_path = t2s.create_speech_from_text(user_input, voice)
            if speech_path.is_file():
                st.audio(str(speech_path), format='audio/mp3')
                t2s.clear_speech_directory()
            else:
                st.error("Ein Fehler ist aufgetreten. Die Sprachdatei konnte nicht erstellt werden.")




